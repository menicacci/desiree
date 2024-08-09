from scripts.constants import Constants

class LlmConstants:

    class Attributes:
        API_KEY = "api_key"
        API_MSG = "api_message"
        API_V = "api_version"
        AZURE_EP = "azure_endpoint"
        GEN_RESPONSE = "generated_response"
        MODEL_RESPONSE = "model_response"
        REQ_ID = "request_id"
        REQ_INFO = "request_info"
        INP_TOKS = "input_tokens"
        OUT_TOKS = "output_tokens"
        REQ_EXC_COUNT = "request_exception_counter"
        REQ_OVR_COUNT = "reqest_overall_counter"
        REQ_OVR_TIME = "request_overall_time"
        REQ_RESULTS = "request_results"
        REQ_SUCCESSFUL = "request_successful"
        REQ_TIME = "request_time"

    class Properties:
        RESPONSE_FILE_FORMAT = ".txt"
        MESSAGE_FILE_FORMAT = ".txt"


    class MsgStructure:
        CONTENT = "content"
        ROLE = "role"

    
    class Roles:
        ASSISTANT = "assistant"
        SYSTEM = "system"
        USER = "user"


class LlmStructures:
    LLM_DIRS = (
        Constants.Directories.ANSWERS,
        Constants.Directories.OUTPUT,
        Constants.Directories.STATS
    )

    STATS_HEADER_STRUCTURE = (
        LlmConstants.Attributes.REQ_ID,
        LlmConstants.Attributes.INP_TOKS,
        LlmConstants.Attributes.OUT_TOKS,
        LlmConstants.Attributes.REQ_TIME
    )
