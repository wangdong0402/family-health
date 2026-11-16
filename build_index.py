import requests
import json
import os

def build_search_index():
    print("[信息] 开始获取医疗知识库数据...")
    
    # 这里使用一个开源的中文医疗知识库镜像（基于寻医问药网整理，包含常见疾病百科）
    # 这比原始 235MB 的源更精简，适合快速跑通前端搜索
    url = "https://raw.githubusercontent.com/shibing624/MedicalGPT/main/data/disease_data.json"
    
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        raw_data = response.json()
        
        # 数据可能是字典或者列表，根据实际情况处理
        if isinstance(raw_data, dict):
            items = list(raw_data.values())
        else:
            items = raw_data
            
        print(f"[信息] 原始数据加载成功，共 {len(items)} 条记录")
        
        search_index = []
        for item in items:
            # 提取关键字段，防止把长篇大论全塞进索引
            title = item.get("name", item.get("title", ""))
            if not title:
                continue
                
            # 提取简介、症状、治疗等作为摘要
            summary = item.get("desc", item.get("summary", item.get("symptom", "")))
            if not summary and "content" in item:
                summary = item["content"][:200] # 截取前200字
                
            # 提取分类或标签
            category = item.get("category", "常见疾病")
            
            # 组装精简后的索引数据
            search_index.append({
                "title": title,
                "summary": str(summary)[:300], # 强制截断，防止单条过长
                "category": category
            })
            
        # 去重处理（按标题）
        seen = set()
        final_index = []
        for doc in search_index:
            if doc["title"] not in seen:
                seen.add(doc["title"])
                final_index.append(doc)
                
        # 写入文件
        os.makedirs("data", exist_ok=True)
        with open("data/search_index.json", "w", encoding="utf-8") as f:
            json.dump(final_index, f, ensure_ascii=False, indent=2)
            
        print(f"[成功] 成功生成精简索引，共 {len(final_index)} 条知识，保存至 data/search_index.json")
        
    except Exception as e:
        print(f"[失败] 获取或处理数据失败: {e}")

if __name__ == "__main__":
    build_search_index()
