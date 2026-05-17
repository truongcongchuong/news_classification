import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import hashlib
import os
import re

from urllib.parse import urlparse
from collections import Counter

# =========================================================
# CONFIG
# =========================================================

DATASET_FILE = "Data.csv"

JSON_FILE = "Data.json"

TARGET_PER_LABEL = 2000

MIN_CONTENT_LENGTH = 300

MAX_LABELS = 2

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
# CATEGORY URLS
# =========================================================

categories = {

    "Kinh tế": [

        "https://vnexpress.net/kinh-doanh",

        "https://dantri.com.vn/kinh-doanh.htm",

        "https://tuoitre.vn/kinh-doanh.htm"
    ],

    "Khoa học - Công nghệ": [

        "https://vnexpress.net/so-hoa",

        "https://vnexpress.net/khoa-hoc",

        "https://dantri.com.vn/suc-manh-so.htm",

        "https://tuoitre.vn/nhip-song-so.htm"
    ],

    "Giáo dục": [

        "https://vnexpress.net/giao-duc",

        "https://dantri.com.vn/giao-duc.htm",

        "https://tuoitre.vn/giao-duc.htm"
    ],

    "Sức khỏe": [

        "https://vnexpress.net/suc-khoe",

        "https://dantri.com.vn/suc-khoe.htm"
    ],

    "Thể thao": [

        "https://vnexpress.net/the-thao",

        "https://dantri.com.vn/the-thao.htm"
    ],

    "Giải trí": [

        "https://vnexpress.net/giai-tri",

        "https://thanhnien.vn/giai-tri.htm"
    ],

    "Thế giới": [

        "https://vnexpress.net/the-gioi",

        "https://dantri.com.vn/the-gioi.htm"
    ],

    "Xe": [

        "https://vnexpress.net/oto-xe-may",

        "https://dantri.com.vn/o-to-xe-may.htm"
    ],

    "Du lịch": [

        "https://vnexpress.net/du-lich",

        "https://thanhnien.vn/du-lich.htm"
    ],

    "Nhà đất": [

        "https://vnexpress.net/bat-dong-san",

        "https://dantri.com.vn/bat-dong-san.htm"
    ],

    "Môi trường": [

        "https://vnexpress.net/khoa-hoc-moi-truong",

        "https://thanhnien.vn/moi-truong.htm"
    ],

    "Chính trị - Pháp luật": [

        "https://vnexpress.net/phap-luat",

        "https://dantri.com.vn/phap-luat.htm"
    ]
}

# =========================================================
# ALLOWED SECONDARY LABELS
# =========================================================

ALLOWED_SECONDARY_LABELS = {

    "Kinh tế": [
        "Khoa học - Công nghệ",
        "Thế giới",
        "Nhà đất"
    ],

    "Khoa học - Công nghệ": [
        "Kinh tế",
        "Giáo dục",
        "Sức khỏe"
    ],

    "Giáo dục": [
        "Khoa học - Công nghệ"
    ],

    "Sức khỏe": [
        "Thế giới",
        "Khoa học - Công nghệ"
    ],

    "Xe": [
        "Kinh tế",
        "Khoa học - Công nghệ"
    ],

    "Thế giới": [
        "Kinh tế",
        "Chính trị - Pháp luật"
    ],

    "Nhà đất": [
        "Kinh tế"
    ]
}

# =========================================================
# SECONDARY LABEL KEYWORDS
# =========================================================

SECONDARY_KEYWORDS = {

    "Khoa học - Công nghệ": [

        "trí tuệ nhân tạo",

        "machine learning",

        "deep learning",

        "chatgpt",

        "openai",

        "robot",

        "chip bán dẫn",

        "blockchain",

        "cybersecurity",

        "an ninh mạng",

        "điện toán đám mây",

        "dữ liệu lớn"
    ],

    "Kinh tế": [

        "đầu tư",

        "tài chính",

        "chứng khoán",

        "ngân hàng",

        "doanh nghiệp",

        "thị trường"
    ],

    "Thế giới": [

        "ukraine",

        "nga",

        "trung quốc",

        "israel",

        "gaza",

        "nato",

        "liên hợp quốc"
    ],

    "Nhà đất": [

        "bất động sản",

        "chung cư",

        "đất nền",

        "dự án"
    ],

    "Giáo dục": [

        "học sinh",

        "sinh viên",

        "trường học",

        "đại học"
    ],

    "Sức khỏe": [

        "bệnh viện",

        "bác sĩ",

        "điều trị",

        "dịch bệnh"
    ],

    "Chính trị - Pháp luật": [

        "quốc hội",

        "chính phủ",

        "tòa án",

        "xét xử",

        "điều tra"
    ]
}

# =========================================================
# MEMORY
# =========================================================

visited_urls = set()

visited_hashes = set()

label_counts = Counter()

all_data = []

# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(text):

    text = re.sub(r"\s+", " ", text)

    return text.strip()

# =========================================================
# HASH
# =========================================================

def create_hash(text):

    text = clean_text(text)

    return hashlib.md5(
        text.encode("utf-8")
    ).hexdigest()

# =========================================================
# KEYWORD MATCH
# =========================================================

def keyword_match(keyword, text):

    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

    return re.search(pattern, text) is not None

# =========================================================
# GENERATE MULTI LABELS
# =========================================================

