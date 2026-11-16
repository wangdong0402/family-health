import json
import os
import html
import shutil
from datetime import datetime, timezone, timedelta

NEWS_FILE = "data/news.json"
INDEX_FILE = "data/search_index.json"
OUTPUT_FILE = "dist/index.html"

def format_relative_time(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        if diff.days == 0:
            if diff.seconds < 3600:
                return f"{diff.seconds // 60} 分钟前"
            return f"{diff.seconds // 3600} 小时前"
        elif diff.days == 1:
            local_dt = dt + timedelta(hours=8)
            return f"昨天 {local_dt.strftime('%H:%M')}"
        else:
            local_dt = dt + timedelta(hours=8)
            return local_dt.strftime('%m-%d %H:%M')
    except Exception:
        return str(value)[:16]

def load_data():
    if not os.path.exists(NEWS_FILE):
        return {"updated": "", "count": 0, "items": []}
    with open(NEWS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def build_cards(items):
    if not items:
        return '<div class="empty">还没有数据。请等待每日自动任务运行。</div>'
    
    existing_categories = set(item.get("category", "") for item in items if item.get("category"))
    desired_order = ["国内健康新闻", "权威聚合", "医学研究", "慢病指南"]
    sorted_categories = []
    for cat in desired_order:
        if cat in existing_categories:
            sorted_categories.append(cat)
            existing_categories.remove(cat)
    sorted_categories.extend(sorted(list(existing_categories)))

    filter_html = '<div class="filter-bar" id="filter-bar">'
    filter_html += f'<button class="filter-btn active" onclick="filterNews(\'all\', this)">全部</button>'
    for cat in sorted_categories:
        filter_html += f'<button class="filter-btn" onclick="filterNews(\'{cat}\', this)">{cat}</button>'
    filter_html += '</div>'

    cards = []
    for item in items:
        title = html.escape(item.get("title", ""))
        link = html.escape(item.get("link", ""))
        summary = html.escape(item.get("summary", ""))
        source = html.escape(item.get("source", ""))
        category = html.escape(item.get("category", ""))
        published = format_relative_time(item.get("published", ""))
        
        tag_style = ""
        border_color = "#e5e7eb"
        if "权威聚合" in category:
            tag_style = "background: #ccfbf1; color: #0f766e;"
            border_color = "#14b8a6"
        elif "国内健康新闻" in category:
            tag_style = "background: #fee2e2; color: #b91c1c;"
            border_color = "#ef4444"
        elif "慢病指南" in category:
            tag_style = "background: #dbeafe; color: #1d4ed8;"
            border_color = "#3b82f6"
        elif "健康指南" in category:
            tag_style = "background: #ffedd5; color: #c2410c;"
            border_color = "#f97316"
        elif "医学研究" in category:
            tag_style = "background: #f3e8ff; color: #7e22ce;"
            border_color = "#a855f7"
        else:
            tag_style = "background: #f3f4f6; color: #374151;"

        summary_html = f'<p class="summary">{summary}</p>' if summary else ""
        
        cards.append(f'''
        <article class="card news-card" data-category="{category}" style="border-left: 4px solid {border_color};">
          <div class="meta">
            <span class="tag" style="{tag_style}">{category}</span>
            <span>{source}</span>
            <span class="time-text">{published}</span>
          </div>
          <h2><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h2>
          {summary_html}
        </article>''')

    return filter_html + "\n".join(cards)

def main():
    data = load_data()
    items = data.get("items", [])
    updated = format_relative_time(data.get("updated", ""))
    count = data.get("count", len(items))
    cards_html = build_cards(items)

    os.makedirs("dist", exist_ok=True)
    
    if os.path.exists(INDEX_FILE):
        shutil.copy(INDEX_FILE, "dist/search_index.json")
        print("已复制 search_index.json 到 dist/")
    else:
        print("警告：未找到 search_index.json，疾病查询功能将不可用。")

    html_doc = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>家庭健康资讯</title>
<style>
:root {{ color-scheme: light dark; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f5f5f7;
  color: #1d1d1f;
}}
header {{
  position: sticky;
  top: 0;
  backdrop-filter: blur(12px);
  background: rgba(245, 245, 247, .85);
  border-bottom: 1px solid rgba(0, 0, 0, .08);
  padding: 16px 16px 0;
  z-index: 100;
}}
.header-top {{ margin-bottom: 12px; }}
h1 {{ font-size: 20px; margin: 0 0 4px; }}
.sub {{ font-size: 12px; color: #6e6e73; }}
.tabs {{ display: flex; gap: 20px; overflow-x: auto; border-bottom: 1px solid #e5e7eb; }}
.tab-btn {{ background: none; border: none; padding: 10px 0; font-size: 15px; font-weight: bold; color: #6e6e73; cursor: pointer; border-bottom: 3px solid transparent; transition: all 0.2s; white-space: nowrap; }}
.tab-btn.active {{ color: #1d1d1f; border-bottom-color: #1d1d1f; }}
main {{ padding: 12px 12px 32px; max-width: 760px; margin: 0 auto; }}
.card {{ background: #fff; border-radius: 14px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0, 0, 0, .04); }}
.meta {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: 12px; color: #6e6e73; margin-bottom: 6px; }}
.tag {{ border-radius: 999px; padding: 2px 8px; font-weight: 500; }}
h2 {{ font-size: 16px; line-height: 1.45; margin: 0 0 6px; }}
h2 a {{ color: inherit; text-decoration: none; }}
h2 a:hover {{ text-decoration: underline; }}
.summary {{ font-size: 14px; line-height: 1.6; color: #3a3a3c; margin: 0; }}
.empty {{ background: #fff; border-radius: 14px; padding: 32px 20px; text-align: center; color: #6e6e73; font-size: 14px; }}

.filter-bar {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 12px; margin-bottom: 4px; }}
.filter-btn {{ background: #fff; border: 1px solid #e5e7eb; padding: 6px 14px; border-radius: 20px; font-size: 13px; color: #3a3a3c; cursor: pointer; white-space: nowrap; transition: all 0.2s; }}
.filter-btn.active {{ background: #1d1d1f; color: #fff; border-color: #1d1d1f; }}

.search-container {{ margin-bottom: 16px; }}
.search-input {{ width: 100%; padding: 12px 16px; border-radius: 10px; border: 1px solid #e5e7eb; font-size: 14px; background: #fff; color: #1d1d1f; outline: none; }}
.search-input:focus {{ border-color: #3b82f6; }}
.search-tips {{ text-align: center; color: #98989d; font-size: 13px; margin-top: 20px; }}

/* 疾病查询卡片内部结构 */
.disease-card h3 {{ font-size: 18px; margin: 0 0 10px; color: #1d1d1f; }}
.disease-section {{ margin-bottom: 10px; font-size: 14px; line-height: 1.6; }}
.disease-section strong {{ color: #3b82f6; margin-right: 6px; }}
.disease-section span {{ color: #3a3a3c; }}

.back-to-top {{ position: fixed; bottom: 30px; right: 20px; width: 44px; height: 44px; background: #1d1d1f; color: #fff; border-radius: 50%; display: none; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; z-index: 999; border: none; font-size: 20px; }}

.disclaimer {{ text-align: center; font-size: 12px; color: #6e6e73; margin-top: 24px; padding: 16px; line-height: 1.8; background: #fff; border-radius: 12px; }}
@media (prefers-color-scheme: dark) {{
  body {{ background: #000; color: #f5f5f7; }}
  header {{ background: rgba(0, 0, 0, .8); border-bottom-color: rgba(255, 255, 255, .12); }}
  .tabs {{ border-bottom-color: #3a3a3c; }}
  .sub, .meta {{ color: #98989d; }}
  .card, .empty, .disclaimer, .filter-btn, .search-input {{ background: #1c1c1e; box-shadow: none; border-color: #3a3a3c; color: #f5f5f7; }}
  .summary {{ color: #d1d1d6; }}
  .filter-btn.active {{ background: #f5f5f7; color: #000; border-color: #f5f5f7; }}
  .disclaimer {{ color: #98989d; }}
  .back-to-top {{ background: #f5f5f7; color: #000; }}
  .tab-btn {{ color: #98989d; }}
  .tab-btn.active {{ color: #f5f5f7; border-bottom-color: #f5f5f7; }}
  
  .disease-card h3 {{ color: #f5f5f7; }}
  .disease-section span {{ color: #d1d1d6; }}
}}
</style>
</head>
<body>
<header>
  <div class="header-top">
    <h1>家庭健康资讯</h1>
    <div class="sub">更新：{updated or "暂无"} · 共 {count} 条</div>
  </div>
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('news')" id="btn-news">每日资讯</button>
    <button class="tab-btn" onclick="switchTab('disease')" id="btn-disease">疾病查询</button>
  </div>
</header>
<main>
  <div id="tab-news">
    {cards_html}
  </div>

  <div id="tab-disease" style="display: none;">
    <div class="search-container">
      <input type="text" id="disease-search" class="search-input" placeholder="🔍 输入疾病名称（如：高血压、糖尿病）..." oninput="debounceSearch()">
    </div>
    <div id="disease-results">
      <div class="search-tips">请输入疾病名称进行查询。<br>（首次搜索需要下载约 4MB 的知识库，秒加载）</div>
    </div>
  </div>

  <div class="disclaimer">
    <strong>💡 阅读小贴士：</strong><br>
    中英文对照阅读效果更佳，英文内容可点击浏览器菜单选择“翻译”。<br><br>
    本网站内容仅供家庭日常参考，不能替代专业医疗诊断。如有不适，请及时就医。
  </div>
</main>

<button class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</button>

<script>
function switchTab(tab) {{
  document.getElementById('tab-news').style.display = 'none';
  document.getElementById('tab-disease').style.display = 'none';
  document.getElementById('btn-news').classList.remove('active');
  document.getElementById('btn-disease').classList.remove('active');

  document.getElementById('tab-' + tab).style.display = 'block';
  document.getElementById('btn-' + tab).classList.add('active');
}}

function filterNews(category, btn) {{
  const buttons = document.querySelectorAll('.filter-btn');
  buttons.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const cards = document.querySelectorAll('.news-card');
  cards.forEach(card => {{
    if (category === 'all' || card.getAttribute('data-category') === category) {{
      card.style.display = 'block';
    }} else {{
      card.style.display = 'none';
    }}
  }});
}}

let diseaseData = null;
let searchTimer = null;

function debounceSearch() {{
  clearTimeout(searchTimer);
  searchTimer = setTimeout(performSearch, 500);
}}

async function performSearch() {{
  const query = document.getElementById('disease-search').value.trim();
  const resultContainer = document.getElementById('disease-results');

  if (query.length < 1) {{
    resultContainer.innerHTML = '<div class="search-tips">请输入疾病名称进行查询。</div>';
    return;
  }}

  if (!diseaseData) {{
    resultContainer.innerHTML = '<div class="search-tips">⏳ 正在加载医学知识库，请稍候...</div>';
    try {{
      const response = await fetch('search_index.json');
      if (!response.ok) throw new Error("加载失败");
      diseaseData = await response.json();
    }} catch (err) {{
      resultContainer.innerHTML = '<div class="search-tips">⚠️ 知识库加载失败，请检查网络。</div>';
      return;
    }}
  }}

  // 精确匹配和模糊匹配
  const matches = diseaseData.filter(item => 
    item.title.includes(query)
  ).slice(0, 5); // 限制最多返回 5 条，避免一屏太长

  if (matches.length === 0) {{
    resultContainer.innerHTML = '<div class="search-tips">未找到该疾病，请尝试输入全称。</div>';
    return;
  }}

  let htmlStr = '';
  matches.forEach(item => {{
    const title = item.title;
    
    let sections = '';
    if (item.desc) sections += `<div class="disease-section"><strong>简介：</strong><span>${{item.desc}}</span></div>`;
    if (item.cause) sections += `<div class="disease-section"><strong>病因：</strong><span>${{item.cause}}</span></div>`;
    if (item.symptom) sections += `<div class="disease-section"><strong>症状：</strong><span>${{item.symptom}}</span></div>`;
    if (item.cure_way) sections += `<div class="disease-section"><strong>治疗：</strong><span>${{item.cure_way}}</span></div>`;
    if (item.prevent) sections += `<div class="disease-section"><strong>预防：</strong><span>${{item.prevent}}</span></div>`;
    if (item.department) sections += `<div class="disease-section"><strong>科室：</strong><span>${{item.department}}</span></div>`;

    htmlStr += `
      <article class="card disease-card" style="border-left: 4px solid #10b981;">
        <h3>${{title}}</h3>
        ${{sections}}
      </article>
    `;
  }});
  resultContainer.innerHTML = htmlStr;
}}

window.onscroll = function() {{
  const btn = document.getElementById('backToTop');
  if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {{
    btn.style.display = 'flex';
  }} else {{
    btn.style.display = 'none';
  }}
}};

function scrollToTop() {{
  window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}
</script>
</body>
</html>'''

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"已生成 {OUTPUT_FILE}，疾病结构化展示已上线。")

if __name__ == "__main__":
    main()
