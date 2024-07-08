import os
from bs4 import BeautifulSoup
from scripts import utils
from scripts.constants import Constants
import copy


def clean_element(element, to_del):
    for e in to_del:
        if e in element.attrs:
            del element[e]


def clean_html(element, remove_citations):
    to_del = ['class', 'style', 'id']

    clean_element(element, to_del)

    for child in element.find_all(recursive=True):
        # Remove all attributes except rowspan and colspan
        attributes_to_keep = {'rowspan', 'colspan'}
        for attribute in list(child.attrs.keys()):
            if attribute not in attributes_to_keep:
                del child[attribute]
        
        clean_element(child, to_del)

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


def clean_extracted_string(extracted_string: str, replace_char=""):
    return utils.remove_new_line(utils.remove_unicodes(extracted_string), replace_char)


def find_table_citations(html_soup, table):
    citations = []

    table_id = table.get('id')
    if table_id:
        paragraphs = html_soup.find_all('p', class_='ltx_p')
        for p in paragraphs:
            if p.find('a', href=f'#{table_id}'):
                p_copy = copy.copy(p)

                nested_figure = p_copy.find('figure', id=table_id)
                if nested_figure:
                    nested_figure.decompose()

                citations.append(clean_extracted_string(p_copy.get_text(), " "))

    return citations


def get_table_caption(table):
    caption = table.find('figcaption')
    return clean_extracted_string(caption.get_text().strip(), " ") if caption else ''


def extract_tables_from_html(html_file_path, remove_citations=False):
    html_content = utils.read_html(html_file_path)
    if html_content is None:
        return []

    html_soup = BeautifulSoup(html_content, 'html.parser')
    tables = html_soup.find_all('figure', class_='ltx_table')

    extracted_tables = []
    for table in tables:
        table_citations = find_table_citations(html_soup, table)
        table_caption = get_table_caption(table)
        
        clean_table = clean_html(table, remove_citations)
        table_string = str(clean_table)
        
        extracted_tables.append({
            Constants.TABLE_ATTR: clean_extracted_string(table_string),
            Constants.CITATIONS_ATTR: table_citations,
            Constants.CAPTION_ATTR: table_caption,
            Constants.PROCESSED_ATTR: False
        })

    return extracted_tables


def extract_table_caption_and_citations(html_file_path):
    html_content = utils.read_html(html_file_path)
    if html_content is None:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('figure', class_='ltx_table')

    return tables


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
    utils.write_json(filtered_tables_map, output_file)


def extract_and_save_tables(articles_directory: str, save_path: str, file_name: str):
    articles_tables_map = extract_tables_from_directory(articles_directory)

    utils.check_path(save_path)
    file_name = os.path.join(save_path, file_name)

    num_tables = 0
    for article_id, article_tables in articles_tables_map.items():
        num_article_tables = len(article_tables)
        num_tables += num_article_tables
        print(f"Article ID: {article_id} - # Tables Found: {num_article_tables}")
    print(f"\nTotal number of tables found: {num_tables}")

    save_tables_to_json(articles_tables_map, file_name)
    