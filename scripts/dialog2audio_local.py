#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
师生剧本配音生成器 —— 本地 TTS 兜底路由（无 GPT-SoVITS 时使用，跨平台）

按平台自动选择合成后端（均系统自带或零安装，输出合同完全一致）：
  macOS   `say`          老师 Tingting（婷婷）/ 学生 Meijia（美佳+抬调）
  Windows PowerShell + System.Speech(SAPI)  自动枚举中文语音包（Huihui/Yaoyao…），
                          师生取不同声音；仅一个中文声音时用 SSML 抬调区分学生
  Linux   espeak-ng      cmn 普通话（机器味较重，能用但音质最差）

输出与 dialog2audio.py（GPT-SoVITS 路由）完全一致的合同：
  outdir/frame_NN.wav   每帧音频（帧内行距 --gap，默认 0.4s）
  outdir/_merged.wav    全课合并（帧间硬编码 0.9s，与 make_standalone --gap 0.9 对应）
  outdir/report.json    顶层 list：[{frame, dur, units:[{speaker,text,pause,pre,dur,start}]}]
统一 32000 Hz / Int16 / 单声道（后端输出采样率不符时自动用 ffmpeg 重采样），阶段 4 零改动。

声音覆盖（环境变量，所有平台通用）：
  SAY_TEACHER / SAY_STUDENT   声音名（macOS 用 `say -v '?' | grep zh_`，Windows 用
                              powershell "Add-Type …; (New-Object …SpeechSynthesizer).GetInstalledVoices()" 查看）

CLI 与 dialog2audio.py 兼容：--takes/--temperature/--no-cleanup/--device 会被
接受但忽略，方便 SKILL.md 里同一条命令在两个路由间切换。

用法：
  python3 dialog2audio_local.py --script script_v2_dialog.txt --outdir /tmp/dlg [--only 1,9]
