import os
import re
import tiktoken
from scripts.constants import Constants
from scripts.table import table_prompt
from scripts import utils


# Returns the number of tokens in a text string
def num_tokens_from_string(string: str) -> int:
    encoding = tiktoken.encoding_for_model("gpt-4")
    num_tokens = len(encoding.encode(string))

    return num_tokens


def message(role, content) -> dict:
    return {
        Constants.MsgStructure.ROLE: role, 
        Constants.MsgStructure.CONTENT: content
    }


def get_structure(messages_path: str):
    msg_paths = []
    for file_name in os.listdir(messages_path):
        if file_name.endswith(".txt"):
            msg_paths.append(os.path.join(messages_path, file_name))

    msg_paths.sort(key=lambda x: int(os.path.basename(x).split('_')[0]))

    messages = [
        message(os.path.basename(msg_filename).split('_')[1].split('.')[0], utils.read_file(msg_filename))
        for msg_filename in msg_paths
    ]

    return messages


def build(messages_file_path, data):
    messages = get_structure(messages_file_path)
    msg_data = utils.load_json(os.path.join(messages_file_path, Constants.Filenames.MSG_INFO))
    
    if msg_data[Constants.Attributes.MSG_TYPE] == Constants.MsgType.TABLE:
        messages = table_prompt.build(data, messages, msg_data)
    # Just one type of message supported for now
    else:
        raise ValueError("Unsupported type")

    num_tokens = sum([num_tokens_from_string(msg[Constants.MsgStructure.CONTENT]) for msg in messages])

    return messages, num_tokens


def save(messages_file_paths: dict, output_path: str):
    msgs = get_structure(messages_file_paths)
    
    prompt_structure = "".join([
        f'        {msg[Constants.MsgStructure.ROLE].upper()}:\n{msg[Constants.MsgStructure.CONTENT]}\n\n\n\n' for msg in msgs
    ])

    with open(os.path.join(output_path, Constants.Filenames.PROMPT), "w") as text_file:
        text_file.write(prompt_structure)


def read(prompt_path: str):
    prompt_structure = utils.read_file(prompt_path)

    pattern = r'\s{8}([A-Z]+):\n(.*?)\n\n\n'
    matches = re.findall(pattern, prompt_structure, re.DOTALL)

    return [message(key.strip().replace(":", "").lower(), value.strip()) for key, value in matches]


def write(messages: list, save_path: str):
    for pos, message in enumerate(messages):
        role_msg_path = os.path.join(save_path, f'{pos}_{message[Constants.MsgStructure.ROLE]}.txt')

        with open(role_msg_path, "w") as file:
            file.write(message[Constants.MsgStructure.CONTENT])
