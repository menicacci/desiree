import os
import requests
import time
from bs4 import BeautifulSoup


def build_search_url(query: str, size: int, start: int) -> str:
    query_parsed = '+'.join(query.split())

    return f"https://arxiv.org/search/?query={query_parsed}&searchtype=all&source=header&order=-announced_date_first&size={size}&start={start}"


def download_html_page(url, save_folder):
    response = requests.get(url)
    if response.status_code == 200:
        file_name = os.path.join(save_folder, url.split("/")[-1] + ".html")

        if os.path.exists(file_name):
            print("\033[38;2;255;165;0mAlready Downloaded\033[0m")
            return True

        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"Page downloaded: {file_name}")
        return True
    else:
        print(f"Failed to download page from: {url}")
        return False


def download_html_article(article_elem, save_path):
    link = article_elem.find("a")['href']
    html_link = link.replace("arxiv.org", "ar5iv.org")

    response_mod = requests.head(html_link, allow_redirects=True)
    if response_mod.url == link:
        print(f"{link} redirects to the original link. Skipping...")
        return False
    
    else:
        print(f"{link} doesn't redirect to the original link. Downloading...")
        return download_html_page(html_link, save_path)
    

def download_pdf_file(pdf_url, save_folder):
    response = requests.get(pdf_url)
    if response.status_code == 200:
        file_name = os.path.join(save_folder, pdf_url.split("/")[-1] + ".pdf")

        if os.path.exists(file_name):
            print("\033[38;2;255;165;0mAlready Downloaded\033[0m")
            return True

        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"PDF downloaded: {file_name}")
        return True
    else:
        print(f"Failed to download PDF from: {pdf_url}")
        return False
    

def download_pdf_article(article_elem, save_path):
    pdf_link_tag = article_elem.find("a", text="pdf")

    if pdf_link_tag is None:
        print("No PDF link found in the article element. Skipping...")
        return False
    
    pdf_link = pdf_link_tag['href']
    download_pdf_file(pdf_link, save_path)


def get_articles(query: str, save_path: str, download_html: bool, download_pdf: bool):
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    articles_found = 0

    start = 0
    size = 200
    while True:
        response = requests.get(build_search_url(query, size, start))
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            article_elems = soup.find_all("p", class_="list-title is-inline-block")

            if not article_elems or len(article_elems) == 0:
                break

            articles_found += len(article_elems)
            for article_elem in article_elems:
                if download_html:
                    download_html_article(article_elem, save_path)
                if download_pdf:
                    download_pdf_article(article_elem, save_path)
                time.sleep(1)

            start += size
        else:
            break

    print(f"# of articles found: {articles_found}")
