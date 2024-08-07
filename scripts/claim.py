import re
import os
from scripts import utils
from scripts.constants import Constants
from scripts.llm import llm_utils


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


def extract_claims(answer: str):
    correct_claims, wrong_claims = [], []

    str_claims = answer.splitlines()
    for str_claim in str_claims:
        if str_claim.endswith('\n'):
            str_claim = str_claim[:-1]

        if str_claim == '':
            continue

        processed_claim = check_claim(str_claim)
        if processed_claim is not None:
            correct_claims.append(processed_claim)
        else:
            wrong_claims.append(str_claim)

    return correct_claims, wrong_claims


def count_specifications(extracted_claims):
    specs_map = {}
    results_map = {}

    all_values = []

    for claim in extracted_claims:
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


def extract_claims_from_answer(model_answer: str):
    extracted_claims, wrong_claims = extract_claims(model_answer)

    return {
        Constants.Attributes.EXTRACTED_CLAIMS: extracted_claims,
        Constants.Attributes.WRONG_CLAIMS: wrong_claims
    }


def extract_claims_from_answers(answers_directory: str, json_path: str):    
    model_output = llm_utils.read_model_output(answers_directory)

    extracted_claims = {
        request_id: extract_claims_from_answer(answer)
        for request_id, answer in model_output.items()
    }

    utils.write_json(extracted_claims, json_path)
    return extracted_claims


def get_claims(data_dir: str):
    model_answers_path = os.path.join(data_dir, Constants.Directories.ANSWERS)
    extracted_claims_path = os.path.join(data_dir, Constants.Filenames.CLAIMS)

    return extract_claims_from_answers(model_answers_path, extracted_claims_path)


def check_claim_type(claims_dict: dict) -> bool | None:
    extracted_claims = claims_dict.get(Constants.Attributes.EXTRACTED_CLAIMS, [])
    wrong_claims = claims_dict.get(Constants.Attributes.WRONG_CLAIMS, [])

    total_extracted_claims = len(extracted_claims)
    total_wrong_claims = len(wrong_claims)

    if total_wrong_claims >= total_extracted_claims:
        return None

    data_claims_count = sum(
        1 for claim in extracted_claims 
        if claim.get(Constants.Attributes.MEASURE) is None and claim.get(Constants.Attributes.OUTCOME) is None
    )

    return data_claims_count < (total_extracted_claims / 2)


def get_claim_types(request_path: str):
    extracted_claims = get_claims(request_path)

    data_claims, outcome_claims, wrong_claims = [], [], []

    claim_type_mapping = {
        None: wrong_claims,
        True: outcome_claims,
        False: data_claims
    }

    for request_id, claims in extracted_claims.items():
        claim_type = check_claim_type(claims)
        claim_type_mapping[claim_type].append(request_id)
    
    return outcome_claims, data_claims, wrong_claims
