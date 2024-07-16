import os
import re
import tiktoken
from scripts.constants import Constants
from scripts import utils


# Returns the number of tokens in a text string
def num_tokens_from_string(string: str) -> int:
    encoding = tiktoken.encoding_for_model("gpt-4")
    num_tokens = len(encoding.encode(string))

    return num_tokens


def message(role, content) -> dict:
    return {"role": role, "content": content}


def build_input_message(content, prompt_data, html_prompt):
    if html_prompt:
        content = utils.replace_placeholder(content, Constants.Attributes.HTML_TABLE, prompt_data)
    else:
        content = utils.replace_placeholder(content, Constants.Attributes.CAPTION, prompt_data[Constants.Attributes.CAPTION])
        content = utils.replace_placeholder(content, Constants.Attributes.CITATION, prompt_data[Constants.Attributes.CITATION])
    
    return content


def get_prompt_data(article_table, html_prompt):
    if html_prompt:
        prompt_data = article_table[Constants.Attributes.TABLE].encode('ascii', 'ignore').decode()
    else:
        prompt_data = {
            Constants.Attributes.CAPTION: article_table[Constants.Attributes.CAPTION],
            Constants.Attributes.CITATION: article_table[Constants.Attributes.CITATIONS][0] if len(article_table[Constants.Attributes.CITATIONS]) > 0 else ""
        }

    return prompt_data


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


def build(article_table, messages_file_path):
    msg_data = utils.load_json(os.path.join(messages_file_path, Constants.Filenames.MSG_INFO))
    
    html_prompt = msg_data["html_table"]
    input_msg = msg_data["input_msg"]

    messages = get_structure(messages_file_path)
    
    messages[input_msg]["content"] = build_input_message(
        messages[input_msg]["content"],
        get_prompt_data(article_table, html_prompt),
        html_prompt
    )

    num_tokens = sum([num_tokens_from_string(msg["content"]) for msg in messages])
    return messages, num_tokens


def save(messages_file_paths: dict, output_path: str):
    msgs = get_structure(messages_file_paths)
    
    prompt_structure = "".join([
        f'        {msg["role"].upper()}:\n{msg["content"]}\n\n\n\n' for msg in msgs
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
        role_msg_path = os.path.join(save_path, f'{pos}_{message["role"]}.txt')

        with open(role_msg_path, "w") as file:
            file.write(message["content"])
