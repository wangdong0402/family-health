import requests
import json
import os

def clean_and_truncate(value, max_len):
    """清理数据：兼容列表，并强制截断长度"""
    if not value:
        return ""
    if isinstance(value, list):
        value = "，".join([str(v).strip() for v in value if v])
    text = str(value).strip()
    # 替换掉文本中可能存在的换行符，方便展示
    text = text.replace("\n", " ").replace("\r", " ")
    if len(text) > max_len:
        return text[:max_len] + "..."
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
    for item in raw_records:
        title = clean_and_truncate(item.get("name"), 50)
        if not title:
            continue
            
        # 【核心调整】：放宽字数限制，保留更多干货，同时兼顾体积
        index.append({
            "title": title,
            "desc": clean_and_truncate(item.get("desc"), 200),        # 简介 200 字
            "cause": clean_and_truncate(item.get("cause"), 300),      # 病因 300 字
            "symptom": clean_and_truncate(item.get("symptom"), 300),  # 症状 300 字
            "cure_way": clean_and_truncate(item.get("cure_way"), 300),# 治疗 300 字
            "prevent": clean_and_truncate(item.get("prevent"), 300),  # 预防 300 字
            "department": clean_and_truncate(item.get("cure_department"), 50),
            "category": "常见疾病"
        })

    os.makedirs("data", exist_ok=True)
    with open("data/search_index.json", "w", encoding="utf-8") as f:
        # 紧凑格式，进一步减小体积
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = os.path.getsize("data/search_index.json") / 1024
    print(f"[完成] 成功生成索引，共 {len(index)} 条数据")
    print(f"[完成] 瘦身后文件体积: {size_kb:.1f} KB (预期在 3MB~5MB 左右)")

if __name__ == "__main__":
    build_search_index()
