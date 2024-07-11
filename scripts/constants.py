
class Constants:

    CLAIMS_FILENAME = "claims.json"
    MSG_INFO_FILENAME = "msg_info.json"
    RESULTS_FILENAME = "results.pkl"
    PROJECT_PATH = "$GITHUB_HOME/claim-extraction"
    TEST_INFO_FILENAME = "test_info.json"
    STATS_FILENAME = "stats.xlsx"

    ARTICLES_DIR = f"articles"
    EXPERIMENTS_DIR = "experiments"
    EXTRACTED_TABLE_DIR = f"extracted_tables"
    GROUND_TRUTH_DIR = "ground_truth"
    LLM_ANSWER_DIR = "answers"
    MESSAGES_DIR = "messages"
    OUTPUT_DIR = "output"
    STATS_DIR = "stats"

    AVG_NUM_INPUT_TOKEN_ATTR = "avg_num_input_token"
    CAPTION_ATTR = "caption"
    CITATION_ATTR = "citation"
    CITATIONS_ATTR = "citations"
    COMMON_ELEMENTS_ATTR = "common_elements"
    CORRECT_ELEMENTS_ATTR = "correct_elements"
    CYCLES_ATTR = "num_cycles"
    COUNT_ATTR = "count"
    DIRECTORY_ATTR = "dir"
    EXTRACTED_CLAIMS_ATTR = "extracted_claims"
    GT_PATH_ATTR = "gt_path"
    HTML_TABLE_ATTR = "html_table"
    MEASURE_ATTR = "measure"
    MESSAGES_PATH_ATTR = "messages_path"
    MISSING_CAPTION_ATTR = "missing_caption"
    MISSING_BOTH_ATTR = "missing_both"
    MISSING_CITATIONS_ATTR = "missing_citations"
    NAME_ATTR = "name"
    NO_MISSING_ATTR = "no_missing_attr"
    NUM_TABLE_ATTR = "num_tables"
    PROCESSED_ATTR = "processed"
    OUTCOME_ATTR = "outcome"
    OUTCOMES_ATTR = "outcomes"
    PRC_CORRECT_ATTR = "prc_correct"
    SIZE_ATTR = "size"
    SPECS_ATTR = "specifications"
    TABLE_ATTR = "table"
    TABLES_PATH_ATTR = "tables_path"
    TABLES_TO_PROC_ATTR = "table_to_process"
    TEST_DATA_ATTR = "test_data"
    TEST_IDX_ATTR = "test_idx"
    WRONG_CLAIMS_ATTR = "wrong_claims"
    VALUE_ATTR = "value"
    VALUES_ATTR = "values"
    
    ASSISTANT_ROLE = "assistant"
    SYSTEM_1_ROLE = "system_1"
    SYSTEM_2_ROLE = "system_2"
    USER_1_ROLE = "user_1"
    USER_2_ROLE = "user_2"

    ARTICLE_ID_HEADER = "article_id"
    INPUT_TOKENS_HEADER = "input_tokens"
    OUTPUT_HEADER = "output"
    OUTPUT_TOKENS_HEADER = "output_tokens"
    REQUEST_TIME_HEADER = "request_time"
    STREAM_HEADER = "stream"
    TABLE_IDX_HEADER = "table_idx"

    STATS_HEADER_STRUCTURE = [
        ARTICLE_ID_HEADER, 
        TABLE_IDX_HEADER, 
        INPUT_TOKENS_HEADER, 
        OUTPUT_TOKENS_HEADER, 
        REQUEST_TIME_HEADER, 
        STREAM_HEADER
    ]

    TYPE_HEADER_STRUCTURE = [
        ARTICLE_ID_HEADER,
        TABLE_IDX_HEADER,
        OUTPUT_HEADER
    ]
    