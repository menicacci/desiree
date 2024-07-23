import os
import pandas as pd
from scripts.constants import Constants
from scripts.table.constants import TableConstants
from scripts import utils, claim, stats
import shutil


def compare_table_types(results: dict, stats_path: str, save_path: str, opts=None):
    utils.check_path(save_path)

    types = TableConstants.Types.TYPES if opts is None else opts[TableConstants.Attributes.TYPES]
    
    # save results for each table type
    range_table_types = range(len(types))

    data_model = {k: [0] * len(range_table_types) for k in TableConstants.Types.ROWS_BASE}
    
    input_tokens = utils.process_excel_columns(
        stats_path, 
        [
            Constants.ColumnHeaders.ARTICLE_ID,
            Constants.ColumnHeaders.TABLE_IDX,
            Constants.ColumnHeaders.INPUT_TOKENS
        ],
        lambda column_values: {f"{value[0]}_{value[1]}": value[2] for value in column_values}
    )
    
    confusion_matrix = [[0] * len(range_table_types) for _ in range_table_types]

    for table_key, (gt_result, outcome) in results.items():
        tokens = int(input_tokens[table_key])
        data_model[TableConstants.Types.TOT_TOKENS][gt_result] += tokens
        data_model[TableConstants.Types.NUM_TABLES][gt_result] += 1
        confusion_matrix[gt_result][outcome] += 1
        data_model[(TableConstants.Types.NUM_CORRECT if gt_result == outcome else TableConstants.Types.NUM_WRONG)][gt_result] += 1

    for i in range_table_types:
        num = data_model[TableConstants.Types.NUM_TABLES][i]
        tot = data_model[TableConstants.Types.TOT_TOKENS][i]
        data_model[TableConstants.Types.AVG_TOKENS][i] = tot / num if num else 0
        correct = data_model[TableConstants.Types.NUM_CORRECT][i]
        wrong = data_model[TableConstants.Types.NUM_WRONG][i]
        data_model[TableConstants.Types.PERC_CORRECT][i] = correct / (correct + wrong) if (correct + wrong) else 0

    data = [data_model[row] for row in TableConstants.Types.ROWS_BASE] + confusion_matrix

    rows_distribution = [TableConstants.Types.ANSWER_DISTR + str(type) for type in types]
    rows = TableConstants.Types.ROWS_BASE + rows_distribution
    header = types

    df = pd.DataFrame(data, index=rows, columns=header)
    df.to_excel(os.path.join(save_path, Constants.Filenames.COMPARISON), index=True, engine="xlsxwriter")

    # save global results
    total_tables = sum(data_model[TableConstants.Types.NUM_TABLES])
    total_correct = sum(data_model[TableConstants.Types.NUM_CORRECT])
    total_wrong = sum(data_model[TableConstants.Types.NUM_WRONG])
    total_tokens = sum(data_model[TableConstants.Types.TOT_TOKENS])

    average_tokens = total_tokens / total_tables if total_tables != 0 else 0
    percentage_correct = total_correct / (total_correct + total_wrong) if (total_correct + total_wrong) != 0 else 0

    totals = {
        TableConstants.Types.NUM_TABLES: total_tables,
        TableConstants.Types.NUM_CORRECT: total_correct,
        TableConstants.Types.NUM_WRONG: total_wrong,
        TableConstants.Types.TOT_TOKENS: total_tokens,
        TableConstants.Types.AVG_TOKENS: average_tokens,
        TableConstants.Types.PERC_CORRECT: percentage_correct,
    }

    utils.write_json(totals, os.path.join(save_path, Constants.Filenames.TOT_RECAP))

    return df


def get_types_from_claims(output_dir: str):
    claim.get_claims(output_dir)
    
    claims_classified = stats.get_claim_types(output_dir)
    table_types = Constants.Claims.CLAIM_STRUCTURES

    temp_dir = os.path.join(output_dir, Constants.Directories.TEMP)
    os.makedirs(temp_dir, exist_ok=True)

    for claims, type in zip(claims_classified, table_types):
        for id in claims:
            filename_txt = id + ".txt"
            with open(os.path.join(temp_dir, filename_txt), "w") as file:
                file.write(str(type % len(table_types)))

    results = stats.read_model_output(temp_dir)
    shutil.rmtree(temp_dir)

    return results


def check_claims_types(gt_answer_path, output_path, save_path):
    gt_res = stats.read_model_output(gt_answer_path)
    result = get_types_from_claims(output_path)
    agg_results = stats.agglomerate_results(gt_res, result)

    return compare_table_types(
        agg_results, 
        os.path.join(output_path, Constants.Filenames.STATS), 
        save_path, 
        {
            TableConstants.Attributes.TYPES: Constants.Claims.CLAIM_STRUCTURES
        }
    )
    