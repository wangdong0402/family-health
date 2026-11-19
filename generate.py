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
/* 优化后的头部样式 */
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
    ⚠️ 导航提示：本板块仅收录官方权威科普链接，内容版权归属原发布单位；所有视频仅作知识参考，不能替代医生面诊。
  </div>
  <div class="video-filter">
    <button class="btn-tab active" data-filter="all">全部</button>
    <button class="btn-tab" data-filter="央视健康">央视健康</button>
    <button class="btn-tab" data-filter="健康中国">健康中国</button>
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
let isLoadingData = false;
let currentDept = 'all';

function preloadData() {{
  if (diseaseData || isLoadingData) return;
  isLoadingData = true;

  try {{
    const cachedStr = localStorage.getItem('health_disease_cache');
    if (cachedStr) {{
      const cacheObj = JSON.parse(cachedStr);
      const now = new Date().getTime();
      if (now - cacheObj.timestamp < 43200000) {{
        diseaseData = cacheObj.data;
        isLoadingData = false;
        performSearch(); 
        return; 
      }}
    }}
  }} catch (e) {{
    console.warn("读取缓存失败，走网络请求", e);
  }}

  fetch('search_index.json') 
    .then(res => {{
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    }})
    .then(data => {{
      diseaseData = data;
      isLoadingData = false;
      performSearch();
      
      try {{
        localStorage.setItem('health_disease_cache', JSON.stringify({{
          timestamp: new Date().getTime(),
          data: data
        }}));
      }} catch (e) {{
        console.warn("存储空间不足", e);
      }}
    }})
    .catch(err => {{
      isLoadingData = false;
      document.getElementById('disease-results').innerHTML = `<div class="search-tips" style="color:red;">⚠️ 加载失败: ${{err.message}}</div>`;
    }});
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

  if (tab === 'disease') {{
    preloadData();
  }} else if (tab === 'videos') {{
    loadVideoPage();
  }}
}}

let videoMemoryCache = null;
let videoMemoryEtag = null;

const VIDEO_DB_NAME = "HealthVideoCache";
const VIDEO_STORE_NAME = "videoStore";
let videoDbInstance = null;
const VIDEO_CACHE_TTL = 7 * 24 * 60 * 60 * 1000;

async function videoOpenDB() {{
  if (videoDbInstance) return videoDbInstance;
  return new Promise(function(resolve, reject) {{
    const req = indexedDB.open(VIDEO_DB_NAME, 1);
    req.onupgradeneeded = function(e) {{
      const db = e.target.result;
      if (!db.objectStoreNames.contains(VIDEO_STORE_NAME)) {{
        db.createObjectStore(VIDEO_STORE_NAME);
      }}
    }};
    req.onsuccess = function(e) {{
      videoDbInstance = e.target.result;
      resolve(videoDbInstance);
    }};
    req.onerror = function(e) {{
      reject(e.target.error);
    }};
  }});
}}

async function videoDbPut(key, value) {{
  const db = await videoOpenDB();
  return new Promise(function(resolve, reject) {{
    const tx = db.transaction(VIDEO_STORE_NAME, "readwrite");
    const store = tx.objectStore(VIDEO_STORE_NAME);
    const req = store.put(value, key);
    req.onsuccess = resolve;
    req.onerror = function(e) {{
      reject(e.target.error);
    }};
  }});
}}

async function videoDbGet(key) {{
  const db = await videoOpenDB();
  return new Promise(function(resolve, reject) {{
    const tx = db.transaction(VIDEO_STORE_NAME, "readonly");
    const store = tx.objectStore(VIDEO_STORE_NAME);
    const req = store.get(key);
    req.onsuccess = function(e) {{
      resolve(e.target.result);
    }};
    req.onerror = function(e) {{
      reject(e.target.error);
    }};
  }});
}}

async function getVideoIndex(jsonUrl = "./videos_index.json") {{
  if (videoMemoryCache) {{
    return videoMemoryCache;
  }}

  let localCacheData = null;
  let localEtag = null;
  let localCacheTime = 0;
  try {{
    localCacheData = await videoDbGet("videoData");
    localEtag = await videoDbGet("videoEtag");
    localCacheTime = await videoDbGet("videoCacheTs") || 0;
  }} catch (err) {{
    console.warn("视频缓存读取失败，重新下载：", err);
  }}

  let remoteEtag = null;
  try {{
    const controller = new AbortController();
    const timer = setTimeout(function() {{ controller.abort(); }}, 5000);
    const headResp = await fetch(jsonUrl, {{
      method: "HEAD",
      signal: controller.signal
    }});
    clearTimeout(timer);
    remoteEtag = headResp.headers.get("etag");
  }} catch (e) {{
    console.warn("视频HEAD校验超时，使用时间兜底缓存");
  }}

  let cacheValid = false;
  if (localCacheData) {{
    if (remoteEtag && localEtag === remoteEtag) {{
      cacheValid = true;
    }} else if (!remoteEtag) {{
      const now = Date.now();
      if ((now - localCacheTime) < VIDEO_CACHE_TTL) {{
        cacheValid = true;
      }}
    }}
  }}

  if (cacheValid) {{
    console.log("[视频缓存命中]");
    videoMemoryCache = localCacheData;
    videoMemoryEtag = localEtag;
    return localCacheData;
  }}

  console.log("[视频缓存未命中] 拉取讲座列表");
  const resp = await fetch(jsonUrl);
  const newEtag = resp.headers.get("etag");
  const data = await resp.json();

  videoMemoryCache = data;
  videoMemoryEtag = newEtag;

  try {{
    await videoDbPut("videoData", data);
    await videoDbPut("videoEtag", newEtag);
    await videoDbPut("videoCacheTs", Date.now());
  }} catch (err) {{
    console.warn("写入视频缓存失败：", err);
  }}
  return data;
}}

