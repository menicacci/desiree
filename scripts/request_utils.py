import tiktoken
import os
import json
import time
from openai.lib.azure import AzureOpenAI
from requests.exceptions import ReadTimeout


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


def check_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


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


def build_messages(file_name, messages_file_path, html_table, output_prompts_folder):
    content_system_1 = read_file(messages_file_path['system_1'])
    content_user_1 = read_file(messages_file_path['user_1'])
    content_assistant = read_file(messages_file_path['assistant'])
    content_user_2 = read_file(messages_file_path['user_2']) + '\n' + html_table
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


def send_request(client, prompt: dict, max_tokens=16000):
    start_time = time.time()

    with client.chat.completions.with_streaming_response.create(
            model="gpt-4-32k",
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


def extract_claims(client, article_table, file_name, messages_file_paths, output_folder):
    table_html = article_table['table'].encode('ascii', 'ignore').decode()

    output_prompts_folder = output_folder + '/prompts'
    check_path(output_prompts_folder)
    prompt, input_tokens = build_messages(file_name, messages_file_paths, table_html, output_prompts_folder)

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
    check_path(output_answers_folder)
    save_answer_and_stats(answer, input_tokens, output_tokens, request_time, stream, file_name, output_answers_folder)
