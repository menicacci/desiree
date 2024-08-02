import os
import re
import shutil
import tiktoken
from scripts.constants import Constants
from scripts.llm.constants import LlmConstants
from scripts import utils


# Returns the number of tokens in a text string
def num_tokens_from_string(string: str, model="gpt-4-32k") -> int:
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(string))

    return num_tokens


# Returns the approximate number of tokens in a request
def num_tokens_request_approx(request, model="gpt-4-32k"):
    return sum([num_tokens_from_string(msg[Constants.MsgStructure.CONTENT]) for msg in request])


# Returns a message compatible with AzureOpenAI API
def message(role, content) -> dict:
    return {
        Constants.MsgStructure.ROLE: role, 
        Constants.MsgStructure.CONTENT: content
    }


# Returns a list containing the prompt structure in the right order
def get_structure(messages_path: str) -> list:
    msg_paths = []
    for file_name in os.listdir(messages_path):
        if file_name.endswith(".txt"):
            msg_paths.append(os.path.join(messages_path, file_name))

    msg_paths.sort(key=lambda x: int(os.path.basename(x).split('_')[0]))

    return [
        message(os.path.basename(msg_filename).split('_')[1].split('.')[0], utils.read_file(msg_filename))
        for msg_filename in msg_paths
    ]


# Saves the prompt structure
def save(messages_file_paths: dict, save_path: str):
    msgs = get_structure(messages_file_paths)
    
    prompt_structure = "".join([
        f'        {msg[Constants.MsgStructure.ROLE].upper()}:\n{msg[Constants.MsgStructure.CONTENT]}\n\n\n\n' for msg in msgs
    ])

    utils.write_file(prompt_structure, os.path.join(save_path, Constants.Filenames.PROMPT))


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


def gen_prompt_dict(request_id: str, prompt: list) -> dict:
    return {
        LlmConstants.Attributes.REQ_ID: request_id,
        LlmConstants.Attributes.API_MSG: prompt
    }


def retrieve_original_prompt(request_path: str, original_msgs_path: str):
    temp_dir = os.path.join(request_path, Constants.Directories.TEMP)
    os.makedirs(temp_dir, exist_ok=True)
    
    msgs_info_path = os.path.join(original_msgs_path, Constants.Filenames.MSG_INFO)
    shutil.copy(msgs_info_path, temp_dir)

    original_prompt = os.path.join(request_path, Constants.Filenames.PROMPT)
    original_prompt_structure = read(original_prompt)

    write(original_prompt_structure, temp_dir)

    return temp_dir
