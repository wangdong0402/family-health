import json
import os
import re
import requests
import sys

# 修复Action ASCII编码报错
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

OUTPUT_PATH = "data/videos_index.json"
MANUAL_PATH = "data/manual_videos.json"
# 健康之路 节目单页（里面是一集一集独立播放页链接）
CCTV_URL = "https://tv.cctv.com/lm/jkzl/videos/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_html(raw_text: str) -> str:
    if not raw_text:
        return ""
    # 清除html标签
    text = re.sub(r"<[^>]+>", "", raw_text)
    # 清除特殊unicode符号、多余空白
    text = re.sub(r'[\u2000-\u206F]', '-', text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def load_manual_data():
    if os.path.exists(MANUAL_PATH):
        with open(MANUAL_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def fetch_cctv_health_road():
    item_list = []
    seen_url = set()
    try:
        resp = requests.get(CCTV_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html_text = resp.text

        # 匹配单条视频播放链接：https://tv.cctv.com/20xx/xx/xx/VIDxxxxxx.shtml
        pattern = re.compile(r'<a\s+href="(https://tv.cctv.com/\d{4}/\d{2}/\d{2}/VID[^"]+\.shtml)"[^>]*title="([^"]+)"')
        matches = pattern.findall(html_text)

        item_id = 1000
        for link, title in matches:
            if not link or link in seen_url:
                continue
            seen_url.add(link)
            clean_title = clean_html(title)
            # 简单关键词自动分类
            category = "代谢三高"
            kw_digest = clean_title
            if any(k in kw_digest for k in ["胃", "肠", "消化", "胃炎", "腹痛", "便秘"]):
                category = "消化胃肠"

            item = {
                "id": item_id,
                "title": clean_title,
                "source": "央视健康之路",
                "category": category,
                "tags": [],
                "url": link,
                "desc": "央视科教《健康之路》专家科普节目"
            }
            item_list.append(item)
            item_id +=1
            if len(item_list)>=30:
                break
        print(f"✅ 网页抓取成功，获取 {len(item_list)} 条央视健康之路单集视频")

    except Exception as e:
        print(f"⚠️ 抓取央视页面失败：{str(e)}，将使用手动兜底数据")
        item_list = []
    return item_list


def main():
    crawl_data = fetch_cctv_health_road()
    manual_data = load_manual_data()

    if crawl_data:
        final = crawl_data + manual_data
    else:
        final = manual_data

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, separators=(',', ':'))

    print(f"✅ 视频索引生成完成，一共 {len(final)} 条")

if __name__ == "__main__":
    main()