def generate_labels(
    main_label,
    title,
    content
):

    labels = [main_label]

    full_text = (
        title + " " + content
    ).lower()

    allowed = ALLOWED_SECONDARY_LABELS.get(
        main_label,
        []
    )

    for secondary_label in allowed:

        keywords = SECONDARY_KEYWORDS.get(
            secondary_label,
            []
        )

        score = 0

        for keyword in keywords:

            if keyword_match(
                keyword,
                full_text
            ):

                score += 1

        # threshold mạnh
        if score >= 2:

            labels.append(
                secondary_label
            )

        # giới hạn số labels
        if len(labels) >= MAX_LABELS:

            break

    return labels

# =========================================================
# GET LINKS
# =========================================================

def get_links(
    url,
    site_type,
    pages=50
):

    links = []

    for i in range(1, pages + 1):

        try:

            if site_type == "vnexpress":

                page_url = f"{url}-p{i}"

            elif site_type == "dantri":

                page_url = f"{url}?page={i}"

            elif site_type == "tuoitre":

                page_url = f"{url}/trang-{i}.htm"

            elif site_type == "thanhnien":

                page_url = f"{url}?trang={i}"

            else:

                continue

            print(page_url)

            res = requests.get(
                page_url,
                headers=headers,
                timeout=10
            )

            soup = BeautifulSoup(
                res.text,
                "html.parser"
            )

            for a in soup.find_all(
                "a",
                href=True
            ):

                link = a["href"]

                if not link.startswith("http"):

                    if "tuoitre.vn" in url:

                        link = (
                            "https://tuoitre.vn"
                            + link
                        )

                    elif "dantri.com.vn" in url:

                        link = (
                            "https://dantri.com.vn"
                            + link
                        )

                    elif "thanhnien.vn" in url:

                        link = (
                            "https://thanhnien.vn"
                            + link
                        )

                if (
                    ".html" not in link
                    and ".htm" not in link
                ):
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

    return list(set(links))

# =========================================================
# PARSERS
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

SITE_PARSERS = {

    "vnexpress.net": parse_vnexpress,

    "dantri.com.vn": parse_dantri,

    "tuoitre.vn": parse_tuoitre,

    "thanhnien.vn": parse_thanhnien
}

# =========================================================
# CRAWL ARTICLE
# =========================================================

def crawl_article(
    url,
    main_label
):

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

        title = clean_text(title)

        content = clean_text(content)

        if len(content) < MIN_CONTENT_LENGTH:

            return None

        text_hash = create_hash(
            title + content
        )

        if text_hash in visited_hashes:

            return None

        visited_hashes.add(text_hash)

        labels = generate_labels(
            main_label,
            title,
            content
        )

        return {

            "title": title,

            "content": content,

            "labels": labels,

            "url": url
        }

    except Exception as e:

        print(e)

        return None

# =========================================================
# MAIN
# =========================================================

for label, urls in categories.items():

    print("\n======================")
    print(f"LABEL: {label}")
    print("======================")

    if label_counts[label] >= TARGET_PER_LABEL:

        continue

    all_links = []

    for url in urls:

        if "vnexpress.net" in url:

            links = get_links(
                url,
                "vnexpress"
            )

        elif "dantri.com.vn" in url:

            links = get_links(
                url,
                "dantri"
            )

        elif "tuoitre.vn" in url:

            links = get_links(
                url,
                "tuoitre"
            )

        elif "thanhnien.vn" in url:

            links = get_links(
                url,
                "thanhnien"
            )

        else:

            continue

        all_links.extend(links)

    all_links = list(set(all_links))

    print(f"Tổng links: {len(all_links)}")

    crawl_count = 0

    for link in all_links:

        if label_counts[label] >= TARGET_PER_LABEL:

            print(f"Đủ dữ liệu cho {label}")

            break

        data = crawl_article(
            link,
            label
        )

        if data:

            all_data.append(data)

            crawl_count += 1

            for lb in data["labels"]:

                label_counts[lb] += 1

            if crawl_count % 10 == 0:

                print(
                    f"Đã crawl: {crawl_count} bài"
                )

        time.sleep(
            random.uniform(0.3, 0.7)
        )

# =========================================================
# SAVE DATASET
# =========================================================

if len(all_data) > 0:

    df = pd.DataFrame(all_data)

    # remove duplicate url
    df = df.drop_duplicates(
        subset=["url"]
    )

    # remove duplicate content
    df["text_hash"] = df.apply(

        lambda x: create_hash(
            str(x["title"])
            + str(x["content"])
        ),

        axis=1
    )

    df = df.drop_duplicates(
        subset=["text_hash"]
    )

    df = df.drop(
        columns=["text_hash"]
    )

    # save csv
    df.to_csv(

        DATASET_FILE,

        index=False,

        encoding="utf-8-sig"
    )

    # save json
    df.to_json(

        JSON_FILE,

        orient="records",

        force_ascii=False,

        indent=4
    )

    print("\n======================")
    print("HOÀN THÀNH")
    print("======================")

    print(f"Tổng dataset: {len(df)}")

    print("\nLABEL DISTRIBUTION:\n")

    sorted_labels = sorted(

        label_counts.items(),

        key=lambda x: x[1],

        reverse=True
    )

    for label, count in sorted_labels:

        print(f"{label}: {count}")

else:

    print("\nKhông có dữ liệu.")