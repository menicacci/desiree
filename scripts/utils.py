import os
import re
import json
import difflib
import pickle
import pandas as pd


def remove_unicodes(input_string):
    return re.sub(r'[^\x00-\x7F]+', '', input_string)


def remove_duplicates(input_list: list):
    return list(set(input_list))


def remove_new_line(input_string: str, replace_car: str):
    return input_string.replace("\n", replace_car)


def split_table_string(table_string: str):
    file_parts = table_string.split("_")
    article_id = file_parts[0]
    table_idx = int(file_parts[1].split(".")[0])

    return article_id, table_idx


def replace_placeholder(content, placeholder, value):
    placeholder = "{" + placeholder + "}"
    return content.replace(placeholder, value)


def check_path(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return False
    return True


def get_test_index(directory):
    if not os.path.exists(directory):
        raise ValueError(f"The directory '{directory}' does not exist.")
    
    dirs = [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d)) and d.isdigit()]
    if not dirs:
        return 1
    else:
        return max(map(int, dirs)) + 1
    

def get_test_path(path):
    return os.path.join(path, str(get_test_index(path)))


def divide_by_sum(a, b):
    a_float = float(a)
    b_float = float(b)
    return a_float / (a_float + b_float)


def calculate_average(values):
    return sum(values) / len(values) if values else float('nan')


def get_json_file_name(query: str) -> str:
    query = ' '.join(query.split())
    file_name = query.replace(' ', '_')
    file_name = file_name.lower() + '.json'
    return file_name


def detect_number(string):
    string = string.replace(' ', '')
    if string == '' or not string[0].isdigit():
        return False

    string = re.sub(r'(?<=\d)\.(?=\d)', '1', string)

    digit_count = sum(c.isdigit() for c in string)
    non_digit_count = len(string) - digit_count

    if digit_count >= 0.5 * (digit_count + non_digit_count):
        numerical_part = re.search(r'[\d.]+', string).group()
        if numerical_part:
            return True

    return False


def count_occurrences(elements):
    occurrences = {}
    for elem in elements:
        if elem in occurrences:
            occurrences[elem] += 1
        else:
            occurrences[elem] = 1

    return occurrences


def remove_items(items, to_remove):
    return [item for item in items if item not in to_remove]


def find_substrings(input_string, search_list, equality_f):
    sub_strings = input_string.split()
    
    output = []
    if len(sub_strings) == 1:
        return output
    

    for sub_s in sub_strings:
        for seach_s in search_list:
            if equality_f(sub_s, seach_s) > 0:
                output.append(seach_s)

    len_output = len(output)
    if len_output < 2:
        return output
    
    to_remove = set()
    for i in range(len_output - 1):
        for j in range(i + 1, len_output):
            if equality_f(output[i], output[j]) > 0:
                sim_to_i = equality_f(input_string, output[i])
                sim_to_j = equality_f(input_string, output[j])

                to_remove.add(output[i] if sim_to_i > sim_to_j else output[j])
    
    output = [s for s in output if s not in to_remove]
    return output


def fuzzy_string_similarity(str_1, str_2, lower=True):
    if lower:
        str_1 = str_1.lower()
        str_2 = str_2.lower()

    return difflib.SequenceMatcher(None, str_1, str_2).ratio()


def load_json(json_path: str):
    try:
        with open(json_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return None
    

def write_json(data: dict, json_path: str, indent=4):
    with open(json_path, 'w') as json_file:
        json.dump(data, json_file, indent=indent)


def load_list(file_path):
    try:
        with open(file_path, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return None


def write_list(file_path: str, data: list):
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)


def read_html(html_file_path: str):
    try:
        with open(html_file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None
    

def read_file(file_path):
    with open(file_path) as file:
        return file.read()
    

def process_excel_column(file_path, column_name, function):
    df = pd.read_excel(file_path)

    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' does not exist in the Excel file.")
    
    column_values = df[column_name].tolist()
    return function(column_values)


def count_articles_dict_elems(article_dict: dict):
    c = 0
    for article_id, article_tables_dict in article_dict.items():
        for table_idx, table_type in article_tables_dict.items():
            c += 1

    return c