import numpy as np
from scripts import check_claim_structure as cs
import difflib
import re


def evaluate_scores(scores_dict):
    # Extract scores from the dictionary
    scores = np.array(list(scores_dict.values()))
    return np.mean(scores)


def detect_number(string):
    string = string.replace(' ', '')
    if string == '' or not string[0].isdigit():
        return False

    # Substitutes a dot between two numbers
    string = re.sub(r'(?<=\d)\.(?=\d)', '1', string)

    digit_count = sum(c.isdigit() for c in string)
    non_digit_count = len(string) - digit_count

    if digit_count >= 0.5 * (digit_count + non_digit_count):
        numerical_part = re.search(r'[\d.]+', string).group()
        if numerical_part:
            return True

    return False


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
        if detect_number(item):
            to_remove = set()

            for match in matches:
                similarity_to_item = difflib.SequenceMatcher(None, item.lower(), match.lower()).ratio()
                if similarity_to_item <= number_threshold:
                    to_remove.add(match)

            similar_strings[item] = [m for m in matches if m not in to_remove]

    scores = {}
    for item, matches in similar_strings.items():
        scores[item] = difflib.SequenceMatcher(None, item.lower(), " ".join(matches).lower()).ratio()

    return similar_strings, scores


def evaluate_extracted_articles(claims: dict, extracted_tables: dict):
    evaluation = {}

    for article_id in claims.keys():
        for table_idx in claims[article_id].keys():

            html_table = extracted_tables[article_id][table_idx]['table']
            table_vales, _ = cs.get_table_values(html_table)

            claim_values = claims[article_id][table_idx]['extracted_claims']
            _, _, values_extracted = cs.count_specifications(claim_values)

            similarities, similarity_scores = find_similar_strings(table_vales, values_extracted)
            evaluation[f"{article_id}_{table_idx}"] = evaluate_scores(similarity_scores)

    return evaluation
