import json
import os
import html
from datetime import datetime, timezone, timedelta

NEWS_FILE = "data/news.json"
OUTPUT_FILE = "dist/index.html"


def format_relative_time(value):
    """将时间转换为相对时间（如：2小时前、昨天 14:30）"""
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
            # 转为北京时间显示
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
    
    # 提取所有分类
    categories = sorted(list(set(item.get("category", "") for item in items if item.get("category"))))
    
    # 构建分类筛选栏
    filter_html = '<div class="filter-bar" id="filter-bar">'
    filter_html += f'<button class="filter-btn active" onclick="filterNews(\'all\', this)">全部</button>'
    for cat in categories:
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
        
        # 健康资讯专属配色
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
  padding: 16px 16px 12px;
  z-index: 100;
}}
h1 {{ font-size: 20px; margin: 0 0 4px; }}
.sub {{ font-size: 12px; color: #6e6e73; }}
main {{ padding: 12px 12px 32px; max-width: 760px; margin: 0 auto; }}
.card {{
  background: #fff;
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, .04);
}}
.meta {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  font-size: 12px;
  color: #6e6e73;
  margin-bottom: 6px;
}}
.tag {{
  border-radius: 999px;
  padding: 2px 8px;
  font-weight: 500;
}}
h2 {{ font-size: 16px; line-height: 1.45; margin: 0 0 6px; }}
h2 a {{ color: inherit; text-decoration: none; }}
h2 a:hover {{ text-decoration: underline; }}
.summary {{ font-size: 14px; line-height: 1.6; color: #3a3a3c; margin: 0; }}
.empty {{
  background: #fff;
  border-radius: 14px;
  padding: 32px 20px;
  text-align: center;
  color: #6e6e73;
  font-size: 14px;
}}

/* 分类筛选栏 */
.filter-bar {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 12px; margin-bottom: 4px; }}
.filter-btn {{ background: #fff; border: 1px solid #e5e7eb; padding: 6px 14px; border-radius: 20px; font-size: 13px; color: #3a3a3c; cursor: pointer; white-space: nowrap; transition: all 0.2s; }}
.filter-btn.active {{ background: #1d1d1f; color: #fff; border-color: #1d1d1f; }}

/* 返回顶部悬浮按钮 */
.back-to-top {{ position: fixed; bottom: 30px; right: 20px; width: 44px; height: 44px; background: #1d1d1f; color: #fff; border-radius: 50%; display: none; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; z-index: 999; border: none; font-size: 20px; }}

.disclaimer {{
  text-align: center;
  font-size: 12px;
  color: #6e6e73;
  margin-top: 24px;
  padding: 16px;
  line-height: 1.8;
  background: #fff;
  border-radius: 12px;
}}
@media (prefers-color-scheme: dark) {{
  body {{ background: #000; color: #f5f5f7; }}
  header {{ background: rgba(0, 0, 0, .8); border-bottom-color: rgba(255, 255, 255, .12); }}
  .sub, .meta {{ color: #98989d; }}
  .card, .empty, .disclaimer, .filter-btn {{ background: #1c1c1e; box-shadow: none; border-color: #3a3a3c; color: #f5f5f7; }}
  .summary {{ color: #d1d1d6; }}
  .filter-btn.active {{ background: #f5f5f7; color: #000; border-color: #f5f5f7; }}
  .disclaimer {{ color: #98989d; }}
  .back-to-top {{ background: #f5f5f7; color: #000; }}
}}
</style>
</head>
<body>
<header>
  <h1>家庭健康资讯</h1>
  <div class="sub">更新：{updated or "暂无"} · 共 {count} 条</div>
</header>
<main>
{cards_html}

<div class="disclaimer">
  <strong>💡 阅读小贴士：</strong><br>
  中英文对照阅读效果更佳，英文内容可点击浏览器菜单选择“翻译”。<br><br>
  本网站内容仅供家庭日常参考，不能替代专业医疗诊断。如有不适，请及时就医。
</div>

</main>

<button class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</button>

<script>
// 新闻分类筛选
function filterNews(category, btn) {{
  // 更新按钮状态
  const buttons = document.querySelectorAll('.filter-btn');
  buttons.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  // 过滤卡片
  const cards = document.querySelectorAll('.news-card');
  cards.forEach(card => {{
    if (category === 'all' || card.getAttribute('data-category') === category) {{
      card.style.display = 'block';
    }} else {{
      card.style.display = 'none';
    }}
  }});
}}

// 返回顶部逻辑
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

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"已生成 {OUTPUT_FILE}，家庭健康资讯前端已优化。")


if __name__ == "__main__":
    main()
