
class TableConstants:

    class Filenames:
        CONF_MATRIX_IDS = "confusion_matrix_ids.pkl"
        STATS = "table_stats.xlsx"

    class Attributes:
        MSGS_PATH = "messages_path"
        NUM_TABLE = "num_tables"
        TABLE = "table"
        TABLES_PATH = "tables_path"
        TYPES = "types"

    class Types:
        UNCLASSIFIED_TABLE = 0
        RESULT_TABLE = 1
        DATA_TABLE = 2
        EXAMPLE_TABLE = 3

        CONTENT_TYPES = [
            UNCLASSIFIED_TABLE,
            RESULT_TABLE,
            DATA_TABLE,
            EXAMPLE_TABLE
        ]

        CLAIMED_TYPES = [
            UNCLASSIFIED_TABLE,
            RESULT_TABLE,
            DATA_TABLE
        ]

        ANSWER_DISTR = "Answers Distribution for type: "
        AVG_TOKENS = "AVG. # Tokens"
        NUM_CORRECT = "# Correct Matches"
        NUM_TABLES = "# Tables"
        NUM_WRONG = "# Wrong Matches"
        PERC_CORRECT = "% Correct Matches"
        TOT_TOKENS = "TOT. # Tokens"

        ROWS_BASE = [
            NUM_TABLES,
            NUM_CORRECT,
            NUM_WRONG,
            PERC_CORRECT,
            TOT_TOKENS,
            AVG_TOKENS
        ]

    class PromptStructure:
        CAP = "CAPTION"
        CAP_CIT = "CAPTION_CITATION"
        CIT = "CITATION"
        HTML = "HTML"

    class PromptAttributes:
        INPUT_MSG = "input_msg"
        INPUT_STRUCTURE = "intput_structure"

    class MsgType:
        TABLE = "table"


    class ColumnHeaders:
        ARTICLE_ID = "article_id"
        INPUT_TOKENS = "input_tokens"
        OUTPUT = "output"
        OUTPUT_TOKENS = "output_tokens"
        REQUEST_TIME = "request_time"
        TABLE_IDX = "table_idx"

        STATS_HEADER_STRUCTURE = (
            ARTICLE_ID,
            TABLE_IDX,
            INPUT_TOKENS, 
            OUTPUT_TOKENS, 
            REQUEST_TIME
        )

        TYPE_HEADER_STRUCTURE = (
            ARTICLE_ID,
            TABLE_IDX,
            OUTPUT
        )

        PROCESS_COLUMN_STRUCTURE = [
            ARTICLE_ID,
            TABLE_IDX,
            INPUT_TOKENS
        ]