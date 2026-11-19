import json
import os
import yaml
import feedparser

OUTPUT_PATH = "data/videos_index.json"
CONFIG_PATH = "sources.yaml"

def main():
    # 读取yaml配置
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    video_sources = cfg.get("video_sources", [])

    result_list = []
    seen_urls = set()
    item_id = 1

    for src in video_sources:
        src_name = src["name"]
        rss_url = src["url"]
        default_cat = src["default_category"]

        # 解析rss
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            link = entry.get("link", "")
            if not link or link in seen_urls:
                continue
            seen_urls.add(link)

            title = entry.get("title", "")
            desc = entry.get("summary", "")

            item = {
                "id": item_id,
                "title": title,
                "source": src_name,
                "category": default_cat,
                "tags": [],
                "url": link,
                "desc": desc
            }
            result_list.append(item)
            item_id += 1

    # 写入json
    os.makedirs("data", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, separators=(',', ':'))

    print(f"✅ 视频索引生成完成，一共 {len(result_list)} 条")

if __name__ == "__main__":
    main()