let allVideoData = [];
let activeFilter = "all";

async function loadVideoPage() {{
  if(allVideoData.length > 0){{
    renderVideoCard();
    return;
  }}
  try{{
    allVideoData = await getVideoIndex();
    renderVideoCard();
  }}catch(e){{
    document.getElementById("videoListBox").innerHTML = "<p>讲座列表加载失败，请稍后重试</p >";
    console.error(e);
  }}
}}

function renderVideoCard(){{
  const box = document.getElementById("videoListBox");
  let filterData = allVideoData;
  if(currentVideoCat !== "all"){{
    filterData = allVideoData.filter(function(item) {{
      return item.category === currentVideoCat;
    }});
  }}
  let html = "";
  filterData.forEach(function(item){{
    html += "<div class=\"video-card\" onclick=\"window.open('"+item.url+"','_blank')\">"
      + "<h4>" + item.title + "</h4>"
      + "<div class=\"video-tag-row\">"
      + "<span class=\"src-tag\">" + item.source + "</span>"
      + "</div>"
      + "<p class=\"video-desc\">" + item.desc + "</p >"
      + "</div>";
  }})
  if(filterData.length === 0){{
    html = "<p>当前分类暂无讲座内容</p >";
  }}
  box.innerHTML = html;

  document.querySelectorAll(".video-card").forEach(function(card){{
    card.onclick = function(){{
      const u = this.dataset.url;
      window.open(u, "_blank");
    }}
  }})
}}

document.querySelectorAll(".filter-item").forEach(function(btn){{
  btn.onclick = function(){{
    document.querySelectorAll(".filter-item").forEach(function(b){{
      b.classList.remove("active");
    }});
    this.classList.add("active");
    activeFilter = this.dataset.filter;
    renderVideoCard();
  }};
}});

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
    resultContainer.innerHTML = '<div class="search-tips">⏳ 正在加载知识库，请稍候...</div>';
    try {{
      const response = await fetch('search_index.json?t=' + new Date().getTime());
      if (!response.ok) throw new Error("HTTP Status: " + response.status);
      diseaseData = await response.json();
    }} catch (err) {{
      resultContainer.innerHTML = `<div class="search-tips" style="color:red;">⚠️ 加载失败: ${{err.message}}</div>`;
      return;
    }}
  }}

  let matches = [];
  
  if (query.length > 0) {{
    matches = diseaseData.filter(item => 
      item.title.includes(query) && (currentDept === 'all' || item.mapped_dept === currentDept)
    ).slice(0, 30);
  }} else {{
    if (currentDept === 'all') {{
      matches = diseaseData.slice(0, 30);
    }} else {{
      matches = diseaseData.filter(item => item.mapped_dept === currentDept).slice(0, 30);
    }}
  }}

  if (matches.length === 0) {{
    resultContainer.innerHTML = '<div class="search-tips">未找到相关疾病，请尝试其他关键词或科室。</div>';
    return;
  }}

  let htmlStr = '';
  window.currentSearchResults = matches;

  matches.forEach((item, index) => {{
    const safeTitle = item.title.replace(/</g, "&lt;");
    const shortDesc = (item.desc || "暂无简介").substring(0, 40) + "...";
    const deptTag = `<span style="font-size:11px; background:#e5e7eb; color:#6b7280; padding:2px 6px; border-radius:4px; float:right; margin-top:2px;">${{item.mapped_dept}}</span>`;
    
    htmlStr += `
      <div class="disease-list-card" onclick="openModal(${{index}})">
        <h3>${{safeTitle}} ${{deptTag}}</h3>
        <p>${{shortDesc}}</p>
      </div>
    `;
  }});
  resultContainer.innerHTML = htmlStr;
}}

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
  
  if (item.drugs && item.drugs.length > 0) {{
    let drugTags = item.drugs.map(d => `<span class="drug-tag">${{d}}</span>`).join('');
    bodyHtml += `
      <div class="detail-section">
        <span class="detail-label label-drug">用药参考</span>
        <div class="drug-tags">${{drugTags}}</div>
      </div>
    `;
  }}

  if (item.department) bodyHtml += `<div class="detail-section"><span class="detail-label label-desc">就诊科室</span><div>${{item.department}}</div></div>`;

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
</script>
</body>
</html>'''

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_doc)

    print(f"已生成 {OUTPUT_FILE}，加入了门诊分类功能与修复逻辑。")

if __name__ == "__main__":
    main()
