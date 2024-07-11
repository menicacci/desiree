import re
import os
import pandas as pd
from scripts import utils
from scripts.constants import Constants
from io import StringIO


def check_tuple(input_str: str):
    pattern = r'^(.+?),\s+(.+)$'
    match = re.match(pattern, input_str)
    if match:
        return match.groups()
    else:
        return None


def check_claim(claim: str):
    if len(claim) > 2 and claim[0] == '<' and claim[-1] == '>':
        claim = claim[1:-1]

        if claim.startswith('{') and '>}' in claim:
            specifications, scientific_result = claim.split('>}', 1)
            specifications = specifications[1:] + '>'
            pattern = r'<\s*[^<>]*\s*>'
            if re.match(rf'^{pattern}(,\s*{pattern})*$', specifications):
                specs_list = re.findall(r'<\s*([^<>]*)\s*>', specifications)

                if scientific_result == '' or scientific_result.startswith(', '):
                    specifications_values = []

                    for spec in specs_list:
                        name_value = check_tuple(spec)
                        if name_value is None:
                            return None

                        specifications_values.append({
                            Constants.Attributes.NAME: name_value[0], 
                            Constants.Attributes.VALUE: name_value[1]
                        })

                    measure = None
                    outcome = None
                    if scientific_result != '':
                        measure_outcome = check_tuple(scientific_result[2:])
                        if measure_outcome is None:
                            return None

                        measure = measure_outcome[0]
                        outcome = measure_outcome[1]

                    return {
                        Constants.Attributes.SPECS: specifications_values,
                        Constants.Attributes.MEASURE: measure,
                        Constants.Attributes.OUTCOME: outcome
                    }

    return None


def extract_claims(txt_claims: list):
    correct_claims, wrong_claims = [], []

    for txt_claim in txt_claims:
        if txt_claim.endswith('\n'):
            txt_claim = txt_claim[:-1]

        if txt_claim == '':
            continue

        processed_claim = check_claim(txt_claim)
        if processed_claim is not None:
            correct_claims.append(processed_claim)
        else:
            wrong_claims.append(txt_claim)

    return correct_claims, wrong_claims


def count_specifications(table_claims):
    specs_map = {}
    results_map = {}

    all_values = []

    for claim in table_claims:
        for spec in claim[Constants.Attributes.SPECS]:
            spec_name = spec[Constants.Attributes.NAME]
            spec_value = spec[Constants.Attributes.VALUE]

            all_values.append(spec_value)
            all_values.append(spec_name)

            if spec_name not in specs_map:
                specs_map[spec_name] = {
                    Constants.Attributes.COUNT: 0, 
                    Constants.Attributes.VALUES: {}
                }

            specs_map[spec_name][Constants.Attributes.COUNT] += 1

            spec_values = specs_map[spec_name][Constants.Attributes.VALUES]
            if spec_value not in spec_values:
                spec_values[spec_value] = 0

            spec_values[spec_value] += 1

        if claim[Constants.Attributes.MEASURE] is not None and claim[Constants.Attributes.OUTCOME] is not None:
            claim_measure = claim[Constants.Attributes.MEASURE]
            claim_outcome = claim[Constants.Attributes.OUTCOME]

            all_values.append(claim_measure)
            all_values.append(claim_outcome)

            if claim_measure not in results_map:
                results_map[claim_measure] = {
                    Constants.Attributes.COUNT: 0, 
                    Constants.Attributes.OUTCOMES: []
                }

            results_map[claim_measure][Constants.Attributes.COUNT] += 1
            results_map[claim_measure][Constants.Attributes.OUTCOMES].append(claim_outcome)

    return specs_map, results_map, all_values


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


def extract_table_answers(file_path: str):
    try:
        with open(file_path, 'r') as file:
            txt_claims = file.readlines()

            extracted_claims, wrong_claims = extract_claims(txt_claims)

            return {
                Constants.Attributes.EXTRACTED_CLAIMS: extracted_claims,
                Constants.Attributes.WRONG_CLAIMS: wrong_claims
            }
        
    except FileNotFoundError:
        return {}


def extract_answers(answers_directory: str, json_path: str):
    claims_extracted = utils.load_json(json_path)
    
    if claims_extracted is not None:
        return claims_extracted

    answers_data = {}
    for filename in os.listdir(answers_directory):
        if filename.endswith(".txt"):
            file_parts = filename.split("_")
            if len(file_parts) == 2:
                article_id = file_parts[0]
                table_idx = int(file_parts[1].split(".")[0])
                file_path = os.path.join(answers_directory, filename)

                if article_id not in answers_data:
                    answers_data[article_id] = {}

                answers_data[article_id][table_idx] = extract_table_answers(file_path)

    utils.write_json(answers_data, json_path)
    return answers_data


def check_claim_type(table_claims: dict) -> bool | None:
    extracted_claims = table_claims.get(Constants.Attributes.EXTRACTED_CLAIMS, [])
    wrong_claims = table_claims.get(Constants.Attributes.WRONG_CLAIMS, [])

    total_extracted_claims = len(extracted_claims)
    total_wrong_claims = len(wrong_claims)

    if total_wrong_claims >= total_extracted_claims:
        return None

    data_claims_count = sum(
        1 for claim in extracted_claims 
        if claim.get(Constants.Attributes.MEASURE) is None and claim.get(Constants.Attributes.OUTCOME) is None
    )

    return data_claims_count < (total_extracted_claims / 2)
