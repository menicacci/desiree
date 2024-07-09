import tiktoken
import os
import json
import time
from openai.lib.azure import AzureOpenAI
from requests.exceptions import ReadTimeout
from scripts import utils, table
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
        content = replace_placeholder(content, Constants.HTML_TABLE_ATTR, prompt_data)
    else:
        content = replace_placeholder(content, Constants.CAPTION_ATTR, prompt_data[Constants.CAPTION_ATTR])
        content = replace_placeholder(content, Constants.CITATION_ATTR, prompt_data[Constants.CITATION_ATTR])
    
    return content
        


def build_messages(file_name, messages_file_path, prompt_data, output_prompts_folder, html_prompt):
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

    # save prompt for replication purposes
    file_name_txt = file_name + '.txt'
    with open(os.path.join(output_prompts_folder, file_name_txt), "w") as text_file:
        text_file.write(json.dumps(messages_dict))
    print(f"\t Saved prompt at: {os.path.join(output_prompts_folder, file_name_txt)}")

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


def save_answer_and_stats(answer, input_tokens, output_tokens, request_time, stream, file_name, output_answers_folder):
    file_name_txt = file_name + '.txt'
    with open(os.path.join(output_answers_folder, file_name_txt), "w") as text_file:
        text_file.write(answer.encode('ascii', 'ignore').decode())
    print(f"\t Saved answer at: {os.path.join(output_answers_folder, file_name_txt)}")

    '''
    data_dict = {"file_name": file_name, "input_tokens": input_tokens, "output_tokens": output_tokens, "request_time": request_time, "stream": stream}
    print(data_dict)
    df = pd.DataFrame([data_dict])
    with pd.ExcelWriter(os.path.join(output_stats_folder, stats_file), engine='openpyxl', if_sheet_exists="overlay", mode='a') as writer:
        df.to_excel(writer, sheet_name='main', startrow=writer.sheets['main'].max_row, index=False, header=False)

    print(f"\t Saved stats at: {os.path.join(output_stats_folder, stats_file)}")
    '''
    return


def set_up_test_dir(project_path: str, dir_name: str, tables_file: str, msgs_dir: dict, html_prompt: bool):
    experiments_path = os.path.join(project_path, Constants.EXPERIMENTS_DIR)
    
    output_path = os.path.join(experiments_path, Constants.OUTPUT_DIR, dir_name)
    if utils.check_path(output_path):
        return

    tables_file_path = os.path.join(experiments_path, Constants.EXTRACTED_TABLE_DIR, tables_file)
    
    msgs_base_path = os.path.join(project_path, Constants.MESSAGES_DIR, msgs_dir)

    msgs_file_path = {
        Constants.SYSTEM_1_ROLE:  f'{msgs_base_path}/{Constants.SYSTEM_1_ROLE}.txt',
        Constants.SYSTEM_2_ROLE:  f'{msgs_base_path}/{Constants.SYSTEM_2_ROLE}.txt',
        Constants.USER_1_ROLE:    f'{msgs_base_path}/{Constants.USER_1_ROLE}.txt',
        Constants.USER_2_ROLE:    f'{msgs_base_path}/{Constants.USER_2_ROLE}.txt',
        Constants.ASSISTANT_ROLE: f'{msgs_base_path}/{Constants.ASSISTANT_ROLE}.txt'
    }

    test_info = {}

    test_info[Constants.MESSAGES_PATH_ATTR] = msgs_file_path
    test_info[Constants.HTML_TABLE_ATTR] = html_prompt
    test_info[Constants.TABLES_PATH_ATTR] = tables_file_path
    test_info[Constants.NUM_TABLE_ATTR] = table.reset_processed_tables(tables_file_path)    

    utils.write_json(test_info, os.path.join(output_path, Constants.TEST_INFO_PATH))


def get_test_info(project_path: str, dir_name):
    experiments_path = os.path.join(project_path, Constants.EXPERIMENTS_DIR)

    output_path = os.path.join(experiments_path, Constants.OUTPUT_DIR, dir_name)
    if not utils.check_path(output_path):
        return None
    
    test_info = utils.load_json(os.path.join(output_path, Constants.TEST_INFO_PATH))
    test_info[Constants.TEST_IDX_ATTR] = utils.get_test_path(output_path)

    return test_info


def extract_claims(client, article_table, file_name, messages_file_paths, output_folder, html_prompt=True):
    if html_prompt:
        prompt_data = article_table[Constants.TABLE_ATTR].encode('ascii', 'ignore').decode()
    else:
        prompt_data = {
            Constants.CAPTION_ATTR: article_table[Constants.CAPTION_ATTR],
            Constants.CITATION_ATTR: article_table[Constants.CITATIONS_ATTR][0] if len(article_table[Constants.CITATIONS_ATTR]) > 0 else ""
        }

    output_prompts_folder = output_folder + '/prompts'
    utils.check_path(output_prompts_folder)
    prompt, input_tokens = build_messages(file_name, messages_file_paths, prompt_data, output_prompts_folder, html_prompt)

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

    output_answers_folder = output_folder + '/answers'
    utils.check_path(output_answers_folder)
    save_answer_and_stats(answer, input_tokens, output_tokens, request_time, stream, file_name, output_answers_folder)


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
                if not article_table[Constants.PROCESSED_ATTR]:
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
    utils.check_path(test_info[Constants.TEST_IDX_ATTR])
    table.reset_processed_tables(test_info[Constants.TABLES_PATH_ATTR])
    
    i = 0
    tables_to_process = 1000
    while tables_to_process > 0 and i < max_cycles:
        tables = table.load_tables_from_json(test_info[Constants.TABLES_PATH_ATTR])
        run(connection_info, test_info[Constants.MESSAGES_PATH_ATTR], tables, test_info[Constants.TEST_IDX_ATTR], min(num_thread, tables_to_process), test_info[Constants.HTML_TABLE_ATTR])

        tables_to_process = table.check_processed_tables(test_info[Constants.TABLES_PATH_ATTR], os.path.join(test_info[Constants.TEST_IDX_ATTR], Constants.LLM_ANSWER_DIR))
        i += 1
    
    return {
        Constants.CYCLES_ATTR: i,
        Constants.TABLES_TO_PROC_ATTR: tables_to_process
    }
    