import os
from scripts import utils, claim
from scripts.constants import Constants
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
    create_stats_file(stats_file_path, Constants.HEADER_STRUCTURE)

    stats_dir = os.path.join(dir, Constants.STATS_DIR)
    for file_name in os.listdir(stats_dir):
        file_path = os.path.join(stats_dir, file_name)
        file_stats = utils.load_json(file_path)

        append_stat(stats_file_path, file_stats)
