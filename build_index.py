import requests
import json
import os

def clean_text(value, max_len=800):
    """清理数据：兼容列表、去除换行、限制最大字数"""
    if not value:
        return ""
    if isinstance(value, list):
        value = "，".join([str(v).strip() for v in value if v])
    
    text = str(value).strip().replace("\n", " ").replace("\r", " ")
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
    # 只取前 2000 条常见病
    for item in raw_records[:2000]:
        title = clean_text(item.get("name"), 50)
        if not title:
            continue
            
        # 提取并合并推荐用药和常用药品
        drugs = []
        if item.get("recommand_drug"):
            drugs.extend(item["recommand_drug"])
        if item.get("common_drug"):
            drugs.extend(item["common_drug"])
        # 去重并截取前 15 个药名，防止某些病变态多
        unique_drugs = list(dict.fromkeys(drugs))[:15]
            
        index.append({
            "title": title,
            "desc": clean_text(item.get("desc")),
            "cause": clean_text(item.get("cause")),
            "symptom": clean_text(item.get("symptom")),
            "cure_way": clean_text(item.get("cure_way")),
            "prevent": clean_text(item.get("prevent")),
            "department": clean_text(item.get("cure_department"), 50),
            "drugs": unique_drugs,
            "category": "常见疾病"
        })

    os.makedirs("data", exist_ok=True)
    with open("data/search_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = os.path.getsize("data/search_index.json") / 1024
    print(f"[完成] 成功生成索引，共 {len(index)} 条核心数据")
    print(f"[完成] 当前文件体积: {size_kb:.1f} KB")

if __name__ == "__main__":
    build_search_index()
