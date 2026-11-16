import requests
import json
import os

def build_search_index():
    print("[信息] 开始获取结构化疾病知识库...")
    
    # 使用经典的 DiseaseKG 结构化数据集（基于寻医问药整理，包含病因、治疗等核心字段）
    # 注意：由于原仓库的 master 分支可能有变动，这里使用了稳定可靠的镜像地址
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
            
            # 该文件实际上是 JSONL 格式（每行一个 JSON 对象）
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
        title = item.get("name", "").strip()
        if not title:
            continue
            
        # 提取你需要的全方位信息
        index.append({
            "title": title,
            "desc": item.get("desc", "").strip(),
            "cause": item.get("cause", "").strip(),
            "prevent": item.get("prevent", "").strip(),
            "symptom": item.get("symptom", "").strip(),
            "cure_way": item.get("cure_way", "").strip(),
            "department": item.get("cure_department", "").strip(),
            "category": "常见疾病"
        })

    os.makedirs("data", exist_ok=True)
    with open("data/search_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize("data/search_index.json") / 1024
    print(f"[完成] 成功生成索引，共 {len(index)} 条高质量疾病数据")
    print(f"[完成] 文件体积: {size_kb:.1f} KB (非常轻量，秒加载)")

if __name__ == "__main__":
    build_search_index()
