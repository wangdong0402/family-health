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

/* 新闻分类栏 */
.filter-bar {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 12px; margin-bottom: 4px; }}
.filter-btn {{ background: #fff; border: 1px solid #e5e7eb; padding: 6px 14px; border-radius: 20px; font-size: 13px; color: #3a3a3c; cursor: pointer; white-space: nowrap; transition: all 0.2s; }}
.filter-btn.active {{ background: #1d1d1f; color: #fff; border-color: #1d1d1f; }}

/* 搜索框 */
.search-container {{ margin-bottom: 16px; }}
.search-input {{ width: 100%; padding: 12px 16px; border-radius: 10px; border: 1px solid #e5e7eb; font-size: 14px; background: #fff; color: #1d1d1f; outline: none; }}
.search-input:focus {{ border-color: #3b82f6; }}
.search-tips {{ text-align: center; color: #98989d; font-size: 13px; margin-top: 20px; }}

/* 疾病列表精简卡片 */
.disease-list-card {{ background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); cursor: pointer; border-left: 4px solid #10b981; transition: transform 0.1s; }}
.disease-list-card:active {{ transform: scale(0.98); }}
.disease-list-card h3 {{ font-size: 16px; margin: 0 0 6px; color: #1d1d1f; }}
.disease-list-card p {{ font-size: 13px; color: #6e6e73; margin: 0; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.5; }}

/* 底部滑出详情弹窗 */
.modal-overlay {{ position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; display: none; opacity: 0; transition: opacity 0.3s; }}
.modal-overlay.show {{ display: block; opacity: 1; }}
.modal-content {{ position: fixed; left: 0; right: 0; bottom: -100%; max-height: 85vh; background: #f5f5f7; border-radius: 20px 20px 0 0; z-index: 1001; transition: bottom 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275); display: flex; flex-direction: column; }}
.modal-content.show {{ bottom: 0; }}
.modal-header {{ padding: 16px 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; background: #fff; border-radius: 20px 20px 0 0; }}
.modal-header h2 {{ font-size: 18px; margin: 0; color: #1d1d1f; }}
.close-btn {{ background: #f3f4f6; border: none; width: 30px; height: 30px; border-radius: 50%; font-size: 16px; color: #6e6e73; cursor: pointer; display: flex; justify-content: center; align-items: center; }}
.modal-body {{ padding: 20px; overflow-y: auto; font-size: 15px; line-height: 1.7; color: #3a3a3c; }}
.detail-section {{ margin-bottom: 20px; background: #fff; padding: 16px; border-radius: 12px; }}
.detail-label {{ display: inline-block; font-size: 12px; font-weight: bold; padding: 2px 8px; border-radius: 4px; margin-bottom: 8px; }}
.label-desc {{ background: #e0f2fe; color: #0284c7; }}
.label-cause {{ background: #fef2f2; color: #dc2626; }}
.label-symptom {{ background: #fdf4ff; color: #c026d3; }}
.label-cure {{ background: #f0fdf4; color: #16a34a; }}
.label-prevent {{ background: #fff7ed; color: #ea580c; }}

.back-to-top {{ position: fixed; bottom: 30px; right: 20px; width: 44px; height: 44px; background: #1d1d1f; color: #fff; border-radius: 50%; display: none; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; z-index: 999; border: none; font-size: 20px; }}

.disclaimer {{ text-align: center; font-size: 12px; color: #6e6e73; margin-top: 24px; padding: 16px; line-height: 1.8; background: #fff; border-radius: 12px; }}

@media (prefers-color-scheme: dark) {{
  body {{ background: #000; color: #f5f5f7; }}
  header, .modal-header, .detail-section {{ background: #1c1c1e; border-color: #3a3a3c; }}
  .tabs {{ border-bottom-color: #3a3a3c; }}
  .sub, .meta {{ color: #98989d; }}
  .card, .empty, .disclaimer, .filter-btn, .search-input, .disease-list-card {{ background: #1c1c1e; box-shadow: none; border-color: #3a3a3c; color: #f5f5f7; }}
  .summary, .disease-list-card p, .modal-body {{ color: #d1d1d6; }}
  .disease-list-card h3, .modal-header h2 {{ color: #f5f5f7; }}
  .filter-btn.active {{ background: #f5f5f7; color: #000; border-color: #f5f5f7; }}
  .disclaimer {{ color: #98989d; }}
  .back-to-top {{ background: #f5f5f7; color: #000; }}
  .tab-btn {{ color: #98989d; }}
  .tab-btn.active {{ color: #f5f5f7; border-bottom-color: #f5f5f7; }}
  .modal-content {{ background: #000; }}
  .close-btn {{ background: #3a3a3c; color: #f5f5f7; }}
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
      <div class="search-tips">请输入疾病名称进行查询。<br>（首次搜索加载约 2 秒，随后秒开）</div>
    </div>
  </div>

  <div class="disclaimer">
    <strong>💡 阅读小贴士：</strong><br>
    中英文对照阅读效果更佳，英文内容可点击浏览器菜单选择“翻译”。<br><br>
    本网站内容仅供家庭日常参考，不能替代专业医疗诊断。如有不适，请及时就医。
  </div>
</main>

<!-- 详情弹窗 -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModal()"></div>
<div class="modal-content" id="modal-content">
  <div class="modal-header">
    <h2 id="modal-title">疾病名称</h2>
    <button class="close-btn" onclick="closeModal()">✕</button>
  </div>
  <div class="modal-body" id="modal-body">
    <!-- 动态填充内容 -->
  </div>
</div>

<button class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</button>

<script>
// ====== Tab 切换 ======
function switchTab(tab) {{
  document.getElementById('tab-news').style.display = 'none';
  document.getElementById('tab-disease').style.display = 'none';
  document.getElementById('btn-news').classList.remove('active');
  document.getElementById('btn-disease').classList.remove('active');

  document.getElementById('tab-' + tab).style.display = 'block';
  document.getElementById('btn-' + tab).classList.add('active');
}}

// ====== 新闻过滤 ======
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

// ====== 疾病检索 ======
let diseaseData = null;
let searchTimer = null;

function debounceSearch() {{
  clearTimeout(searchTimer);
  searchTimer = setTimeout(performSearch, 300);
}}

async function performSearch() {{
  const query = document.getElementById('disease-search').value.trim();
  const resultContainer = document.getElementById('disease-results');

  if (query.length < 1) {{
    resultContainer.innerHTML = '<div class="search-tips">请输入疾病名称进行查询。</div>';
    return;
  }}

  if (!diseaseData) {{
    resultContainer.innerHTML = '<div class="search-tips">⏳ 正在加载知识库...</div>';
    try {{
      const response = await fetch('search_index.json');
      if (!response.ok) throw new Error("加载失败");
      diseaseData = await response.json();
    }} catch (err) {{
      resultContainer.innerHTML = '<div class="search-tips">⚠️ 知识库加载失败，请检查网络。</div>';
      return;
    }}
  }}

  const matches = diseaseData.filter(item => item.title.includes(query)).slice(0, 10);

  if (matches.length === 0) {{
    resultContainer.innerHTML = '<div class="search-tips">未找到该疾病，请尝试其他关键词。</div>';
    return;
  }}

  let htmlStr = '';
  matches.forEach((item, index) => {{
    const safeTitle = item.title.replace(/</g, "&lt;");
    const shortDesc = (item.desc || "暂无简介").substring(0, 40) + "...";
    
    // 将数据存入全局数组，方便弹窗根据索引取用
    window.currentSearchResults = matches;

    htmlStr += `
      <div class="disease-list-card" onclick="openModal(${{index}})">
        <h3>${{safeTitle}}</h3>
        <p>${{shortDesc}}</p>
      </div>
    `;
  }});
  resultContainer.innerHTML = htmlStr;
}}

// ====== 弹窗控制 ======
function openModal(index) {{
  const item = window.currentSearchResults[index];
  if (!item) return;

  document.getElementById('modal-title').innerText = item.title;
  
  let bodyHtml = '';
  
  if (item.desc) bodyHtml += `<div class="detail-section"><span class="detail-label label-desc">简介</span><div>${{item.desc}}</div></div>`;
  if (item.cause) bodyHtml += `<div class="detail-section"><span class="detail-label label-cause">病因</span><div>${{item.cause}}</div></div>`;
  if (item.symptom) bodyHtml += `<div class="detail-section"><span class="detail-label label-symptom">症状</span><div>${{item.symptom}}</div></div>`;
  if (item.cure_way) bodyHtml += `<div class="detail-section"><span class="detail-label label-cure">治疗</span><div>${{item.cure_way}}</div></div>`;
  if (item.prevent) bodyHtml += `<div class="detail-section"><span class="detail-label label-prevent">预防</span><div>${{item.prevent}}</div></div>`;
  if (item.department) bodyHtml += `<div class="detail-section"><span class="detail-label label-desc">就诊科室</span><div>${{item.department}}</div></div>`;

  document.getElementById('modal-body').innerHTML = bodyHtml;
  
  document.getElementById('modal-overlay').classList.add('show');
  document.getElementById('modal-content').classList.add('show');
  document.body.style.overflow = 'hidden'; // 防止背景滚动
}}

function closeModal() {{
  document.getElementById('modal-overlay').classList.remove('show');
  document.getElementById('modal-content').classList.remove('show');
  document.body.style.overflow = '';
}}

// ====== 返回顶部 ======
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

    print(f"已生成 {OUTPUT_FILE}，疾病列表与详情弹窗已上线。")

if __name__ == "__main__":
    main()
