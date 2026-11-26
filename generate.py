import json
import os
import html
import shutil
from datetime import datetime, timezone, timedelta

NEWS_FILE = "data/news.json"
INDEX_FILE = "data/search_index.json"
VIDEO_FILE = "data/videos_index.json"
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

    if os.path.exists(VIDEO_FILE):
        shutil.copy(VIDEO_FILE, "dist/videos_index.json")

    html_doc = f'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>家庭健康资讯</title>
<style>
:root {{ color-scheme: light dark; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f5f7; color: #1d1d1f; }}
header {{ position: sticky; top: 0; backdrop-filter: blur(12px); background: rgba(245, 245, 247, .85); border-bottom: 1px solid rgba(0, 0, 0, .08); padding: 16px 16px 0; z-index: 100; }}
.header-top {{ margin-bottom: 12px; display: flex; flex-direction: column; gap: 6px; }}
h1 {{ 
  font-size: 22px; 
  margin: 0; 
  font-weight: 800;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-block;
}}
.sub {{ 
  font-size: 12px; 
  color: #6e6e73; 
  background: rgba(0, 0, 0, 0.04);
  padding: 4px 10px;
  border-radius: 12px;
  display: inline-block;
  align-self: flex-start;
  font-weight: 500;
}}
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
.search-container {{ margin-bottom: 12px; }}
.search-input {{ width: 100%; padding: 12px 16px; border-radius: 10px; border: 1px solid #e5e7eb; font-size: 14px; background: #fff; color: #1d1d1f; outline: none; }}
.search-input:focus {{ border-color: #3b82f6; }}
.search-tips {{ text-align: center; color: #98989d; font-size: 13px; margin-top: 20px; }}
.dept-bar {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 12px; margin-bottom: 12px; border-bottom: 1px solid #e5e7eb; }}
.dept-btn {{ background: #f3f4f6; border: none; padding: 6px 14px; border-radius: 8px; font-size: 13px; color: #4b5563; cursor: pointer; white-space: nowrap; transition: all 0.2s; }}
.dept-btn.active {{ background: #10b981; color: #fff; }}
.disease-list-card {{ background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); cursor: pointer; border-left: 4px solid #10b981; transition: transform 0.1s; }}
.disease-list-card:active {{ transform: scale(0.98); }}
.disease-list-card h3 {{ font-size: 16px; margin: 0 0 6px; color: #1d1d1f; }}
.disease-list-card p {{ font-size: 13px; color: #6e6e73; margin: 0; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.5; }}
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
.label-drug {{ background: #f3e8ff; color: #9333ea; }}
.drug-tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px; }}
.drug-tag {{ background: #f8fafc; border: 1px solid #e2e8f0; color: #475569; font-size: 13px; padding: 4px 10px; border-radius: 6px; }}
.back-to-top {{ position: fixed; bottom: 30px; right: 20px; width: 44px; height: 44px; background: #1d1d1f; color: #fff; border-radius: 50%; display: none; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(0,0,0,0.15); cursor: pointer; z-index: 999; border: none; font-size: 20px; }}
.disclaimer {{ text-align: center; font-size: 12px; color: #6e6e73; margin-top: 24px; padding: 16px; line-height: 1.8; background: #fff; border-radius: 12px; }}
@media (prefers-color-scheme: dark) {{
  body {{ background: #000; color: #f5f5f7; }}
  header, .modal-header, .detail-section {{ background: #1c1c1e; border-color: #3a3a3c; }}
  .tabs, .dept-bar {{ border-bottom-color: #3a3a3c; }}
  .sub, .meta {{ color: #98989d; }}
  .card, .empty, .disclaimer, .filter-btn, .search-input, .disease-list-card, .dept-btn {{ background: #1c1c1e; box-shadow: none; border-color: #3a3a3c; color: #f5f5f7; }}
  .summary, .disease-list-card p, .modal-body {{ color: #d1d1d6; }}
  .disease-list-card h3, .modal-header h2 {{ color: #f5f5f7; }}
  .filter-btn.active {{ background: #f5f5f7; color: #000; border-color: #f5f5f7; }}
  .disclaimer {{ color: #98989d; }}
  .back-to-top {{ background: #f5f5f7; color: #000; }}
  .tab-btn {{ color: #98989d; }}
  .tab-btn.active {{ color: #f5f5f7; border-bottom-color: #f5f5f7; }}
  .modal-content {{ background: #000; }}
  .close-btn {{ background: #3a3a3c; color: #f5f5f7; }}
  .drug-tag {{ background: #2c2c2e; border-color: #3a3a3c; color: #d1d1d6; }}
  .dept-btn.active {{ background: #10b981; color: #fff; }}
}}
.notice-tip {{
  padding:10px;
  background:#fff8e6;
  border-radius:6px;
  margin:10px 0;
  font-size:14px;
  color:#946300;
}}
.video-filter {{
  display:flex;
  gap:8px;
  margin:12px 0;
  flex-wrap:wrap;
}}
.filter-item {{
  padding:6px 12px;
  border:1px solid #ccc;
  border-radius:999px;
  background:#fff;
}}
.filter-item.active {{
  background:#2b74d9;
  color:#fff;
  border-color:#2b74d9;
}}
.video-list {{
  display:grid;
  gap:12px;
}}
.video-card {{
  border:1px solid #e8e8e8;
  border-radius:8px;
  padding:14px;
  cursor:pointer;
  background:#fff;
}}
.video-tag-row {{
  display:flex;
  gap:6px;
  margin:6px 0;
}}
.src-tag,.cat-tag {{
  font-size:12px;
  padding:2px 6px;
  background:#f0f4fa;
  border-radius:4px;
  color:#2b74d9;
}}
.video-desc {{
  margin:6px 0 0;
  font-size:14px;
  color:#555;
}}
.source-card {{
  border: 1px solid #eee;
  border-radius: 12px;
  padding:16px;
  margin-bottom:12px;
  background:#fff;
}}
.source-card h3 {{
  margin:0 0 8px 0;
  font-size:18px;
}}
.source-card .source-desc {{
  margin:0;
  color:#666;
  font-size:14px;
  line-height:1.5;
}}

.dl-bar {{
  position: fixed; top: 0; left: 0; right: 0; height: 3px; z-index: 9999;
  background: rgba(16,185,129,.10); pointer-events: none;
  opacity: 1; transition: opacity .5s ease;
}}
.dl-bar.done {{ opacity: 0; }}
.dl-bar i {{ display: block; height: 100%; width: 0;
  background: linear-gradient(90deg,#10b981,#34d399); transition: width .25s ease; }}
</style>
</head>
<body>
<div class="dl-bar" id="dlBar"><i></i></div>
<header>
  <div class="header-top">
    <h1>家庭健康资讯</h1>
    <div class="sub">更新：{updated or "暂无"} · 共 {count} 条</div>
  </div>
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('news')" id="btn-news">每日资讯</button>
    <button class="tab-btn" onclick="switchTab('disease')" id="btn-disease">疾病查询</button>
    <button class="tab-btn" onclick="switchTab('videos')" id="btn-videos">健康大视野</button>
  </div>
</header>
<main>
  <div id="tab-news">{cards_html}</div>
  <div id="tab-disease" style="display: none;">
    <div class="search-container">
      <input type="text" id="disease-search" class="search-input" placeholder="🔍 输入疾病名称（如：感冒、高血压）..." oninput="debounceSearch()">
    </div>
    
    <div class="dept-bar" id="dept-bar">
      <button class="dept-btn active" onclick="filterDept('all', this)">全部</button>
      <button class="dept-btn" onclick="filterDept('内科', this)">内科</button>
      <button class="dept-btn" onclick="filterDept('外科', this)">外科</button>
      <button class="dept-btn" onclick="filterDept('儿科', this)">儿科</button>
      <button class="dept-btn" onclick="filterDept('妇产科', this)">妇产科</button>
      <button class="dept-btn" onclick="filterDept('五官科', this)">五官科</button>
      <button class="dept-btn" onclick="filterDept('皮肤科', this)">皮肤科</button>
      <button class="dept-btn" onclick="filterDept('中医科', this)">中医科</button>
    </div>
    <div id="disease-results">
      <div class="search-tips">请选择科室或输入疾病名称查询。</div>
    </div>
  </div>
  
  <div class="tab-content" id="tab-videos" style="display: none;">
  <div class="notice-tip">
    ⚠️ 导航提示：本板块仅收录官方科普频道合集，内容版权归属原发布单位；所有视频仅作知识参考，不能替代医生面诊。
  </div>
  <div id="videoListBackBar" style="display:none;margin-bottom:12px;">
  <button onclick="backToSourceHome()" style="padding:8px 12px;border-radius:8px;border:1px solid #ccc;background:#fff;">← 返回数据源首页</button>
  </div>
  <div class="video-list" id="videoListBox"></div>
  </div>
  
  <div class="disclaimer">
    <strong>💡 阅读小贴士：</strong><br>
    本网站内容仅供家庭日常参考，不能替代专业医疗诊断。用药请遵医嘱。如有不适，请及时就医。
  </div>
</main>
<div class="modal-overlay" id="modal-overlay" onclick="closeModal()"></div>
<div class="modal-content" id="modal-content">
  <div class="modal-header">
    <h2 id="modal-title">疾病名称</h2>
    <button class="close-btn" onclick="closeModal()">✕</button>
  </div>
  <div class="modal-body" id="modal-body"></div>
</div>
<button class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</button>
<script>
let diseaseData = null;
let diseaseLoading = null;
let currentDept = 'all';

const DISEASE_URL = 'search_index.json';
const DISEASE_CACHE = 'health-disease-v1.4';
const DISEASE_META_KEY = 'health_disease_meta';
const DISEASE_RECHECK_MS = 10 * 60 * 1000;
const DISEASE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

// 旧版把 3.8MB 塞进 localStorage；这里顺手清掉，释放配额
try {{ localStorage.removeItem('health_disease_cache'); }} catch (e) {{}}

function dlMb(n) {{ return (n / 1048576).toFixed(1) + ' MB'; }}

function dlSet(pct, text) {{
  var fill = document.querySelector('#dlBar i');
  var wrap = document.getElementById('dlBar');
  if (fill && pct !== null && pct !== undefined) {{
    fill.style.width = Math.max(0, Math.min(100, pct)) + '%';
  }}
  if (wrap && pct >= 100) {{ wrap.classList.add('done'); }}
  if (text) {{ window.__dlText = text; }}
  var msg = document.getElementById('dl-msg');
  if (msg && text) {{ msg.textContent = '⏳ ' + text; }}
}}

function readMeta() {{
  try {{ return JSON.parse(localStorage.getItem(DISEASE_META_KEY) || '{{}}') || {{}}; }}
  catch (e) {{ return {{}}; }}
}}

function writeMeta(patch) {{
  try {{
    var m = readMeta();
    for (var k in patch) {{ m[k] = patch[k]; }}
    localStorage.setItem(DISEASE_META_KEY, JSON.stringify(m));
  }} catch (e) {{}}
}}

function headerStamp(headers) {{
  return (headers.get('last-modified') || '') + '|' + (headers.get('etag') || '');
}}

async function openDiseaseCache() {{
  try {{
    if (typeof caches === 'undefined' || !caches.open) return null;
    return await caches.open(DISEASE_CACHE);
  }} catch (e) {{
    console.warn('Cache Storage 不可用，本次退化为内存模式', e);
    return null;
  }}
}}

async function fetchWithProgress(url, fallbackTotal) {{
  var res = await fetch(url, {{ cache: 'no-store' }});
  if (!res.ok) throw new Error('HTTP ' + res.status);
  var total = parseInt(res.headers.get('content-length') || '0', 10) || (fallbackTotal || 0);
  var reader = (res.body && res.body.getReader) ? res.body.getReader() : null;
  if (!reader) {{
    var txt = await res.text();
    return {{ text: txt, bytes: txt.length, headers: res.headers }};
  }}
  var chunks = [];
  var received = 0;
  while (true) {{
    var step = await reader.read();
    if (step.done) break;
    chunks.push(step.value);
    received += step.value.length;
    var real = total ? Math.round(received / Math.max(total, received) * 100) : null;
    var pct = real === null ? null : Math.round(real * 0.84);
    dlSet(pct, '知识库下载中 ' + (real === null ? '' : real + '% · ') +
      dlMb(received) + (total ? ' / ' + dlMb(total) : ''));
  }}
  var blob = new Blob(chunks, {{ type: 'application/json' }});
  return {{ blob: blob, bytes: received, headers: res.headers }};
}}

async function innerLoadDisease() {{
  var cache = await openDiseaseCache();
  var cached = null;
  if (cache) {{
    try {{ cached = await cache.match(DISEASE_URL); }} catch (e) {{ cached = null; }}
  }}
  var meta = readMeta();

  if (cached && meta.stamp && meta.checkedAt &&
      (Date.now() - meta.checkedAt) < DISEASE_RECHECK_MS) {{
    return await cached.json();
  }}

  var remoteStamp = '';
  try {{
    var head = await fetch(DISEASE_URL, {{ method: 'HEAD', cache: 'no-store' }});
    if (head.ok) remoteStamp = headerStamp(head.headers);
  }} catch (e) {{}}

  if (cached && remoteStamp && meta.stamp === remoteStamp) {{
    writeMeta({{ stamp: remoteStamp, checkedAt: Date.now() }});
    dlSet(null, '');
    return await cached.json();
  }}

  try {{
    dlSet(0, '知识库准备中…');
    var got = await fetchWithProgress(DISEASE_URL, meta.bytes || 0);
    var text = got.blob ? await got.blob.text() : got.text;
    var data = JSON.parse(text);
    dlSet(88, '正在解析 ' + data.length + ' 条疾病…');
    if (cache && got.blob) {{
      var keep = new Headers();
      ['content-type', 'etag', 'last-modified'].forEach(function (k) {{
        var v = got.headers.get(k);
        if (v) keep.set(k, v);
      }});
      try {{
        await cache.put(DISEASE_URL, new Response(got.blob, {{ status: 200, headers: keep }}));
      }} catch (e) {{
        console.warn('写入缓存失败，本次内存中仍可用', e);
      }}
    }}
    writeMeta({{
      stamp: remoteStamp || ('local:' + Date.now()),
      checkedAt: Date.now(),
      bytes: got.bytes || 0
    }});
    dlSet(100, '');
    return data;
  }} catch (err) {{
    if (cached) {{
      if (meta.checkedAt && (Date.now() - meta.checkedAt) > DISEASE_TTL_MS) {{
        console.warn('本地缓存已超过 7 天，且下载失败，暂用旧数据', err);
      }} else {{
        console.warn('下载失败，退回本地缓存', err);
      }}
      dlSet(100, '');
      return await cached.json();
    }}
    throw err;
  }}
}}

function loadDiseaseData() {{
  if (diseaseData) return Promise.resolve(diseaseData);
  if (diseaseLoading) return diseaseLoading;
  var p = innerLoadDisease().then(function (data) {{
    diseaseData = data;
    diseaseLoading = null;
    return data;
  }}, function (err) {{
    diseaseLoading = null;
    throw err;
  }});
  diseaseLoading = p;
  return p;
}}

function showDiseaseLoadingTip() {{
  var box = document.getElementById('disease-results');
  if (!box) return;
  box.innerHTML = '<div class="search-tips" id="dl-msg">⏳ ' + (window.__dlText || '知识库准备中…') + '</div>';
}}

function scheduleDiseasePrefetch() {{
  var nc = navigator.connection || {{}};
  if (nc.saveData === true) {{ console.log('省流量模式，跳过疾病知识库预取'); return; }}
  if (/slow-2g|2g/.test(nc.effectiveType || '')) {{ console.log('当前网络较慢，跳过预取'); return; }}
  loadDiseaseData().catch(function (e) {{ console.warn('疾病知识库预取失败', e); }});
}}

function switchTab(tab) {{
  document.getElementById('tab-news').style.display = 'none';
  document.getElementById('tab-disease').style.display = 'none';
  document.getElementById('tab-videos').style.display = 'none';
  document.getElementById('btn-news').classList.remove('active');
  document.getElementById('btn-disease').classList.remove('active');
  document.getElementById('btn-videos').classList.remove('active');
  document.getElementById('tab-' + tab).style.display = 'block';
  document.getElementById('btn-' + tab).classList.add('active');
  localStorage.setItem('lastActiveTab', tab);
  if (tab === 'disease') {{
    showDiseaseLoadingTip();
    loadDiseaseData().then(performSearch, function (err) {{
      document.getElementById('disease-results').innerHTML =
        '<div class="search-tips" style="color:red;">⚠️ 加载失败: ' + err.message + '</div>';
    }});
  }} else if (tab === 'videos') {{
    loadVideoPage();
  }}
}}

let videoMemoryCache = null;
async function getVideoIndex(url) {{
  if (videoMemoryCache) {{
    return videoMemoryCache;
  }}
  const res = await fetch(url);
  if (!res.ok) {{
    throw new Error("视频索引文件加载失败");
  }}
  const data = await res.json();
  videoMemoryCache = data;
  return data;
}}

async function loadVideoPage() {{
  const listBox = document.getElementById('videoListBox');
  // 加载提示写进内部容器，不会冲掉上方 notice‑tip
  listBox.innerHTML = '<div style="padding:20px;text-align:center;color:#666;">⏳ 正在加载视频资源...</div>';
  try {{
    const allVideoData = await getVideoIndex('./videos_index.json');
    renderSourceCardList(allVideoData);
  }} catch(e) {{
    listBox.innerHTML = '<div style="padding:20px;text-align:center;color:#c00;">❌ 数据源加载失败</div>';
    console.error(e);
  }}
}}

function renderSourceCardList(list) {{
  const listBox = document.getElementById('videoListBox');
  if (!list || list.length === 0) {{
    listBox.innerHTML = '<div style="padding:20px;text-align:center;color:#666;">暂无视频资源</div>';
    return;
  }}
  let html = '';
  list.forEach(function(item){{
    html += `<div class="disease-list-card" data-url="${{item.url}}">
      <h3>${{item.title}} <span style="font-size:11px; background:#e5e7eb; color:#6b7280; padding:2px 6px; border-radius:4px; float:right;">视频合集</span></h3>
      <p>${{item.desc}}</p>
    </div>`;
  }});
  listBox.innerHTML = html;

  const cards = listBox.querySelectorAll('.disease-list-card');
  cards.forEach(function(card){{
    card.onclick = function(){{
      const u = this.dataset.url;
      if(u){{
        window.open(u, '_blank');
      }}
    }};
  }});
}}

function filterNews(category, btn) {{
  const buttons = document.querySelectorAll('.filter-btn');
  buttons.forEach(function(b) {{ b.classList.remove('active'); }});
  btn.classList.add('active');
  const cards = document.querySelectorAll('.news-card');
  cards.forEach(function(card) {{
    if (category === 'all' || card.getAttribute('data-category') === category) {{
      card.style.display = 'block';
    }} else {{
      card.style.display = 'none';
    }}
  }});
}}

function filterDept(dept, btn) {{
  currentDept = dept;
  document.querySelectorAll('.dept-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  performSearch();
}}

let searchTimer = null;
function debounceSearch() {{
  clearTimeout(searchTimer);
  searchTimer = setTimeout(performSearch, 300);
}}

async function performSearch() {{
  const query = document.getElementById('disease-search').value.trim();
  const resultContainer = document.getElementById('disease-results');
  if (!diseaseData) {{
    resultContainer.innerHTML = '<div class="search-tips" id="dl-msg">⏳ 正在准备疾病知识库…</div>';
    try {{
      await loadDiseaseData();
    }} catch (err) {{
      resultContainer.innerHTML = '<div class="search-tips" style="color:red;">⚠️ 加载失败: ' + err.message + '</div>';
      return;
    }}
  }}
  let matches = [];
  
  if (query.length > 0) {{
    matches = diseaseData.filter(function(item){{
      return item.title.includes(query) && (currentDept === 'all' || item.mapped_dept === currentDept);
    }}).slice(0, 30);
  }} else {{
    if (currentDept === 'all') {{
      matches = diseaseData.slice(0, 30);
    }} else {{
      matches = diseaseData.filter(function(item){{
        return item.mapped_dept === currentDept;
      }}).slice(0, 30);
    }}
  }}
  if (matches.length === 0) {{
    resultContainer.innerHTML = '<div class="search-tips">未找到相关疾病，请尝试其他关键词或科室。</div>';
    return;
  }}
  let htmlStr = '';
  window.currentSearchResults = matches;
  matches.forEach(function(item, index) {{
    const safeTitle = item.title.replace(/</g, "&lt;");
    const shortDesc = (item.desc || "暂无简介").substring(0, 40) + "...";
    const deptTag = '<span style="font-size:11px; background:#e5e7eb; color:#6b7280; padding:2px 6px; border-radius:4px; float:right; margin-top:2px;">' + item.mapped_dept + '</span>';
    
    htmlStr += '<div class="disease-list-card" onclick="openModal(' + index + ')">'
      + '<h3>' + safeTitle + ' ' + deptTag + '</h3>'
      + '<p>' + shortDesc + '</p>'
      + '</div>';
  }});
  resultContainer.innerHTML = htmlStr;
}}

function openModal(index) {{
  const item = window.currentSearchResults[index];
  if (!item) return;
  document.getElementById('modal-title').innerText = item.title;
  
  let bodyHtml = '';
  if (item.desc) bodyHtml += '<div class="detail-section"><span class="detail-label label-desc">简介</span><div>' + item.desc + '</div></div>';
  if (item.cause) bodyHtml += '<div class="detail-section"><span class="detail-label label-cause">病因</span><div>' + item.cause + '</div></div>';
  if (item.symptom) bodyHtml += '<div class="detail-section"><span class="detail-label label-symptom">症状</span><div>' + item.symptom + '</div></div>';
  if (item.cure_way) bodyHtml += '<div class="detail-section"><span class="detail-label label-cure">治疗</span><div>' + item.cure_way + '</div></div>';
  if (item.prevent) bodyHtml += '<div class="detail-section"><span class="detail-label label-prevent">预防</span><div>' + item.prevent + '</div></div>';
  
  if (item.drugs && item.drugs.length > 0) {{
    let drugTags = item.drugs.map(function(d){{
      return '<span class="drug-tag">' + d + '</span>';
    }}).join('');
    bodyHtml += '<div class="detail-section"><span class="detail-label label-drug">用药参考</span><div class="drug-tags">' + drugTags + '</div></div>';
  }}
  if (item.department) bodyHtml += '<div class="detail-section"><span class="detail-label label-desc">就诊科室</span><div>' + item.department + '</div></div>';
  document.getElementById('modal-body').innerHTML = bodyHtml;
  
  document.getElementById('modal-overlay').classList.add('show');
  document.getElementById('modal-content').classList.add('show');
  document.body.style.overflow = 'hidden';
}}

function closeModal() {{
  document.getElementById('modal-overlay').classList.remove('show');
  document.getElementById('modal-content').classList.remove('show');
  document.body.style.overflow = '';
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

window.onload = function(){{
  const lastTab = localStorage.getItem('lastActiveTab');
  if(lastTab){{
    switchTab(lastTab);
  }}
  if ('requestIdleCallback' in window) {{
    requestIdleCallback(scheduleDiseasePrefetch, {{ timeout: 4000 }});
  }} else {{
    setTimeout(scheduleDiseasePrefetch, 2500);
  }}
}}
</script>
</body>
</html>'''

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_doc)
    print(f"已生成 {OUTPUT_FILE}，修复JS语法错误。")


if __name__ == "__main__":
    main()
