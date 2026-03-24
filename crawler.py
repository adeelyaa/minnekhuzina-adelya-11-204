import requests
from bs4 import BeautifulSoup
import os
import time

START_URL = "https://en.wikipedia.org/wiki/Web_scraping"
MAX_PAGES = 100

visited = set()
queue = [START_URL]

os.makedirs("pages", exist_ok=True)

index_file = open("index.txt", "w", encoding="utf-8")

page_id = 1

while queue and page_id <= MAX_PAGES:
    url = queue.pop(0)

    if url in visited:
        continue

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            continue

        html = response.text

        # сохраняем HTML как есть
        filename = f"pages/page_{page_id}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

        # записываем в index.txt
        index_file.write(f"{page_id} {url}\n")

        print(f"[{page_id}] {url}")

        visited.add(url)
        page_id += 1

        soup = BeautifulSoup(html, "html.parser")

        # ищем ссылки
        for link in soup.find_all("a", href=True):
            href = link["href"]

            if href.startswith("/wiki/"):
                full_url = "https://en.wikipedia.org" + href

                if full_url not in visited:
                    queue.append(full_url)

        time.sleep(1)  # чтобы не спамить сервер

    except Exception as e:
        print("Error:", e)

index_file.close()

print("DONE")