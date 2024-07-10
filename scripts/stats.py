import os
from scripts import utils, claim
from scripts.constants import Constants
import pandas as pd
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter


def get_claim_types(data_dir):
    claims_path = os.path.join(data_dir, Constants.CLAIMS_FILENAME)
    extracted_claims = utils.load_json(claims_path)

    data_claims, outcome_claims, wrong_claims = [], [], []

    for article_id, article_claims in extracted_claims.items():
        for table_id, table_claims in article_claims.items():
            table_key = f"{article_id}_{table_id}"
            claim_type = claim.check_claim_type(table_claims)

            if claim_type is None:
                wrong_claims.append(table_key)
            elif claim_type:
                outcome_claims.append(table_key)
            else:
                data_claims.append(table_key)
    
    return outcome_claims, data_claims, wrong_claims


def wrong_claims_prc(data_dir: str):
    model_answers_path = os.path.join(data_dir, Constants.LLM_ANSWER_DIR)
    extracted_claims_path = os.path.join(data_dir, Constants.CLAIMS_FILENAME)
    extracted_claims = claim.extract_answers(model_answers_path, extracted_claims_path)

    claims_correctness_prc = {}
    ovr_crt = 0
    ovr_wrg = 0

    for article_id, tables_dict in extracted_claims.items():
        for table_id, table_dict in tables_dict.items():
            correct_table_claims = table_dict[Constants.EXTRACTED_CLAIMS_ATTR]
            wrong_table_claims = table_dict[Constants.WRONG_CLAIMS_ATTR]

            table_crt = len(correct_table_claims)
            table_wrg = len(wrong_table_claims)

            claims_correctness_prc[f"{article_id}_{table_id}"] = utils.divide_by_sum(table_crt, table_wrg)

            ovr_crt += table_crt
            ovr_wrg += table_wrg

    return list(claims_correctness_prc.items()), utils.divide_by_sum(ovr_crt, ovr_wrg)


def create_stats_file(file_path, headers):
    workbook = Workbook()
    sheet = workbook.active

    for idx, header in enumerate(headers, start=1):
        sheet.cell(row=1, column=idx, value=header)

    workbook.save(file_path)


def append_stat(file_path, data_dict):
    workbook = openpyxl.load_workbook(file_path)
    sheet = workbook.active

    first_empty_row = sheet.max_row + 1

    for idx, key in enumerate(data_dict.keys(), start=1):
        sheet.cell(row=first_empty_row, column=idx, value=data_dict[key])

    workbook.save(file_path)
    

def save_stats(dir: str):
    stats_file_path = os.path.join(dir, Constants.STATS_FILENAME)
    create_stats_file(stats_file_path, Constants.STATS_HEADER_STRUCTURE)

    stats_dir = os.path.join(dir, Constants.STATS_DIR)
    for file_name in os.listdir(stats_dir):
        file_path = os.path.join(stats_dir, file_name)
        file_stats = utils.load_json(file_path)

        append_stat(stats_file_path, file_stats)


def write_ground_truth(gt_path: str, output_dir: str):
    utils.check_path(output_dir)

    data = pd.read_excel(gt_path, engine='odf', dtype={h: str for h in Constants.TYPE_HEADER_STRUCTURE})
    for _, row in data.iterrows():
        article_id, table_idx, table_type = [row[header_attr] for header_attr in Constants.TYPE_HEADER_STRUCTURE]

        file_name = f"{article_id}_{table_idx}.txt"
        file_content = str(table_type)

        with open(os.path.join(output_dir, file_name), 'w') as file:
            file.write(file_content)


def read_model_output(output_dir: str):
    results = {}

    for file_name in os.listdir(output_dir):
        if file_name.endswith(".txt"):
            article_id, table_idx = utils.split_table_string(file_name)
            
            with open(os.path.join(output_dir, file_name), 'r') as file:
                file_content = int(file.read().strip())
            
            if article_id not in results:
                results[article_id] = []
            results[article_id].append([int(table_idx), file_content])

    results = {article_id: sorted(article_results) for article_id, article_results in results.items()}
    results = {article_id: [table_result[1] for table_result in article_results] for article_id, article_results in results.items()}

    return results


def calculate_output_accuracy(gt_dict, outcome_dict):
    total_elements = 0
    correct_elements = 0
    
    for key in gt_dict:
        gt_values = gt_dict[key]
        oc_values = outcome_dict[key]
        
        for gt_val, oc_val in zip(gt_values, oc_values):
            total_elements += 1
            if gt_val == oc_val:
                correct_elements += 1
                
    accuracy_percentage = (correct_elements / total_elements) * 100
    return accuracy_percentage
