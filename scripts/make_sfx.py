#!/usr/bin/env python3
"""自动生成音效时刻表与混流命令（阶段 4 用）。

输入三样，全部已有产物，无需人工听音频定位：
  1. 剧本 script_v2_dialog.txt（用于数每帧台词行、识别不念词的表情行）
  2. sfx_plan.txt（阶段 1 gate 确认的音效提案，每行：帧 行 音效名 [台词前缀]）
  3. report.json + 帧音频目录（最终采用的变速版本；帧起点=Σ前帧dur+0.9，帧内句尾用 silencedetect 实测）

用法：
  python3 $SK/scripts/make_sfx.py \
    --script "$H/视频课/script_v2_dialog.txt" \
    --plan "$H/视频课/sfx_plan.txt" \
    --audio "$W/音频_v2_125" \
    --sfx-dir "$SK/assets/sfx" \
    --intro 7.5 \
    --out "$H/视频课/音效时刻.txt"

输出：音效时刻.txt（每行：音效名 + 正片秒 + 成片秒），并打印可直接执行的 ffmpeg 混流命令。
退出码：定位失败/前缀对不上时 exit 1（宁可失败不要错位进成片）。
"""
import argparse, json, os, re, subprocess, sys

GAP = 0.9          # 帧间静音（dialog2audio 合同）
SFX_DELAY = 0.15   # 音效在目标句结束后的起播延迟
MIN_SPEECH = 0.2   # 短于此的有声区间视为杂音，不计段


def parse_script(path):
    """返回 {帧号: [is_silent_line, ...]}，行序即剧本角色行序。"""
    frames, cur = {}, None
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        m = re.match(r"【第\s*(\d+)\s*帧】", line)
        if m:
            cur = int(m.group(1)); frames[cur] = []
        elif cur and re.match(r"^(老师|学生)[：:]", line):
            frames[cur].append(("哭脸" in line or "笑脸" in line))
    return frames


