#!/usr/bin/env bash
# make_video.sh — 阶段 4c 静帧版合成（唯一可靠路径，封装成脚本消灭手打错误）
#
# 为什么不能直接 -framerate 30 读 shots/：各截图区间时长不同（schedule.json 的
# intervals），直接读会把每张 shot 当 1/30s → 音画失步。concat demuxer（VFR）
# 与 concat 上加 -r/-fps 滤镜也都实测漂移。唯一可靠：先按 durations.txt 把每张
# shot 硬链接 round(dur*30) 次，得到严格 30fps 的帧序列，再两步法编码+混流。
#
# 用法：
#   bash make_video.sh <工作目录> <输出.mp4> [merged音频]
# 输入：
#   <工作目录>/shots/shot_0000.png …（make_standalone+capture 产物）
#   <工作目录>/durations.txt（每区间秒数，与 shot 一一对应）
#   [merged音频] 默认 <工作目录>/audio/_merged.wav
# 产出：
#   <工作目录>/seq/（硬链接帧序列，复用可删）
#   <工作目录>/video_cfr.mp4（无声 CFR 中间产物，换音色重混流可复用）
#   <输出.mp4>（最终成片）
#
# 动效版（capture_anim.js 产出 f%05d.jpg，本身就是均匀 30fps）不需要本脚本，
# 直接：ffmpeg -framerate 30 -i frames/f%05d.jpg …（见 references/stages/4-compose.md 4c）。
#
# 环境变量：FFMPEG 覆盖 ffmpeg 路径（默认 env > PATH > /opt/homebrew）
set -euo pipefail

W="${1:?用法: bash make_video.sh <工作目录> <输出.mp4> [merged音频]}"
OUT="${2:?缺输出路径}"
MERGED="${3:-$W/audio/_merged.wav}"

FFMPEG="${FFMPEG:-$(command -v ffmpeg || echo /opt/homebrew/bin/ffmpeg)}"
SHOTS="$W/shots"; DUR="$W/durations.txt"; SEQ="$W/seq"

[ -d "$SHOTS" ] || { echo "❌ 缺 $SHOTS（先跑 make_standalone.py + capture.js）"; exit 2; }
[ -f "$DUR" ]  || { echo "❌ 缺 $DUR"; exit 2; }
[ -f "$MERGED" ] || { echo "❌ 缺 $MERGED（先跑阶段 3）"; exit 2; }

NSHOT="$(ls "$SHOTS"/shot_*.png 2>/dev/null | wc -l | tr -d ' ')"
NDUR="$(wc -l < "$DUR" | tr -d ' ')"
[ "$NSHOT" -eq "$NDUR" ] || { echo "❌ shots($NSHOT) 与 durations($NDUR) 数量不一致"; exit 2; }

# 1) 硬链接帧序列：第 i 张 shot 链接 round(dur*30) 次
rm -rf "$SEQ"; mkdir -p "$SEQ"
TOTAL=0; i=0
while read -r d; do
  [ -n "$d" ] || continue
  K="$(awk -v x="$d" 'BEGIN{printf "%d", (x*30)+0.5}')"
  [ "$K" -gt 0 ] || { echo "❌ 第 $((i+1)) 区间时长 $d s → 0 帧"; exit 2; }
  SRC="$(printf '%s/shot_%04d.png' "$SHOTS" "$i")"
  [ -f "$SRC" ] || { echo "❌ 缺 $SRC"; exit 2; }
  for ((j=0; j<K; j++)); do
    ln "$SRC" "$(printf '%s/f%05d.png' "$SEQ" "$TOTAL")"
    TOTAL=$((TOTAL+1))
  done
  i=$((i+1))
done < "$DUR"
echo "帧序列: $TOTAL 帧（$i 区间）→ 预计 ${TOTAL}s/30 = $(awk -v t=$TOTAL 'BEGIN{printf "%.1f", t/30}')s"

# 2) 编码（严格 CFR 30fps）
"$FFMPEG" -y -v error -framerate 30 -i "$SEQ/f%05d.png" \
  -c:v libx264 -pix_fmt yuv420p -crf 20 -r 30 "$W/video_cfr.mp4"
echo "编码完成: $W/video_cfr.mp4"

# 3) 混流（第二步 -c:a，concat PNG 不能与 -c:a 同步走——会被静默忽略）
"$FFMPEG" -y -v error -i "$W/video_cfr.mp4" -i "$MERGED" \
  -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest "$OUT"
echo "成片: $OUT"

# 4) 自检打印（对照 schedule 抽时刻 QC 由 agent 执行，见 references/stages/4-compose.md 4c）
VD="$(command -v ffprobe >/dev/null 2>&1 && ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT" || echo '?')"
AD="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MERGED")"
echo "自检: 成片 ${VD}s / 音源 ${AD}s（相差应 <1s）"
