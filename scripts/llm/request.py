# code inspired from: @mahmoudhage21

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
from scripts.llm.constants import LlmConstants
from scripts.llm import prompt, llm_utils


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
        estimated_tokens = prompt.num_tokens_request_approx(system_user_message)
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
                utils.write_file(generated_response, save_path)

                request_time = time.time() - start_time
                self.input_token_count += response.usage.prompt_tokens
                self.output_token_count += response.usage.completion_tokens

                model_response = llm_utils.object_to_dict(response)
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

    
    def run(self, messages_dict, directory_path: str):
        (answers_dir, output_dir, stats_dir) = llm_utils.get_req_directories(directory_path)

        request_results = []
        api_original_prompts = []
        
        start_time = time.time()
        req_ovr_counter = 0
        req_exc_counter = 0

        with ThreadPoolExecutor(max_workers=self.request_rate_limit) as executor:
            future_to_info = {
                executor.submit(
                    self.send, 
                    item[LlmConstants.Attributes.API_MSG],
                    os.path.join(answers_dir, f"{item[LlmConstants.Attributes.REQ_ID]}.txt")
                ): item for item in messages_dict
            }
            
            for future in as_completed(future_to_info):
                output = future_to_info[future]
                req_id = {LlmConstants.Attributes.REQ_ID: output[LlmConstants.Attributes.REQ_ID]}

                req_ovr_counter += 1
                try:
                    result = {key: value for key, value in future.result().items()}
                    result.update(req_id)
                    result.update({LlmConstants.Attributes.REQ_SUCCESSFUL: True})

                    request_results.append(result)
                    api_original_prompts.append(output)

                except Exception as e:
                    req_exc_counter += 1

                    result = {LlmConstants.Attributes.REQ_ID: future_to_info[future][LlmConstants.Attributes.REQ_ID]}
                    result.update({"response": f"Error processing message: {str(e)}"})
                    result.update({LlmConstants.Attributes.REQ_SUCCESSFUL: True})
                    request_results.append(result)
                
        llm_utils.save_results(stats_dir, request_results)
        llm_utils.save_results(output_dir, api_original_prompts)

        elapsed_time = time.time() - start_time
        hours, remainder = divmod(elapsed_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_taken = f"{int(hours)}:{int(minutes)}:{int(seconds)}"

        return {
            LlmConstants.Attributes.REQ_RESULTS: request_results,
            LlmConstants.Attributes.REQ_OVR_TIME: time_taken,
            LlmConstants.Attributes.REQ_OVR_COUNT: req_ovr_counter,
            LlmConstants.Attributes.REQ_EXC_COUNT: req_exc_counter
        }
