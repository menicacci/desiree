import os
import time
import json
import threading
from pydantic import BaseModel
from threading import Semaphore
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_fixed, wait_random
from scripts import utils
from scripts.constants import Constants
from scripts.llm.llm_constants import LlmConstants
from scripts.llm import llm_prompt, llm_utils, llm_stats
from scripts.table.table_prompt import TablePrompts

# code inspired from: @mahmoudhage21

class ParallelAPIRequesterConfig(BaseModel):
    model: str
    max_tokens: int = 8000
    temperature: Optional[float] = 0
    request_rate_limit_per_minute: Optional[int] = 50
    token_rate_limit_per_minute: Optional[int] = 7500
    check_Intent_keys_and_values: Optional[bool] = False


class TokenSemaphore:
    def __init__(self, max_tokens):
        self.tokens = max_tokens
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def acquire(self, required_tokens):
        with self.lock:
            while self.tokens < required_tokens:
                self.condition.wait()
            self.tokens -= required_tokens

    def release(self, released_tokens):
        with self.lock:
            self.tokens += released_tokens
            self.condition.notify_all()


class ParallelAPIRequester:
    def __init__(self,
                 connection_info_path: str,
                 configuration_path: str):
        client_info = utils.load_json(connection_info_path)

        config_data = utils.load_json(configuration_path)
        config = ParallelAPIRequesterConfig(**config_data)

        self.model = config.model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature

        self.request_rate_limit = config.request_rate_limit_per_minute
        self.request_semaphore = Semaphore(self.request_rate_limit)
        self.token_rate_limit = config.token_rate_limit_per_minute
        self.token_semaphore = TokenSemaphore(self.token_rate_limit)

        self.input_token_count = 0
        self.output_token_count = 0

        self.client = AzureOpenAI(
            azure_endpoint=client_info[LlmConstants.Attributes.AZURE_EP],
            api_key=client_info[LlmConstants.Attributes.API_KEY],
            api_version=client_info[LlmConstants.Attributes.API_V]
        )


    def handle_last_retry_error(retry_state):
        print(f"All retry attempts failed for: {retry_state.args[0]}\nReturning None for this request.")
        return


    @retry(wait=wait_fixed(2) + wait_random(10, 20),
            stop=stop_after_attempt(2),
            before_sleep= lambda retry_state: print("Retrying..."),
            retry_error_callback=handle_last_retry_error)
    def send(self, system_user_message: List, save_path: str):
        estimated_tokens = llm_prompt.num_tokens_request_approx(system_user_message)
        if estimated_tokens >= self.max_tokens:
            raise Exception("Max Tokens limit reached")

        self.request_semaphore.acquire()
        
        start_time = time.time()
        try:
            self.token_semaphore.acquire(estimated_tokens)
            try:
                print(f"Sending request for: {os.path.basename(save_path)}")

                response = self.client.chat.completions.create(
                            model=self.model,
                            messages=system_user_message,
                            temperature=self.temperature,
                            max_tokens=self.max_tokens,
                            response_format=None,
                        )
                
                generated_response = response.choices[0].message.content
                llm_utils.save_answer(save_path, generated_response)

                request_time = time.time() - start_time
                self.input_token_count += response.usage.prompt_tokens
                self.output_token_count += response.usage.completion_tokens

                model_response = utils.object_to_dict(response)
                request_info = {
                    LlmConstants.Attributes.REQ_TIME: request_time,
                    LlmConstants.Attributes.INP_TOKS: response.usage.prompt_tokens,
                    LlmConstants.Attributes.OUT_TOKS: response.usage.completion_tokens,
                }

                return {
                    LlmConstants.Attributes.MODEL_RESPONSE: model_response,
                    LlmConstants.Attributes.REQ_INFO: request_info
                }
            except json.JSONDecodeError:
                print(f"Invalid JSON response for message {system_user_message}")
                raise
            except Exception as e:
                print(f"Error while processing: {str(e)}")
                raise
            finally:
                self.token_semaphore.release(estimated_tokens)
        finally:
            self.request_semaphore.release()
            time.sleep(60 / self.request_rate_limit)

    
    def run(self, request_path: str, prompts: list):
        # Get the directories to save the request data
        (answers_dir, output_dir, stats_dir) = llm_utils.get_req_directories(request_path)

        start_time = time.time()
        req_ovr_counter = 0
        req_exc_counter = 0
        with ThreadPoolExecutor(max_workers=self.request_rate_limit) as executor:
            future_to_info = {
                executor.submit(
                    self.send, 
                    item[LlmConstants.Attributes.API_MSG],
                    os.path.join(answers_dir, f"{item[LlmConstants.Attributes.REQ_ID]}")
                ): item for item in prompts
            }
            
            for future in as_completed(future_to_info):
                output = future_to_info[future]
                req_id = {LlmConstants.Attributes.REQ_ID: output[LlmConstants.Attributes.REQ_ID]}

                req_ovr_counter += 1
                try:
                    result = {key: value for key, value in future.result().items()}
                    result.update(req_id)
                    result.update({LlmConstants.Attributes.REQ_SUCCESSFUL: True})

                    llm_utils.save_result(output_dir, output)
                    llm_utils.save_result(stats_dir, result)

                except Exception as e:
                    req_exc_counter += 1

                    result = {
                        LlmConstants.Attributes.REQ_ID: future_to_info[future][LlmConstants.Attributes.REQ_ID]
                    }
                    result.update({"response": f"Error processing message: {str(e)}"})
                    result.update({LlmConstants.Attributes.REQ_SUCCESSFUL: False})
                    
                    llm_utils.save_result(stats_dir, result)

        elapsed_time = time.time() - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_taken = f"{int(hours)}:{int(minutes)}:{int(seconds)}"

        llm_stats.save(request_path)

        return {
            LlmConstants.Attributes.REQ_OVR_TIME: time_taken,
            LlmConstants.Attributes.REQ_OVR_COUNT: req_ovr_counter,
            LlmConstants.Attributes.REQ_EXC_COUNT: req_exc_counter
        }


class Executor:
    def __init__(self, 
                 output_dir: str, 
                 tables_file_name: str, 
                 msgs_dir: str,
                 request_type: str = LlmConstants.PromptTypes.TABLE,
                 connection_info_path: str = Constants.CONNECTION_INFO_STANDARD, 
                 request_conf_path: str = Constants.REQUEST_CONF_STANDARD):

        self.output_path = utils.get_abs_path(output_dir, Constants.OUTPUT_PATH, False)
        self.tables_file_path = utils.get_abs_path(tables_file_name, Constants.EXTRACTED_TABLES_PATH)
        self.msgs_path = utils.get_abs_path(msgs_dir, Constants.MESSAGES_PATH)

        self.prompts = []
        self.results = []

        if request_type == LlmConstants.PromptTypes.TABLE:
            self.prompt_gen = TablePrompts(self.output_path, self.tables_file_path, self.msgs_path)
        else:
            raise ValueError("Only TablePrompt supported right now")
        
        self.llm = ParallelAPIRequester(connection_info_path, request_conf_path)


    def prepare(self, check_processed: bool = False, override: bool = False):
        self.prompts = self.prompt_gen.generate(check_processed, override)


    def execute(self):
        self.results = self.llm.run(self.output_path, self.prompts)
