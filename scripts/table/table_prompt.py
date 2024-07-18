import os
from scripts import utils
from scripts.constants import Constants
from scripts.table.constants import TableConstants


def build_input_msg(input_msg, table_data, input_structure):
    if input_structure == TableConstants.PromptStructure.HTML:
        input_msg = utils.replace_placeholder(input_msg, Constants.Attributes.HTML_TABLE, table_data[Constants.Attributes.TABLE].encode('ascii', 'ignore').decode())
    else:
        if input_structure == TableConstants.PromptStructure.CAP or input_structure == TableConstants.PromptStructure.CAP_CIT:
            input_msg = utils.replace_placeholder(input_msg, Constants.Attributes.CAPTION, table_data[Constants.Attributes.CAPTION])
        if input_structure == TableConstants.PromptStructure.CIT or input_structure == TableConstants.PromptStructure.CAP_CIT:
            input_msg = utils.replace_placeholder(input_msg, Constants.Attributes.CITATION, table_data[Constants.Attributes.CITATIONS][0] if len(table_data[Constants.Attributes.CITATIONS]) > 0 else "")

    return input_msg

def build(article_table, messages, msg_data):
    input_structure = msg_data[TableConstants.PromptAttributes.INPUT_STRUCTURE]
    input_msg = msg_data[TableConstants.PromptAttributes.INPUT_MSG]

    messages[input_msg][Constants.MsgStructure.CONTENT] = build_input_msg(
        messages[input_msg][Constants.MsgStructure.CONTENT],
        article_table,
        input_structure
    )

    return messages
