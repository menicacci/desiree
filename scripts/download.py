import os
import requests
from bs4 import BeautifulSoup


def build_search_url(query: str, size: int, start: int) -> str:
    query_parsed = '+'.join(query.split())

    return f"https://arxiv.org/search/?query={query_parsed}&searchtype=all&source=header&order=-announced_date_first&size={size}&start={start}"


def download_page(url, save_folder):
    response = requests.get(url)
    if response.status_code == 200:
        file_name = os.path.join(save_folder, url.split("/")[-1] + ".html")
        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"Page downloaded: {file_name}")
    else:
        print(f"Failed to download page from: {url}")


def download_articles(articles, save_folder):
    for article in articles:
        link = article.find("a")['href']
        html_link = link.replace("arxiv.org", "ar5iv.org")

        response_mod = requests.head(html_link, allow_redirects=True)
        if response_mod.url == link:
            print(f"{link} redirects to the original link. Skipping...")
        else:
            print(f"{link} doesn't redirect to the original link. Downloading...")
            download_page(html_link, save_folder)


def get_articles(query: str, save_folder: str):
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    start = 0
    size = 200

    while True:
        response = requests.get(build_search_url(query, size, start))
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            articles = soup.find_all("p", class_="list-title is-inline-block")

            if not articles or len(articles) == 0:
                break

            download_articles(articles, save_folder)

            start += size
        else:
            break
