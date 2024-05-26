from scripts import utils, table, check_claim_structure as cs
from scripts.similarity import Similarity
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


def evaluate_extracted_articles(claims: dict, extracted_tables: dict):
    evaluation = {}
    similarity = Similarity()

    for article_id in claims.keys():
        for table_idx in claims[article_id].keys():

            html_table = extracted_tables[article_id][table_idx]['table']
            table_values, _ = cs.get_table_values(html_table)
            unique_table_values = utils.remove_duplicates(table_values)

            claim_values = claims[article_id][table_idx]['extracted_claims']
            claim_specs, claim_results, values_extracted = cs.count_specifications(claim_values)
            unique_values_extracted = utils.remove_duplicates(values_extracted)

            similarities = similarity.find_similar_strings(unique_table_values, unique_values_extracted)
            evaluation[f"{article_id}_{table_idx}"] = evaluate(similarities, table_values, values_extracted)

    return evaluation


def process_datasets(tables_path, requests_path):
    dataset_results = {}

    # Iterate through all directories in dataset_path
    for directory in os.listdir(requests_path):
        if os.path.isdir(os.path.join(requests_path, directory)):
            model_answers_path = os.path.join(requests_path, directory, 'answers')
            extracted_claims_path = os.path.join(requests_path, directory, 'claims.json')

            extracted_claims = cs.extract_answers(model_answers_path, extracted_claims_path)
            extracted_tables = table.load_tables_from_json(tables_path)

            results = evaluate_extracted_articles(extracted_claims, extracted_tables)
            results = list(results.items())
            results.sort()

            dataset_results[directory] = results

    return dataset_results

"""
### Old script
def find_similar_strings(input_list, search_list, standard_threshold=0.6, number_threshold=0.75):
    similar_strings = {}
    for item in input_list:
        item_lower = item.lower()
        similar_strings[item] = []
        original_match_found = False
        # Check for exact match
        for string in search_list:
            string_lower = string.lower()
            if item_lower == string_lower:
                similar_strings[item] = [string]
                original_match_found = True
                break

        if not original_match_found:
            # Check for similar substrings
            for sub_item in item.split():
                sub_item_lower = sub_item.lower()
                for string in search_list:
                    string_lower = string.lower()
                    similarity_ratio = difflib.SequenceMatcher(None, sub_item_lower, string_lower).ratio()
                    if similarity_ratio >= standard_threshold:
                        similar_strings[item].append(string)

    # Remove similar strings within each result
    for item, matches in similar_strings.items():
        if len(matches) > 1:
            to_remove = set()
            for i in range(len(matches)):
                for j in range(i + 1, len(matches)):
                    similarity_ratio = difflib.SequenceMatcher(None, matches[i].lower(), matches[j].lower()).ratio()
                    if similarity_ratio >= standard_threshold:
                        similarity_to_item_i = difflib.SequenceMatcher(None, item.lower(), matches[i].lower()).ratio()
                        similarity_to_item_j = difflib.SequenceMatcher(None, item.lower(), matches[j].lower()).ratio()

                        if similarity_to_item_i > similarity_to_item_j:
                            to_remove.add(matches[j])
                        else:
                            to_remove.add(matches[i])

            similar_strings[item] = [m for m in matches if m not in to_remove]

    for item, matches in similar_strings.items():
        if utils.detect_number(item):
            to_remove = set()

            for match in matches:
                similarity_to_item = difflib.SequenceMatcher(None, item.lower(), match.lower()).ratio()
                if similarity_to_item <= number_threshold:
                    to_remove.add(match)

            similar_strings[item] = [m for m in matches if m not in to_remove]

    for item, matches in similar_strings.items():
        if not matches:
            for item_input in search_list:
                if item in item_input:
                    matches.append(item_input)
                    continue

    scores = {}
    for item, matches in similar_strings.items():
        scores[item] = difflib.SequenceMatcher(None, item.lower(), " ".join(matches).lower()).ratio()

    return similar_strings, scores
"""