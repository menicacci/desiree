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

    return positive_score/global_score


def evaluate_table(sim: Similarity, html_table: str, claim_values: dict):
    table_values, _ = cs.get_table_values(html_table)
    unique_table_values = utils.remove_duplicates(table_values)

    claim_specs, claim_results, values_extracted = cs.count_specifications(claim_values)
    unique_values_extracted = utils.remove_duplicates(values_extracted)

    similarities = sim.find_similar_strings(unique_table_values, unique_values_extracted)
    return evaluate(similarities, table_values, values_extracted)


def evaluate_extracted_articles(claims: dict, extracted_tables: dict, use_embeddings: bool):
    evaluation = {}
    sim = Similarity(use_embeddings=use_embeddings)

    for article_id in claims.keys():
        for table_idx in claims[article_id].keys():
            html_table = extracted_tables[article_id][table_idx]['table']
            claim_dict = claims[article_id][table_idx]['extracted_claims']

            evaluation[f"{article_id}_{table_idx}"] = evaluate_table(sim, html_table, claim_dict)

    return evaluation


def process_datasets(tables_path, requests_path, use_embeddings=True):
    dataset_results = {}

    # Iterate through all directories in dataset_path
    for directory in os.listdir(requests_path):
        if os.path.isdir(os.path.join(requests_path, directory)):
            model_answers_path = os.path.join(requests_path, directory, Constants.LLM_ANSWER_DIR)
            extracted_claims_path = os.path.join(requests_path, directory, Constants.CLAIMS_FILENAME)

            extracted_claims = cs.extract_answers(model_answers_path, extracted_claims_path)
            extracted_tables = table.load_tables_from_json(tables_path)

            results = evaluate_extracted_articles(extracted_claims, extracted_tables, use_embeddings)
            results = list(results.items())
            results.sort()

            dataset_results[directory] = results

    return dataset_results
