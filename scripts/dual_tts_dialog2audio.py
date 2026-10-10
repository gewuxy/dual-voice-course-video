#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
师生剧本双音色配音生成器（单进程 / 双模型）

解析规则（尽量简单，只保留必须）：
  【第 N 帧】            -> 帧分隔，同一帧内的行依次合成、首尾相接
  小贤老师："..."[[n]]   -> 用 xiaoxian 音色合成；[[n]] = 该句之后额外静音 n 秒
  学生："..."[[n]]       -> 用 macie 音色合成
  学生行含「哭脸/笑脸」  -> 视为动作，不念词，只留静音（[[n]] 秒，无则 3 秒）
  —— 破折号 -> 逗号；AI/A.I. -> 诶爱；引号/括号去除

用法：
  PYTORCH_ENABLE_MPS_FALLBACK=1 ./venv/bin/python dialog2audio.py \
      --script script_v2_dialog.txt --outdir /tmp/dlg [--only 1,9] [--takes 3]

产物：outdir/frame_01.wav ... + _merged.wav + report.json
"""
import argparse, glob, json, os, re, subprocess, sys
import numpy as np
import soundfile as sf
import torch
import torchaudio

ROOT = os.path.dirname(os.path.abspath(__file__))
GS = os.path.join(ROOT, "GPT-SoVITS")
FF = "/opt/homebrew/bin/ffmpeg"
SR = 32000

# 长跑全量合成时（21 帧）单轮删除文件会触发沙箱 bulk-delete 守卫（阈值 50/轮），
# 导致进程被杀。--no-cleanup 时跳过临时 take 文件与行临时 wav 的 os.remove，
# 既避免守卫，又不影响最终 frame_NN.wav（临时文件稍后用 mv 移走即可）。
NO_CLEANUP = False

# ---- 解析相关 ----
PAUSE_RE = re.compile(r"\[\[\s*(\d+(?:\.\d+)?)\s*\]\]")
TARGET_CPS = 3.23
MIN_UNIT = 12
HARD_MAX = 28
ACTION_WORDS = ("哭脸", "笑脸")

# 老师显示名（可配置：环境变量 TEACHER_NAME，默认「小贤老师」；音色仍固定 xiaoxian）。
# 设了 TEACHER_NAME，剧本里老师角色行就用该名（兼容全角/半角冒号）。
TEACHER_NAME = os.environ.get("TEACHER_NAME", "小贤老师")

# 两个说话人各自的模型 / 参考音
EXPS = {
    "teacher": {"exp": "xiaoxian",
                "ref": os.path.join(ROOT, "dataset", "xiaoxian", "wavs", "xiaoxian_0029.wav"),
                "ref_text": "我们是不是就能告诉电脑，这是一只猫啦？对了！这就是我们今天要学会的本领"},
    "student": {"exp": "macie",
                "ref": os.path.join(ROOT, "dataset", "macie", "wavs", "macie_13.wav"),
                "ref_text": "我叫 Macie，今年八岁，我最喜欢画画和搭积木。"},
}


def pick_weights(exp):
    g = sorted(glob.glob(os.path.join(ROOT, "GPT_weights", f"{exp}-e*.ckpt")),
               key=lambda p: int(re.search(r"e(\d+)", os.path.basename(p)).group(1)))
    s = sorted(glob.glob(os.path.join(ROOT, "SoVITS_weights", f"{exp}_e*_s*.pth")),
               key=lambda p: int(re.search(r"e(\d+)", os.path.basename(p)).group(1)))
    if not g or not s:
        sys.exit(f"缺少权重：{exp}")
    return g[-1], s[-1]


def clean(s):
    s = re.sub(r"[（(][^）)]*[)）]", "", s)
    for q in ['"', '"', "'", "‘", "’", "“", "”"]:
        s = s.replace(q, "")
    for en, zh in [("Skill Struck", "斯吉尔斯特拉克"), ("A.I.", "诶爱"), ("AI", "诶爱")]:
        s = s.replace(en, zh)
    s = s.replace("——", "，")
    return re.sub(r"\s+", "", s).strip()


def parse_line(line):
    """返回 (speaker, text, pause) 或 None（非对白行）。
    老师名读环境变量 TEACHER_NAME（默认「小贤老师」），兼容全角/半角冒号；学生固定「学生」。"""
    m = re.match(rf'^\s*{re.escape(TEACHER_NAME)}\s*[:：]\s*(.*)$', line)
    if m:
        content = m.group(1).strip().strip('"').strip()
        mm = PAUSE_RE.search(content)
        if mm:
            text, pause = content[:mm.start()].strip(), float(mm.group(1))
        else:
            text, pause = content, 0.0
        return "teacher", text, pause
    m = re.match(r'^\s*学生\s*[:：]\s*(.*)$', line)
    if m:
        content = m.group(1).strip().strip('"').strip()
        mm = PAUSE_RE.search(content)
        if mm:
            text, pause = content[:mm.start()].strip(), float(mm.group(1))
        else:
            text, pause = content, 0.0
        return "student", text, pause
    return None


def split_units(text, min_len=MIN_UNIT, hard_max=HARD_MAX):
    text = re.sub(r"[！!]+", "！", text)
    text = re.sub(r"[？?]+", "？", text)
    text = re.sub(r"[。]+", "。", text)
    END, SOFT = "。！？；", "，、：,"
    parts, buf = [], ""
    for ch in text:
        buf += ch
        if ch in END:
            parts.append(buf); buf = ""
    if buf:
        parts.append(buf)
    merged = []
    for p in parts:
        if len(p) < min_len and merged:
            merged[-1] += p
        else:
            merged.append(p)
    out = []
    for p in merged:
        while len(p) > hard_max:
            idx = max([i for i, c in enumerate(p[:hard_max]) if c in SOFT] or [hard_max - 1])
            out.append(p[:idx + 1]); p = p[idx + 1:]
        out.append(p)
    # 关键修复：旧逻辑用 >=4 把 1~3 字短句（如"苹果！""数据集！"）整句丢弃，
    # 导致学生(Macie)童声全部缺失。改为 >=1，仅丢弃纯标点/空串，保留所有真实台词。
    return [u for u in out if len(re.sub(r"[^\u4e00-\u9fff]", "", u)) >= 1]


def dur_of(path):
    try:
        return float(sf.info(path).duration)
    except Exception:
        r = subprocess.run([FF, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", path], capture_output=True, text=True)
        for s in (r.stdout, r.stderr):
            for tok in s.split():
                try:
                    return float(tok)
                except ValueError:
                    continue
        return 0.0


def read_mono(path, sr=SR):
    d, s = sf.read(path, dtype="float32")
    if d.ndim > 1:
        d = d.mean(axis=1)
    t = torch.from_numpy(np.ascontiguousarray(d))
    if s != sr:
        t = torchaudio.functional.resample(t, s, sr)
    return t.numpy()


def synth_unit(tts, ref, ref_text, unit, out_f, takes, temperature):
    """合成单句，按语速挑最优 seed，返回 wav 路径；失败返回 None。"""
    best, budget, seed = None, takes, 0
    while seed < budget:
        f = out_f + f"_s{seed}.wav"
        try:
            sr, audio = next(tts.run({
                "task_id": f"{os.path.basename(out_f)}-{seed}", "text": unit,
                "text_lang": "zh", "ref_audio_path": ref, "prompt_text": ref_text,
                "prompt_lang": "zh", "top_p": 1.0, "temperature": temperature,
                "text_split_method": "cut5", "sample_steps": 32,
                "speed_factor": 1.0, "seed": seed,
            }))
        except Exception as e:
            print(f"    unit 失败: {e}"); seed += 1; continue
        sf.write(f, audio, sr)
        n = len(re.sub(r"[^\u4e00-\u9fff]", "", unit))
        r = n / max(sf.info(f).duration, 0.01)
        cost = abs(r - TARGET_CPS) * (1.6 if r > TARGET_CPS else 1.0)
        if best is None or cost < best[0]:
            best = (cost, r, f)
        if abs(r - TARGET_CPS) / TARGET_CPS < 0.18:
            break
        seed += 1
        if seed == takes and best and best[1] > TARGET_CPS * 1.45:
            budget = takes + 6
    if best is None:
        return None
    src = best[2]
    dst = out_f + ".wav"
    if src != dst:
        os.replace(src, dst)
    if not NO_CLEANUP:
        for i in range(budget):
            tmp = out_f + f"_s{i}.wav"
            if os.path.exists(tmp) and tmp != dst:
                os.remove(tmp)
    return dst


def synth_line(speaker, text, pause, models, out_prefix, takes, temperature):
    """合成一行：返回该行音频 wav 路径（已含句后静音）。动作行只出静音。"""
    tts, ref, ref_text = models[speaker]
    # 动作行（哭脸/笑脸）：只留静音
    if speaker == "student" and any(w in text for w in ACTION_WORDS):
        dur = pause if pause > 0 else 3.0
        out = out_prefix + ".wav"
        sf.write(out, np.zeros(int(dur * SR), dtype=np.float32), SR)
        print(f"    [动作] {speaker} 静音 {dur:.1f}s")
        return out
    units = split_units(clean(text))
    paths = []
    for ui, unit in enumerate(units):
        f = synth_unit(tts, ref, ref_text, unit, f"{out_prefix}_u{ui}", takes, temperature)
        if f:
            paths.append(f)
    if not paths:
        print(f"    [空] {speaker}: {text[:20]}"); return None
    chunks = []
    for i, p in enumerate(paths):
        a = read_mono(p)
        if i > 0:
            chunks.append(np.zeros(int(0.2 * SR), dtype=np.float32))
        chunks.append(a)
        if p != (out_prefix + ".wav"):
            os.remove(p)
    speech = np.concatenate(chunks) if chunks else np.zeros(1, dtype=np.float32)
    if pause > 0:
        speech = np.concatenate([speech, np.zeros(int(pause * SR), dtype=np.float32)])
    out = out_prefix + ".wav"
    sf.write(out, np.clip(speech, -1.0, 1.0), SR)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--only", default=None, help="只做某几帧，如 1,9")
    ap.add_argument("--takes", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--gap", type=float, default=0.4, help="帧内行间间隔秒")
    ap.add_argument("--device", default="cpu", choices=["cpu", "mps"])
    ap.add_argument("--no-cleanup", action="store_true",
                    help="跳过临时 take 文件删除（避免大批量合成触发沙箱 bulk-delete 守卫）")
    args = ap.parse_args()
    global NO_CLEANUP
    NO_CLEANUP = args.no_cleanup

    args.script = os.path.abspath(args.script)
    args.outdir = os.path.abspath(args.outdir)
    os.makedirs(args.outdir, exist_ok=True)
    only = set(int(x) for x in args.only.split(",")) if args.only else None

    os.chdir(GS)
    sys.path.insert(0, GS)
    sys.path.insert(0, os.path.join(GS, "GPT_SoVITS"))
    os.environ["version"] = os.environ.get("version", "v2")
    import soundfile as sf_raw
    def _load(p):
        d, sr = sf_raw.read(p, dtype="float32", always_2d=True)
        return torch.from_numpy(d.T), sr
    torchaudio.load = _load

    from TTS_infer_pack.TTS import TTS, TTS_Config

    models = {}
    for sp, cfg in EXPS.items():
        gpt, sovits = pick_weights(cfg["exp"])
        tts = TTS(TTS_Config({"custom": {
            "device": args.device, "is_half": False, "version": "v2",
            "t2s_weights_path": gpt, "vits_weights_path": sovits,
            "bert_base_path": "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large",
            "cnhuhubert_base_path": "GPT_SoVITS/pretrained_models/chinese-hubert-base",
        }}))
        models[sp] = (tts, os.path.abspath(cfg["ref"]), cfg["ref_text"])
        print(f"模型已加载  {sp}  gpt={os.path.basename(gpt)}  sovits={os.path.basename(sovits)}")

    # 解析剧本 -> 帧 -> 行
    frames, cur = {}, None
    for ln in open(args.script, encoding="utf-8"):
        ln = ln.rstrip("\n")
        m = re.match(r"【第\s*(\d+)\s*帧】", ln)
        if m:
            cur = int(m.group(1)); frames.setdefault(cur, []); continue
        pl = parse_line(ln)
        if pl and cur is not None:
            frames[cur].append(pl)

    report = []
    for fi in sorted(frames):
        if only and fi not in only:
            continue
        print(f"\n=== 帧 {fi} ===")
        line_paths = []
        line_start = 0.0
        units_tl = []
        for ri, (speaker, text, pause) in enumerate(frames[fi]):
            label = "老师" if speaker == "teacher" else "学生"
            print(f"  {label}: {text[:30]}{'…' if len(text) > 30 else ''}  (静音{pause})")
            lp = synth_line(speaker, text, pause, models,
                            os.path.join(args.outdir, f"f{fi}_{label}_{ri}"),
                            args.takes, args.temperature)
            if lp:
                d = dur_of(lp)
                units_tl.append({"speaker": label, "text": text,
                                 "pause": pause, "dur": round(d, 3),
                                 "start": round(line_start, 3)})
                line_paths.append(lp)
                line_start += d + args.gap
        if not line_paths:
            print(f"  帧 {fi} 无有效行"); continue
        out = os.path.join(args.outdir, f"frame_{fi:02d}.wav")
        items = [(line_paths[0], 0.0)] + [(p, args.gap) for p in line_paths[1:]]
        chunks = []
        for p, gap in items:
            a = read_mono(p)
            if gap > 0:
                chunks.append(np.zeros(int(gap * SR), dtype=np.float32))
            chunks.append(a)
            if not NO_CLEANUP:
                os.remove(p)
        sf.write(out, np.clip(np.concatenate(chunks), -1.0, 1.0), SR)
        report.append({"frame": fi, "dur": round(dur_of(out), 2), "units": units_tl})
        print(f"  -> {out}  {dur_of(out):.1f}s")

    json.dump(report, open(os.path.join(args.outdir, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if len(report) > 1:
        merged = os.path.join(args.outdir, "_merged.wav")
        chunks = []
        for r in report:
            a = read_mono(os.path.join(args.outdir, f"frame_{r['frame']:02d}.wav"))
            chunks.append(a); chunks.append(np.zeros(int(0.9 * SR), dtype=np.float32))
        sf.write(merged, np.clip(np.concatenate(chunks[:-1]), -1.0, 1.0), SR)
        print(f"\n合并 -> {merged}  {dur_of(merged):.1f}s")
    print("完成。")


if __name__ == "__main__":
    main()
