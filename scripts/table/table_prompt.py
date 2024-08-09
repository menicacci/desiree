import os
import shutil
import copy
from scripts import utils
from scripts.constants import Constants
from scripts.table import table_utils
from scripts.table.table_constants import TableConstants
from scripts.llm import llm_prompt, llm_utils
from scripts.llm.llm_constants import LlmConstants


def build_input_msg(input_msg, table_data, input_structure):
    if input_structure == TableConstants.PromptStructure.HTML:
        input_msg = utils.replace_placeholder(input_msg, Constants.Attributes.HTML_TABLE, table_data[Constants.Attributes.TABLE].encode('ascii', 'ignore').decode())
    else:
        if input_structure == TableConstants.PromptStructure.CAP or input_structure == TableConstants.PromptStructure.CAP_CIT:
            input_msg = utils.replace_placeholder(input_msg, Constants.Attributes.CAPTION, table_data[Constants.Attributes.CAPTION])
        if input_structure == TableConstants.PromptStructure.CIT or input_structure == TableConstants.PromptStructure.CAP_CIT:
            input_msg = utils.replace_placeholder(input_msg, Constants.Attributes.CITATION, table_data[Constants.Attributes.CITATIONS][0] if len(table_data[Constants.Attributes.CITATIONS]) > 0 else "")

    return input_msg


class TablePrompts:

    def __init__(self, request_path: str, tables_path=None, messagges_path=None):
        already_existed = llm_utils.generate_main_req_directory(request_path)
        test_info_path = os.path.join(request_path, Constants.Filenames.TEST_INFO)
        
        if not already_existed and utils.check_not_none_and_type([tables_path, messagges_path], str):
            test_info = {
                TableConstants.Attributes.MSGS_PATH: messagges_path,
                TableConstants.Attributes.TABLES_PATH: tables_path,
                TableConstants.Attributes.NUM_TABLE: table_utils.reset_processed_tables(tables_path)
            }
            utils.write_json(
                test_info,
                test_info_path
            )
            llm_prompt.save(messagges_path, request_path)

        elif already_existed:
            test_info = utils.load_json(test_info_path)
            messagges_path = llm_prompt.retrieve_original_prompt(
                request_path, 
                test_info[TableConstants.Attributes.MSGS_PATH]
            )
        else:
            shutil.rmtree(request_path)
            raise RuntimeError("Provide all paths if directory doesn't exist")
        
        self.request_path = request_path
        self.tables_path = test_info[TableConstants.Attributes.TABLES_PATH]

        self.msgs_structure = llm_prompt.get_structure(messagges_path)
        msgs_data = utils.load_json(os.path.join(messagges_path, Constants.Filenames.MSG_INFO))
        self.input_structure = msgs_data[TableConstants.PromptAttributes.INPUT_STRUCTURE]
        self.input_msg = msgs_data[TableConstants.PromptAttributes.INPUT_MSG]

        if already_existed:
            shutil.rmtree(messagges_path)


    def build(self, table_data: dict):
        messages = copy.deepcopy(self.msgs_structure)

        messages[self.input_msg][LlmConstants.MsgStructure.CONTENT] = build_input_msg(
            messages[self.input_msg][LlmConstants.MsgStructure.CONTENT],
            table_data,
            self.input_structure
        )
        
        return messages


    def generate(self, override=False):
        prompts = []

        tables = utils.load_json(self.tables_path)
        table_ids = table_utils.get_table_ids(tables)
        
        if not override:
            tables_processed = llm_utils.get_successful_request_ids(self.request_path)
            table_ids = [id for id in table_ids if id not in tables_processed]

        for table_id in table_ids:
            article_id, table_idx = table_id.split("_")
            table_data = tables[article_id][int(table_idx)]

            prompts.append(
                llm_prompt.gen_prompt_dict(
                    table_id, 
                    self.build(table_data)
                )
            )
        
        return prompts
