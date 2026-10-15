#!/usr/bin/env bash
# 蜡笔风动态片头一键生成（渲染帧 → 配乐 → 出 mp4）
#
# 用法：
#   bash make_intro.sh --out /path/片头.mp4 --title "第 3 课 · <em>事物的特征</em>"
#
# 常用参数：
#   --out <mp4>        必填，输出文件
#   --portrait         出竖版片头（1080×1440，用 intro_crayon_portrait_template.html；
#                      与横版同一套 4 拍时间轴/令牌；**竖版正片必须用竖版片头**，横版片头尺寸不同不能 concat）
#   --total 6.5        片头时长（秒），基准时间轴按 7.5s（4 拍分屏）设计、等比缩放
#   --work <dir>       工作目录（默认 /tmp/intro_<时间戳>；存 intro.html / frames / music.wav）
#   --title <html>     课名（可含 <em>关键词</em>，em 会自动加黄色高亮胶囊）
#   --brand <text>     品牌名（默认「小贤 AI 青少年教育」）
#   --claim <html>     主张句（可含 <b>强调</b>）
#   --lead <text>      三件套引导词（默认「配套」）
#   --k1/--k2/--k3     三件套文字（默认 教案 / 课件（PPT）/ 学习任务单）
#   --noplug <text>    收尾句（默认「不插电即可开课」）
#   --music <wav>      直接复用现成配乐（跳过生成）
#   --fade 2.0         片头配乐在结尾前 N 秒淡出至静音（默认 2.0；0 = 不淡出）
#   --curve qsin       淡出曲线（默认 qsin 四分之一正弦，比线性更柔；可选 tri/log/exp/par…）
#   --bpm 100          配乐速度        --bells  加卡点铃铛（默认关，用户 2026-10-08 定案不要）
#   --keep-frames      保留帧序列
#
# 环境变量可覆盖：MUSIC_PY（需 numpy+scipy 的 python）/ FFMPEG / CHROME_BIN
set -euo pipefail

SK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# 外部工具：优先环境变量，否则从 PATH 查找，最后回退常见 Mac 路径（换机无需修改）
FFMPEG="${FFMPEG:-$(command -v ffmpeg || echo /opt/homebrew/bin/ffmpeg)}"
FFPROBE="${FFPROBE:-$(command -v ffprobe || echo /opt/homebrew/bin/ffprobe)}"
PY_SUB="${PY_SUB:-$(command -v python3 || echo /opt/homebrew/bin/python3)}"
# 配乐需要 numpy + scipy：优先 $MUSIC_PY，其次 $VOICE_CLONE 的 venv，最后回退系统 python（可能缺库，会报错提示）
VOICE_CLONE="${VOICE_CLONE:-}"
if [ -n "${MUSIC_PY:-}" ]; then :;
elif [ -n "$VOICE_CLONE" ] && [ -x "$VOICE_CLONE/venv/bin/python" ]; then MUSIC_PY="$VOICE_CLONE/venv/bin/python";
else MUSIC_PY="${PY_SUB}"; fi

OUT=""; TOTAL="7.5"; WORK=""; TITLE="第 3 课 · <em>事物的特征</em>"
BRAND="小贤 AI 青少年教育"
CLAIM='为学校、教培机构和家庭提供<b>体系化 AI 课程与实训项目</b>'
LEAD="配套"; K1="教案"; K2="课件（PPT）"; K3="学习任务单"; NOPLUG="不插电即可开课"
MUSIC=""; BPM="100"; BELLS="0"; KEEP="0"; FADE="2.0"; CURVE="qsin"; ORIENT="land"

while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2;;
    --total) TOTAL="$2"; shift 2;;
    --work) WORK="$2"; shift 2;;
    --title) TITLE="$2"; shift 2;;
    --brand) BRAND="$2"; shift 2;;
    --claim) CLAIM="$2"; shift 2;;
    --lead) LEAD="$2"; shift 2;;
    --k1) K1="$2"; shift 2;;
    --k2) K2="$2"; shift 2;;
    --k3) K3="$2"; shift 2;;
    --noplug) NOPLUG="$2"; shift 2;;
    --portrait) ORIENT="port"; shift;;
    --music) MUSIC="$2"; shift 2;;
    --fade) FADE="$2"; shift 2;;
    --curve) CURVE="$2"; shift 2;;
    --bpm) BPM="$2"; shift 2;;
    --bells) BELLS="1"; shift;;
    --keep-frames) KEEP="1"; shift;;
    -h|--help) sed -n '2,26p' "$0"; exit 0;;
    *) echo "未知参数: $1（--help 看用法）" >&2; exit 2;;
  esac
