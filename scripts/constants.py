
class Constants:

    PROJECT_PATH = "$GITHUB_HOME/claim-extraction"

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
    
    class Roles:
        ASSISTANT = "assistant"
        SYSTEM = "system"
        USER = "user"

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

    class TableTypes:
        UNCLASSIFIED_TABLE = 0
        RESULT_TABLE = 1
        DATA_TABLE = 2
        EXAMPLE_TABLE = 3

        TYPES = [
            UNCLASSIFIED_TABLE,
            RESULT_TABLE,
            DATA_TABLE,
            EXAMPLE_TABLE
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



