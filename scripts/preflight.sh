#!/usr/bin/env bash
# 运行流水线前的环境自检。缺项会明确告诉你怎么补。
#
# 用法：
#   bash preflight.sh [课程目录]      # 课程目录可选，给了就顺便校验 $H/视频课/index_present.html
#
# 配置（统一来源，见 SKILL.md「路径与配置」）：
#   - 机器相关路径/音色优先读 config.local.json（由 config.example.json 复制而来，gitignore）
#   - 环境变量 VOICE_CLONE/CHROME_BIN/FFMPEG/SYS_PY 可临时覆盖，优先级最高
#   不再写死任何绝对路径；换机只改 config.local.json 或 export 环境变量
#
# 阶段 3 配音有两条路由，自动二选一：
#   路由 A  GPT-SoVITS 双音色克隆（xiaoxian_v2 + macie，音质最佳）
#   路由 B  macOS 本地 TTS（scripts/dialog2audio_local.py，纯标准库，零依赖兜底；
#           音质为系统级合成，后续可按 SKILL.md「换音色重合成」流程无缝升级到路由 A）

# 本 skill 目录：始终相对本脚本推导，clone 到任何位置都可用
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
CFG_PY="$SKILL_DIR/scripts/load_config.py"

# 配置优先级：环境变量 > config.local.json（缺失回退 config.example.json）
_vc() { python3 "$CFG_PY" --get paths.voice_clone_dir 2>/dev/null; }
VOICE_CLONE="${VOICE_CLONE:-$(_vc)}"
if [ -z "$VOICE_CLONE" ]; then
  echo "⚠️ 未配置 voice_clone 目录：复制 config.example.json 为 config.local.json 并填 paths.voice_clone_dir，或 export VOICE_CLONE"
fi
_chrome() { python3 "$CFG_PY" --get paths.chrome_bin 2>/dev/null; }
CHROME_BIN="${CHROME_BIN:-$(_chrome)}"
CHROME_BIN="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
# 说明：config 里的值可能是裸命令名（如 "ffmpeg"）也可能是绝对路径。
# 裸命令名必须用 command -v 解析，不能用 [ -x ]（-x 不查 PATH，裸名必然为假 → 假阴性）。
_ff() { python3 "$CFG_PY" --get paths.ffmpeg 2>/dev/null; }
FFMPEG="${FFMPEG:-$(_ff)}"
FFMPEG="${FFMPEG:-$(command -v ffmpeg || echo ffmpeg)}"
_sp() { python3 "$CFG_PY" --get paths.sys_py 2>/dev/null; }
SYS_PY="${SYS_PY:-$(_sp)}"
SYS_PY="${SYS_PY:-$(command -v python3 || echo python3)}"
H="${1:-}"
TPL="${TPL:-$SKILL_DIR/assets/templates/crayon/封面模板_横版课件_1920x1080.html}"

# 打印本次实际解析到的路径（路径不该靠文档记忆，靠脚本说出来）
echo "解析到的路径："
printf "  SKILL_DIR    %s\n" "$SKILL_DIR"
printf "  VOICE_CLONE  %s\n" "${VOICE_CLONE:-（未配置）}"
printf "  FFMPEG       %s\n" "$FFMPEG"
printf "  SYS_PY       %s\n" "$SYS_PY"
printf "  CHROME_BIN   %s\n" "$CHROME_BIN"
printf "  模板          %s\n" "$TPL"
printf "  H            %s\n" "${H:-（未传课程目录）}"
echo

ok=0; bad=0
chk() { # chk "说明" "命令" [提示]
  if eval "$2" >/dev/null 2>&1; then printf "  ✅ %s\n" "$1"; ok=$((ok+1));
  else printf "  ❌ %s\n     ↳ 修复：%s\n" "$1" "${3:-（见 SKILL.md 环境依赖）}"; bad=$((bad+1)); fi
}
# 路由 A 逐项检查（缺项不计入全局 bad，只要路由 B 可用即可）
gchk() {
  if eval "$2" >/dev/null 2>&1; then printf "  ✅ %s\n" "$1";
  else printf "  ·  %s\n" "$1（路由 B 可跳过）"; fi
}

echo "== 1. 配音路由（阶段3：A=GPT-SoVITS 克隆 / B=macOS 本地 TTS，自动二选一）=="
# 音色名/参考音统一从 config.voices 读取（单一真相源，不写死）
T_EXP="$(python3 "$CFG_PY" --get voices.teacher.exp 2>/dev/null)"
S_EXP="$(python3 "$CFG_PY" --get voices.student.exp 2>/dev/null)"
T_REF="$(python3 "$CFG_PY" --get voices.teacher.ref 2>/dev/null)"
S_REF="$(python3 "$CFG_PY" --get voices.student.ref 2>/dev/null)"
gchk "voice_clone 目录：$VOICE_CLONE" "[ -d '$VOICE_CLONE' ]"
gchk "venv python（Python 3.11 + torch）" "'$VOICE_CLONE/venv/bin/python' -c 'import torch, numpy, soundfile'"
gchk "GPT-SoVITS 仓库" "[ -d '$VOICE_CLONE/GPT-SoVITS/GPT_SoVITS' ]"
gchk "预训练底模（chinese-roberta / chinese-hubert / gsv-v2final）" \
    "[ -d '$VOICE_CLONE/GPT-SoVITS/GPT_SoVITS/pretrained_models/gsv-v2final-pretrained' ] && [ -d '$VOICE_CLONE/GPT-SoVITS/GPT_SoVITS/pretrained_models/chinese-hubert-base' ] && [ -d '$VOICE_CLONE/GPT-SoVITS/GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large' ]"
