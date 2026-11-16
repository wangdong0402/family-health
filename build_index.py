import requests
import json
import os

def clean_text(value):
    """清理数据：兼容字符串、列表、None 等多种格式"""
    if not value:
        return ""
    if isinstance(value, list):
        # 如果是列表，将里面的元素转化为字符串并用逗号拼接
        return "，".join([str(v).strip() for v in value if v])
    # 其他情况（字符串、数字等）统一转为字符串并去首尾空格
    return str(value).strip()

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
            
            # JSONL 格式逐行解析
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
        # 使用 clean_text 统一处理所有字段，彻底避免 list 报错
        title = clean_text(item.get("name"))
        if not title:
            continue
            
        index.append({
            "title": title,
            "desc": clean_text(item.get("desc")),
            "cause": clean_text(item.get("cause")),
            "prevent": clean_text(item.get("prevent")),
            "symptom": clean_text(item.get("symptom")),
            "cure_way": clean_text(item.get("cure_way")),
            "department": clean_text(item.get("cure_department")),
            "category": "常见疾病"
        })

    os.makedirs("data", exist_ok=True)
    with open("data/search_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize("data/search_index.json") / 1024
    print(f"[完成] 成功生成索引，共 {len(index)} 条高质量疾病数据")
    print(f"[完成] 文件体积: {size_kb:.1f} KB")

if __name__ == "__main__":
    build_search_index()
