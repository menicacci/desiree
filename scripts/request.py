import os
import json
import time
import shutil
from openai.lib.azure import AzureOpenAI
from requests.exceptions import ReadTimeout
from scripts import utils, table, stats, prompt as p_utils
from scripts.constants import Constants
import concurrent.futures


def extract_infos(json_file_path) -> dict:
    with open(json_file_path, 'r') as file:
        return json.load(file)


def init_client(infos: dict):
    client = AzureOpenAI(
        azure_endpoint=infos['azure_endpoint'],
        api_key=infos['api_key'],
        api_version=infos['api_version']
    )

    return client


def send_request(client, prompt: dict, model="gpt-4-32k", max_tokens=16000):
    start_time = time.time()

    with client.chat.completions.with_streaming_response.create(
            model=model,
            max_tokens=8000,
            temperature=0,
            stream=True,
            messages=prompt,
    ) as response:
        answer = ''
        current_answer = ''
        output_tokens = 0
        stream = ''

        for line in response.iter_lines():

            stream += line + '\n'

            if len(line) > 0:
                output_tokens += 1
                line = line.replace('data: ', '')
                if line == '[DONE]':
                    break
                json_line = json.loads(line)
                if len(json_line['choices']) > 0 and json_line['choices'][0] is not None and json_line['choices'][0][
                    'delta'] is not None and len(json_line['choices'][0]['delta']) > 0 and \
                        json_line['choices'][0]['delta'][
                            'content'] is not None:
                    current_token = json_line['choices'][0]['delta']['content']
                    # answer += json_line['choices'][0]['delta']['content']
                    answer += current_token
                    current_answer += current_token
                    if '\n' in current_token:
                        print(current_answer)
                        current_answer = ''
    request_time = time.time() - start_time

    return answer, output_tokens, request_time, stream


def save_answer_and_stats(answer, input_tokens, output_tokens, request_time, stream, file_name, output_folder):
    file_name_txt = file_name + '.txt'

    # Save answer
    output_answers_folder = os.path.join(output_folder, Constants.Directories.LLM_ANSWER)
    utils.check_path(output_answers_folder)
    save_path = os.path.join(output_answers_folder, file_name_txt)

    with open(save_path, "w") as text_file:
        text_file.write(answer.encode('ascii', 'ignore').decode())
    print(f"\t Saved answer at: {save_path}")

    # Save stats
    article_id, table_idx = utils.split_table_string(file_name)

    data_to_save = [article_id, table_idx, input_tokens, output_tokens, request_time, stream]
    data_dict = {attr: val for attr, val in zip(Constants.ColumnHeaders.STATS_HEADER_STRUCTURE, data_to_save)}

    stats_path = os.path.join(output_folder, Constants.Directories.STATS, file_name + ".json")
    utils.write_json(data_dict, stats_path)


def set_up_test_dir(output_path: str, tables_path: str, msgs_path: dict):
    if utils.check_path(output_path):
        return None

    test_info = {}
    test_info[Constants.Attributes.MESSAGES_PATH] = msgs_path
    test_info[Constants.Attributes.TABLES_PATH] = tables_path
    test_info[Constants.Attributes.NUM_TABLE] = table.reset_processed_tables(tables_path)    

    utils.write_json(test_info, os.path.join(output_path, Constants.Filenames.TEST_INFO))


def get_test_info(output_path: str):
    if not os.path.exists(output_path):
        return None
    
    test_info = utils.load_json(os.path.join(output_path, Constants.Filenames.TEST_INFO))
    test_info[Constants.Attributes.TEST_IDX] = utils.get_test_path(output_path)

    return test_info