def speech_segments(wav):
    """silencedetect 细切有声段 [(start, end)]。句内自然停顿会把它切得比台词行数多，
    由 merge_by_gap 按需合并。"""
    p = subprocess.run(
        ["ffmpeg", "-i", wav, "-af", "silencedetect=noise=-35dB:d=0.15", "-f", "null", "-"],
        capture_output=True, text=True)
    sil = [(float(a), float(b)) for a, b in re.findall(
        r"silence_start:\s*([\d.]+).*?silence_end:\s*([\d.]+)", p.stderr, re.S)]
    # 有声 = 全长的 silence 补集
    segs, cur, total = [], 0.0, float(re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", p.stderr) and
        int(re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", p.stderr).group(1)) * 3600 +
        int(re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", p.stderr).group(2)) * 60 +
        float(re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", p.stderr).group(3)))
    for s, e in sil:
        if s - cur >= MIN_SPEECH:
            segs.append((cur, s))
        cur = max(cur, e)
    if total - cur >= MIN_SPEECH:
        segs.append((cur, total))
    return segs, sil


def merge_by_gap(segs, sil, thr):
    """把被短于 thr 的静音隔开的有声段合并（thr=0 不合并）。"""
    if not segs:
        return segs
    merged = [list(segs[0])]
    for i, (s, e) in enumerate(sil[:len(segs) - 1]):
        if e - s < thr:
            merged[-1][1] = segs[i + 1][1]
        else:
            merged.append(list(segs[i + 1]))
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--audio", required=True, help="最终变速版本的音频目录（含 report.json 与 frame_NN.wav）")
    ap.add_argument("--sfx-dir", required=True)
    ap.add_argument("--intro", type=float, default=0.0, help="片头时长（成片秒 = 正片秒 + intro）")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    script = parse_script(args.script)
    report = json.load(open(os.path.join(args.audio, "report.json"), encoding="utf-8"))
    durs = {e["frame"]: float(e["dur"]) for e in report}
    starts = {}
    t = 0.0
    for f in sorted(durs):
        starts[f] = t
        t += durs[f] + GAP

    rows, cmds, errors = [], [], []
    for raw in open(args.plan, encoding="utf-8"):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        fno, lno, name = int(parts[0]), int(parts[1]), parts[2]
        prefix = parts[3] if len(parts) > 3 else ""
        wav = os.path.join(args.audio, f"frame_{fno:02d}.wav")
        sfx = os.path.join(args.sfx_dir, f"{name}.wav")
        if not os.path.isfile(wav):
            errors.append(f"帧 {fno}: 找不到 {wav}"); continue
        if not os.path.isfile(sfx):
            errors.append(f"音效 {name}: 找不到 {sfx}"); continue
        if fno not in script:
            errors.append(f"帧 {fno}: 剧本中不存在"); continue
        lines = script[fno]
        if not (1 <= lno <= len(lines)):
            errors.append(f"帧 {fno} 行 {lno}: 超出范围（该帧共 {len(lines)} 行）"); continue
        raw, sil = speech_segments(wav)
        spoken = [i for i, s in enumerate(lines) if not s]  # 有声行下标
        # 自适应合并：句内自然停顿会多切，按间隙阈值阶梯合并到台词行数；对不齐即失败
        target = len(spoken)
        segs = None
        for thr in (0.0, 0.5, 0.75, 0.9, 1.1, 1.3):
            cand = merge_by_gap(raw, sil, thr)
            if len(cand) == target:
                if thr:
                    print(f"帧 {fno}: 细切 {len(raw)} 段 → 合并阈值 {thr}s 对齐 {target} 行")
                segs = cand
                break
        if segs is None:
            errors.append(f"帧 {fno}: 任何合并阈值都对不齐 {target} 个台词段（细切 {len(raw)} 段），请人工检查音频")
            continue
        # 该帧台词前缀校验（从剧本原文取该行前 8 字）
        full = open(args.script, encoding="utf-8").read()
        fm = re.search(rf"【第\s*{fno}\s*帧】([\s\S]*?)(?=【第\s*\d+\s*帧】|$)", full)
        frame_lines = re.findall(r"^(?:老师|学生)[：:](.+)$", fm.group(1), re.M) if fm else []
        if prefix and frame_lines and lno <= len(frame_lines):
            head = re.sub(r"\[\[.*?\]\]", "", frame_lines[lno - 1]).strip().strip('"“”')
            if prefix and not head.startswith(prefix):
                errors.append(f"帧 {fno} 行 {lno}: 前缀不符（剧本该句是「{head[:12]}…」）"); continue
        k = spoken.index(lno - 1) + 1  # 该行是帧内第几个有声段
        if k > len(segs):
            errors.append(f"帧 {fno} 行 {lno}: 只实测到 {len(segs)} 个有声段"); continue
        pos = starts[fno] + segs[k - 1][1] + SFX_DELAY
        rows.append((name, pos, pos + args.intro))

    if errors:
        print("\n".join("❌ " + e for e in errors), file=sys.stderr)
        sys.exit(1)
    if not rows:
        print("plan 为空，无事可做"); return

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("音效时刻（make_sfx.py 自动生成，正片秒基于最终变速音频实测）\n")
        for name, pos, cpos in rows:
            f.write(f"{name}\t{pos:.2f}\t{cpos:.2f}\n")
    # 打印混流命令（成片时间轴）
    inputs, chains, labels = [], [], ""
    for i, (name, pos, cpos) in enumerate(rows):
        inputs.append(f'-i "$SK/assets/sfx/{name}.wav"')
        ms = int(round(cpos * 1000))
        chains.append(f'[{i + 2}:a]volume=0.85,adelay={ms}|{ms}[s{i + 1}];')
        labels += f'[s{i + 1}]'
    n = len(rows)
    print("混流命令（在 4c 第二步混流基础上加输入与链，成片时间轴）：\n")
    print(f"ffmpeg -i video_cfr.mp4 -i {os.path.join(args.audio, '_merged.wav')} "
          f"{' '.join(inputs)} \\\n  -filter_complex \"{''.join(chains)}"
          f"[1:a]{labels}amix=inputs={n + 1}:duration=first:normalize=0[a]\" \\\n"
          f"  -map 0:v -map \"[a]\" -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest 成片.mp4")
    print(f"\n时刻表已写入 {args.out}")


if __name__ == "__main__":
    main()
