import os
from scripts import utils, claim
from scripts.constants import Constants
import pandas as pd
import openpyxl
from openpyxl import Workbook
from openpyxl.utils import get_column_letter


def get_claim_types(data_dir):
    claims_path = os.path.join(data_dir, Constants.Filenames.CLAIMS)
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
    model_answers_path = os.path.join(data_dir, Constants.Directories.LLM_ANSWER)
    extracted_claims_path = os.path.join(data_dir, Constants.Filenames.CLAIMS)
    extracted_claims = claim.extract_answers(model_answers_path, extracted_claims_path)

    claims_correctness_prc = {}
    ovr_crt = 0
    ovr_wrg = 0

    for article_id, tables_dict in extracted_claims.items():
        for table_id, table_dict in tables_dict.items():
            correct_table_claims = table_dict[Constants.Attributes.EXTRACTED_CLAIMS]
            wrong_table_claims = table_dict[Constants.Attributes.WRONG_CLAIMS]

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
    stats_file_path = os.path.join(dir, Constants.Filenames.STATS)
    create_stats_file(stats_file_path, Constants.ColumnHeaders.STATS_HEADER_STRUCTURE)

    stats_dir = os.path.join(dir, Constants.Directories.STATS)
    for file_name in os.listdir(stats_dir):
        file_path = os.path.join(stats_dir, file_name)
        file_stats = utils.load_json(file_path)

        append_stat(stats_file_path, file_stats)


def write_ground_truth(gt_file_path: str, output_dir: str):
    utils.check_path(output_dir)

    data = pd.read_excel(gt_file_path, engine='odf', dtype={h: str for h in Constants.ColumnHeaders.TYPE_HEADER_STRUCTURE})
    for _, row in data.iterrows():
        article_id, table_idx, table_type = [row[header_attr] for header_attr in Constants.ColumnHeaders.TYPE_HEADER_STRUCTURE]

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
                results[article_id] = {}
            results[article_id][int(table_idx)] = file_content

    return results


def calculate_output_accuracy(gt_dict, outcome_dict, check_correctness=lambda x, y: x == y):
    common_elements = 0
    correct_elements = 0
    
    for article_id, article_tables_dict in gt_dict.items():
        if article_id not in outcome_dict:
            continue

        for table_idx, table_type in article_tables_dict.items():
            if table_idx not in outcome_dict[article_id]:
                continue
            
            common_elements += 1
            if check_correctness(table_type, outcome_dict[article_id][table_idx]):
                correct_elements += 1
                
    return common_elements, correct_elements


def compare_results(gt_path: str, output_dirs: list[tuple[str, int]], save_json_path: str):
    gt_result = read_model_output(gt_path)

    output_paths = [os.path.join(dir, str(test_idx), Constants.Directories.LLM_ANSWER) for dir, test_idx in output_dirs]
    results = [read_model_output(path) for path in output_paths]
    
    comparison = [calculate_output_accuracy(gt_result, result) for result in results]

    stats_paths = [os.path.join(dir, str(test_idx), Constants.Filenames.STATS) for dir, test_idx in output_dirs]
    avg_input_tokens = [utils.process_excel_column(path, Constants.ColumnHeaders.INPUT_TOKENS, utils.calculate_average) for path in stats_paths]

    dirs_data = [ 
        {
            Constants.Attributes.DIRECTORY: output_dirs[i][0],
            Constants.Attributes.TEST_IDX: output_dirs[i][1],
            Constants.Attributes.SIZE: utils.count_articles_dict_elems(results[i]),
            Constants.Attributes.COMMON_ELEMENTS: comparison[i][0],
            Constants.Attributes.CORRECT_ELEMENTS: comparison[i][1],
            Constants.Attributes.PRC_CORRECT: comparison[i][1]/comparison[i][0],
            Constants.Attributes.AVG_NUM_INPUT_TOKEN: avg_input_tokens[i]
        } for i in range(len(output_dirs))
    ]

    output = {
        Constants.Attributes.GT_PATH: gt_path,
        Constants.Attributes.SIZE: utils.count_articles_dict_elems(gt_result),
        Constants.Attributes.TEST_DATA: dirs_data
    }

    utils.write_json(output, save_json_path)

    return output
