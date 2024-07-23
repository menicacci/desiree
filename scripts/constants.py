
class Constants:

    PROJECT_PATH = "$GITHUB_HOME/desiree"

    class Filenames:
        CLAIMS = "claims.json"
        COMPARISON = "comparison.xlsx"   
        MSG_INFO = "msg_info.json"
        PROMPT = "prompt.txt"
        RESULTS = "results.pkl"
        STATS = "stats.xlsx"
        TEST_INFO = "test_info.json"
        TOT_RECAP = "tot_recap.json"

    class Directories:
        ARTICLES = "articles"
        COMPARISONS = "comparisons"
        EXPERIMENTS = "experiments"
        EXTRACTED_TABLE = f"extracted_tables"
        GROUND_TRUTH = "ground_truth"
        LLM_ANSWER = "answers"
        MESSAGES = "messages"
        OUTPUT = "output"
        STATS = "stats"
        TEMP = "temp"

    class Attributes:
        AVG_NUM_INPUT_TOKEN = "avg_num_input_token"
        CAPTION = "caption"
        CITATION = "citation"
        CITATIONS = "citations"
        COMMON_ELEMENTS = "common_elements"
        CORRECT_ELEMENTS = "correct_elements"
        CYCLES = "num_cycles"
        COUNT = "count"
        DIRECTORY = "dir"
        ELEMENT_TYPES = "element_types"
        EXTRACTED_CLAIMS = "extracted_claims"
        GT_PATH = "gt_path"
        HTML_TABLE = "html_table"
        MEASURE = "measure"
        MESSAGES_PATH = "messages_path"
        MISSING_CAPTION = "missing_caption"
        MISSING_BOTH = "missing_both"
        MISSING_CITATIONS = "missing_citations"
        MSG_TYPE = "msg_type"
        NAME = "name"
        NO_MISSING = "no_missing_attr"
        NUM_TABLE = "num_tables"
        PROCESSED = "processed"
        OUTCOME = "outcome"
        OUTCOMES = "outcomes"
        PRC_CORRECT = "prc_correct"
        SIZE = "size"
        SPECS = "specifications"
        TABLE = "table"
        TABLES_PATH = "tables_path"
        TABLE_PROC = "table_processed"
        TABLES_TO_PROC = "table_to_process"
        TEST_DATA = "test_data"
        TEST_IDX = "test_idx"
        WRONG_CLAIMS = "wrong_claims"
        VALUE = "value"
        VALUES = "values"

    class ColumnHeaders:
        ARTICLE_ID = "article_id"
        INPUT_TOKENS = "input_tokens"
        OUTPUT = "output"
        OUTPUT_TOKENS = "output_tokens"
        REQUEST_TIME = "request_time"
        STREAM = "stream"
        TABLE_IDX = "table_idx"

        STATS_HEADER_STRUCTURE = (
            ARTICLE_ID, 
            TABLE_IDX, 
            INPUT_TOKENS, 
            OUTPUT_TOKENS, 
            REQUEST_TIME, 
            STREAM
        )

        TYPE_HEADER_STRUCTURE = (
            ARTICLE_ID,
            TABLE_IDX,
            OUTPUT
        )

    class MsgStructure:
        CONTENT = "content"
        ROLE = "role"

    class MsgType:
        TABLE = "table"

    class Claims:
        RESULT_STRUCTURE = 1
        NOT_RESULT_STRUCTURE = 2
        WRONG_STRUCTURE = 3

        CLAIM_STRUCTURES = [
            RESULT_STRUCTURE,
            NOT_RESULT_STRUCTURE,
            WRONG_STRUCTURE
        ]

