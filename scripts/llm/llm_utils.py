import os
from scripts import utils
from scripts.constants import Constants
from scripts.llm.llm_constants import LlmConstants, LlmStructures


def generate_req_directories(request_path):
    req_dirs = [
        os.path.join(request_path, req_dir) 
        for req_dir in LlmStructures.LLM_DIRS
    ]
    
    for dir in req_dirs:
        utils.check_path(dir)


def get_req_directories(request_path):
    return [
        os.path.join(request_path, dir) for dir in LlmStructures.LLM_DIRS
    ]


def generate_main_req_directory(request_path: str) -> bool:
    if not utils.check_path(request_path):
        generate_req_directories(request_path)    
        return False
    
    return True


def object_to_dict(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    elif hasattr(obj, "__dict__"):
        return {key: object_to_dict(value) for key, value in obj.__dict__.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [object_to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: object_to_dict(value) for key, value in obj.items()}
    return obj


def save_results(dir_path, request_results):
    for result in request_results:
        utils.write_json(result, os.path.join(dir_path, f"{result[LlmConstants.Attributes.REQ_ID]}.json"))


def get_successful_request_ids(req_path):
    answer_path = os.path.join(req_path, Constants.Directories.ANSWERS)
    return utils.get_file_names(answer_path)
