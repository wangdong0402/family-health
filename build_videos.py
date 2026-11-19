import json
import os
import re
import requests

OUTPUT_PATH = "data/videos_index.json"
MANUAL_PATH = "data/manual_videos.json"
# 央视健康之路列表页面
CCTV_URL = "https://tv.cctv.com/lm/jkzl/"
HEADERS = {
    "User‑Agent": "Mozilla/5.0 (Windows NT10; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_html(raw_text: str) -> str:
    """清除html标签、换行空格"""
    if not raw_text:
        return ""
    text = re.sub(r"<[^>]+>", "", raw_text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def load_manual_data():
    """加载手动兜底视频库"""
    if os.path.exists(MANUAL_PATH):
        with open(MANUAL_PATH, "r", encoding="utf‑8") as f:
            return json.load(f)
    return []

def fetch_cctv_health_road():
    """抓取央视健康之路列表，解析视频条目"""
    item_list = []
    seen_url = set()
    try:
        resp = requests.get(CCTV_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        html_text = resp.text

        # 正则提取节目标题、链接（适配当前页面结构）
        # 匹配形如 <a href="xxx" title="《健康之路》 xxxx">
        pattern = re.compile(r'<a\s+href="(https?://[^"]+)"[^>]*title="(《健康之路》[^"]+)"')
        matches = pattern.findall(html_text)

        item_id = 1000  # 抓取数据id从1000开始，和兜底id区分
        for link, title in matches:
            if not link or link in seen_url:
                continue
            seen_url.add(link)
            item = {
                "id": item_id,
                "title": clean_html(title),
                "source": "央视健康之路",
                "category": "代谢三高",
                "tags": [],
                "url": link,
                "desc": "央视科教《健康之路》专家科普节目"
            }
            item_list.append(item)
            item_id +=1
            # 控制最多抓取30条，避免json过大
            if len(item_list)>=30:
                break
        print(f"✅ 网页抓取成功，获取 {len(item_list)} 条央视健康之路节目")

    except Exception as e:
        print(f"⚠️ 抓取央视页面失败：{str(e)}，将使用手动兜底数据")
        item_list = []
    return item_list


def main():
    crawl_data = fetch_cctv_health_road()
    manual_data = load_manual_data()

    # 如果抓取到内容：抓取数据优先，兜底数据追加在后面
    if crawl_data:
        final = crawl_data + manual_data
    else:
        # 抓取完全失败，只用兜底
        final = manual_data

    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf‑8") as f:
        json.dump(final, f, ensure_ascii=False, separators=(',', ':'))

    print(f"✅ 视频索引生成完成，一共 {len(final)} 条")

if __name__ == "__main__":
    main()
