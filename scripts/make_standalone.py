#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 standalone.html：用「全局时间驱动 step 显隐」把 index_present.html + 音频时间轴对齐。

用法：
  python3 make_standalone.py \
      --present <课目录>/视频课/index_present.html \
      --report  /tmp/<课>/audio/report.json \
      --out     /tmp/<课>/standalone.html \
      --sched   /tmp/<课>/schedule.json \
      [--nf 16] [--title "课程名"] [--keep-audio]

帧间静音秒不再是命令行参数：由 load_config.frame_gap() 唯一决定（默认 0.9，改
config 的 defaults.frame_gap）。阶段 3 拼 _merged.wav 用的是同一个值，所以不可能
错配。脚本末尾还会拿 _merged.wav 实测时长对一遍，漂移 >0.15s 直接报错退出。

关键设计（踩坑后固化）：
  1. **HTML 结构原样输出，一个字符都不删**。旧版用正则把 step 从 frame 里删掉当 static，
     会破坏 div 嵌套（残留孤立 </div>），导致第 2 帧之后整屏空白。
  2. CSS 复用 index_present.html 的原始 <style>，视觉 100% 一致。
  3. 兼容两种 frame 写法：`<div class="stage-frame" id="f04">` 与 `<div id="f04" class="frame stage-frame">`。
  4. 默认**剥掉 <audio>**：阶段 4 的成片音轨由 ffmpeg 混入 _merged.wav，
     放映版里内嵌的儿歌音频若留在 standalone 会重复出声。
  5. bind_delays：step 数 == 对话行数时 1:1 锚定每句起始秒（`units[i].start`）；
     不相等则帧内均匀分布——绝不能让所有 step 都堆在 0s，否则画面提前泄题。
