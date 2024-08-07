import os
from scripts import stats, utils
from scripts.constants import Constants
from scripts.llm.llm_constants import LlmConstants, LlmStructures


def get(request_path: str):
    stats_data = []

    stats_dir_path = os.path.join(request_path, Constants.Directories.STATS)
    for file_name in os.listdir(stats_dir_path):
        file_path = os.path.join(stats_dir_path, file_name)
        stats_file_content = utils.load_json(file_path)

        stat_to_save = stats_file_content[LlmConstants.Attributes.REQ_INFO]
        stat_to_save.update({
            LlmConstants.Attributes.REQ_ID: stats_file_content[LlmConstants.Attributes.REQ_ID]
        })

        stats_data.append(stat_to_save)

    return stats_data


def save(request_path: str):
    stats_data = get(request_path)
    stats_header = LlmStructures.STATS_HEADER_STRUCTURE

    stats_file_path = os.path.join(request_path, Constants.Filenames.STATS)

    stats.save(stats_file_path, stats_data, stats_header)
