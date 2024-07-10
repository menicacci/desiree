
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

    CAPTION_ATTR = "caption"
    CITATION_ATTR = "citation"
    CITATIONS_ATTR = "citations"
    CYCLES_ATTR = "num_cycles"
    COUNT_ATTR = "count"
    EXTRACTED_CLAIMS_ATTR = "extracted_claims"
    HTML_TABLE_ATTR = "html_table"
    MEASURE_ATTR = "measure"
    MESSAGES_PATH_ATTR = "messages_path"
    NAME_ATTR = "name"
    NUM_TABLE_ATTR = "num_tables"
    PROCESSED_ATTR = "processed"
    OUTCOME_ATTR = "outcome"
    OUTCOMES_ATTR = "outcomes"
    SPECS_ATTR = "specifications"
    TABLE_ATTR = "table"
    TABLES_PATH_ATTR = "tables_path"
    TABLES_TO_PROC_ATTR = "table_to_process"
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
    OUTPUT_TOKENS_HEADER = "output_tokens"
    REQUEST_TIME_HEADER = "request_time"
    STREAM_HEADER = "stream"
    TABLE_IDX_HEADER = "table_idx"

    HEADER_STRUCTURE = [
        ARTICLE_ID_HEADER, 
        TABLE_IDX_HEADER, 
        INPUT_TOKENS_HEADER, 
        OUTPUT_TOKENS_HEADER, 
        REQUEST_TIME_HEADER, 
        STREAM_HEADER
    ]