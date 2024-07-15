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


def build_user_message(message_path, prompt_data, html_prompt):
    content = utils.read_file(message_path)

    if html_prompt:
        content = utils.replace_placeholder(content, Constants.Attributes.HTML_TABLE, prompt_data)
    else:
        content = utils.replace_placeholder(content, Constants.Attributes.CAPTION, prompt_data[Constants.Attributes.CAPTION])
        content = utils.replace_placeholder(content, Constants.Attributes.CITATION, prompt_data[Constants.Attributes.CITATION])
    
    return content


def build_messages(messages_file_path, prompt_data, html_prompt):
    content_system_1 = utils.read_file(messages_file_path['system_1'])
    content_user_1 = utils.read_file(messages_file_path['user_1'])
    content_assistant = utils.read_file(messages_file_path['assistant'])
    content_user_2 = build_user_message(messages_file_path['user_2'], prompt_data, html_prompt)
    content_system_2 = utils.read_file(messages_file_path['system_2'])

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


def build_prompt(article_table, messages_file_paths, html_prompt):
    if html_prompt:
        prompt_data = article_table[Constants.Attributes.TABLE].encode('ascii', 'ignore').decode()
    else:
        prompt_data = {
            Constants.Attributes.CAPTION: article_table[Constants.Attributes.CAPTION],
            Constants.Attributes.CITATION: article_table[Constants.Attributes.CITATIONS][0] if len(article_table[Constants.Attributes.CITATIONS]) > 0 else ""
        }

    return build_messages(messages_file_paths, prompt_data, html_prompt)


def save_prompt_structure(messages_file_paths: dict, output_path: str):
    original_prompt = f'''
        {Constants.Roles.SYSTEM_1.upper()}:\n{utils.read_file(messages_file_paths[Constants.Roles.SYSTEM_1])}\n\n
        {Constants.Roles.USER_1.upper()}:\n{utils.read_file(messages_file_paths[Constants.Roles.USER_1])}\n\n
        {Constants.Roles.ASSISTANT.upper()}:\n{utils.read_file(messages_file_paths[Constants.Roles.ASSISTANT])}\n\n
        {Constants.Roles.USER_2.upper()}:\n{utils.read_file(messages_file_paths[Constants.Roles.USER_2])}\n\n
        {Constants.Roles.SYSTEM_2.upper()}:\n{utils.read_file(messages_file_paths[Constants.Roles.SYSTEM_2])}\n\n
    '''

    with open(os.path.join(output_path, Constants.Filenames.PROMPT), "w") as text_file:
        text_file.write(original_prompt)


def read_prompt(prompt_path: str):
    prompt_text = utils.read_file(prompt_path)

    pattern = r'\s{8}([A-Z_\d]+):\n(.*?)\n\n'
    matches = re.findall(pattern, prompt_text, re.DOTALL)

    return {key.strip().replace(":", "").replace(" ", "_").lower(): value.strip() for key, value in matches}


def write_prompt_structure(prompt_messages: dict, save_path: str):
    msg_paths = {}
    for role, message in prompt_messages.items():
        role_msg_path = os.path.join(save_path, f"{role}.txt")
        with open(role_msg_path, "w") as file:
            file.write(message)

        msg_paths[role] = role_msg_path

    return msg_paths