import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import hashlib
import os
import ast
import re

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
# MULTI LABEL KEYWORDS
# =========================================================

TOPIC_MAPPING = {

    "Chính trị - Pháp luật": [
        "luật",
        "quốc hội",
        "chính phủ",
        "tòa án",
        "vi phạm",
        "pháp luật",
        "công an",
        "xét xử",
        "điều tra"
    ],

    "Kinh tế - Đầu tư": [
        "doanh nghiệp",
        "đầu tư",
        "tài chính",
        "ngân hàng",
        "chứng khoán",
        "giá vàng",
        "thị trường",
        "kinh doanh"
    ],

    "Y tế - Sức khỏe": [
        "bệnh viện",
        "bác sĩ",
        "sức khỏe",
        "điều trị",
        "dịch bệnh",
        "thuốc",
        "cấp cứu",
        "tai nạn"
    ],

    "Giao thông - Xe": [
        "ôtô",
        "ô tô",
        "xe máy",
        "tai nạn",
        "giao thông",
        "cao tốc",
        "đường bộ",
        "xe tải",
        "container"
    ],

    "Giáo dục - Đào tạo": [
        "trường học",
        "học sinh",
        "sinh viên",
        "giáo viên",
        "thi tốt nghiệp",
        "đại học"
    ],

    "Khoa học - Công nghệ": [
        "ai",
        "trí tuệ nhân tạo",
        "công nghệ",
        "phần mềm",
        "chip",
        "robot",
        "dữ liệu",
        "internet"
    ],

    "Văn hóa - Giải trí": [
        "ca sĩ",
        "diễn viên",
        "âm nhạc",
        "phim",
        "showbiz",
        "concert"
    ],

    "Thể thao": [
        "bóng đá",
        "v-league",
        "tennis",
        "olympic",
        "marathon",
        "nba"
    ],

    "Du lịch - Đời sống": [
        "du lịch",
        "khách sạn",
        "ẩm thực",
        "đời sống",
        "gia đình"
    ],

    "Môi trường - Sinh thái": [
        "môi trường",
        "ô nhiễm",
        "biến đổi khí hậu",
        "động vật",
        "rừng"
    ],

    "Thế giới": [
        "ukraine",
        "nga",
        "trung quốc",
        "liên hợp quốc",
        "eu",
        "nato",
        "israel",
        "gaza",
        "iran",
        "triều tiên",
        "hàn quốc",
        "nhật bản",
        "thái lan",
        "campuchia",
        "ngoại giao",
        "chiến sự",
        "xung đột",
        "quốc tế"
    ],

    "Xã hội": [
        "người dân",
        "đời sống",
        "cộng đồng",
        "xã hội"
    ],

    "Nhà đất": [
        "bất động sản",
        "nhà đất",
        "chung cư",
        "dự án",
        "đất nền"
    ],

    "Thời sự": [
        "thời sự",
        "sự việc",
        "hiện trường",
        "địa phương",
        "người dân"
    ]
}

# =========================================================
# CHỈ CRAWL LABEL THIẾU
# =========================================================

categories = {

    "Thế giới": [

        "https://vnexpress.net/the-gioi",

        "https://tuoitre.vn/the-gioi.htm",

        "https://dantri.com.vn/the-gioi.htm",

        "https://thanhnien.vn/the-gioi.htm"
    ],

    "Xã hội": [

        "https://dantri.com.vn/xa-hoi.htm",

        "https://tuoitre.vn/thoi-su.htm",

        "https://thanhnien.vn/thoi-su.htm"
    ],

    "Nhà đất": [

        "https://vnexpress.net/bat-dong-san",

        "https://dantri.com.vn/bat-dong-san.htm"
    ],

    "Du lịch - Đời sống": [

        "https://vnexpress.net/du-lich",

        "https://tuoitre.vn/du-lich.htm",

        "https://thanhnien.vn/du-lich.htm"
    ],

    "Y tế - Sức khỏe": [

        "https://vnexpress.net/suc-khoe",

        "https://dantri.com.vn/suc-khoe.htm",

        "https://thanhnien.vn/suc-khoe.htm"
    ],

    "Giáo dục - Đào tạo": [

        "https://vnexpress.net/giao-duc",

        "https://tuoitre.vn/giao-duc.htm",

        "https://dantri.com.vn/giao-duc.htm"
    ],

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
# LOAD OLD DATASET
# =========================================================

if os.path.exists(DATASET_FILE):

    old_df = pd.read_csv(DATASET_FILE)

    print(f"Đã load dataset cũ: {len(old_df)} bài")

    if "url" in old_df.columns:

        visited_urls.update(
            old_df["url"].dropna().tolist()
        )

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
# KEYWORD MATCH
# =========================================================

def keyword_match(keyword, text):

    pattern = r"\b" + re.escape(keyword.lower()) + r"\b"

    return re.search(pattern, text) is not None

# =========================================================
# MULTI LABEL GENERATOR
# =========================================================

def generate_labels(
    default_label,
    title,
    content
):

    labels = set()

    labels.add(default_label)

    full_text = (
        title + " " + content
    ).lower()

    for topic, keywords in TOPIC_MAPPING.items():

        score = 0

        for keyword in keywords:

            if keyword_match(keyword, full_text):

                score += 1

        # thế giới threshold thấp hơn
        if topic == "Thế giới":

            if score >= 1:

                labels.add(topic)

        else:

            if score >= 2:

                labels.add(topic)

    return list(labels)

# =========================================================
# GET LINKS VNEXPRESS
# =========================================================

def get_links_vnexpress(url, pages=80):

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
# GET LINKS DANTRI
# =========================================================

def get_links_dantri(url=80, pages=80):

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
# GET LINKS TUOITRE
# =========================================================

def get_links_tuoitre(url=80, pages=80):

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
# GET LINKS THANHNIEN
# =========================================================

def get_links_thanhnien(url=80, pages=80):

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
# VNEXPRESS PARSER
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
# DANTRI PARSER
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
# TUOITRE PARSER
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
# THANHNIEN PARSER
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

        # lọc bài ngắn
        if len(content) < 300:

            return None

        # duplicate bằng hash trong RAM
        text_hash = create_hash(
            title + content
        )

        if text_hash in visited_hashes:

            return None

        visited_hashes.add(text_hash)

        # generate labels
        final_labels = generate_labels(
            label,
            title,
            content
        )

        return {

            "title": title,

            "content": content,

            "labels": final_labels,

            "url": url
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

    if current_count >= TARGET_PER_LABEL:

        print(f"SKIP {label}")

        continue

    all_links = []

    # GET LINKS
    for url in urls:

        if "vnexpress.net" in url:

            links = get_links_vnexpress(
                url
            )

        elif "dantri.com.vn" in url:

            links = get_links_dantri(
                url
            )

        elif "tuoitre.vn" in url:

            links = get_links_tuoitre(
                url
            )

        elif "thanhnien.vn" in url:

            links = get_links_thanhnien(
                url
            )

        else:

            continue

        all_links.extend(links)

    print(f"Tổng links: {len(all_links)}")

    # CRAWL
    count = 0

    for link in all_links:

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

            # update counts
            for lb in data["labels"]:

                existing_label_counts[lb] += 1

            if count % 10 == 0:

                print(
                    f"Đã crawl: {count} bài"
                )

        time.sleep(
            random.uniform(0.3, 0.6)
        )

# =========================================================
# SAVE
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

    # remove duplicate url
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