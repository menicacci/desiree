import os
import json
from bs4 import BeautifulSoup


def clean_html(element, remove_citations):
    if 'class' in element.attrs:
        del element['class']
    if 'style' in element.attrs:
        del element['style']
    if 'id' in element.attrs:
        del element['id']

    for child in element.find_all(recursive=True):
        # Remove all attributes except rowspan and colspan
        attributes_to_keep = {'rowspan', 'colspan'}
        for attribute in list(child.attrs.keys()):
            if attribute not in attributes_to_keep:
                del child[attribute]
        # Remove classes
        if 'class' in child.attrs:
            del child['class']
        # Remove inline styles
        if 'style' in child.attrs:
            del child['style']
        # Remove IDs
        if 'id' in child.attrs:
            del child['id']

    if remove_citations:
        # Remove <cite> tags
        for cite_tag in element.find_all('cite'):
            cite_tag.extract()

    nested_tables = element.find_all('table')
    for t in nested_tables:
        parent = t.find_parent('td')
        if parent:
            tags = t.find_all()
            for tag in tags:
                if tag.name in ['table', 'tr', 'td']:
                    tag.unwrap()

    return element


def extract_tables_from_html(html_file_path, remove_citations=False):
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('figure', class_='ltx_table')

    extracted_tables = []
    for table in tables:
        clean_table = clean_html(table, remove_citations)

        table_string = clean_table.encode(encoding='utf-8').decode('utf-8')
        table_string = table_string.replace('\n', '')
        extracted_tables.append({'table': table_string, 'processed': False})

    return extracted_tables


def extract_tables_from_directory(dir_path):
    extracted_tables_map = {}

    for filename in os.listdir(dir_path):
        if filename.endswith(".html"):
            file_path = os.path.join(dir_path, filename)
            article_id = os.path.splitext(filename)[0]
            extracted_tables = extract_tables_from_html(file_path)
            extracted_tables_map[article_id] = extracted_tables

    return extracted_tables_map


def save_tables_to_json(extracted_tables_map, output_file):
    filtered_tables_map = {article_id: tables for article_id, tables in extracted_tables_map.items() if tables}
    with open(output_file, 'w') as json_file:
        json.dump(filtered_tables_map, json_file, indent=4)
