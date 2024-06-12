from scripts import utils, table, check_claim_structure as cs
from scripts.similarity import Similarity
from scripts.constants import Constants
import os


def evaluate(similarities, table_values, values_extracted):
    table_strings_occurrences = utils.count_occurrences(table_values)
    claim_strings_occurrences = utils.count_occurrences(values_extracted)

    global_score = 0
    positive_score = 0
    for table_string, similar_claim_strings in similarities.items():
        t_string_occurrences = table_strings_occurrences[table_string]

        global_score += t_string_occurrences
        if bool(similar_claim_strings):
            c_string_occurrences = min(
                [claim_strings_occurrences[similar_string] for similar_string in similar_claim_strings]
            )
            positive_score += min(c_string_occurrences, t_string_occurrences)

    return positive_score/global_score if global_score is not 0 else 0


def evaluate_table(sim: Similarity, html_table: str, claim_values: dict):
    table_values, _ = cs.get_table_values(html_table)
    unique_table_values = utils.remove_duplicates(table_values)

    claim_specs, claim_results, values_extracted = cs.count_specifications(claim_values)
    unique_values_extracted = utils.remove_duplicates(values_extracted)

    similarities = sim.find_similar_strings(unique_table_values, unique_values_extracted)
    return evaluate(similarities, table_values, values_extracted)


def wrong_claims_prc(data_dir: str):
    model_answers_path = os.path.join(data_dir, Constants.LLM_ANSWER_DIR)
    extracted_claims_path = os.path.join(data_dir, Constants.CLAIMS_FILENAME)
    extracted_claims = cs.extract_answers(model_answers_path, extracted_claims_path)

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


def evaluate_extracted_articles(tables_path: str, data_dir: str, use_embeddings: bool):
    model_answers_path = os.path.join(data_dir, Constants.LLM_ANSWER_DIR)
    extracted_claims_path = os.path.join(data_dir, Constants.CLAIMS_FILENAME)

    extracted_claims = cs.extract_answers(model_answers_path, extracted_claims_path)
    extracted_tables = table.load_tables_from_json(tables_path)

    evaluation = {}
    sim = Similarity(use_embeddings=use_embeddings)
    for article_id in extracted_claims.keys():
        for table_idx in extracted_claims[article_id].keys():
            html_table = extracted_tables[article_id][table_idx][Constants.TABLE_ATTR]
            claim_dict = extracted_claims[article_id][table_idx][Constants.EXTRACTED_CLAIMS_ATTR]

            evaluation[f"{article_id}_{table_idx}"] = evaluate_table(sim, html_table, claim_dict)

    return list(evaluation.items())


def process_datasets(tables_path, requests_path, use_embeddings=True):
    dataset_results = {}

    for directory in os.listdir(requests_path):
        data_dir = os.path.join(requests_path, directory)

        if os.path.isdir(data_dir):
            results = evaluate_extracted_articles(tables_path, data_dir, use_embeddings)
            results.sort()

            dataset_results[directory] = results

    return dataset_results
