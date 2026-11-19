import json
import os
import re
import requests
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

OUTPUT_PATH = "data/videos_index.json"
MANUAL_PATH = "data/manual_videos.json"
# ✅ 修正后的正确链接
CCTV_URL = "https://tv.cctv.com/lm/jkzl/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_html(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]+>", "", raw_text)
    text = re.sub(r'[\u2000-\u206F]', '', text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def load_manual():
    if os.path.exists(MANUAL_PATH):
        with open(MANUAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def fetch_cctv():
    item_list = []
    seen_url = set()
    try:
        resp = requests.get(CCTV_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text
        pattern = re.compile(r'href="(https://tv.cctv.com/[^"]+/VID[^"]+\.shtml)"[^>]*title="([^"]+)"')
        matches = pattern.findall(html)
        item_id = 1000
        for link, title in matches:
            if link in seen_url:
                continue
            seen_url.add(link)
            clean_title = clean_html(title)
            item = {
                "id": item_id,
                "title": clean_title,
                "source": "央视健康",
                "url": link,
                "desc": "央视《健康之路》科普视频"
            }
            item_list.append(item)
            item_id += 1
            if len(item_list) >= 30:
                break
        print(f"✅ 央视健康抓取成功，共 {len(item_list)} 条")
    except Exception as e:
        print(f"⚠️ 央视健康抓取失败：{str(e)}")
    return item_list

def main():
    cctv_data = fetch_cctv()
    manual_data = load_manual()
    all_data = cctv_data + manual_data
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"✅ 总数据生成完成，合计 {len(all_data)} 条")

if __name__ == "__main__":
    main()
