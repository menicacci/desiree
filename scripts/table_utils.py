import json
import os


def load_tables_from_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)
    return data


def reset_processed_tables(json_file_path: str):
    data = load_tables_from_json(json_file_path)

    for table_id, table_list in data.items():
        for table_data in table_list:
            table_data['processed'] = False

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)


def check_processed_tables(json_file_path: str, tables_directory_path: str):
    if not os.path.exists(tables_directory_path):
        return

    data = load_tables_from_json(json_file_path)

    for file_name in os.listdir(tables_directory_path):
        if file_name.endswith('.txt'):
            parts = file_name.split('_')
            if len(parts) == 2:
                article_id = parts[0]
                table_index = int(parts[1].split('.')[0])
            else:
                continue

            if article_id in data:
                article = data[article_id]
                if 0 <= table_index < len(article):
                    article[table_index]['processed'] = True

    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

