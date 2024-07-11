import tiktoken
import os
import json
import time
from openai.lib.azure import AzureOpenAI
from requests.exceptions import ReadTimeout
from scripts import utils, table, stats
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


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-4")
    num_tokens = len(encoding.encode(string))

    return num_tokens


def message(role, content) -> dict:
    return {"role": role, "content": content}


def read_file(absolute_path):
    with open(absolute_path) as file:
        return file.read()
    

def replace_placeholder(content, placeholder, value):
    placeholder = f"{placeholder}"
    return content.replace(placeholder, value)


def build_user_message(message_path, prompt_data, html_prompt):
    content = read_file(message_path)

    if html_prompt:
        content = replace_placeholder(content, Constants.Attributes.HTML_TABLE, prompt_data)
    else:
        content = replace_placeholder(content, Constants.Attributes.CAPTION, prompt_data[Constants.Attributes.CAPTION])
        content = replace_placeholder(content, Constants.Attributes.CITATION, prompt_data[Constants.Attributes.CITATION])
    
    return content
        


def build_messages(messages_file_path, prompt_data, html_prompt):
    content_system_1 = read_file(messages_file_path['system_1'])
    content_user_1 = read_file(messages_file_path['user_1'])
    content_assistant = read_file(messages_file_path['assistant'])
    content_user_2 = build_user_message(messages_file_path['user_2'], prompt_data, html_prompt)
    content_system_2 = read_file(messages_file_path['system_2'])

    messages_dict = [
        message("system", content_system_1),
        message("user", content_user_1),
        message("assistant", content_assistant),
        message("user", content_user_2),
        message("system", content_system_2)
    ]

    # number of input tokens
    input_tokens = num_tokens_from_string(
        content_system_1 + content_user_1 + content_assistant + content_user_2 + content_system_2)

    return messages_dict, input_tokens


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


def set_up_test_dir(project_path: str, dir_name: str, tables_file: str, msgs_dir: dict):
    experiments_path = os.path.join(project_path, Constants.Directories.EXPERIMENTS)
    
    output_path = os.path.join(experiments_path, Constants.Directories.OUTPUT, dir_name)
    if utils.check_path(output_path):
        return

    tables_file_path = os.path.join(experiments_path, Constants.Directories.EXTRACTED_TABLE, tables_file)
    
    msgs_base_path = os.path.join(project_path, Constants.Directories.MESSAGES, msgs_dir)

    msgs_file_path = {
        Constants.Roles.SYSTEM_1:  f'{msgs_base_path}/{Constants.Roles.SYSTEM_1}.txt',
        Constants.Roles.SYSTEM_2:  f'{msgs_base_path}/{Constants.Roles.SYSTEM_2}.txt',
        Constants.Roles.USER_1:    f'{msgs_base_path}/{Constants.Roles.USER_1}.txt',
        Constants.Roles.USER_2:    f'{msgs_base_path}/{Constants.Roles.USER_2}.txt',
        Constants.Roles.ASSISTANT: f'{msgs_base_path}/{Constants.Roles.ASSISTANT}.txt'
    }

    test_info = {}

    test_info[Constants.Attributes.MESSAGES_PATH] = msgs_file_path
    test_info[Constants.Attributes.HTML_TABLE] = utils.load_json(os.path.join(msgs_base_path, Constants.Filenames.MSG_INFO))[Constants.Attributes.HTML_TABLE]
    test_info[Constants.Attributes.TABLES_PATH] = tables_file_path
    test_info[Constants.Attributes.NUM_TABLE] = table.reset_processed_tables(tables_file_path)    

    utils.write_json(test_info, os.path.join(output_path, Constants.Filenames.TEST_INFO))


def get_test_info(project_path: str, dir_name):
    experiments_path = os.path.join(project_path, Constants.Directories.EXPERIMENTS)

    output_path = os.path.join(experiments_path, Constants.Directories.OUTPUT, dir_name)
    if not utils.check_path(output_path):
        return None
    
    test_info = utils.load_json(os.path.join(output_path, Constants.Filenames.TEST_INFO))
    test_info[Constants.Attributes.TEST_IDX] = utils.get_test_path(output_path)

    return test_info


def build_prompt(article_table, messages_file_paths, html_prompt):
    if html_prompt:
        prompt_data = article_table[Constants.Attributes.TABLE].encode('ascii', 'ignore').decode()
    else:
        prompt_data = {
            Constants.Attributes.CAPTION: article_table[Constants.Attributes.CAPTION],
            Constants.Attributes.CITATION: article_table[Constants.Attributes.CITATIONS][0] if len(article_table[Constants.Attributes.CITATIONS]) > 0 else ""
        }

    return build_messages(messages_file_paths, prompt_data, html_prompt)


def extract_claims(client, article_table, file_name, messages_file_paths, output_folder, html_prompt=True, save_prompt=True):
    prompt, input_tokens = build_prompt(article_table, messages_file_paths, html_prompt)

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


def run(connection_data: dict, messages_file_paths: dict, articles_tables: dict, output_path: str, num_threads: int, html_prompt=True):
    clients = [init_client(connection_data) for _ in range(num_threads)]

    original_prompt = f'''
        SYSTEM 1: \n{read_file(messages_file_paths['system_1'])}\n\n
        USER 1:\n{read_file(messages_file_paths['user_1'])}\n\n
        ASSISTANT:\n{read_file(messages_file_paths['assistant'])}\n\n
        USER 2:\n{read_file(messages_file_paths['user_2'])}\n\n
        SYSTEM 2:\n{read_file(messages_file_paths['system_2'])}\n\n
    '''

    with open(os.path.join(output_path, 'prompt.txt'), "w") as text_file:
        text_file.write(original_prompt)

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
                        output_path,
                        html_prompt
                    )

                    progress += 1

    for client in clients:
        client.close()

    return


def run_test(connection_info: dict, test_info: dict, num_thread: int, max_cycles: int):
    test_dir = test_info[Constants.Attributes.TEST_IDX]
    utils.check_path(test_dir)
    
    stats_dir = os.path.join(test_dir, Constants.Directories.STATS)
    utils.check_path(stats_dir)

    table.reset_processed_tables(test_info[Constants.Attributes.TABLES_PATH])
    
    i = 0
    tables_to_process = 1000
    while tables_to_process > 0 and i < max_cycles:
        tables = table.load_tables_from_json(test_info[Constants.Attributes.TABLES_PATH])
        run(
            connection_info, 
            messages_file_paths=test_info[Constants.Attributes.MESSAGES_PATH], 
            articles_tables=tables, 
            output_path=test_info[Constants.Attributes.TEST_IDX], 
            num_threads=min(num_thread, tables_to_process), 
            html_prompt=test_info[Constants.Attributes.HTML_TABLE]
        )

        tables_to_process = table.check_processed_tables(test_info[Constants.Attributes.TABLES_PATH], os.path.join(test_info[Constants.Attributes.TEST_IDX], Constants.Directories.LLM_ANSWER))
        i += 1

    stats.save_stats(test_dir)
    
    return {
        Constants.Attributes.CYCLES: i,
        Constants.Attributes.TABLES_TO_PROC: tables_to_process
    }
    