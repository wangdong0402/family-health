import requests
import json
import os

# 候选数据源：(描述, URL, 格式)
SOURCES = [
    (
        "DiseaseKG (nuolade/disease-kb)",
        "https://raw.githubusercontent.com/nuolade/disease-kb/master/data/medical.json",
        "json"
    ),
    (
        "DiseaseKG 镜像",
        "https://cdn.jsdelivr.net/gh/nuolade/disease-kb@master/data/medical.json",
        "json"
    ),
    (
        "A Hospital Medical Wiki Dataset (articles.jsonl)",
        "https://huggingface.co/datasets/Pathwit/a-hospital-medical-wiki-dataset/resolve/main/articles.jsonl",
        "jsonl"
    ),
]


def try_download(url):
    resp = requests.get(url, timeout=30, headers={
        "User-Agent": "Mozilla/5.0 (compatible; HealthIndexBot/1.0)"
    })
    resp.raise_for_status()
    return resp.content


def parse_json(content):
    """尝试把原始内容解析为记录列表"""
    data = json.loads(content)
    if isinstance(data, list):
        return data
    # 有些仓库把数据包在 "data" 或 "items" 键下
    for key in ("data", "items", "records"):
        if isinstance(data.get(key), list):
            return data[key]
    # 字典结构：values 视为记录
    if isinstance(data, dict):
        return list(data.values())
    raise ValueError("无法识别的 JSON 结构")


def parse_jsonl(content):
    """逐行解析 JSONL"""
    records = []
    for line in content.decode("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def extract_title(record):
    for key in ("title", "name", "disease", "entity"):
        val = record.get(key)
        if val:
            return str(val).strip()
    return ""


def extract_summary(record):
    for key in ("summary", "desc", "description", "content", "symptom", "intro"):
        val = record.get(key)
        if val:
            return str(val).strip()
    return ""


def extract_category(record):
    val = record.get("category") or record.get("categories") or record.get("type")
    if isinstance(val, list):
        return " / ".join(str(v) for v in val[:3])
    return str(val) if val else "常见疾病"


def build():
    raw_records = None
    used_source = None

    for desc, url, fmt in SOURCES:
        print(f"[尝试] {desc} -> {url}")
        try:
            content = try_download(url)
            if fmt == "jsonl":
                raw_records = parse_jsonl(content)
            else:
                raw_records = parse_json(content)
            used_source = desc
            print(f"[成功] 从 {desc} 解析到 {len(raw_records)} 条原始记录")
            break
        except Exception as e:
            print(f"[跳过] {desc} 失败: {e}")

    if not raw_records:
        print("[失败] 所有候选数据源均不可用，无法生成索引。")
        # 生成一个空索引，保证后续 generate.py 和部署流程不中断
        os.makedirs("data", exist_ok=True)
        with open("data/search_index.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False)
        print("[保底] 已写入空索引 data/search_index.json（0 条）")
        return

    # 清洗、精简、去重
    seen = set()
    index = []
    for record in raw_records:
        title = extract_title(record)
        if not title:
            continue
        if title in seen:
            continue
        seen.add(title)

        summary = extract_summary(record)
        if len(summary) > 300:
            summary = summary[:300]

        index.append({
            "title": title,
            "summary": summary,
            "category": extract_category(record),
        })

    index.sort(key=lambda x: x["title"])

    os.makedirs("data", exist_ok=True)
    with open("data/search_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    size_kb = os.path.getsize("data/search_index.json") / 1024
    print(f"[完成] 数据源: {used_source}")
    print(f"[完成] 索引条目: {len(index)} 条，文件体积: {size_kb:.1f} KB")
    print("[完成] 已保存至 data/search_index.json")


if __name__ == "__main__":
    build()
