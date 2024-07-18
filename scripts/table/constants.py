
class TableConstants:

    class Types:
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

    class PromptStructure:
        CAP = "CAPTION"
        CAP_CIT = "CAPTION_CITATION"
        CIT = "CITATION"
        HTML = "HTML"

    class PromptAttributes:
        INPUT_MSG = "input_msg"
        INPUT_STRUCTURE = "intput_structure"
