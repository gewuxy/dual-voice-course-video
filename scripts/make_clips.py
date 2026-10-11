#!/usr/bin/env python3
"""make_clips.py — 从双音色成片自动切出视频号引流短视频（第 6 阶段）

用法:
  python3 make_clips.py --final <成片.mp4> --report <音频时长_report.json> \
      --outdir <输出目录> --clips clips.json

clips.json 格式（帧号取剧本【第 N 帧】的 N）:
[
  {"name": "切片1_积木分家家", "fstart": 4, "fend": 5, "hook": "hook1.png"},
  {"name": "切片2_决策树",     "fstart": 7, "fend": 8, "hook": "hook2.png"}
]
- 切片范围 = 帧fstart起点 → 帧fend起点前(去掉帧间 gap，取 frame_gap())，与句子边界对齐，不会切半句。
- hook 为 1920x1080 PNG 钩子卡（蜡笔风模板见 assets/clip_cards_template.html）；
  片尾统一使用 outdir 同级的 endcard.png，没有则跳过。
- 时长核对: fstart/fend 也可直接用 "start"/"end" 秒数覆盖帧号。

要点: 帧时间 = sum(前面各帧 dur) + GAP*帧序；GAP 取 load_config.frame_gap()，
与阶段 3 拼 _merged.wav、阶段 4 standalone 时间轴同源，改 config 即可改节奏。
"""
import argparse, json, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_config import frame_gap   # 帧间静音唯一来源（勿在此写字面量）

GAP = frame_gap()

def frame_starts(report):
    t, starts = 0.0, {}
    for fr in report:
        starts[fr["frame"]] = t
        t += fr["dur"] + GAP
    return starts

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--clips", required=True, help="clips.json，见文件头注释")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    report = json.load(open(a.report))
    starts = frame_starts(report)
    total = max(v for k, v in starts.items()) + report[-1]["dur"]
    endcard = os.path.join(os.path.dirname(a.outdir.rstrip("/")), "endcard.png")
    if not os.path.exists(endcard):
        endcard = os.path.join(os.path.dirname(a.outdir.rstrip("/")), "视频课", "endcard.png")
    has_end = os.path.exists(endcard)
    for spec in json.load(open(a.clips)):
        if "start" in spec:
            s, e = spec["start"], spec["end"]
        else:
            s = starts[spec["fstart"]]
            e = (starts[spec["fend"]] - GAP) if "fend" in spec else total
        name, hook = spec["name"], spec["hook"]
        out = os.path.join(a.outdir, f"{name}.mp4")
        inputs = ["-loop", "1", "-t", "2.5", "-i", hook, "-ss", f"{s:.2f}", "-to", f"{e:.2f}", "-i", a.final]
        parts_v, parts_a, n = ["[0:v]fps=30,format=yuv420p[v0]"], None, 2
        tail_v, tail_a = "", ""
        if has_end:
            inputs += ["-loop", "1", "-t", "2.5", "-i", endcard]
            tail_v = f";[{n}:v]fps=30,format=yuv420p[v{n}]"
            tail_a = f";aevalsrc=0:c=stereo:s=44100:d=2.5[a{n}]"
            n += 1
        fc = ("[0:v]fps=30,format=yuv420p[v0];"
              f"[1:v]fps=30,format=yuv420p[v1]{tail_v};"
              "aevalsrc=0:c=stereo:s=44100:d=2.5[a0];"
              f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo[a1]{tail_a};")
        vch = "".join(f"[v{i}]" for i in range(n))
        ach = "".join(f"[a{i}]" for i in range(n))
        fc += f"{vch}concat=n={n}:v=1:a=0[v];{ach}concat=n={n}:v=0:a=1[a]"
        cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
               "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
        print(f"==> {name}  {s:.1f}s → {e:.1f}s  ({e - s:.1f}s + 卡)")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-1200:]); sys.exit(f"clip failed: {name}")
        d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
        print(f"    done  dur={d}s")
    print("all clips done")

if __name__ == "__main__":
    main()
