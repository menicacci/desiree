import os
import shutil
from scripts.constants import Constants
from scripts import utils
from scripts.llm import llm_utils
from scripts.table import table_utils
from scripts.table.table_prompt import TablePrompts
from scripts.llm.llm_request import Executor


def two_step_table_extraction(output_dir: str,
                              tables_file_name: str,
                              msgs_dir_step_1: str = "CS_Label_Caption_NEW",
                              msgs_dir_step_2: list[str] = ["CS_Outcome", "CS_Data"],
                              output_dirs_step_2: list[str] = ["Outcome", "Data"]):
    
    base_output_path = utils.get_abs_path(output_dir, Constants.OUTPUT_PATH, False)
    tables_file_path = utils.get_abs_path(tables_file_name, Constants.EXTRACTED_TABLES_PATH)

    msgs_path_1 = utils.get_abs_path(msgs_dir_step_1, Constants.MESSAGES_PATH)
    output_step_1 = os.path.join(base_output_path, "STEP_1")

    executor_1 = Executor(output_step_1, tables_file_path, msgs_path_1)
    executor_1.prepare()
    executor_1.execute()

    tables_labeled = [[] for i in range(len(output_dirs_step_2) + 1)]
    labeled_path = os.path.join(output_step_1, Constants.Directories.ANSWERS)
    for labeled_file_path in os.listdir(labeled_path):
        with open(os.path.join(labeled_path, labeled_file_path), "r") as file:
            label = file.read()

            try:
                label_index = int(label)
                table_key = label_index if label_index >= 0 and label_index <= len(output_dirs_step_2) else 0
            except ValueError:
                table_key = 0

            tables_labeled[table_key].append(llm_utils.get_key_index(labeled_file_path))

    output_step_2 = os.path.join(base_output_path, "STEP_2")
    tables_to_proc = [os.path.join(output_step_2, f"{dir}.json") for dir in output_dirs_step_2]
    msgs_paths_2 = [utils.get_abs_path(msgs_dir, Constants.MESSAGES_PATH) for msgs_dir in msgs_dir_step_2]

    labeled_paths = []
    for i in range(1, len(tables_labeled)):
        tables_json = tables_to_proc[i]
        tables_labeled = tables_labeled[i]
        shutil.copy(tables_file_path, tables_json)
        table_utils.set_tables_to_process(tables_json, tables_labeled)

        labeled_paths.append(os.path.join(output_step_2, output_dirs_step_2[i - 1]))

    for i in range(len(labeled_paths)):
        executor_2 = Executor(labeled_paths[i], tables_to_proc[i], msgs_paths_2[i])
        executor_2.prepare()
        executor_2.execute()
        