import requests
import json
import os
import re

def clean_and_shorten(value):
    """清理数据：截取到第一个句号，最大100字"""
    if not value:
        return ""
    if isinstance(value, list):
        value = "，".join([str(v).strip() for v in value if v])
    
    text = str(value).strip().replace("\n", " ").replace("\r", " ")
    # 尝试截取第一句话，保留核心定义
    match = re.search(r'([^。！？]+[。！？])', text)
    if match:
        text = match.group(1)
        
    if len(text) > 100:
        return text[:100] + "..."
    return text

def build_search_index():
    print("[信息] 开始获取结构化疾病知识库...")
    
    urls = [
        "https://raw.githubusercontent.com/nuolade/disease-kb/master/data/medical.json",
        "https://cdn.jsdelivr.net/gh/nuolade/disease-kb@master/data/medical.json"
    ]
    
    raw_records = []
    for url in urls:
        try:
            print(f"[尝试] 下载 {url} ...")
            resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            
            for line in resp.text.splitlines():
                if line.strip():
                    raw_records.append(json.loads(line))
            
            if raw_records:
                print(f"[成功] 成功下载并解析 {len(raw_records)} 条疾病结构化数据")
                break
        except Exception as e:
            print(f"[跳过] 下载失败: {e}")

    if not raw_records:
        print("[失败] 无法获取数据源，生成空索引。")
        os.makedirs("data", exist_ok=True)
        with open("data/search_index.json", "w", encoding="utf-8") as f:
            json.dump([], f)
        return

    index = []
    # 【核心限制】：只取前 2000 条常见病
    for item in raw_records[:2000]:
        title = clean_and_shorten(item.get("name"))
        if not title:
            continue
            
        index.append({
            "title": title,
            "desc": clean_and_shorten(item.get("desc")),
            "cause": clean_and_shorten(item.get("cause")),
            "symptom": clean_and_shorten(item.get("symptom")),
            "cure_way": clean_and_shorten(item.get("cure_way")),
            "prevent": clean_and_shorten(item.get("prevent")),
            "department": clean_and_shorten(item.get("cure_department")),
            "category": "常见疾病"
        })

    os.makedirs("data", exist_ok=True)
    with open("data/search_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = os.path.getsize("data/search_index.json") / 1024
    print(f"[完成] 成功生成索引，共 {len(index)} 条核心数据")
    print(f"[完成] 极限瘦身后文件体积: {size_kb:.1f} KB (预计 500KB 左右)")

if __name__ == "__main__":
    build_search_index()
