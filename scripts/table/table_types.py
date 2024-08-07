import os
import shutil
import pickle
import pandas as pd
from scripts.constants import Constants
from scripts.table.table_constants import TableConstants
from scripts import utils, claim, stats
from scripts.table import table_utils


def compare_table_types(table_results: dict, stats_path: str, save_path: str, opts=None):    
    utils.check_path(save_path)

    types = TableConstants.Types.CONTENT_TYPES if opts is None else opts[TableConstants.Attributes.TYPES]
    
    # save results for each table type
    range_table_types = range(len(types))

    data_model = {k: [0] * len(range_table_types) for k in TableConstants.Types.ROWS_BASE}
    
    input_tokens = utils.process_excel_columns(
        stats_path, 
        TableConstants.ColumnHeaders.PROCESS_COLUMN_STRUCTURE,
        lambda column_values: {f"{value[0]}_{value[1]}": value[2] for value in column_values}
    )
    
    confusion_matrix = [[0] * len(range_table_types) for _ in range_table_types]
    confusion_matrix_ids = [[[] for _ in range_table_types] for _ in range_table_types]

    for table_key, (gt_result, outcome) in table_results.items():
        tokens = int(input_tokens[table_key])
        gt_result_int = int(gt_result)
        outcome_int = int(outcome)
        
        data_model[TableConstants.Types.TOT_TOKENS][gt_result_int] += tokens
        data_model[TableConstants.Types.NUM_TABLES][gt_result_int] += 1
        
        confusion_matrix[gt_result_int][outcome_int] += 1
        confusion_matrix_ids[gt_result_int][outcome_int].append(table_key)
        
        result_type = TableConstants.Types.NUM_CORRECT if gt_result == outcome else TableConstants.Types.NUM_WRONG
        data_model[result_type][gt_result_int] += 1
    


    with open(os.path.join(save_path, TableConstants.Filenames.CONF_MATRIX_IDS), "wb") as file:
        pickle.dump(confusion_matrix_ids, file)

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

    results = table_utils.read_model_output(temp_dir)
    shutil.rmtree(temp_dir)

    return results


def check_claims_types(gt_answer_path, request_path, save_path):
    gt_res = table_utils.read_model_output(gt_answer_path)
    result = get_types_from_claims(request_path)

    table_results = table_utils.agglomerate_results(gt_res, result)

    stats_path = table_utils.convert_stats(request_path)
    return compare_table_types(
        table_results, 
        stats_path, 
        save_path, 
        {
            TableConstants.Attributes.TYPES: Constants.Claims.CLAIM_STRUCTURES
        }
    )
    