"""
import argparse, contextlib, json, os, re, sys, wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_config import frame_gap     # 帧间静音唯一来源（勿在此写字面量）


def highlight(text, kws):
    """给关键词包上 <span class="kw">；kws 按长度降序，避免短词截断长词。"""
    if not kws:
        return text
    pat = re.compile("(" + "|".join(re.escape(k) for k in sorted(kws, key=len, reverse=True)) + ")")
    return pat.sub(r'<span class="kw">\1</span>', text)


def srt_ts(sec):
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def chunk_text(text, hard=30, soft=18):
    """把长句按标点切成字幕条片段：强标点（。？！）在 len>=soft 后断，
    超过 hard 硬断；尾巴太短并回上一段。返回片段列表。"""
    strong = "。？！?!?"
    parts, buf = [], ""
    i = 0
    while i < len(text):
        ch = text[i]
        buf += ch
        # 破折号「——」整体作断点
        if ch == "—" and i + 1 < len(text) and text[i + 1] == "—":
            buf += "—"
            i += 1
            if len(buf) >= soft:
                parts.append(buf)
                buf = ""
        elif (ch in strong and len(buf) >= soft) or len(buf) >= hard:
            parts.append(buf)
            buf = ""
        i += 1
    if buf:
        if parts and len(buf) <= 5:
            parts[-1] += buf
        else:
            parts.append(buf)
    return parts


# step 匹配：按 class 分词匹配（兼容 <div class="step"> 与 <div class="step anim-pop">）。
# ⛔ 不要改回精确串 `class="step"` —— 阶段 2 要求给 step 挂动效 class（anim-pop/anim-slam/
#    anim-fade-rise…），精确串会静默漏掉这些 step：JS 侧 querySelectorAll('.step') 认得它们，
#    Python 侧却不算数，结果是这些 step 拿不到 .on、被 CSS 的 .step{opacity:0} 永久隐藏，
#    成片里画面凭空消失且不报错。
STEP_RE = re.compile(r'<div\b[^>]*\bclass\s*=\s*"[^"]*(?<![-\w])step(?![-\w])[^"]*"[^>]*>', re.I)


def extract_frames(html):
    """按 stage-frame 标签配对切出每帧 inner HTML（原样，不删任何字符）。"""
    frames, order = {}, []
    for m in re.finditer(r'<div[^>]*class="[^"]*stage-frame[^"]*"[^>]*>', html):
        tag = m.group(0)
        fm = re.search(r'id="f(\d+)"', tag)
        if not fm:
            continue
        fid = int(fm.group(1))
        # 从标签结束处按 <div>/</div> 配对，找到本帧真正的收尾
        i = m.end()
        depth = 1
        for t in re.finditer(r'<div\b|</div>', html[i:]):
            depth += 1 if t.group(0) == '<div' else -1
            if depth == 0:
                inner = html[i:i + t.start()]
                frames[fid] = inner
                order.append(fid)
                break
    return frames, order


def strip_audio(html):
    html = re.sub(r'<audio\b.*?</audio>', '', html, flags=re.S | re.I)
    html = re.sub(r'<audio\b[^>]*/?>', '', html, flags=re.I)
    return html


def wav_duration(path):
    """纯 stdlib 读 WAV 时长；不是 WAV 或读不了时返回 None（不因此阻断出片）。"""
    try:
        with contextlib.closing(wave.open(path, "rb")) as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return None


def main():
    # 旧命令/旧文档会传 `--gap 0.9` 或 `--gap 0.25`。现在帧间 gap 由 config 唯一决定，
    # 传这个值必然是照旧文档抄的，与其让 argparse 报 unrecognized，不如说清去哪改。
    if any(a == "--gap" or a.startswith("--gap=") for a in sys.argv[1:]):
        sys.exit("❌ --gap 已移除：帧间静音由 config 的 defaults.frame_gap 唯一决定"
                 f"（当前 {frame_gap()}s），命令行不接受。要改节奏改 config.local.json。")
    ap = argparse.ArgumentParser()
    ap.add_argument("--present", required=True, help="index_present.html 路径")
    ap.add_argument("--report", required=True, help="阶段3 产出的 report.json")
    ap.add_argument("--out", required=True, help="输出 standalone.html")
    ap.add_argument("--sched", required=True, help="输出 schedule.json")
    ap.add_argument("--nf", type=int, default=None, help="帧数；缺省按 HTML 自动识别")
    ap.add_argument("--title", default="课程双音色成片")
    ap.add_argument("--keep-audio", action="store_true", help="保留内嵌 <audio>（默认剥掉）")
    ap.add_argument("--subtitles", action="store_true", help="在 standalone 里加底部字幕条（师生分色+关键词高亮）")
    ap.add_argument("--animate", action="store_true", help="保留入场动效（实时渲染管线用；默认冻结动画供静帧截图）")
    ap.add_argument("--keywords", default="", help="逗号分隔的关键词表，字幕中高亮")
    ap.add_argument("--srt", default=None, help="同时输出 .srt 字幕文件路径")
    args = ap.parse_args()
    kws = [k.strip() for k in args.keywords.split(",") if k.strip()]
    gap = frame_gap()

    html = open(args.present, encoding="utf-8").read()
    styles = re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)
    BASE_CSS = "\n".join(styles) if styles else ""

    # 从源放映版 #stageWrap 读取舞台尺寸（竖版 1080×1440 / 横版 1920×1080，不写死）。
    # 匹配 <div id="stageWrap" style="...width:1080px...height:1440px"> 或 CSS #stageWrap{...}
    dm = re.search(r'id="stageWrap"[^>]*style="[^"]*?width:\s*(\d+)px[^"]*?height:\s*(\d+)px', html) \
        or re.search(r'#stageWrap\s*\{[^}]*?width:\s*(\d+)px[^}]*?height:\s*(\d+)px', html)
    W = int(dm.group(1)) if dm else 1920
    H = int(dm.group(2)) if dm else 1080

    frames, order = extract_frames(html)
    if not frames:
        sys.exit("没有解析到任何 stage-frame，检查 index_present.html 结构")
    NF = args.nf or max(frames)

    report = json.load(open(args.report, encoding="utf-8"))
    dur_map = {r["frame"]: r["dur"] for r in report}
    units_map = {r["frame"]: r.get("units", []) for r in report}

    starts, cum = {}, 0.0
    for fi in range(1, NF + 1):
        starts[fi] = round(cum, 3)
        cum += dur_map.get(fi, 0.0) + gap
    total = round(cum - gap, 3)

    # 音画总时长对账：任何一侧用了不同的帧间 gap，末帧就会漂移数秒、成片报废。
    # 与其在文档里写「--gap 必须 0.9」，不如让脚本自己拿 _merged.wav 实测一遍。
    merged_wav = os.path.join(os.path.dirname(os.path.abspath(args.report)), "_merged.wav")
    adur = wav_duration(merged_wav) if os.path.exists(merged_wav) else None
    if adur is not None:
        diff = total - adur
        if abs(diff) > 0.15:
            sys.exit(
                f"❌ 音画总时长对不上：时间轴 {total:.2f}s vs {os.path.basename(merged_wav)} "
                f"{adur:.2f}s（差 {diff:+.2f}s）。常见原因：report.json 缺帧/多帧、"
                f"--nf 与音频帧数不符、或音频侧与画面侧帧间 gap 不一致"
                f"（帧间 gap 唯一来源 = config defaults.frame_gap，当前 {gap}s）。")
        print(f"音画时长对账: 时间轴 {total:.2f}s vs 音频 {adur:.2f}s（差 {diff:+.3f}s）✅")
    else:
        print("⚠️ 未找到 _merged.wav 与之对账，跳过时长校验"
              f"（期望路径 {merged_wav}）")

    def bind_delays(n_steps, units, fdur):
        if n_steps == 0:
            return []
        if n_steps == len(units) and units:
            delays = [u["start"] for u in units]
        else:
            span = max((u["start"] + u["dur"] for u in units), default=fdur) or fdur
            delays = [round(i / n_steps * max(span - 0.05, 0.0), 3) for i in range(n_steps)]
        for i in range(1, len(delays)):          # 单调化，避免倒序
            delays[i] = max(delays[i], delays[i - 1])
        return delays

    DATA, changes, SUBS = {}, set(), []
    for fi in range(1, NF + 1):
        if fi not in frames:
            print("!! 缺少帧 f%02d" % fi)
            continue
        inner = frames[fi] if args.keep_audio else strip_audio(frames[fi])
        fdur = dur_map.get(fi, 0.0)
        gstart = starts[fi]
        gend = round(gstart + fdur + gap, 3)   # 显示到下一帧前，避免白屏闪烁

        steps = list(STEP_RE.finditer(inner))
        delays = bind_delays(len(steps), units_map.get(fi, []), fdur)
        steps_data = []
        for i, sm in enumerate(steps):
            appear = round(gstart + (delays[i] if i < len(delays) else 0), 3)
            hm = re.search(r'data-hide-at="(\d+)"', sm.group(0))
            if hm:
                idx = int(hm.group(1)) - 1
                disappear = round(gstart + (delays[idx] if idx < len(delays) else fdur), 3)
            else:
                disappear = gend   # step 显示到下一帧前，避免帧间空隙画面清空闪烁
            steps_data.append({"ap": appear, "di": max(disappear, appear)})
            changes.update([appear, max(disappear, appear)])

        DATA["f%02d" % fi] = {"gstart": gstart, "gend": gend, "steps": steps_data}
        changes.update([gstart, gend])

        if args.subtitles:
            units = units_map.get(fi, [])
            for ui, u in enumerate(units):
                t0 = round(gstart + u.get("start", 0.0), 3)
                # 最后一句延长到 gend（含帧间 gap），避免帧切换时字幕闪灭
                nxt = (round(gstart + units[ui + 1].get("start", 0.0), 3)
                       if ui + 1 < len(units) else gend)
                t1 = round(max(nxt - 0.05, t0 + 0.4), 3)
                txt = re.sub(r'["“”]', "", u.get("text", "")).strip()
                if not txt:
                    continue
                stu = 1 if "学生" in u.get("speaker", "") else 0
                chunks = chunk_text(txt)
                tot = sum(len(c) for c in chunks) or 1
                cur = t0
                for c in chunks:
                    d = (t1 - t0) * len(c) / tot
                    SUBS.append({"t0": round(cur, 3), "t1": round(cur + d, 3),
                                 "h": highlight(c, kws), "k": stu})
                    # 字幕切换点必须进截图区间，否则截图时字幕停在上一个区间的状态
                    changes.update([round(cur, 3), round(cur + d, 3)])
                    cur += d

    changes.add(total)
    changes = sorted(round(c, 3) for c in changes)
    intervals = [{"t": changes[k], "dur": round(changes[k + 1] - changes[k], 3)}
                 for k in range(len(changes) - 1) if changes[k + 1] - changes[k] > 0.001]

    OVERRIDE_CSS = """
  /* ===== 时间轴驱动（standalone） ===== */
  html, body { margin:0; padding:0; background:#FFF7EC; }
  #root { position:relative; width:%dpx; height:%dpx; overflow:hidden; background:#FFF7EC; }
  .stage-frame { display:none; }
  .stage-frame.on { display:block; }
  .step { opacity:0; transform:none; }
  .step.on { opacity:1; transform:none; }
""" + ("" if args.animate else """
  /* 冻结所有过渡动画：静帧截图管线在 applyTime 后仅等 ~90ms，
     课件原生的 .45s 渐入会被拍在半路（半透明"置灰"帧）。
     --animate 模式（实时渲染管线）保留动效，由 CSS 动画接管入场。 */
  .step, .step.on, .step.gone, .stage-frame, #subtitle, #subbar {
          transition:none !important; animation:none !important; }
