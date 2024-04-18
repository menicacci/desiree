import os
import json
from scripts import request_utils as ru


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
This is the general structure of the data that I want to extract:

<{list of specifications}, m, o>. "m" is the measure and "o" is the associated result. 
The list of specifications is a list of couples that follow this structure: <name, value>, where name is the type of specification and value is the value of the specification.
Measure and outcome could not be present (like in some examples), in that case the structure will follow this format: <{list of specifications}>

Examples (correct):

<{<Method, HM(40)>, <Dataset, D_{n4}>}, F1, 91.39>
<{<Method, HM(40)>,<Dataset, D_{n4}>}, F1, 91.39>
<{<Method, HM(40)>, <Dataset, D_{n5}>}, F1, 58.52>
<{<Method, HM(40)>,<Dataset, D_{n5}>}, F1, 58.52>
<{<Model, DNN + BranchyNet>, <Dataset, FSPS>, <Mechanism, With BranchyNet>}, F1(Macro), 0.55>
<{<Model, DNN + BranchyNet>, <Dataset, FSPS>, <Mechanism, With BranchyNet>}, Accuracy, 89.6>
<{<Dataset, Abt-Buy>, <Existing Dataset, Dt1>}>
<{<Dataset, Abt-Buy>, <New Dataset, Dn1>}>
<{<Method, Barhom etal. (2019)>, <Dataset, GVC (Events)>}, Precision, 66.0>
<{<Method, Barhom etal. (2019)>, <Dataset, GVC (Events)>}, F1, 72.7>

Examples (wrong):
<{<Method, HM(40), <Dataset, D_{n4}>}, F1, 91.39>
<{<Method, HM(40)>,<Dataset, D_{n5}>} F1, 58.52>
<{<Dataset, Abt-Buy>, <Existing Dataset, Dt1>>
<<Dataset, Abt-Buy>,<New Dataset, Dn1>}>
<<Dataset, Abt-Buy>,<New Dataset, Dn1>}>
{<Dataset, Abt-Buy>, <New Dataset, Dn1>}>
{<Dataset, Abt-Buy>, <New Dataset, Dn1>}


Write a Python script that:
(1) Check if the structure isn't wrong (there aren't errors)
(2) Saves the data inside in Python (lists or dict, or ...)

The function needs to return the correct data inside those structures, and a list of wrong structures
'''

req_id = '0024'

run(connection_infos, prompts_folder, answers_folder, instr, req, req_id)
