import os
import json
from scripts import request as ru


def build_messages(file_name: str, output_prompts_folder: str, instructions: str, request: str):
    messages_dict = [
        ru.message("system", instructions),
        ru.message("user", request)
    ]

    file_name_txt = file_name + '.txt'
    with open(os.path.join(output_prompts_folder, file_name_txt), "w") as text_file:
        text_file.write(json.dumps(messages_dict))
    print(f"\t Saved prompt at: {os.path.join(output_prompts_folder, file_name_txt)}")

    input_tokens = ru.num_tokens_from_string(instructions + request)

    return messages_dict, input_tokens


def save_answer(answer, output_answers_folder, file_name):
    file_name_txt = file_name + '.txt'
    with open(os.path.join(output_answers_folder, file_name_txt), "w") as text_file:
        text_file.write(answer)
    print(f"\t Saved answer at: {os.path.join(output_answers_folder, file_name_txt)}")

    return


def run(connection_data: dict, output_prompts_folder: str, output_answers_folder: str, instructions: str, request: str,
        request_id: str):
    client = ru.init_client(connection_data)

    prompt, input_tokens = build_messages(request_id, output_prompts_folder, instructions, request)
    print(f"Sending request [{request_id}]")
    answer, output_tokens, request_time, stream = ru.send_request(client, prompt)

    save_answer(answer, output_answers_folder, request_id)


prompts_folder = 'requests/prompts'
answers_folder = 'requests/answers'
connection_infos = ru.extract_infos('private.json')

instr = '''
Act as a computer scientist.

Write just the function.
'''

req = '''
With this function I create a map:

def count_specifications(table_claims):
    specs_map = {}

    for claim in table_claims:
        for spec in claim['specifications']:
            spec_name = spec['name']
            spec_value = spec['value']

            if spec_name not in specs_map:
                specs_map[spec_name] = {"count": 0, "values": {}}

            specs_map[spec_name]["count"] += 1

            spec_values = specs_map[spec_name]["values"]
            if spec_value not in spec_values:
                spec_values[spec_value] = 0

            spec_values[spec_value] += 1

    return specs_map

Write a function to print it
'''

req_id = '0027'

run(connection_infos, prompts_folder, answers_folder, instr, req, req_id)
