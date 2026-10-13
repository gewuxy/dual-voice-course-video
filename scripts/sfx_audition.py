#!/usr/bin/env python3
"""生成音效试听页：抓取 Mixkit 各分类候选音效，嵌入 base64 音频输出单个 HTML。

用法：
  python3 sfx_audition.py --out /tmp/sfx_audition          # 全部五类
  python3 sfx_audition.py --names laugh,ding --per 10      # 指定类别、每类条数

产出 <out>/试听.html：每条含播放器/标题/时长，当前已用素材标记「在用」。
选定后把对应 preview mp3 按 make_sfx.py 约定转成 48kHz wav 覆盖 assets/sfx/<名>.wav，
再重跑 make_sfx.py + 混流即可（TTS/视频零重合成）。

许可：Mixkit License（免费商用、无需署名）https://mixkit.co/license/
"""
import argparse
import base64
import html
import re
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
BASE = "https://mixkit.co"
PREVIEW = "https://assets.mixkit.co/active_storage/sfx/{i}/{i}-preview.mp3"

# 音效名 -> Mixkit 分类页（有效分类以站内为准：boing 在 cartoon、wow 在 gasp、cheer 在 win）
CATEGORIES = {
    "laugh": ["laugh"],
    "ding": ["ding"],
    "cheer": ["win", "children"],
    "boing": ["cartoon"],
    "wow": ["gasp", "girl"],
}
CURRENT = {"laugh": 343, "ding": 235, "cheer": 344, "boing": 2894, "wow": 967}


def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_items(page):
    """返回 [(sid, title, dur)]，按页面顺序。"""
    out = []
    for b in re.split(r'data-audio-player-item-id-value="', page)[1:]:
        sid = b[: b.index('"')]
        m = re.search(r'class="item-grid-card__title"[^>]*>\s*([^<]{3,80})', b)
        d = re.search(r'data-test-id="duration">\s*([0-9]:[0-9]{2})', b)
        title = html.unescape(m.group(1)).strip() if m else "?"
        out.append((sid, title, d.group(1) if d else "?"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default=",".join(CATEGORIES))
    ap.add_argument("--per", type=int, default=8, help="每类抓取条数")
    ap.add_argument("--out", default="/tmp/sfx_audition")
    args = ap.parse_args()

    import os
    os.makedirs(args.out, exist_ok=True)

    sections, audio_cache = [], {}
    for name in [n.strip() for n in args.names.split(",") if n.strip()]:
        cats = CATEGORIES.get(name)
        if not cats:
            print(f"⚠️ 未知音效类别 {name}（可选：{', '.join(CATEGORIES)}）", file=sys.stderr)
            continue
        items, seen = [], set()
        for cat in cats:
            try:
                page = fetch(f"{BASE}/free-sound-effects/{cat}/").decode("utf-8", "ignore")
            except Exception as e:
                print(f"⚠️ {cat} 页面抓取失败：{e}", file=sys.stderr)
                continue
            for sid, title, dur in parse_items(page):
                if sid not in seen:
                    seen.add(sid)
                    items.append((sid, title, dur, cat))
        rows = []
        for sid, title, dur, cat in items[: args.per]:
            cur = " <b>【在用】</b>" if int(sid) == CURRENT.get(name) else ""
            if sid not in audio_cache:
                try:
                    audio_cache[sid] = base64.b64encode(fetch(PREVIEW.format(i=sid))).decode()
                except Exception as e:
                    print(f"⚠️ 音频 {sid} 下载失败：{e}", file=sys.stderr)
                    continue
            src = f"data:audio/mpeg;base64,{audio_cache[sid]}"
            rows.append(f"""<div class="row{' cur' if cur else ''}">
<audio controls preload="none" src="{src}"></audio>
<div class="meta"><span class="t">{html.escape(title)}{cur}</span>
<span class="d">#{sid} · {dur} · {cat}</span></div></div>""")
        sections.append(f"<h2>{name} <small>（当前在用：#{CURRENT.get(name, '—')}）</small></h2>"
                        + "".join(rows) or f"<h2>{name}</h2><p class=warn>无候选</p>")
        print(f"{name}: {len(rows[: args.per])} 条候选")

    page = f"""<!DOCTYPE html><html lang="zh"><meta charset="utf-8">
<title>SFX 试听</title><style>
body{{font-family:-apple-system,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;background:#faf9f6;color:#1d2d49}}
h2{{margin:28px 0 8px;border-bottom:2px solid #ffd84d;padding-bottom:4px}}
h2 small{{color:#888;font-weight:400}}
.row{{display:flex;align-items:center;gap:12px;padding:8px 4px;border-bottom:1px solid #eee}}
.row.cur{{background:#fff7d6}}
audio{{width:300px;height:32px}}
.meta{{display:flex;flex-direction:column}}
.t{{font-weight:600}}.d{{color:#888;font-size:12px}}
.warn{{color:#c00}}
footer{{margin-top:24px;color:#888;font-size:12px}}
</style>
<h1>音效试听台</h1>
<p>选中后告知编号，替换流程：下载 → 掐头静音(-50dB) → 48kHz 单声道 wav → <code>assets/sfx/&lt;名&gt;.wav</code> → 重跑 make_sfx.py + 混流（约 1 分钟，TTS/视频零重合成）。</p>
{''.join(sections)}
<footer>素材：Mixkit（免费商用、无需署名）· 本页由 sfx_audition.py 生成</footer>"""
    outp = os.path.join(args.out, "试听.html")
    open(outp, "w", encoding="utf-8").write(page)
    print(f"✅ {outp}")


if __name__ == "__main__":
    main()
