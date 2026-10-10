#!/usr/bin/env python3
"""把「独立片头卡 + 正片 + 片尾卡」三段拼成最终成片。
用法:
  python make_intro_outro.py --video <正片.mp4> --out <输出.mp4> [--speed 1.5]
固定资产（assets/intro_outro/）: introcard.png / endcard.png / anchor_line.wav
告别词: voice_clone/dataset/xiaoxian_v2/wavs/xiaoxian_v2_036.wav
结构:
  片头 6.5s: 蜡笔风片头卡 + 锚句配音（0.25s 起，同样倍速），首尾淡入淡出
  正片: 原样保留，不做任何叠加/闪避
  片尾 5.2s: 收尾卡 + 告别词
  输出: loudnorm -16 LUFS + faststart
注意: 三段统一 30fps + video_track_timescale 15360，否则 concat -c copy 会静默截断。
"""
import argparse, os, sys, shutil, subprocess, tempfile

# ffmpeg：优先环境变量，其次 PATH 查找，最后回退常见 Mac 路径（换机无需修改）
FFMPEG = os.environ.get("FFMPEG", shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg")
# skill 内部资源：始终相对本脚本推导（scripts/ 的上一级），clone 到任何位置都可用
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(SKILL_DIR, "assets", "intro_outro")
# 告别词音频属于外部 voice_clone 项目：优先 FAREWELL_WAV，其次用 VOICE_CLONE 拼接
VOICE_CLONE = os.environ.get("VOICE_CLONE", "")
FAREWELL = os.environ.get("FAREWELL_WAV", "")
if not FAREWELL and VOICE_CLONE:
    FAREWELL = os.path.join(VOICE_CLONE, "dataset/xiaoxian_v2/wavs/xiaoxian_v2_036.wav")
if not FAREWELL:
    sys.exit("✗ 找不到告别词音频。请设置环境变量 FAREWELL_WAV（指向 voice_clone/dataset/xiaoxian_v2/wavs/xiaoxian_v2_036.wav），或先设置 VOICE_CLONE。")

ap = argparse.ArgumentParser()
ap.add_argument("--video", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--speed", type=float, default=1.5, help="与课程音频一致的倍速")
a = ap.parse_args()

spd = a.speed
anchor = os.path.join(SKILL, "anchor_line.wav")
endcard = os.path.join(SKILL, "endcard.png")
introcard = os.path.join(SKILL, "introcard.png")
tmp = tempfile.mkdtemp(prefix="intro_outro_")

# ---- 1) 片头卡段（6.5s：锚句配音 0.25s 起）----
intro = os.path.join(tmp, "intro.mp4")
anchor_fast = os.path.join(tmp, "anchor_fast.wav")
subprocess.run([FFMPEG, "-y", "-i", anchor, "-af", f"atempo={spd}", "-ar", "32000", anchor_fast],
               check=True, capture_output=True)
subprocess.run([FFMPEG, "-y", "-loop", "1", "-i", introcard, "-i", anchor_fast,
                "-filter_complex",
                "[0:v]scale=1920:1080,format=yuv420p,fade=t=in:st=0:d=0.3,fade=t=out:st=6.2:d=0.3[v];"
                "[1:a]adelay=250|250,apad=whole_dur=6.5,afade=t=out:st=5.9:d=0.6[a]",
                "-map", "[v]", "-map", "[a]", "-t", "6.5", "-r", "30",
                "-video_track_timescale", "15360",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", intro], check=True, capture_output=True)
print("片头卡段完成")

# ---- 2) 正片段（重编码统一参数，不加任何叠加）----
body = os.path.join(tmp, "body.mp4")
subprocess.run([FFMPEG, "-y", "-i", a.video,
                "-vf", "scale=1920:1080,format=yuv420p",
                "-r", "30", "-video_track_timescale", "15360",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", body], check=True, capture_output=True)
print("正片段统一参数完成")

# ---- 3) 片尾卡段（5.2s：告别词 0.4s 起）----
end = os.path.join(tmp, "end.mp4")
farewell_fast = os.path.join(tmp, "farewell_fast.wav")
subprocess.run([FFMPEG, "-y", "-i", FAREWELL, "-af", f"atempo={spd}", "-ar", "32000", farewell_fast],
               check=True, capture_output=True)
subprocess.run([FFMPEG, "-y", "-loop", "1", "-i", endcard, "-i", farewell_fast,
                "-filter_complex",
                "[0:v]scale=1920:1080,format=yuv420p,fade=t=out:st=4.7:d=0.5[v];"
                "[1:a]adelay=400|400,apad=whole_dur=5.2,afade=t=out:st=4.4:d=0.8[a]",
                "-map", "[v]", "-map", "[a]", "-t", "5.2", "-r", "30",
                "-video_track_timescale", "15360",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", end], check=True, capture_output=True)
print("片尾卡段完成")

# ---- 4) 无损拼接 + 音频响度归一 + faststart ----
concat_list = os.path.join(tmp, "list.txt")
with open(concat_list, "w") as f:
    f.write(f"file '{intro}'\nfile '{body}'\nfile '{end}'\n")
joined = os.path.join(tmp, "joined.mp4")
subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                "-c", "copy", joined], check=True, capture_output=True)
subprocess.run([FFMPEG, "-y", "-i", joined,
                "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", a.out], check=True, capture_output=True)
print(f"完成 -> {a.out}")
