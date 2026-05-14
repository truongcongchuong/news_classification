import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import hashlib
import os
import ast

from collections import Counter
from urllib.parse import urlparse

# =========================================================
# CONFIG
# =========================================================

DATASET_FILE = "Data.csv"

JSON_FILE = "Data.json"

TARGET_PER_LABEL = 2000

headers = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/121 Safari/537.36"
    )
}

# =========================================================
# CHỈ CRAWL NHỮNG LABEL THIẾU
# =========================================================

categories = {

    # =========================================
    # THẾ GIỚI
    # =========================================

    "Thế giới": [

        "https://vnexpress.net/the-gioi",

        "https://tuoitre.vn/the-gioi.htm",

        "https://dantri.com.vn/the-gioi.htm",

        "https://thanhnien.vn/the-gioi.htm"
    ],

    # =========================================
    # XÃ HỘI
    # =========================================

    "Xã hội": [

        "https://dantri.com.vn/xa-hoi.htm",

        "https://tuoitre.vn/thoi-su.htm",

        "https://thanhnien.vn/thoi-su.htm"
    ],

    # =========================================
    # NHÀ ĐẤT
    # =========================================

    "Nhà đất": [

        "https://vnexpress.net/bat-dong-san",

        "https://dantri.com.vn/bat-dong-san.htm"
    ],

    # =========================================
    # DU LỊCH
    # =========================================

    "Du lịch": [

        "https://vnexpress.net/du-lich",

        "https://tuoitre.vn/du-lich.htm",

        "https://thanhnien.vn/du-lich.htm"
    ],

    # =========================================
    # SỨC KHỎE
    # =========================================

    "Sức khỏe": [

        "https://vnexpress.net/suc-khoe",

        "https://dantri.com.vn/suc-khoe.htm",

        "https://thanhnien.vn/suc-khoe.htm"
    ],

    # =========================================
    # GIÁO DỤC
    # =========================================

    "Giáo dục": [

        "https://vnexpress.net/giao-duc",

        "https://tuoitre.vn/giao-duc.htm",

        "https://dantri.com.vn/giao-duc.htm"
    ],

    # =========================================
    # THỜI SỰ
    # =========================================

    "Thời sự": [

        "https://vnexpress.net/thoi-su",

        "https://tuoitre.vn/thoi-su.htm",

        "https://thanhnien.vn/thoi-su.htm"
    ]
}

# =========================================================
# MEMORY
# =========================================================

visited_urls = set()

visited_hashes = set()

existing_label_counts = Counter()

all_data = []

# =========================================================
# LOAD DATASET CŨ
# =========================================================

if os.path.exists(DATASET_FILE):

    old_df = pd.read_csv(DATASET_FILE)

    print(f"Đã load dataset cũ: {len(old_df)} bài")

    # URL
    if "url" in old_df.columns:

        visited_urls.update(
            old_df["url"].dropna().tolist()
        )

    # HASH
    if "text_hash" in old_df.columns:

        visited_hashes.update(
            old_df["text_hash"].dropna().tolist()
        )

    # LABEL COUNT
    if "labels" in old_df.columns:

        for labels in old_df["labels"]:

            try:

                labels = ast.literal_eval(labels)

                existing_label_counts.update(labels)

            except:
                pass

print("\nPHÂN PHỐI LABEL HIỆN TẠI:\n")

for label, count in existing_label_counts.items():

    print(f"{label}: {count}")

# =========================================================
# HASH
# =========================================================

def create_hash(text):

    return hashlib.md5(
        text.encode("utf-8")
    ).hexdigest()

# =========================================================
# GET LINKS VNEXPRESS
# =========================================================

def get_links_vnexpress(url, pages=30):

    links = []

    for i in range(1, pages + 1):

        page_url = f"{url}-p{i}"

        try:

            print(f"VNEXPRESS: {page_url}")

            res = requests.get(
                page_url,
                headers=headers,
                timeout=10
            )

            soup = BeautifulSoup(
                res.text,
                "html.parser"
            )

            items = soup.find_all(
                ['h2', 'h3'],
                class_=['title-news', 'title_news']
            )

            for item in items:

                a_tag = item.find('a')

                if not a_tag:
                    continue

                link = a_tag.get('href')

                if not link:
                    continue

                if not link.endswith(".html"):
                    continue

                if link in visited_urls:
                    continue

                visited_urls.add(link)

                links.append(link)

            time.sleep(
                random.uniform(0.5, 1.0)
            )

        except Exception as e:

            print(e)

    return links

