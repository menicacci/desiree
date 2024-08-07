import json
import os
from scripts import utils, stats
from scripts.constants import Constants
from scripts.llm import llm_utils
from scripts.table import table_stats


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


def reset_processed_tables(json_file_path: str):
    data = load_tables_from_json(json_file_path)
    num_tables = 0

    for table_id, table_list in data.items():
        for table_data in table_list:
            table_data[Constants.Attributes.PROCESSED] = False
            num_tables += 1

    utils.write_json(data, json_file_path)
    return num_tables


def check_processed_tables(json_file_path: str, tables_directory_path: str):
    utils.check_path(tables_directory_path)

    tables_to_process = reset_processed_tables(json_file_path)
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


def split_table_string(request_id: str):
    file_parts = request_id.split("_")
    article_id = file_parts[0]
    table_idx = int(file_parts[1])

    return article_id, table_idx


def get_tables_from_model_output(model_output: dict) -> dict:
    table_results = {}
    for request_id, output in model_output.items():
        article_id, table_idx = split_table_string(request_id)

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