done
[ -n "$OUT" ] || { echo "必须给 --out <输出.mp4>（--help 看用法）" >&2; exit 2; }
[ -n "$WORK" ] || WORK="/tmp/intro_$(date +%Y%m%d-%H%M%S)"
mkdir -p "$WORK" "$(dirname "$OUT")"
TPL="intro_crayon_template.html"; [ "$ORIENT" = "port" ] && TPL="intro_crayon_portrait_template.html"

echo "== 片头生成 =="
echo "   skill   : $SK"
echo "   工作目录: $WORK"
echo "   时长    : ${TOTAL}s"
echo "   取向    : $([ "$ORIENT" = "port" ] && echo 竖版 1080x1440 || echo 横版 1920x1080)   模板: $TPL"

# 1) 准备 HTML（模板 + logo + 令牌替换）
cp "$SK/assets/style-packs/crayon/intro/$TPL" "$WORK/intro.html"
cp "$SK/assets/style-packs/crayon/intro/logo.svg" "$WORK/logo.svg"
"$PY_SUB" - "$WORK/intro.html" <<PYEOF
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
rep = {
    "{{TOTAL}}": "${TOTAL}", "{{BRAND}}": """${BRAND}""",
    "{{CLAIM}}": """${CLAIM}""", "{{LEAD}}": """${LEAD}""",
    "{{K1}}": """${K1}""", "{{K2}}": """${K2}""", "{{K3}}": """${K3}""",
    "{{NOPLUG}}": """${NOPLUG}""", "{{TITLE}}": """${TITLE}""",
    "{{LOGO}}": "logo.svg",
}
for k, v in rep.items():
    s = s.replace(k, v)
left = [x.split("}}")[0] for x in s.split("{{")[1:]]
assert not left, "还有未替换令牌: %s" % left
open(p, "w", encoding="utf-8").write(s)
print("   令牌替换完成")
PYEOF

# 2) 逐帧渲染（确定性 30fps）
rm -rf "$WORK/frames"; mkdir -p "$WORK/frames"
CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}" \
  node "$SK/scripts/capture_anim.js" "$WORK/intro.html" "$WORK/frames" "$TOTAL"

# 3) 配乐
if [ -n "$MUSIC" ]; then
  cp "$MUSIC" "$WORK/music.wav"; echo "   配乐: 复用 $MUSIC"
else
  BELLARG=""; [ "$BELLS" = "1" ] && BELLARG="--bells"
  "$MUSIC_PY" "$SK/scripts/make_intro_music.py" --out "$WORK/music.wav" \
    --duration "$TOTAL" --bpm "$BPM" $BELLARG
fi

# 4) 编码（参数与正片对齐：30fps + video_track_timescale 15360，便于后续 concat -c copy）
#    配乐在结尾前 FADE 秒淡出至静音（默认 1.0s + qsin 曲线），与画面擦除（末 0.3s）同步收声
AF=""; FADEST=""
if [ "$FADE" != "0" ]; then
  FADEST="$(awk -v t="$TOTAL" -v f="$FADE" 'BEGIN{st=t-f; if (st<0) st=0; printf "%.3f", st}')"
  AF="-af afade=t=out:st=${FADEST}:d=${FADE}:curve=${CURVE}"
  echo "   配乐淡出: ${FADEST}s → ${TOTAL}s（${CURVE}）"
fi
"$FFMPEG" -y -v error -framerate 30 -i "$WORK/frames/f%05d.jpg" -i "$WORK/music.wav" \
  ${AF:+$AF} \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -preset medium -r 30 -video_track_timescale 15360 \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -shortest "$OUT"

DUR="$("$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$OUT")"
NA="$("$FFPROBE" -v error -select_streams a -show_entries stream=index -of csv=p=0 "$OUT" | wc -l | tr -d ' ')"
echo "== 完成 =="
echo "   输出    : $OUT"
echo "   时长    : ${DUR}s（目标 ${TOTAL}s）"
echo "   音轨数  : ${NA}（应为 1；出现 2 说明配乐与复用音乐叠加了）"
[ "$KEEP" = "1" ] || rm -rf "$WORK/frames"
