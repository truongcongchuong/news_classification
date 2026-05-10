import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import json

# =========================================================
# 1. CẤU HÌNH BỘ TỪ ĐIỂN NHÃN (TOPIC MAPPING) MỞ RỘNG
# =========================================================
TOPIC_MAPPING = {
    "Chính trị - Pháp luật": ["luật", "thể chế", "nghị quyết", "quốc hội", "chính phủ", "pháp lý", "thẩm quyền", "pháp chế", "tòa án", "vi phạm"],
    "Kinh tế - Đầu tư": ["doanh nghiệp", "tài chính", "vốn", "tài khóa", "đầu tư", "kinh doanh", "thị trường", "ngân hàng", "giá vàng", "bất động sản"],
    "Môi trường - Sinh thái": ["chim", "động vật", "quý hiếm", "sách đỏ", "kiểm lâm", "thiên nhiên", "môi trường", "ô nhiễm", "biến đổi khí hậu"],
    "Khoa học - Công nghệ": ["khoa học", "công nghệ", "thử nghiệm", "dữ liệu", "số hóa", "ai", "trí tuệ nhân tạo", "phần mềm", "chip", "bán dẫn"],
    "Y tế - Sức khỏe": ["bệnh viện", "bác sĩ", "y tế", "sức khỏe", "vắc xin", "dịch bệnh", "điều trị", "thuốc", "dược phẩm"],
    "Giáo dục - Đào tạo": ["trường học", "sinh viên", "giáo viên", "đào tạo", "tuyển sinh", "học phí", "đại học", "thi cử", "điểm thi"],
    "Thể thao": [
        "bóng đá", "v-league", "ngoại hạng anh", "tennis", "quần vợt", "nadal", "djokovic", 
        "bóng rổ", "nba", "cầu lông", "bóng chuyền", "võ thuật", "mma", "boxing", 
        "điền kinh", "marathon", "bơi lội", "huy chương", "giải đấu", "olympic"
    ],
    "Văn hóa - Giải trí": ["nghệ sĩ", "ca sĩ", "diễn viên", "phim", "âm nhạc", "showbiz", "sự kiện", "triển lãm", "cuộc thi"],
    "Giao thông - Xe": ["xe máy", "ô tô", "vinfast", "giao thông", "đường bộ", "cao tốc", "hàng không", "xe điện"],
    "Du lịch - Đời sống": ["du lịch", "điểm đến", "khách sạn", "ẩm thực", "gia đình", "con cái", "kết hôn", "hôn nhân"]
}

# =========================================================
# 2. DANH SÁCH CHUYÊN MỤC CÀO ĐẦY ĐỦ
# =========================================================
categories = {
    "Thời sự": {"url": "https://vnexpress.net/thoi-su", "num_pages": 50},
    "Thế giới": {"url": "https://vnexpress.net/the-giol", "num_pages": 50},
    "Kinh tế": {"url": "https://vnexpress.net/kinh-doanh", "num_pages": 50},
    "Thể thao": {"url": "https://vnexpress.net/the-thao", "num_pages": 50},
    "Giải trí": {"url": "https://vnexpress.net/giai-tri", "num_pages": 50},
    "Pháp luật": {"url": "https://vnexpress.net/phap-luat", "num_pages": 50},
    "Giáo dục": {"url": "https://vnexpress.net/giao-duc", "num_pages": 50},
    "Sức khỏe": {"url": "https://vnexpress.net/suc-khoe", "num_pages": 50},
    "Đời sống": {"url": "https://vnexpress.net/gia-dinh", "num_pages": 50},
    "Du lịch": {"url": "https://vnexpress.net/du-lich", "num_pages": 50},
    "Khoa học": {"url": "https://vnexpress.net/khoa-hoc", "num_pages": 50},
    "Số hóa": {"url": "https://vnexpress.net/so-hoa", "num_pages": 50},
    "Xe": {"url": "https://vnexpress.net/oto-xe-may", "num_pages": 50}
}

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"}
all_data = []
visited_urls = set()

# =========================================================
# 3. LOGIC CÀO VÀ XỬ LÝ NHÃN DẠNG LIST
# =========================================================

def get_article_links(cat_name, cat_url, pages):
    links = []
    for i in range(1, pages + 1):
        page_url = f"{cat_url}-p{i}"
        print(f"--- Đang quét link: {cat_name} (Trang {i}) ---")
        try:
            res = requests.get(page_url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, "html.parser")
            items = soup.find_all(['h2', 'h3'], class_=['title-news', 'title_news'])
            for item in items:
                a_tag = item.find('a')
                if a_tag and 'href' in a_tag.attrs:
                    link = a_tag['href']
                    if link.endswith('.html') and link not in visited_urls:
                        links.append(link)
                        visited_urls.add(link)
            time.sleep(random.uniform(0.5, 1.0))
        except: continue
    return links

def crawl_and_label_article(url, default_label):
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        
        title_tag = soup.find("h1", class_="title-detail")
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        paragraphs = soup.find_all("p", class_="Normal")
        content = " ".join([p.get_text(strip=True) for p in paragraphs])
        
        if len(content) < 300: return None

        tags_elements = soup.find_all("h4", class_="item-tag")
        raw_tags = [t.get_text(strip=True).lower() for t in tags_elements]
        full_text_lower = (title + " " + content).lower()

        # TẠO NHÃN DẠNG LIST
        final_labels = set()
        final_labels.add(default_label)

        for topic, keywords in TOPIC_MAPPING.items():
            for word in keywords:
                if word in raw_tags or word in full_text_lower:
                    final_labels.add(topic)
                    break 
        
        return {
            "title": title,
            "content": content,
            "labels": list(final_labels), # Lưu dưới dạng List thực thụ
            "url": url
        }
    except: return None

# =========================================================
# 4. CHƯƠNG TRÌNH CHÍNH
# =========================================================

for cat_name, info in categories.items():
    links = get_article_links(cat_name, info['url'], info['num_pages'])
    count = 0
    for link in links:
        data = crawl_and_label_article(link, cat_name)
        if data:
            all_data.append(data)
            count += 1
            if count % 10 == 0:
                print(f"  > Đã cào: {count}/{len(links)} bài [{cat_name}]")
        time.sleep(random.uniform(0.3, 0.5))

# Lưu file kết quả
if all_data:
    df = pd.DataFrame(all_data)
    
    # Khi lưu CSV, List sẽ bị biến thành chuỗi dạng "[label1, label2]".
    # Đây là định dạng chuẩn của Pandas khi lưu list vào CSV.
    filename = "vnexpress_multilabel_list.csv"
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    
    # Ngoài ra, tôi khuyên bạn nên lưu thêm 1 bản JSON để giữ nguyên định dạng list xịn
    df.to_json("vnexpress_multilabel_list.json", orient="records", force_ascii=False, indent=4)
    
    print(f"\n--- HOÀN THÀNH ---")
    print(f"Tổng số bài: {len(df)}")
    print(f"Đã lưu CSV và JSON với nhãn dạng list.")