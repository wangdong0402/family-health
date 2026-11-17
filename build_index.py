import requests
import json
import os
import re

def clean_text(value, max_len=500):
    """清理数据：去除换行，强制截断"""
    if not value:
        return ""
    if isinstance(value, list):
        value = "，".join([str(v).strip() for v in value if v])
    text = str(value).strip().replace("\n", " ").replace("\r", " ")
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text

def map_department(dept_str):
    """将杂乱的科室名称归类到 6 大一级科室"""
    if not dept_str:
        return "其他"
    
    # 优先级映射字典
    mapping = {
        "内科": ["内科", "心血管", "消化", "呼吸", "神经", "内分泌", "血液", "风湿", "肾内", "传染"],
        "外科": ["外科", "骨科", "泌尿", "肛肠", "肝胆", "血管外", "烧伤", "整形"],
        "儿科": ["小儿", "儿科", "新生儿", "儿童"],
        "妇产科": ["妇科", "产科", "妇产"],
        "五官科": ["眼", "耳鼻喉", "口腔", "牙"],
        "皮肤科": ["皮肤"]
    }
    
    for main_dept, keywords in mapping.items():
        for kw in keywords:
            if kw in dept_str:
                return main_dept
    return "其他"

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
                print(f"[成功] 成功下载并解析 {len(raw_records)} 条疾病数据")
                break
        except Exception as e:
            print(f"[跳过] 下载失败: {e}")

    if not raw_records:
        print("[失败] 无法获取数据源。")
        os.makedirs("data", exist_ok=True)
        with open("data/search_index.json", "w", encoding="utf-8") as f:
            json.dump([], f)
        return

    # 常见病词库（用于提升权重，排在前面）
    common_keywords = ["感冒", "发烧", "发热", "高血压", "糖尿病", "胃炎", "胃溃疡", "失眠", "头痛", "便秘", "腹泻", "湿疹", "鼻炎", "咽炎", "关节炎", "痛风", "冠心病", "脑梗", "痔疮", "阑尾炎", "痛经", "近视", "结膜炎", "中耳炎", "蛀牙", "贫血", "哮喘", "肺炎", "脂肪肝", "肾结石"]

    index = []
    for item in raw_records[:2000]:
        title = clean_text(item.get("name"), 50)
        if not title:
            continue
            
        raw_dept = clean_text(item.get("cure_department"), 100)
        mapped_dept = map_department(raw_dept)

        # 提取药品，去重，只取前 5 个
        drugs = []
        if item.get("recommand_drug"):
            drugs.extend(item["recommand_drug"])
        if item.get("common_drug"):
            drugs.extend(item["common_drug"])
        unique_drugs = list(dict.fromkeys(drugs))[:5]
            
        index.append({
            "title": title,
            "desc": clean_text(item.get("desc")),
            "cause": clean_text(item.get("cause")),
            "symptom": clean_text(item.get("symptom")),
            "cure_way": clean_text(item.get("cure_way")),
            "prevent": clean_text(item.get("prevent")),
            "department": raw_dept,
            "mapped_dept": mapped_dept,
            "drugs": unique_drugs
        })

    # 排序逻辑：先按高频词置顶，再按名称长度升序
    def sort_weight(item):
        is_common = any(kw in item["title"] for kw in common_keywords)
        # 常见词返回 (0, 长度)，其他返回 (1, 长度)
        return (0 if is_common else 1, len(item["title"]))

    index.sort(key=sort_weight)

    os.makedirs("data", exist_ok=True)
    with open("data/search_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = os.path.getsize("data/search_index.json") / 1024
    print(f"[完成] 成功生成索引，共 {len(index)} 条数据")
    print(f"[完成] 当前文件体积: {size_kb:.1f} KB")

if __name__ == "__main__":
    build_search_index()
