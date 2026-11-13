import json
import os
import html
from datetime import datetime

NEWS_FILE = "data/news.json"
REPORTS_FILE = "data/reports.json"
SENTIMENT_FILE = "data/sentiment.json"
MACRO_FILE = "data/macro.json"
OUTPUT_FILE = "dist/index.html"


def format_time(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(value)[:16]


def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_news_cards(items):
    if not items:
        return '<div class="empty">还没有新闻数据。</div>'
    cards = []
    for item in items:
        title = html.escape(item.get("title", ""))
        link = html.escape(item.get("link", ""))
        summary = html.escape(item.get("summary", ""))
        source = html.escape(item.get("source", ""))
        category = html.escape(item.get("category", ""))
        published = html.escape(format_time(item.get("published", "")))
        
        # 更新后的多色彩标签系统
        tag_style = ""
        if "权威聚合" in category:
            tag_style = "background: #ccfbf1; color: #0f766e; border: 1px solid #14b8a6;"   # 青色（明白健康）
        elif "国内健康新闻" in category:
            tag_style = "background: #fee2e2; color: #b91c1c; border: 1px solid #ef4444;"   # 中国红（中新网）
        elif "慢病指南" in category:
            tag_style = "background: #dbeafe; color: #1d4ed8; border: 1px solid #3b82f6;"   # 蓝色（患者信息）
        elif "健康指南" in category:
            tag_style = "background: #ffedd5; color: #c2410c; border: 1px solid #f97316;"   # 橙色（MedlinePlus）
        elif "医学研究" in category:
            tag_style = "background: #f3e8ff; color: #7e22ce; border: 1px solid #a855f7;"   # 紫色（每日科学）
        else:
            tag_style = "background: #f3f4f6; color: #374151;"   # 默认灰

        summary_html = f'<p class="summary">{summary}</p>' if summary else ""
        cards.append(f'''
        <article class="card">
          <div class="meta">
            <span class="tag" style="{tag_style}">{category}</span>
            <span>{source}</span>
            <span>{published}</span>
          </div>
          <h2><a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a></h2>
          {summary_html}
        </article>''')
    return "\n".join(cards)


def main():
    news_data = load_json(NEWS_FILE, {"updated": "", "count": 0, "items": []})
    news_items = news_data.get("items", [])
    news_updated = format_time(news_data.get("updated", ""))
    news_count = news_data.get("count", len(news_items))
    news_cards_html = build_news_cards(news_items)

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
  .card, .empty, .disclaimer {{ background: #1c1c1e; box-shadow: none; }}
  .summary {{ color: #d1d1d6; }}
  .disclaimer {{ color: #98989d; }}
}}
</style>
</head>
<body>
<header>
  <h1>家庭健康资讯</h1>
  <div class="sub">更新：{news_updated or "暂无"} · 共 {news_count} 条</div>
</header>
<main>
{news_cards_html}

<div class="disclaimer">
  <strong>💡 阅读小贴士：</strong><br>
  中英文对照阅读效果更佳，英文内容可点击浏览器菜单选择“翻译”。<br><br>
  本网站内容仅供家庭日常参考，不能替代专业医疗诊断。如有不适，请及时就医。
</div>

</main>
</body>
</html>'''

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print(f"已生成 {OUTPUT_FILE}，包含新分类颜色。")


if __name__ == "__main__":
    main()