""")
    OVERRIDE_CSS = OVERRIDE_CSS % (W, H)   # 注入舞台尺寸（竖版/横版自适应）
    SUB_CSS = """
  /* ===== 视频版四角布局：左上徽章(不动) / 右上标语 / 底部居中字幕 / 右下品牌 ===== */
  #f01 .hdr { left:76px !important; }   /* 第1帧徽章行贴左上，与其他帧一致 */
  .foot { position:absolute; inset:0; display:block; gap:0; justify-content:normal;
          padding:0; background:none; pointer-events:none; }
  .foot > span:not(.brand) { position:absolute; top:52px; right:44px;
          font-size:34px; color:#5F5E5A; letter-spacing:2px; }
  .foot .brand { position:absolute; right:44px; bottom:26px; font-size:26px;
          padding:8px 26px; border-radius:999px; border:3px solid #1D2D49; }
  /* ===== 底部字幕条（单行、无边框、师生分色 + 关键词高亮） ===== */
  #subbar { position:fixed; left:50%; transform:translateX(-50%); bottom:26px; z-index:999;
            display:none; }
  #subbar.on { display:block; }
  #subtitle { font-family:var(--font-title,'圆体-简','Yuanti SC',sans-serif); font-weight:700;
              font-size:34px; line-height:1.35; text-align:center; white-space:nowrap;
              padding:0 12px; background:none;
              color:#1D2D49;
              text-shadow:0 0 6px rgba(255,250,238,.95),0 0 14px rgba(255,250,238,.85),
                          0 2px 3px rgba(29,45,73,.28); }
  #subtitle.stu { color:#C2255C; }
  #subtitle .kw { color:#D9480F; background:#F6E360; border-radius:10px; padding:0 7px;
                  font-size:1.12em; }
