import os
import json
import time
import tiktoken
from openai import AzureOpenAI


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
    encoding = tiktoken.encoding_for_model("gpt-4")
    num_tokens = len(encoding.encode(string))

    return num_tokens


def message(role, content) -> dict:
    return {"role": role, "content": content}


def read_file(absolute_path):
    with open(absolute_path) as file:
        return file.read()


def build_messages(file_name: str, output_prompts_folder: str, instructions: str, request: str):
    messages_dict = [
        message("system", instructions),
        message("user", request)
    ]

    # save prompt for replication purposes
    file_name_txt = file_name + '.txt'
    with open(os.path.join(output_prompts_folder, file_name_txt), "w") as text_file:
        text_file.write(json.dumps(messages_dict))
    print(f"\t Saved prompt at: {os.path.join(output_prompts_folder, file_name_txt)}")

    # number of input tokens
    input_tokens = num_tokens_from_string(instructions + request)

    return messages_dict, input_tokens


def send_request(client, prompt: dict, max_tokens=16000):
    start_time = time.time()

    with client.chat.completions.with_streaming_response.create(
            model="gpt-4-32k",  # model = "deployment_name".
            max_tokens=6000,
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
                if len(json_line['choices']) > 0 and json_line['choices'][0] != None and json_line['choices'][0][
                    'delta'] != None and len(json_line['choices'][0]['delta']) > 0 and json_line['choices'][0]['delta'][
                    'content'] != None:
                    current_token = json_line['choices'][0]['delta']['content']
                    # answer += json_line['choices'][0]['delta']['content']
                    answer += current_token
                    current_answer += current_token
                    if '\n' in current_token:
                        print(current_answer)
                        current_answer = ''

    request_time = time.time() - start_time
    return answer, output_tokens, request_time, stream


def save_answer(answer, output_answers_folder, file_name):
    file_name_txt = file_name + '.txt'
    with open(os.path.join(output_answers_folder, file_name_txt), "w") as text_file:
        text_file.write(answer)
    print(f"\t Saved answer at: {os.path.join(output_answers_folder, file_name_txt)}")

    return


def run(connection_data: dict, output_prompts_folder: str, output_answers_folder: str, instructions: str, request: str, request_id: str):
    client = init_client(connection_data)

    prompt, input_tokens = build_messages(request_id, output_prompts_folder, instructions, request)
    print(f"Sending request [{request_id}]")
    answer, output_tokens, request_time, stream = send_request(client, prompt)

    save_answer(answer, output_answers_folder, request_id)



prompts_folder = 'requests/prompts'
answers_folder = 'requests/answers'
connection_infos = extract_infos('private.json')

instr = '''
Put your instructions here
'''

req = '''
Put your request here
'''

req_id = '0011'

run(connection_infos, prompts_folder, answers_folder, instr, req, req_id)
