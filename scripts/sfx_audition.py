#!/usr/bin/env python3
"""交互式音效试听台：抓 Mixkit 候选 + 内嵌对白整轨，浏览器端 Web Audio 实时重混。

用法：
  python3 sfx_audition.py --out /tmp/sfx_audition \
      --mix 对白轨.m4a --timings 音效时刻_快混.txt \
      --picks laugh=2265,ding=1743,cheer=600,boing=744

--mix     干净对白轨（不含音效；如 _merged.wav 转的低码率 m4a）
--timings make_sfx.py 输出的时刻表（名\t正片秒\t成片秒；成片=正片+片头时用成片秒）
--picks   预选候选（可省略；页内随时换，点「确定·重新混音」即听）

产出 <out>/试听.html：选音效 → 确定重混 → 整段/逐点试听，循环直到满意。
选定后转 48kHz wav 覆盖 assets/sfx/<名>.wav → 重跑 make_sfx.py + 混流（约 1 分钟零重合成）。
许可：Mixkit License（免费商用、无需署名）https://mixkit.co/license/
"""
import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
BASE = "https://mixkit.co"
PREVIEW = "https://assets.mixkit.co/active_storage/sfx/{i}/{i}-preview.mp3"

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
    out = []
    for b in re.split(r'data-audio-player-item-id-value="', page)[1:]:
        sid = b[: b.index('"')]
        m = re.search(r'class="item-grid-card__title"[^>]*>\s*([^<]{3,80})', b)
        d = re.search(r'data-test-id="duration">\s*([0-9]:[0-9]{2})', b)
        title = html.unescape(m.group(1)).strip() if m else "?"
        out.append((sid, title, d.group(1) if d else "?"))
    return out


def parse_timings(path):
    """时刻表 -> [{name, t}]，取成片秒（第三列；无则第二列）。"""
    moments = []
    for line in open(path, encoding="utf-8"):
        parts = line.split()
        if len(parts) >= 3 and re.match(r"^[\d.]+$", parts[1]):
            t = float(parts[2]) if len(parts) >= 3 and re.match(r"^[\d.]+$", parts[2]) else float(parts[1])
            moments.append({"name": parts[0], "t": round(t, 2)})
        elif len(parts) == 2 and re.match(r"^[\d.]+$", parts[1]):
            moments.append({"name": parts[0], "t": round(float(parts[1]), 2)})
    return moments


def mmss(t):
    return f"{int(t // 60)}:{int(t % 60):02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default=",".join(CATEGORIES))
    ap.add_argument("--per", type=int, default=8)
    ap.add_argument("--out", default="/tmp/sfx_audition")
    ap.add_argument("--mix", help="对白整轨音频（不含音效）")
    ap.add_argument("--timings", help="make_sfx.py 时刻表")
    ap.add_argument("--picks", help="预选，如 laugh=2265,ding=1743")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    picks = {}
    if args.picks:
        for kv in args.picks.split(","):
            k, v = kv.split("=")
            picks[k.strip()] = v.strip()
    moments = parse_timings(args.timings) if args.timings else []

    cats, audio_cache = {}, {}
    for name in [n.strip() for n in args.names.split(",") if n.strip()]:
        cats_c = CATEGORIES.get(name)
        if not cats_c:
            print(f"⚠️ 未知类别 {name}", file=sys.stderr)
            continue
        items, seen = [], set()
        for cat in cats_c:
            try:
                page = fetch(f"{BASE}/free-sound-effects/{cat}/").decode("utf-8", "ignore")
            except Exception as e:
                print(f"⚠️ {cat} 抓取失败：{e}", file=sys.stderr)
                continue
            for sid, title, dur in parse_items(page):
                if sid not in seen:
                    seen.add(sid)
                    items.append({"id": sid, "title": title, "dur": dur, "cat": cat})
        chosen = picks.get(name, str(CURRENT.get(name, "")))
        for it in items[: args.per]:
            if it["id"] not in audio_cache:
                try:
                    audio_cache[it["id"]] = base64.b64encode(fetch(PREVIEW.format(i=it["id"]))).decode()
                except Exception as e:
                    print(f"⚠️ {it['id']} 下载失败：{e}", file=sys.stderr)
                    continue
            it["b64"] = audio_cache[it["id"]]
        cats[name] = {"current": CURRENT.get(name), "pick": chosen, "items": items[: args.per]}
        print(f"{name}: {len(cats[name]['items'])} 条，预选 #{chosen}")

    dialog_b64 = ""
    if args.mix:
        dialog_b64 = base64.b64encode(open(args.mix, "rb").read()).decode()
        print(f"对白轨 {args.mix} -> {len(dialog_b64) // 1024} KB(base64)")

    data = {"dialog": dialog_b64, "moments": moments, "cats": cats}
    page = _HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    outp = os.path.join(args.out, "试听.html")
    open(outp, "w", encoding="utf-8").write(page)
    print(f"✅ {outp}  ({os.path.getsize(outp) // 1024} KB)")