"""
    SUB_HTML = ('<div id="subbar"><div id="subtitle"></div></div>\n') if args.subtitles else ""
    frames_html = ['<div class="stage-frame" id="f%02d">%s</div>' % (fi, DATA and (frames[fi] if args.keep_audio else strip_audio(frames[fi])).rstrip())
                   for fi in sorted(frames) if fi <= NF]

    SUB_JS = ""
    if args.subtitles:
        SUB_JS = ("var SUBS=" + json.dumps(SUBS, ensure_ascii=False) + ";\n"
                  "var subBar=document.getElementById('subbar'),"
                  "subEl=document.getElementById('subtitle'),curSub=null;\n"
                  "function applySub(t){\n"
                  "  var sub=null;\n"
                  "  for(var i=0;i<SUBS.length;i++){var s=SUBS[i];"
                  " if(t>=s.t0-0.0005&&t<s.t1-0.0005){sub=s;break;}}\n"
                  "  if(sub){ if(curSub!==sub){ subEl.innerHTML=sub.h;"
                  " subEl.className=sub.k?'stu':''; curSub=sub; } subBar.classList.add('on'); }\n"
                  "  else { subBar.classList.remove('on'); curSub=null; }\n"
                  "}\n")

    script = ("<script>\nvar HF_DATA = " + json.dumps(DATA, ensure_ascii=False) + ";\n"
              + SUB_JS +
              "function applyTime(t){\n"
              "  var ids = Object.keys(HF_DATA);\n"
              "  for(var k=0;k<ids.length;k++){\n"
              "    var d = HF_DATA[ids[k]], el = document.getElementById(ids[k]);\n"
              "    if(!el) continue;\n"
              "    var on = (t >= d.gstart - 0.0005 && t < d.gend - 0.0005);\n"
              "    el.classList.toggle('on', on);\n"
              "    if(!on) continue;\n"
              "    var ss = el.querySelectorAll('.step');\n"
              "    for(var i=0;i<ss.length;i++){\n"
              "      var s = d.steps[i];\n"
              "      ss[i].classList.toggle('on', !!(s && t >= s.ap - 0.0005 && t < s.di - 0.0005));\n"
              "    }\n"
              "  }\n"
              + ("  applySub(t);\n" if args.subtitles else "") +
              "}\nwindow.applyTime = applyTime;\napplyTime(0);\n</script>\n")

    doc = ('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">'
           + '<meta name="hf-size" content="%dx%d">' % (W, H)
           + '<title>' + args.title +
           '</title><style>\n' + BASE_CSS + OVERRIDE_CSS
           + (SUB_CSS if args.subtitles else "") + '\n</style></head><body>\n<div id="root">\n'
           + "\n".join(frames_html) + "\n</div>\n" + SUB_HTML + script + "</body></html>")

    open(args.out, "w", encoding="utf-8").write(doc)
    json.dump({"total": total, "intervals": intervals}, open(args.sched, "w"), ensure_ascii=False, indent=1)

    if args.subtitles and args.srt:
        with open(args.srt, "w", encoding="utf-8") as f:
            for i, s in enumerate(SUBS, 1):
                plain = re.sub(r"<[^>]+>", "", s["h"])
                f.write("%d\n%s --> %s\n%s\n\n" % (i, srt_ts(s["t0"]), srt_ts(s["t1"]), plain))

    print("写出", args.out)
    print("总时长 %.2fs | 帧 %d | 截图区间 %d" % (total, len(frames_html), len(intervals)))
    print("step 总数:", sum(len(v["steps"]) for v in DATA.values()))
    bad = [("f%02d" % fi) for fi in sorted(frames) if fi <= NF and frames[fi].count("<div") != frames[fi].count("</div>")]
    print("div 不配平(应为空):", bad if bad else "无")
    # step 数 vs 台词句数：不一致时该帧走「帧内均匀分布」兜底，音画不再 1:1 锚定。
    # 门禁由 verify_steps.py 把关（它会 exit 1），这里只做显式提示，避免静默降级。
    mism = ["f%02d(step%d/台词%d)" % (fi, len(DATA["f%02d" % fi]["steps"]), len(units_map.get(fi, [])))
            for fi in sorted(frames) if fi <= NF and "f%02d" % fi in DATA
            and len(DATA["f%02d" % fi]["steps"]) != len(units_map.get(fi, []))]
    print("step 数 vs 台词句数 不一致(应为空):", mism if mism else "无")
    if mism:
        print("⚠️ 以上帧会退化为「帧内均匀分布」，画面不再逐句锚定；"
              "先跑 verify_steps.py <课目录> 修到一致再出片")


if __name__ == "__main__":
    main()
