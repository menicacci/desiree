import os
import pandas as pd
from scripts.constants import Constants
from scripts import utils


def map_key_to_tokens(column_values):
    output = {}
    
    for value in column_values:
        output[f"{value[0]}_{value[1]}"] = value[2]

    return output


def compare_table_types(results: dict, stats_path: str, save_path: str):
    # save results for each table type
    range_table_types = range(len(Constants.TableTypes.TYPES))

    data_model = {k: [0] * len(range_table_types) for k in Constants.TableTypes.ROWS_BASE}
    
    input_tokens = utils.process_excel_columns(
        stats_path, 
        [
            Constants.ColumnHeaders.ARTICLE_ID,
            Constants.ColumnHeaders.TABLE_IDX,
            Constants.ColumnHeaders.INPUT_TOKENS
        ],
        map_key_to_tokens
    )
    
    confusion_matrix = [[0] * len(range_table_types) for _ in range_table_types]

    for table_key, (gt_result, outcome) in results.items():
        tokens = int(input_tokens[table_key])
        data_model[Constants.TableTypes.TOT_TOKENS][gt_result] += tokens
        data_model[Constants.TableTypes.NUM_TABLES][gt_result] += 1
        confusion_matrix[gt_result][outcome] += 1
        data_model[(Constants.TableTypes.NUM_CORRECT if gt_result == outcome else Constants.TableTypes.NUM_WRONG)][gt_result] += 1

    for i in range_table_types:
        num = data_model[Constants.TableTypes.NUM_TABLES][i]
        tot = data_model[Constants.TableTypes.TOT_TOKENS][i]
        data_model[Constants.TableTypes.AVG_TOKENS][i] = tot / num if num else 0
        correct = data_model[Constants.TableTypes.NUM_CORRECT][i]
        wrong = data_model[Constants.TableTypes.NUM_WRONG][i]
        data_model[Constants.TableTypes.PERC_CORRECT][i] = correct / (correct + wrong) if (correct + wrong) else 0

    data = [data_model[row] for row in Constants.TableTypes.ROWS_BASE] + confusion_matrix

    rows_distribution = [Constants.TableTypes.ANSWER_DISTR + str(type) for type in Constants.TableTypes.TYPES]
    rows = Constants.TableTypes.ROWS_BASE + rows_distribution
    header = Constants.TableTypes.TYPES

    df = pd.DataFrame(data, index=rows, columns=header)
    df.to_excel(os.path.join(save_path, Constants.Filenames.COMPARISON), index=True, engine="xlsxwriter")

    # save global results
    total_tables = sum(data_model[Constants.TableTypes.NUM_TABLES])
    total_correct = sum(data_model[Constants.TableTypes.NUM_CORRECT])
    total_wrong = sum(data_model[Constants.TableTypes.NUM_WRONG])
    total_tokens = sum(data_model[Constants.TableTypes.TOT_TOKENS])

    average_tokens = total_tokens / total_tables if total_tables != 0 else 0
    percentage_correct = total_correct / (total_correct + total_wrong) if (total_correct + total_wrong) != 0 else 0

    totals = {
        Constants.TableTypes.NUM_TABLES: total_tables,
        Constants.TableTypes.NUM_CORRECT: total_correct,
        Constants.TableTypes.NUM_WRONG: total_wrong,
        Constants.TableTypes.TOT_TOKENS: total_tokens,
        Constants.TableTypes.AVG_TOKENS: average_tokens,
        Constants.TableTypes.PERC_CORRECT: percentage_correct,
    }

    utils.write_json(totals, os.path.join(save_path, Constants.Filenames.TOT_RECAP))

    return df
