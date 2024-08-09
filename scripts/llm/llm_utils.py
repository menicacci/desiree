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
    if not os.path.exists(request_path):
        generate_req_directories(request_path)    
        return False
    
    return True


def save_answer(save_path: str, answer: str):
    utils.write_file(answer, f"{save_path}{LlmConstants.Properties.RESPONSE_FILE_FORMAT}")


def save_results(dir_path, request_results):
    for result in request_results:
        save_result(dir_path, result)


def save_result(dir_path, request_result):
    utils.write_json(
        request_result, 
        os.path.join(dir_path, f"{request_result[LlmConstants.Attributes.REQ_ID]}.json")
    )


def get_successful_request_ids(req_path):
    answer_path = os.path.join(req_path, Constants.Directories.ANSWERS)
    return utils.get_file_names(answer_path)


def read_model_output(answer_dir: str) -> dict:
    if not os.path.exists(answer_dir):
        return
    
    model_output = {}
    output_file_name = utils.get_file_names(answer_dir, LlmConstants.Properties.RESPONSE_FILE_FORMAT)

    for request_id in output_file_name:
        file_name = f"{request_id}{LlmConstants.Properties.RESPONSE_FILE_FORMAT}"
        model_output[request_id] = utils.read_file(
            os.path.join(answer_dir, file_name)
        )

    return model_output


def get_request_info(request_path: str) -> dict:
    request_info_path = os.path.join(request_path, Constants.Filenames.TEST_INFO)
    
    if not os.path.exists(request_info_path):
        raise FileNotFoundError(request_info_path)

    return utils.load_json(request_info_path)
