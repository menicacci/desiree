import os
from scripts import utils, claim
from scripts.constants import Constants
import pandas as pd
import openpyxl
from openpyxl import Workbook


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
    model_answers_path = os.path.join(data_dir, Constants.Directories.ANSWERS)
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


def save(file_path: str, data_to_save: list, header: list):
    workbook = Workbook()
    sheet = workbook.active

    for idx, header_name in enumerate(header, start=1):
        sheet.cell(row=1, column=idx, value=header_name)

    for row_idx, data_dict in enumerate(data_to_save, start=2):
        for col_idx, key in enumerate(header, start=1):
            sheet.cell(row=row_idx, column=col_idx, value=data_dict.get(key))

    workbook.save(file_path)

# ToDo: Refactor to make it indipendent from the table types
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


def agglomerate_results(gt_dict, outcome_dict):
    common_elements = {}
    
    for article_id, article_tables_dict in gt_dict.items():
        if article_id not in outcome_dict:
            continue

        for table_idx, gt_output in article_tables_dict.items():
            if table_idx not in outcome_dict[article_id]:
                continue

            common_elements[f"{article_id}_{table_idx}"] = (gt_output, outcome_dict[article_id][table_idx])
                
    return common_elements


def compare_multiple_results(
        gt_path: str, 
        output_dirs: list[str],
        save_path: str,
        compare_function,
        stat_file_name=Constants.Filenames.STATS,
        opts=None
):
    gt_results = read_model_output(gt_path)

    for output_dir in output_dirs:
        save_results_path = os.path.join(save_path, os.path.basename(output_dir))
        answer_path = os.path.join(output_dir, Constants.Directories.ANSWERS)

        stats_path = os.path.join(output_dir, stat_file_name)
        results = read_model_output(answer_path)
        agg_results = agglomerate_results(gt_results, results)

        compare_function(agg_results, stats_path, save_results_path, opts)