"""
import argparse, base64, json, os, re, shutil, subprocess, sys, tempfile, wave
from array import array

SR = 32000
FF = os.environ.get("FFMPEG", "ffmpeg")  # 各平台均要求 ffmpeg 已装（后续阶段本来就必需）
PLATFORM = sys.platform  # darwin / win32 / linux

# ---- 解析（与 dialog2audio.py 保持一致）----
PAUSE_RE = re.compile(r"\[\[\s*(\d+(?:\.\d+)?)\s*\]\]")
MIN_UNIT = 12
HARD_MAX = 28
ACTION_WORDS = ("哭脸", "笑脸")

# 剧本里老师角色标签固定为通用「老师：」（与显示名解耦）；同时兼容旧剧本「小贤老师：」
# 与自定义 TEACHER_NAME（方案 A 遗留写法）。显示名只影响 HTML，不影响声线判定。
_TEACHER_PREFIXES = ["老师", "小贤老师"]
_custom_tn = os.environ.get("TEACHER_NAME")
if _custom_tn and _custom_tn not in _TEACHER_PREFIXES:
    _TEACHER_PREFIXES.append(_custom_tn)


def clean(s):
    s = re.sub(r"[（(][^）)]*[)）]", "", s)
    for q in ['"', '"', "'", "‘", "’", "“", "”"]:
        s = s.replace(q, "")
    for en, zh in [("Skill Struck", "斯吉尔斯特拉克"), ("A.I.", "诶爱"), ("AI", "诶爱")]:
        s = s.replace(en, zh)
    s = s.replace("——", "，")
    return re.sub(r"\s+", "", s).strip()


def parse_line(line):
    """返回 (speaker, text, pause, pre) 或 None（非对白行）。
    老师名读环境变量 TEACHER_NAME（默认「小贤老师」），兼容全角/半角冒号；学生固定「学生」。"""
    for name, sp in [(n, "teacher") for n in _TEACHER_PREFIXES] + [("学生", "student")]:
        m = re.match(rf'^\s*{re.escape(name)}\s*[:：]\s*(.*)$', line)
        if not m:
            continue
        content = m.group(1).strip().strip('"').strip()
        pre, pause, text_parts, pos = 0.0, 0.0, [], 0
        for mm in PAUSE_RE.finditer(content):
            mid = content[pos:mm.start()]
            text_parts.append(mid)
            if mid.strip():
                pause = float(mm.group(1))
            else:
                pre += float(mm.group(1))
            pos = mm.end()
        text_parts.append(content[pos:])
        text = "".join(text_parts).strip()
        return sp, text, pause, pre
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
    return [u for u in out if len(re.sub(r"[^\u4e00-\u9fff]", "", u)) >= 1]


# ---- wav 读写（Int16 单声道 32k）----
def read_wav(path):
    with wave.open(path, "rb") as w:
        if w.getframerate() != SR or w.getnchannels() != 1 or w.getsampwidth() != 2:
            raise ValueError(f"异常格式: {path} ({w.getframerate()}Hz ch{w.getnchannels()})")
        return array("h", w.readframes(w.getnframes()))


def write_wav(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(samples.tobytes())


def dur_of(path):
    try:
        with wave.open(path, "rb") as w:
            return w.getnframes() / w.getframerate()
    except Exception:
        r = subprocess.run([FF, "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", path], capture_output=True, text=True)
        for tok in (r.stdout + r.stderr).split():
            try:
                return float(tok)
            except ValueError:
                continue
        return 0.0


def resample_to_32k(src, dst):
    """后端输出非 32k 时用 ffmpeg 重采样（ffmpeg 是流水线硬依赖，必在）。"""
    r = subprocess.run([FF, "-y", "-loglevel", "error", "-i", src,
                        "-ar", str(SR), "-ac", "1", "-sample_fmt", "s16", dst])
    return r.returncode == 0


# ============ 各平台合成后端 ============

def _synth_say(unit, voice, out):
    """macOS say。prosody 嵌入命令由调用方拼进 unit。"""
    r = subprocess.run(["say", "-v", voice, "-o", out, "--data-format=LEI16@32000", unit],
                       capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(out)


def _ps_encoded(script):
    """PowerShell -EncodedCommand：UTF-16LE base64，彻底绕开中文/引号转义问题。"""
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")


def _sapi_voices():
    """枚举 Windows 已装中文声音。返回 [声音名,...]（zh 优先级排序），失败返回 []。"""
    ps = r'''
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name + "|" + $_.VoiceInfo.Culture.Name }
'''
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", _ps_encoded(ps)],
                           capture_output=True, text=True, timeout=60)
        zh = [ln.split("|")[0].strip() for ln in r.stdout.splitlines()
              if "|" in ln and ln.split("|")[1].strip().lower().startswith("zh")]
        # 中文普通话优先
        zh.sort(key=lambda n: (0 if "Huihui" in n else 1 if "Yaoyao" in n else 2 if "Kangkang" in n else 3))
        return zh
    except Exception:
        return []


def _synth_sapi(unit, voice, out, pitch_pct=0, rate_pct=0):
    """Windows SAPI（System.Speech）。pitch/rate 为百分比（正=升高/加快）。
    中文文本经 SSML + EncodedCommand 传递，无控制台编码问题。"""
    esc = unit.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    prosody = f'<prosody pitch="{pitch_pct:+d}%" rate="{rate_pct:+d}%">{esc}</prosody>' \
        if (pitch_pct or rate_pct) else esc
    ssml = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">'
            f'{prosody}</speak>')
    vq = voice.replace("'", "''")
    oq = out.replace("\\", "/").replace("'", "''")
    ps = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(32000,[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,[System.Speech.AudioFormat.AudioChannel]::Mono)
$s.SetOutputToWaveFile('{oq}', $fmt)
$s.SelectVoice('{vq}')
$ssml = @'
{ssml}
'@
try {{ $s.SpeakSsml($ssml) }} catch {{ }}
$s.Dispose()
"""
    # SSML 失败时退回纯文本（去掉 XML 标签重试）
    plain = f"""
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$fmt = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(32000,[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,[System.Speech.AudioFormat.AudioChannel]::Mono)
$s.SetOutputToWaveFile('{oq}', $fmt)
$s.SelectVoice('{vq}')
$s.Rate = {1 if rate_pct > 0 else (-1 if rate_pct < 0 else 0)}
$s.Speak(@'
{esc}
'@)
$s.Dispose()
"""
    r = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", _ps_encoded(ps)],
                       capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not os.path.exists(out) or os.path.getsize(out) < 100:
        r = subprocess.run(["powershell", "-NoProfile", "-EncodedCommand", _ps_encoded(plain)],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not os.path.exists(out):
            return False
    # SAPI 个别机器忽略自定义格式 → 非 32k 时重采样
    try:
        with wave.open(out, "rb") as w:
            if w.getframerate() != SR:
                tmp = out + "_rs.wav"
                if resample_to_32k(out, tmp):
                    os.replace(tmp, out)
    except Exception:
        pass
    return True


def _synth_espeak(unit, voice, out, student=False):
    """Linux espeak-ng。quality 最差但可用。"""
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        return False
    r = subprocess.run([exe, "-v", voice, "-p", "80" if student else "50",
                        "-s", "150", "-a", "180", "-w", out, unit],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        return False
    try:
        with wave.open(out, "rb") as w:
            if w.getframerate() != SR:
                tmp = out + "_rs.wav"
                if resample_to_32k(out, tmp):
                    os.replace(tmp, out)
    except Exception:
        pass
    return True


# ---- 后端探测与声音选择 ----
class Backend:
    def __init__(self):
        self.platform = PLATFORM
        self.teacher = os.environ.get("SAY_TEACHER")
        self.student = os.environ.get("SAY_STUDENT")
        self.notes = []
        if PLATFORM == "darwin":
            self.name = "say (macOS)"
            self.teacher = self.teacher or "Tingting"
            self.student = self.student or "Meijia"
            self.ok = shutil.which("say") is not None
        elif PLATFORM == "win32":
            self.name = "PowerShell SAPI (Windows)"
            zh = _sapi_voices()
            if not zh:
                self.ok = False
                self.notes.append("未枚举到中文语音包：设置 → 时间和语言 → 语言和区域 → 添加语言「中文(简体)」并勾选语音")
            else:
                self.ok = True
                self.teacher = self.teacher or zh[0]
                # 学生取第二个中文声音；只有一个时用 SSML 抬调区分
                self.student = self.student or (zh[1] if len(zh) > 1 else zh[0])
                self.student_same_voice = (self.student == self.teacher)
                self.notes.append(f"中文声音: {zh}")
        else:
            self.name = "espeak-ng (Linux)"
            self.teacher = self.teacher or "cmn"
            self.student = self.student or "cmn"
            self.ok = shutil.which("espeak-ng") or shutil.which("espeak")
            if not self.ok:
                self.notes.append("未找到 espeak-ng：apt install espeak-ng（音质有限，建议改用 GPT-SoVITS 路由 A）")

    def synth(self, speaker, unit, out):
        """合成单句到 out；失败返回 False。学生自带差异化韵律。"""
        is_student = (speaker == "student")
        if self.platform == "darwin":
            prosody = "[[pbas +110]][[rate +15]]" if is_student else ""
            return _synth_say(prosody + unit, self.student if is_student else self.teacher, out)
        if self.platform == "win32":
            if is_student and getattr(self, "student_same_voice", False):
                return _synth_sapi(unit, self.student, out, pitch_pct=25, rate_pct=8)
            return _synth_sapi(unit, self.student if is_student else self.teacher, out,
                               rate_pct=8 if is_student else 0)
        return _synth_espeak(unit, self.teacher, out, student=is_student)


def synth_line(backend, speaker, text, pause, out_prefix, pre=0.0):
    """合成一行，返回 wav 路径（已含句前/句后静音）。动作行只出静音。"""
    out = out_prefix + ".wav"
    if speaker == "student" and any(w in text for w in ACTION_WORDS):
        dur = pause if pause > 0 else 3.0
        write_wav(out, array("h", bytes(int((dur + pre) * SR) * 2)))
        print(f"    [动作] {speaker} 静音 {dur:.1f}s")
        return out
    units = split_units(clean(text))
    if not units:
        print(f"    [空] {speaker}: {text[:20]}"); return None
    chunks = []
    written = 0
    for i, unit in enumerate(units):
        tmp = f"{out_prefix}_u{i}.wav"
        if not backend.synth(speaker, unit, tmp):
            print(f"    [失败] {backend.name}: {unit[:20]}"); continue
        try:
            a = read_wav(tmp)
        except ValueError:
            print(f"    [警告] 非标准格式已重采样: {unit[:15]}")
            a = read_wav(tmp)
        os.remove(tmp)
        if not len(a):
            continue
        if written > 0:
            chunks.append(array("h", bytes(int(0.2 * SR) * 2)))
        chunks.append(a)
        written += 1
    if not chunks:
        return None
    if pre > 0:
        chunks.insert(0, array("h", bytes(int(pre * SR) * 2)))
    speech = _concat(chunks)
    if pause > 0:
        speech.extend(array("h", bytes(int(pause * SR) * 2)))
    write_wav(out, speech)
    return out


def _concat(chunks):
    out = array("h")
    for c in chunks:
        out.extend(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--only", default=None, help="只做某几帧，如 1,9")
    ap.add_argument("--gap", type=float, default=0.4, help="帧内行间间隔秒")
    # 兼容 GPT-SoVITS 路由的参数（接受但忽略）
    ap.add_argument("--takes", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--device", default=None)
    ap.add_argument("--no-cleanup", action="store_true")
    args = ap.parse_args()

    backend = Backend()
    print(f"本地 TTS 兜底路由 · 平台后端: {backend.name}")
    print(f"老师声音: {backend.teacher}   学生声音: {backend.student}")
    for n in backend.notes:
        print(f"提示: {n}")
    if not backend.ok:
        sys.exit("❌ 本地 TTS 后端不可用（见上方提示），或安装 GPT-SoVITS 走路由 A。")

    args.script = os.path.abspath(args.script)
    args.outdir = os.path.abspath(args.outdir)
    os.makedirs(args.outdir, exist_ok=True)
    only = set(int(x) for x in args.only.split(",")) if args.only else None

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
        line_paths, line_start, units_tl = [], 0.0, []
        for ri, (speaker, text, pause, pre) in enumerate(frames[fi]):
            label = "老师" if speaker == "teacher" else "学生"
            print(f"  {label}: {text[:30]}{'…' if len(text) > 30 else ''}  (前{pre} 后{pause})")
            lp = synth_line(backend, speaker, text, pause,
                            os.path.join(args.outdir, f"f{fi}_{label}_{ri}"), pre=pre)
            if lp:
                d = dur_of(lp)
                units_tl.append({"speaker": label, "text": text,
                                 "pause": pause, "pre": pre, "dur": round(d, 3),
                                 "start": round(line_start, 3)})
                line_paths.append(lp)
                line_start += d + args.gap
        if not line_paths:
            print(f"  帧 {fi} 无有效行"); continue
        out = os.path.join(args.outdir, f"frame_{fi:02d}.wav")
        chunks = [read_wav(line_paths[0])]
        for p in line_paths[1:]:
            chunks.append(array("h", bytes(int(args.gap * SR) * 2)))
            chunks.append(read_wav(p))
        write_wav(out, _concat(chunks))
        report.append({"frame": fi, "dur": round(dur_of(out), 2), "units": units_tl})
        print(f"  -> {out}  {dur_of(out):.1f}s")

    json.dump(report, open(os.path.join(args.outdir, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    if len(report) > 1:
        merged = os.path.join(args.outdir, "_merged.wav")
        chunks = []
        for r in report:
            chunks.append(read_wav(os.path.join(args.outdir, f"frame_{r['frame']:02d}.wav")))
            chunks.append(array("h", bytes(int(0.9 * SR) * 2)))
        write_wav(merged, _concat(chunks[:-1]))
        print(f"\n合并 -> {merged}  {dur_of(merged):.1f}s")
    print("完成。（本地 TTS 兜底路由：音质为系统级合成，可按 SKILL.md『换音色重合成』流程随时升级到 GPT-SoVITS 路由 A）")


if __name__ == "__main__":
    main()
