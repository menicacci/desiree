from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from scripts import check_claim_structure as cs


def get_max_similarity(l1, l2):
    results = []

    l1_processed = [''.join(c.lower() for c in s if c.isalnum() or c.isspace()) for s in l1]
    l2_processed = [''.join(c.lower() for c in s if c.isalnum() or c.isspace()) for s in l2]

    processed = l1_processed + l2_processed
    vectorizer = CountVectorizer().fit_transform(processed)
    similarity_matrix = cosine_similarity(vectorizer)

    for i, string1 in enumerate(l1_processed):
        max_similarity = 0
        most_similar_string = ""

        for j, string2 in enumerate(l2_processed, start=len(l1)):
            similarity = similarity_matrix[i][j]
            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_string = l2[j - len(l1)]

        results.append((l1[i], most_similar_string, max_similarity))

    return results


def calculate_list_similarity(list_similarity):
    similarity_scores = np.array([item[2] for item in list_similarity]).reshape(1, -1)

    scores_mean = np.mean(similarity_scores)
    scores_mse = np.mean((similarity_scores - scores_mean) ** 2)

    return 1 / (1 + scores_mse)


def evaluate_extracted_articles(claims: dict, extracted_tables: dict):
    evaluation = []

    for article_id in claims.keys():
        for table_idx in claims[article_id].keys():

            html_table = extracted_tables[article_id][table_idx]['table']
            table_vales, _ = cs.get_table_values(html_table)

            claim_values = claims[article_id][table_idx]['extracted_claims']
            _, _, values_extracted = cs.count_specifications(claim_values)

            similarity = get_max_similarity(table_vales, values_extracted)
            evaluation.append([f"{article_id}-{table_idx}", calculate_list_similarity(similarity)])

    evaluation.sort(key=lambda x: x[1], reverse=True)
    return evaluation
