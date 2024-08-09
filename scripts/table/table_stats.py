import os
import pandas as pd
from scripts.evaluation import stats
from scripts.constants import Constants
from scripts.llm.llm_constants import LlmConstants
from scripts.table import table_types
from scripts.table.table_constants import TableConstants


def convert(request_path: str) -> str:
    stats_file = os.path.join(request_path, Constants.Filenames.STATS)

    stats_df = pd.read_excel(stats_file)
    
    req_column = LlmConstants.Attributes.REQ_ID
    split_req_id = stats_df[req_column].apply(lambda x: pd.Series(x.split('_')))
    new_columns = [TableConstants.ColumnHeaders.ARTICLE_ID, TableConstants.ColumnHeaders.TABLE_IDX]
    stats_df[new_columns] = split_req_id

    stats_df.drop(columns=[req_column], inplace=True)

    save_path = os.path.join(request_path, TableConstants.Filenames.STATS)
    stats_df.to_excel(save_path, index=True, engine="xlsxwriter")

    return save_path


def compare_multiple_results(
        ground_truth_path: str,
        request_paths: list,
        comparison_path: str,
        compare_function=table_types.compare_table_types,
        check_type=TableConstants.Types.CLAIMED_TYPES
):
    # Convert request stats file into table stats file
    for request_path in request_paths:
        convert(request_path)

    # Run comparison
    stats.compare_multiple_results(
        gt_path=ground_truth_path,
        output_dirs=request_paths,
        save_path=comparison_path,
        compare_function=compare_function,
        stat_file_name=TableConstants.Filenames.STATS,
        opts={TableConstants.Attributes.TYPES: check_type}
    )