def extract_claims(client, article_table, file_name, messages_file_paths, output_folder, save_prompt=True):
    prompt, input_tokens = p_utils.build(article_table, messages_file_paths)

    if save_prompt:
        # For replication purposes
        output_prompts_folder = os.path.join(output_folder, Constants.Directories.OUTPUT)
        utils.check_path(output_prompts_folder)

        file_name_txt = file_name + '.txt'
        with open(os.path.join(output_prompts_folder, file_name_txt), "w") as text_file:
            text_file.write(json.dumps(prompt))
        print(f"\t Saved prompt at: {os.path.join(output_prompts_folder, file_name_txt)}")

    print(f"Sending request for: [{file_name}]")
    for attempt in range(2):
        try:
            answer, output_tokens, request_time, stream = send_request(client, prompt)
            break
        except ReadTimeout:
            print(f"ReadTimeout occurred. Retrying... Attempt")
    else:
        print("All retry attempts failed. Handle the error or raise it again.")
        return

    save_answer_and_stats(answer, input_tokens, output_tokens, request_time, stream, file_name, output_folder)


def process_tables(connection_info: dict, test_info: dict, max_cycles: int, num_thread: int):
    table_processed = 0
    cycle = 0
    answer_path = os.path.join(test_info[Constants.Attributes.TEST_IDX], Constants.Directories.LLM_ANSWER)
    tables_to_process = table.check_processed_tables(test_info[Constants.Attributes.TABLES_PATH], answer_path)
    while tables_to_process > 0 and cycle < max_cycles:
        tables = table.load_tables_from_json(test_info[Constants.Attributes.TABLES_PATH])

        it_num_thread = min(num_thread, tables_to_process)
        table_processed += it_num_thread
        parallel_excecution(
            connection_info, 
            messages_file_paths=test_info[Constants.Attributes.MESSAGES_PATH], 
            articles_tables=tables, 
            output_path=test_info[Constants.Attributes.TEST_IDX], 
            num_threads=it_num_thread
        )

        tables_to_process = table.check_processed_tables(test_info[Constants.Attributes.TABLES_PATH], answer_path)
        cycle += 1

    stats.save_stats(test_info[Constants.Attributes.TEST_IDX])
    return {
        Constants.Attributes.CYCLES: cycle,
        Constants.Attributes.TABLE_PROC: table_processed,
        Constants.Attributes.TABLES_TO_PROC: tables_to_process
    }


def parallel_excecution(connection_data: dict, messages_file_paths: dict, articles_tables: dict, output_path: str, num_threads: int):
    clients = [init_client(connection_data) for _ in range(num_threads)]

    p_utils.save(messages_file_paths, output_path)

    progress = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        for article_id, article_tables in articles_tables.items():
            for index, article_table in enumerate(article_tables):
                if not article_table[Constants.Attributes.PROCESSED]:
                    executor.submit(
                        extract_claims,
                        clients[progress % num_threads],
                        article_table,
                        f"{article_id}_{index}",
                        messages_file_paths,
                        output_path
                    )

                    progress += 1

    for client in clients:
        client.close()


def run_test(connection_info: dict, test_info: dict, num_thread: int, max_cycles: int):
    test_dir = test_info[Constants.Attributes.TEST_IDX]
    utils.check_path(test_dir)
    utils.check_path(os.path.join(test_dir, Constants.Directories.STATS))

    table.reset_processed_tables(test_info[Constants.Attributes.TABLES_PATH])
    return process_tables(connection_info, test_info, max_cycles, num_thread)
    

def repeat_test(connection_info: dict, output_path: str, test_idx: int, num_thread: int, max_cycles: int, ovveride=False):
    test_dir = os.path.join(output_path, str(test_idx))
    if not os.path.exists(test_dir):
        return None

    temp_dir = os.path.join(test_dir, Constants.Directories.TEMP)
    os.makedirs(temp_dir, exist_ok=True)

    test_info = get_test_info(output_path)

    # copy prompt properties
    original_msgs_path = os.path.join(test_info[Constants.Attributes.MESSAGES_PATH], Constants.Filenames.MSG_INFO)
    shutil.copy(original_msgs_path, temp_dir)

    test_info[Constants.Attributes.TEST_IDX] = test_dir
    test_info[Constants.Attributes.MESSAGES_PATH] = temp_dir 

    original_prompt = p_utils.read(os.path.join(test_dir, Constants.Filenames.PROMPT))
    p_utils.write(original_prompt, temp_dir)

    run_data = process_tables(connection_info, test_info, max_cycles, num_thread)

    shutil.rmtree(temp_dir)
    return run_data
    