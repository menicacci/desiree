from scripts import claim, utils, table
from scripts.similarity import Similarity
from scripts.constants import Constants
import os
import pandas as pd
from io import StringIO


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

    return positive_score/global_score if global_score != 0 else 0


def evaluate_table(sim: Similarity, html_table: str, claim_values: dict):
    table_values, _ = claim.get_table_values(html_table)
    unique_table_values = utils.remove_duplicates(table_values)

    claim_specs, claim_results, values_extracted = claim.count_specifications(claim_values)
    unique_values_extracted = utils.remove_duplicates(values_extracted)

    similarities = sim.find_similar_strings(unique_table_values, unique_values_extracted)
    return evaluate(similarities, table_values, values_extracted)


def get_tables_and_claims(data_dir: str, tables_path: str):
    model_answers_path = os.path.join(data_dir, Constants.Directories.LLM_ANSWER)
    extracted_claims_path = os.path.join(data_dir, Constants.Filenames.CLAIMS)

    extracted_claims = claim.extract_answers(model_answers_path, extracted_claims_path)
    extracted_tables = table.load_tables_from_json(tables_path)

    return extracted_tables, extracted_claims


def get_table_and_claim(extracted_tables: dict, extracted_claims: dict, article_id: str, table_idx: str):
    html_table = extracted_tables[article_id][int(table_idx)][Constants.Attributes.TABLE]
    claim_dict = extracted_claims[article_id][table_idx][Constants.Attributes.EXTRACTED_CLAIMS]

    return html_table, claim_dict


def evaluate_extracted_articles(tables_path: str, data_dir: str, override: bool, use_embeddings: bool):
    results_file_path = os.path.join(data_dir, Constants.Filenames.RESULTS)
    
    if not override:
        results = utils.load_list(results_file_path)
        if results is not None:
            return results

    extracted_tables, extracted_claims = get_tables_and_claims(data_dir, tables_path)

    evaluation = {}
    sim = Similarity(use_embeddings=use_embeddings)
    for article_id in extracted_claims.keys():
        for table_idx in extracted_claims[article_id].keys():
            html_table, claim_dict = get_table_and_claim(extracted_tables, extracted_claims, article_id, table_idx)

            evaluation[f"{article_id}_{table_idx}"] = evaluate_table(sim, html_table, claim_dict)

    results = list(evaluation.items())

    utils.write_list(results_file_path, results)
    return results


def evaluate_extracted_article(tables_path: str, data_dir: str, article_id: str, table_idx: int, use_embeddings=False):
    extracted_tables, extracted_claims = get_tables_and_claims(data_dir, tables_path)

    sim = Similarity(use_embeddings)

    html_table, claim_dict = get_table_and_claim(extracted_tables, extracted_claims, article_id, table_idx)

    table_values, _ = claim.get_table_values(html_table)
    unique_table_values = utils.remove_duplicates(table_values)

    _, _, values_extracted = claim.count_specifications(claim_dict)
    unique_values_extracted = utils.remove_duplicates(values_extracted)

    similarities = sim.find_similar_strings(unique_table_values, unique_values_extracted)

    return similarities, pd.read_html(StringIO(html_table))[0], unique_values_extracted, claim_dict


def process_datasets(tables_path, requests_path, use_embeddings=True):
    dataset_results = {}

    for directory in os.listdir(requests_path):
        data_dir = os.path.join(requests_path, directory)

        if os.path.isdir(data_dir):
            results = evaluate_extracted_articles(tables_path, data_dir, use_embeddings)
            results.sort()

            dataset_results[directory] = results

    return dataset_results