_HTML = r"""<!DOCTYPE html><html lang="zh"><meta charset="utf-8">
<title>SFX 混音试听台</title><style>
body{font-family:-apple-system,sans-serif;max-width:820px;margin:20px auto;padding:0 16px;background:#faf9f6;color:#1d2d49}
h1{font-size:22px}h2{margin:24px 0 6px;border-bottom:2px solid #ffd84d;padding-bottom:4px}
h2 small{color:#888;font-weight:400}
.bar{background:#fff;border:1px solid #e5e0d5;border-radius:12px;padding:14px 16px;margin:10px 0}
button{background:#1d2d49;color:#fff;border:none;border-radius:8px;padding:7px 14px;font-size:14px;cursor:pointer;margin:2px 4px 2px 0}
button:hover{background:#33507a}button:disabled{opacity:.4;cursor:wait}
.chip{background:#f2efe8;color:#1d2d49;font-size:12px;padding:5px 10px}
.chip.on{background:#ffd84d}
.row{display:flex;align-items:center;gap:10px;padding:6px 4px;border-bottom:1px solid #eee;flex-wrap:wrap}
.row.playing{background:#fff7d6}
.row input{accent-color:#1d2d49}
.row audio{width:240px;height:28px}
.meta{display:flex;flex-direction:column;min-width:170px}
.t{font-weight:600}.d{color:#888;font-size:12px}
#status{color:#666;font-size:13px;min-height:18px}
footer{margin-top:20px;color:#888;font-size:12px}
</style>
<h1>🎛️ SFX 混音试听台</h1>
<div class="bar">
  <b>操作</b>：每类选一个候选 → 点「🔊 确定并重新混音」→ 整段听或逐点试听；不满意继续换再点确定。
  <div id="status"></div>
</div>
<div class="bar" id="playerBar">
  <button id="btnFull">▶ 从头试听全段</button>
  <button id="btnStop">■ 停止</button>
  <span style="color:#888;font-size:13px">逐音效点：</span>
  <span id="momentChips"></span>
</div>
<div id="sections"></div>
<footer>素材：Mixkit（免费商用、无需署名）· 本页由 sfx_audition.py 生成 · 选定后转 48kHz wav 覆盖 assets/sfx/<名>.wav，重跑 make_sfx.py + 混流约 1 分钟零重合成</footer>
<script>
const DATA = __DATA__;
const VOLUME = 0.85, ctx = new (window.AudioContext||window.webkitAudioContext)();
const state = {};           // name -> 选中的 id
let sources = [], playingChips = [];

// ---- 初始化 UI ----
const sec = document.getElementById('sections');
for (const [name, c] of Object.entries(DATA.cats)) {
  state[name] = c.pick || String(c.current || '');
  const div = document.createElement('div');
  div.innerHTML = `<h2>${name} <small>（当前入库：#${c.current ?? '—'}）</small></h2>` +
    c.items.map(it => `
    <div class="row" data-row="${name}-${it.id}">
      <input type="radio" name="${name}" value="${it.id}" ${state[name]===it.id?'checked':''}>
      <audio controls preload="none" src="data:audio/mpeg;base64,${it.b64}"></audio>
      <div class="meta"><span class="t">${it.title}</span><span class="d">#${it.id} · ${it.dur} · ${it.cat}</span></div>
    </div>`).join('');
  sec.appendChild(div);
  div.addEventListener('change', e => { if (e.target.type==='radio') state[name]=e.target.value; });
}

// ---- 音效时刻 chips ----
const chipsEl = document.getElementById('momentChips');
const moments = DATA.moments;
chipsEl.innerHTML = moments.map((m,i) =>
  `<button class="chip" data-i="${i}">${mmss(m.t)} ${m.name}</button>`).join('');
chipsEl.addEventListener('click', e => {
  const b = e.target.closest('.chip'); if (!b) return;
  const m = moments[+b.dataset.i];
  playMix(Math.max(0, m.t - 2), 14, +b.dataset.i);
});

// ---- 解码 ----
function b2ab(b64){ const bin=atob(b64), u=new Uint8Array(bin.length);
  for(let i=0;i<bin.length;i++) u[i]=bin.charCodeAt(i); return u.buffer; }
const bufCache = {};
async function decode(key, b64){
  if (!bufCache[key]) bufCache[key] = await ctx.decodeAudioData(b2ab(b64));
  return bufCache[key];
}
async function ensureDialog(){
  if (!DATA.dialog) throw new Error('未提供对白轨（--mix）');
  return decode('dialog', DATA.dialog);
}

// ---- 混音播放：from 秒开始播 dur 秒，时刻表内音效按当前选择叠加 ----
function stopAll(){
  sources.forEach(s => { try{ s.src.stop(); }catch{} });
  sources = []; playingChips.forEach(c=>c.classList.remove('playing')); playingChips=[];
}
async function playMix(from, dur, focusI=-1){
  stopAll();
  const st = document.getElementById('status');
  try{
    st.textContent = '解码中…（首次约几秒）';
    const dlg = await ensureDialog();
    const need = [...new Set(moments.map(m=>state[m.name]).filter(Boolean))];
    await Promise.all(need.map(id => decode('sfx'+id,
      Object.values(DATA.cats).flatMap(c=>c.items).find(i=>i.id===id).b64)));
    if (ctx.state === 'suspended') await ctx.resume();
    const t0 = ctx.currentTime + 0.06;
    const s1 = ctx.createBufferSource(); s1.buffer = dlg; s1.connect(ctx.destination);
    s1.start(t0, from, dur); sources.push({src:s1});
    let n = 0;
    moments.forEach((m, i) => {
      const id = state[m.name]; if (!id) return;
      if (m.t < from - 0.01 || m.t > from + dur) return;
      const g = ctx.createGain(); g.gain.value = VOLUME; g.connect(ctx.destination);
      const s = ctx.createBufferSource(); s.buffer = bufCache['sfx'+id];
      s.connect(g); s.start(t0 + (m.t - from)); sources.push({src:s});
      n++;
      if (i === focusI || focusI === -2) {   // focusI=-2: 全部标亮
        const chip = chipsEl.children[i];
        chip.classList.add('playing'); playingChips.push(chip);
      }
    });
    st.textContent = `播放中：从 ${mmss(from)} 起 ${Math.round(dur)}s，叠加 ${n} 个音效`;
  }catch(e){ st.textContent = '❌ ' + e.message; }
}
document.getElementById('btnFull').onclick = () => playMix(0, 1e9, -2);
document.getElementById('btnStop').onclick = () => { stopAll(); document.getElementById('status').textContent='已停止'; };
</script>"""

if __name__ == "__main__":
    main()
