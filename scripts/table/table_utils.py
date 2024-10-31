import json
import os
import pandas as pd
from io import StringIO
from scripts import utils
from scripts.constants import Constants
from scripts.evaluation import stats
from scripts.llm import llm_utils
from scripts.table import table_stats
from scripts.table.table_constants import TableConstants


def load_tables_from_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data


def get_table_ids(tables_dict: dict) -> list:
    table_ids = []

    for article_id, tables_list in tables_dict.items():
        for table_idx, _ in enumerate(tables_list):
            table_ids.append(f"{article_id}_{table_idx}")

    return table_ids


def set_same_processed_status_tables(json_file_path: str, status: bool):
    data = load_tables_from_json(json_file_path)
    num_tables = 0

    for table_id, table_list in data.items():
        for table_data in table_list:
            table_data[Constants.Attributes.PROCESSED] = status
            num_tables += 1

    utils.write_json(data, json_file_path)
    return num_tables

def reset_all_processed_tables(json_file_path: str):
    set_same_processed_status_tables(json_file_path, False)


def set_all_processed_tables(json_file_path: str):
    set_same_processed_status_tables(json_file_path, True)


def set_tables_to_process(json_file_path: str, to_process: list, set_all=True):
    if set_all:
        set_all_processed_tables(json_file_path)
    
    data = load_tables_from_json(json_file_path)
    for article_key, table_idx in to_process:
        data[article_key][table_idx][Constants.Attributes.PROCESSED] = False

    utils.write_json(data, json_file_path)


def check_processed_tables(json_file_path: str, tables_directory_path: str):
    utils.check_path(tables_directory_path)

    tables_to_process = reset_all_processed_tables(json_file_path)
    data = load_tables_from_json(json_file_path)

    for file_name in os.listdir(tables_directory_path):
        if file_name.endswith('.txt'):
            parts = file_name.split('_')
            if len(parts) == 2:
                article_id = parts[0]
                table_index = int(parts[1].split('.')[0])
            else:
                continue

            if article_id in data:
                article = data[article_id]
                if 0 <= table_index < len(article):
                    article[table_index][Constants.Attributes.PROCESSED] = True
                    tables_to_process -= 1
                    
    utils.write_json(data, json_file_path)
    return tables_to_process


def split_request_id(request_id: str):
    file_parts = request_id.split("_")
    article_id = file_parts[0]
    table_idx = int(file_parts[1])

    return article_id, table_idx


def get_original_table(extracted_tables: dict, request_id: str):
    article_id, table_id = split_request_id(request_id)

    return extracted_tables[article_id][int(table_id)][TableConstants.Attributes.TABLE]


def get_tables_from_model_output(model_output: dict) -> dict:
    table_results = {}
    for request_id, output in model_output.items():
        article_id, table_idx = split_request_id(request_id)

        if article_id not in table_results:
            table_results[article_id] = {}

        table_results[article_id][table_idx] = output
    
    return table_results


def read_model_output(request_dir: str) -> dict:
    return llm_utils.read_model_output(request_dir)


def agglomerate_results(ground_truth_answers: dict, model_output: dict):
    return stats.agglomerate_results(ground_truth_answers, model_output)


def convert_stats(request_path: str) -> str:
    return table_stats.convert(request_path)


def combine_column_names(columns):
    if columns is None or type(columns[0]) is int:
        return []

    combined_names = []
    for col in columns:
        if type(col) is tuple:
            name_parts = [part for part in col if 'Unnamed' not in part]
            combined_names.append(' '.join(name_parts))
        else:
            combined_names.append(col)

    return combined_names


def get_non_null_values(df):
    non_null_values = []
    for column in df.columns:
        non_null_values.extend([value for value in df[column] if pd.notnull(value) and value != '-'])
    return non_null_values


def get_table_values(html_table):
    try:
        table = pd.read_html(StringIO(html_table))
    except ValueError:
        return [], []

    column_names = []
    table_values = []
    for pd_table in table:
        column_names += combine_column_names(pd_table.columns.tolist())
        table_values += get_non_null_values(pd_table)

    all_values = []
    all_values.extend(utils.remove_unicodes(str(value)) for value in table_values)
    all_values.extend(utils.remove_unicodes(str(value)) for value in column_names)

    return all_values, table