# =========================================================
# GET LINKS DÂN TRÍ
# =========================================================

def get_links_dantri(url, pages=30):

    links = []

    for i in range(1, pages + 1):

        page_url = f"{url}?page={i}"

        try:

            print(f"DANTRI: {page_url}")

            res = requests.get(
                page_url,
                headers=headers,
                timeout=10
            )

            soup = BeautifulSoup(
                res.text,
                "html.parser"
            )

            articles = soup.find_all("h3")

            for item in articles:

                a_tag = item.find("a")

                if not a_tag:
                    continue

                link = a_tag.get("href")

                if not link:
                    continue

                if ".htm" not in link:
                    continue

                if not link.startswith("http"):

                    link = (
                        "https://dantri.com.vn"
                        + link
                    )

                if link in visited_urls:
                    continue

                visited_urls.add(link)

                links.append(link)

            time.sleep(
                random.uniform(0.5, 1.0)
            )

        except Exception as e:

            print(e)

    return links

# =========================================================
# GET LINKS TUỔI TRẺ
# =========================================================

def get_links_tuoitre(url, pages=30):

    links = []

    for i in range(1, pages + 1):

        page_url = f"{url}/trang-{i}.htm"

        try:

            print(f"TUOITRE: {page_url}")

            res = requests.get(
                page_url,
                headers=headers,
                timeout=10
            )

            soup = BeautifulSoup(
                res.text,
                "html.parser"
            )

            articles = soup.find_all("h3")

            for item in articles:

                a_tag = item.find("a")

                if not a_tag:
                    continue

                link = a_tag.get("href")

                if not link:
                    continue

                if ".htm" not in link:
                    continue

                if not link.startswith("http"):

                    link = (
                        "https://tuoitre.vn"
                        + link
                    )

                if link in visited_urls:
                    continue

                visited_urls.add(link)

                links.append(link)

            time.sleep(
                random.uniform(0.5, 1.0)
            )

        except Exception as e:

            print(e)

    return links

# =========================================================
# GET LINKS THANH NIÊN
# =========================================================

def get_links_thanhnien(url, pages=30):

    links = []

    for i in range(1, pages + 1):

        page_url = f"{url}?trang={i}"

        try:

            print(f"THANHNIEN: {page_url}")

            res = requests.get(
                page_url,
                headers=headers,
                timeout=10
            )

            soup = BeautifulSoup(
                res.text,
                "html.parser"
            )

            articles = soup.find_all("h3")

            for item in articles:

                a_tag = item.find("a")

                if not a_tag:
                    continue

                link = a_tag.get("href")

                if not link:
                    continue

                if ".htm" not in link:
                    continue

                if not link.startswith("http"):

                    link = (
                        "https://thanhnien.vn"
                        + link
                    )

                if link in visited_urls:
                    continue

                visited_urls.add(link)

                links.append(link)

            time.sleep(
                random.uniform(0.5, 1.0)
            )

        except Exception as e:

            print(e)

    return links

# =========================================================
# PARSER VNEXPRESS
# =========================================================

def parse_vnexpress(soup):

    title_tag = soup.find(
        "h1",
        class_="title-detail"
    )

    title = (
        title_tag.get_text(strip=True)
        if title_tag else ""
    )

    paragraphs = soup.find_all(
        "p",
        class_="Normal"
    )

    content = " ".join([
        p.get_text(strip=True)
        for p in paragraphs
    ])

    return title, content

# =========================================================
# PARSER DÂN TRÍ
# =========================================================

def parse_dantri(soup):

    title_tag = soup.find("h1")

    title = (
        title_tag.get_text(strip=True)
        if title_tag else ""
    )

    content_div = soup.find(
        "div",
        class_="singular-content"
    )

    if content_div:

        paragraphs = content_div.find_all("p")

        content = " ".join([
            p.get_text(strip=True)
            for p in paragraphs
        ])

    else:

        content = ""

    return title, content

# =========================================================
# PARSER TUỔI TRẺ
# =========================================================

def parse_tuoitre(soup):

    title_tag = soup.find("h1")

    title = (
        title_tag.get_text(strip=True)
        if title_tag else ""
    )

    content_div = soup.find(
        "div",
        class_="detail-content"
    )

    if content_div:

        paragraphs = content_div.find_all("p")

        content = " ".join([
            p.get_text(strip=True)
            for p in paragraphs
        ])

    else:

        content = ""

    return title, content

