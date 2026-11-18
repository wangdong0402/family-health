import requests
import json
import os

def clean_text(value, max_len=500):
    """清理数据：去除换行，强制截断至 500 字"""
    if not value:
        return ""
    if isinstance(value, list):
        value = "，".join([str(v).strip() for v in value if v])
    text = str(value).strip().replace("\n", " ").replace("\r", " ")
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text

def map_department(dept_str):
    """将杂乱的科室名称归类到 8 大一级科室"""
    if not dept_str:
        return "其他"
    
    mapping = {
        "内科": ["内科", "心血管", "消化", "呼吸", "神经", "内分泌", "血液", "风湿", "肾内", "传染"],
        "外科": ["外科", "骨科", "泌尿", "肛肠", "肝胆", "血管外", "烧伤", "整形", "普外"],
        "儿科": ["小儿", "儿科", "新生儿", "儿童"],
        "妇产科": ["妇科", "产科", "妇产"],
        "五官科": ["眼", "耳鼻喉", "口腔", "牙"],
        "皮肤科": ["皮肤", "性病"],
        "中医科": ["中医", "中西医结合"],
        "其他": []
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
        return

        # 扩充多维度高频词库
    priority_dict = {
        "eye": ["近视", "远视", "散光", "白内障", "青光眼", "结膜炎", "角膜炎", "干眼症", "麦粒肿"],
        "gyn": ["痛经", "月经不调", "阴道炎", "盆腔炎", "子宫肌瘤", "乳腺增生", "孕期", "妊娠"],
        "peds": ["小儿", "儿童", "幼儿", "新生儿", "手足口病", "水痘", "小儿感冒"],
        "derm": ["湿疹", "皮炎", "荨麻疹", "痤疮", "牛皮癣", "白癜风", "脱发", "带状疱疹"],
        "global": ["感冒", "发烧", "发热", "高血压", "糖尿病", "胃炎", "失眠", "头痛", "便秘", "腹泻", "鼻炎", "关节炎", "痛风", "痔疮", "冠心病"]
    }

    index = []
    # 1. 遍历全部数据（不再预先截断，让所有病都有机会被选中）
    for item in raw_records:
        title = clean_text(item.get("name"), 50)
        if not title:
            continue
            
        raw_dept = clean_text(item.get("cure_department"), 100)
        mapped_dept = map_department(raw_dept)

        # 计算权重得分（命中你刚才配置的 priority_dict 词库，得分越高）
        score = 0
        for cat, kws in priority_dict.items():
            if any(kw in title for kw in kws):
                score += 1

        drugs = []
        if item.get("recommand_drug"):
            drugs.extend(item["recommand_drug"])
        if item.get("common_drug"):
            drugs.extend(item["common_drug"])
        # 药品去重后，只保留前 3 个
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
            "drugs": unique_drugs,
            "_score": score  # 暂存得分用于排序
        })

    # 2. 排序规则：先按得分降序（命中心词的排在前面），得分相同的按名称长度升序
    index.sort(key=lambda x: (-x["_score"], len(x["title"])))

    # 3. 最后一步截断：排好序后，只取前 1500 条！
    index = index[:1500]

    # 清理掉临时得分字段，避免写入 JSON 文件增大体积
    for item in index:
        del item["_score"]

    os.makedirs("data", exist_ok=True)
    with open("data/search_index.json", "w", encoding="utf-8") as f:
        # 使用紧凑格式压缩体积
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))

    size_kb = os.path.getsize("data/search_index.json") / 1024
    print(f"[完成] 成功生成索引，共 {len(index)} 条数据")
    print(f"[完成] 当前文件体积: {size_kb:.1f} KB")

if __name__ == "__main__":
    build_search_index()
