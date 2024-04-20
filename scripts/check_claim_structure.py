import re
import os
import json
import pandas as pd


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

                        specifications_values.append({"name": name_value[0], "value": name_value[1]})

                    measure = None
                    outcome = None
                    if scientific_result != '':
                        measure_outcome = check_tuple(scientific_result[2:])
                        if measure_outcome is None:
                            return None

                        measure = measure_outcome[0]
                        outcome = measure_outcome[1]

                    return {
                        'specifications': specifications_values,
                        'measure': measure,
                        'outcome': outcome
                    }

    else:
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
        for spec in claim['specifications']:
            spec_name = spec['name']
            spec_value = spec['value']

            all_values.append(spec_value)
            all_values.append(spec_name)

            if spec_name not in specs_map:
                specs_map[spec_name] = {"count": 0, "values": {}}

            specs_map[spec_name]["count"] += 1

            spec_values = specs_map[spec_name]["values"]
            if spec_value not in spec_values:
                spec_values[spec_value] = 0

            spec_values[spec_value] += 1

        if claim['measure'] is not None and claim['outcome'] is not None:
            claim_measure = claim['measure']
            claim_outcome = claim['outcome']

            all_values.append(claim_measure)
            all_values.append(claim_outcome)

            if claim_measure not in results_map:
                results_map[claim_measure] = {"count": 0, "outcomes": []}

            results_map[claim_measure]["count"] += 1
            results_map[claim_measure]["outcomes"].append(claim_outcome)

    all_values = remove_duplicates(all_values)
    all_values.sort()

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
        non_null_values.extend(df[column].dropna().tolist())
    return non_null_values


def remove_duplicates(input_list: list):
    return list(set(input_list))


def get_table_values(html_table):
    table = pd.read_html(html_table)

    column_names = []
    table_values = []
    for pd_table in table:
        column_names += combine_column_names(pd_table.columns.tolist())
        table_values += get_non_null_values(pd_table)

    table_values = remove_duplicates(column_names + table_values)
    table_values = [str(value) for value in table_values]

    return table_values, table


def extract_answers(answers_directory: str, json_path: str):
    answers_data = {}

    for filename in os.listdir(answers_directory):
        if filename.endswith(".txt"):
            file_parts = filename.split("_")
            if len(file_parts) == 2:
                article_id = file_parts[0]
                table_idx = int(file_parts[1].split(".")[0])
                filepath = os.path.join(answers_directory, filename)
                with open(filepath, 'r') as file:
                    if article_id not in answers_data:
                        answers_data[article_id] = {}

                    txt_claims = file.readlines()

                    extracted_claims, wrong_claims = extract_claims(txt_claims)

                    answers_data[article_id][table_idx] = {
                        "extracted_claims": extracted_claims,
                        "wrong_claims": wrong_claims
                    }

    with open(json_path, 'w') as json_file:
        json.dump(answers_data, json_file, indent=4)

    return answers_data