# =========================================================
# PARSER THANH NIÊN
# =========================================================

def parse_thanhnien(soup):

    title_tag = soup.find("h1")

    title = (
        title_tag.get_text(strip=True)
        if title_tag else ""
    )

    content_div = soup.find(
        "div",
        class_="detail__cmain"
    )

    if content_div:

        paragraphs = content_div.find_all("p")

        content = " ".join([
            p.get_text(strip=True)
            for p in paragraphs
        ])

    else:

        content = ""

    return title, content

# =========================================================
# PARSER MAP
# =========================================================

SITE_PARSERS = {

    "vnexpress.net": parse_vnexpress,

    "dantri.com.vn": parse_dantri,

    "tuoitre.vn": parse_tuoitre,

    "thanhnien.vn": parse_thanhnien
}

# =========================================================
# CRAWL ARTICLE
# =========================================================

def crawl_article(url, label):

    try:

        res = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        soup = BeautifulSoup(
            res.text,
            "html.parser"
        )

        domain = urlparse(url).netloc

        parser_function = None

        for site, parser in SITE_PARSERS.items():

            if site in domain:

                parser_function = parser

                break

        if parser_function is None:

            return None

        title, content = parser_function(soup)

        if len(content) < 300:

            return None

        text_hash = create_hash(
            title + content
        )

        # chống duplicate
        if text_hash in visited_hashes:

            return None

        visited_hashes.add(text_hash)

        return {

            "title": title,

            "content": content,

            "labels": [label],

            "url": url,

            "text_hash": text_hash
        }

    except Exception as e:

        print(e)

        return None

# =========================================================
# MAIN
# =========================================================

for label, urls in categories.items():

    current_count = existing_label_counts[label]

    print("\n======================")
    print(f"LABEL: {label}")
    print(f"HIỆN TẠI: {current_count}")
    print("======================")

    # skip label đủ rồi
    if current_count >= TARGET_PER_LABEL:

        print(f"SKIP {label}")

        continue

    all_links = []

    # =========================================
    # GET LINKS
    # =========================================

    for url in urls:

        if "vnexpress.net" in url:

            links = get_links_vnexpress(
                url,
                pages=40
            )

        elif "dantri.com.vn" in url:

            links = get_links_dantri(
                url,
                pages=40
            )

        elif "tuoitre.vn" in url:

            links = get_links_tuoitre(
                url,
                pages=40
            )

        elif "thanhnien.vn" in url:

            links = get_links_thanhnien(
                url,
                pages=40
            )

        else:

            continue

        all_links.extend(links)

    print(f"Tổng links: {len(all_links)}")

    # =========================================
    # CRAWL
    # =========================================

    count = 0

    for link in all_links:

        # đủ label thì dừng
        if existing_label_counts[label] >= TARGET_PER_LABEL:

            print(f"Đã đủ dữ liệu cho {label}")

            break

        data = crawl_article(
            link,
            label
        )

        if data:

            all_data.append(data)

            count += 1

            existing_label_counts[label] += 1

            if count % 10 == 0:

                print(
                    f"Đã crawl: {count} bài"
                )

        time.sleep(
            random.uniform(0.3, 0.6)
        )

# =========================================================
# SAVE DATASET
# =========================================================

if len(all_data) > 0:

    new_df = pd.DataFrame(all_data)

    if os.path.exists(DATASET_FILE):

        old_df = pd.read_csv(DATASET_FILE)

        final_df = pd.concat(
            [old_df, new_df],
            ignore_index=True
        )

    else:

        final_df = new_df

    # remove duplicate
    final_df = final_df.drop_duplicates(
        subset=["text_hash"]
    )

    final_df = final_df.drop_duplicates(
        subset=["url"]
    )

    # save csv
    final_df.to_csv(
        DATASET_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # save json
    final_df.to_json(
        JSON_FILE,
        orient="records",
        force_ascii=False,
        indent=4
    )

    print("\n======================")
    print("HOÀN THÀNH")
    print("======================")

    print(f"Bài mới: {len(new_df)}")

    print(f"Tổng dataset: {len(final_df)}")

    print("\nLABEL DISTRIBUTION:")

    sorted_labels = sorted(
        existing_label_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for label, count in sorted_labels:

        print(f"{label}: {count}")

else:

    print("\nKhông có dữ liệu mới.")