gchk "老师权重 $T_EXP（GPT_weights + SoVITS_weights）" "ls '$VOICE_CLONE'/GPT_weights/${T_EXP}-e*.ckpt '$VOICE_CLONE'/SoVITS_weights/${T_EXP}_e*_s*.pth"
gchk "学生权重 $S_EXP（GPT_weights + SoVITS_weights）" "ls '$VOICE_CLONE'/GPT_weights/${S_EXP}-e*.ckpt '$VOICE_CLONE'/SoVITS_weights/${S_EXP}_e*_s*.pth"
gchk "参考音 $T_REF" "[ -f '$VOICE_CLONE/$T_REF' ]"
gchk "参考音 $S_REF" "[ -f '$VOICE_CLONE/$S_REF' ]"
gchk "双音色脚本 dialog2audio.py（路由 A 权威脚本，位于 voice_clone 项目）" "[ -f '$VOICE_CLONE/dialog2audio.py' ]" "voice_clone 项目自带；skill 不再维护副本"

if [ -x "$VOICE_CLONE/venv/bin/python" ] && [ -f "$VOICE_CLONE/dialog2audio.py" ] && [ -d "$VOICE_CLONE/GPT-SoVITS/GPT_SoVITS" ]; then
  echo "  → 配音路由：A（GPT-SoVITS 双音色克隆）"
else
  echo "  → GPT-SoVITS 不完整，转路由 B（本地 TTS 兜底，跨平台）："
  OS="$(uname -s 2>/dev/null || echo Windows_NT)"
  if [ "$OS" = "Darwin" ]; then
    chk "say 命令" "command -v say" "路由 B 的 macOS 后端"
    chk "中文声音（zh_CN，say -v '?' 查看）" "say -v '?' | grep -q zh_CN" "系统设置 → 辅助功能 → 朗读内容 → 系统声音 → 管理声音，添加中文声音"
    echo "  → 配音路由：B（macOS say 本地 TTS；音质降级，可后续换音色重合成）"
  elif [ "$OS" = "Linux" ]; then
    chk "espeak-ng" "command -v espeak-ng || command -v espeak" "apt install espeak-ng（音质最差，建议改用路由 A）"
    echo "  → 配音路由：B（Linux espeak-ng；音质降级明显，强烈建议装 GPT-SoVITS 走路由 A）"
  else
    chk "PowerShell（SAPI 中文语音包）" "command -v powershell || command -v pwsh" "Windows 自带；中文语音包缺失时：设置 → 时间和语言 → 语言和区域 → 添加中文(简体)并勾选语音"
    echo "  → 配音路由：B（Windows SAPI，dialog2audio_local.py 自动枚举中文声音）"
  fi
  chk "python3（兜底脚本仅需标准库）" "command -v python3"
fi

echo "== 2. 画面/截图/合成（阶段2、4、5 必需）=="
chk "Google Chrome：$CHROME_BIN" "[ -x '$CHROME_BIN' ]" "装 Chrome，或设 CHROME_BIN=<路径>"
chk "ffmpeg：$FFMPEG" "command -v '$FFMPEG' >/dev/null 2>&1 || [ -x '$FFMPEG' ]" "brew install ffmpeg，或设 FFMPEG=<路径>"
chk "puppeteer-core（npx 缓存或 node_modules）" "ls ~/.npm/_npx/*/node_modules/puppeteer-core >/dev/null 2>&1 || node -e \"require.resolve('puppeteer-core')\"" \
    "cd ~/.workbuddy/binaries/node/workspace && npm i puppeteer-core"
chk "系统 python 带 PIL：$SYS_PY" "command -v '$SYS_PY' >/dev/null 2>&1 && '$SYS_PY' -c 'import PIL'" "$SYS_PY 装 Pillow：'<py> -m pip install Pillow'，或设 SYS_PY=<带PIL的python>"
chk "蜡笔风封面模板" "[ -f '$TPL' ]" "确认共享模板路径"
chk "node（建议 22.x；只校验可用）" "node -v" "装 Node.js 22"

if [ -n "$H" ]; then
  echo "== 3. 本节课程目录 =="
  chk "课目录：$H" "[ -d '$H' ]"
  chk "演讲稿 script_v2_dialog.txt" "[ -f '$H/视频课/script_v2_dialog.txt' ]"
  chk "放映版 index_present.html" "[ -f '$H/视频课/index_present.html' ]"
fi

echo
echo "自检结果：通过 $ok 项，缺失 $bad 项。"
[ "$bad" -eq 0 ] || echo "⚠️ 有缺失项，先补齐再跑流水线（不要在缺件情况下硬跑）。"
exit $([ "$bad" -eq 0 ] && echo 0 || echo 1)
