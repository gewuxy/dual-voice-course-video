\---  
name: dual-voice-course-video  
version: 1.0.0  
display_name: 主题一键成课：互动课件+讲解视频  
display_name_en: Topic-to-Course — Interactive Slides and Narrated Video  
description_zh: 给一个主题（或一页旧课件/PPT），自动产出全套课程内容：演讲稿剧本 → 互动放映版 HTML 课件（逐步演示、可课堂使用）→ 老师/学生双音色配音讲解视频（逐帧音画对齐 mp4 + 字幕）→ 配套横竖版封面。适合教师、知识博主、企业培训师、课程产品团队、家长等任何需要把知识点变成视频课的人。配音路由自动判定：有 GPT-SoVITS 用克隆音色（音质最佳），没有则落本地系统 TTS（macOS/Windows/Linux 全平台兜底），后续可无缝换音色重合成。  
description_en: Give it a topic (or an old PPT) and get a full lesson package automatically — narration script -> interactive step-by-step HTML slides -> dual-voice (teacher + student) narrated video with frame-accurate alignment and subtitles -> matching cover images. Built for teachers, content creators, corporate trainers, course teams, and parents. Voice route is auto-detected — GPT-SoVITS cloned voices when available, otherwise local system TTS (macOS/Windows/Linux) — with a seamless re-synthesis path for later voice upgrades.  
description: 主题一键成课：用户给一个课程主题（或已有课件/PPT），自动产出演讲稿、互动放映版 HTML 课件、老师/学生双音色配音讲解视频（逐帧对齐）与配套封面。制作顺序为「先写演讲稿并确认 → 再做 HTML 放映版并确认 → 按稿生成双音色音频 → 把音频和 HTML 整合成最终视频 → 最后生成配套封面」。适合教师备课、知识博主出片、企业培训、课程打样、家庭定制讲解。当用户要求"为一节课/一个主题生成带配音的视频""把放映版 HTML 和时间轴对齐成视频""做双音色课程视频""演讲稿转视频""顺带出个封面"时使用。  
agent_created: true  
\---

# 双音色课程视频制作流水线

把一节 AI 课的 **演讲稿 → HTML 放映版 → 双音色音频 → 音画整合出片 → 配套封面** 五步固化，产出「老师讲、学生也在问」、画面动作精确到每一句的 mp4 与可发布的视频号封面。

## 快速开始（任何 agent / 新会话照这个跑）

```bash
SK=<本 skill 目录，你 clone 到的路径>     # 本 skill
H="<课目录>"                                                      # 例：…/AI-L1. Human Senses vs Computer Sensors
W=/tmp/$(basename "$H" | tr ' ' '_')                              # 工作目录（音频/截图/成片）

# 0) 环境自检（缺件会明确报错，不要在缺件下硬跑）
bash $SK/scripts/preflight.sh "$H"

# 1) 演讲稿  →  $H/视频课/script_v2_dialog.txt         （人工确认 gate）
# 2) 放映版  →  $H/视频课/index_present.html           （人工确认 gate）
python3 $SK/scripts/verify_steps.py "$H"        # 铁律校验：每帧 .step 数 == 该帧台词句数

# 3) 双音色音频 —— 两条路由二选一（preflight 自动判定，见阶段 3）
#    路由 A：GPT-SoVITS 克隆音色（音质最佳）
cd "$VC" && PYTORCH_ENABLE_MPS_FALLBACK=1 ./venv/bin/python ./dialog2audio.py \
  --script "$H/视频课/script_v2_dialog.txt" --outdir $W/audio --no-cleanup
#    路由 B（无 GPT-SoVITS 时）：macOS 本地 TTS，纯标准库零依赖，输出合同完全一致
python3 $SK/scripts/dialog2audio_local.py --script "$H/视频课/script_v2_dialog.txt" --outdir $W/audio

# 4) 音画对齐 → 截图 → 合成（--gap 必须 = merged 的帧间 0.9s，见阶段 4a）
python3 $SK/scripts/make_standalone.py --present "$H/视频课/index_present.html" \
  --report $W/audio/report.json --out $W/standalone.html --sched $W/schedule.json \
  --gap 0.9 --title "<课程名>" --subtitles --srt $W/subtitles.srt \
  --keywords "触觉传感器,化学传感器,传感器,摄像头,麦克风,感官"   # 按本课术语定制
# ── 动效版（用户 2026-10-03 起要求：入场动效进视频）──
# make_standalone 加 --animate 保留动画，然后用 capture_anim.js 确定性逐帧渲染：
node $SK/scripts/capture_anim.js $W/standalone.html $W/frames
# 输出 f%05d.jpg（30fps 严格无漂移），直接 -framerate 30 编码；约 10 帧/s，7 分钟片 ≈ 20 分钟
# 音效混流时刻 = 帧起点 + unit.start + unit.dur - unit.pause（★dur 含句后停顿，语音实际结束点要减 pause）
# ── 静帧版（旧管线，无动效）──
node $SK/scripts/capture.js $W
# 逐区间时长不同，不能用 -framerate 直读 shots；先按 30fps 生成硬链接帧序列（见阶段 4c）
python3 - <<'EOF'
import os
durs=[float(x) for x in open('/tmp/<课>/durations.txt')]
os.makedirs('/tmp/<课>/frames', exist_ok=True)
cum=0
for i,d in enumerate(durs):
    for k in range(round(cum*30), round((cum+d)*30)):
        os.link(f'/tmp/<课>/shots/shot_{i:04d}.png', f'/tmp/<课>/frames/f{k:05d}.png')
    cum+=d
EOF
ffmpeg -y -framerate 30 -i $W/frames/f%05d.png -c:v libx264 -pix_fmt yuv420p -crf 20 $W/video_cfr.mp4
ffmpeg -y -i $W/video_cfr.mp4 -i $W/audio/_merged_norm.wav -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -movflags +faststart -shortest "$H/视频课/<课程名>_双音色成片.mp4"
# ★ _merged_norm.wav = 合成音频先做两遍式 loudnorm（见 references/known_pitfalls.md §6，合成直出仅约 -19 LUFS）
#   第一遍: ffmpeg -i $W/audio/_merged.wav -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null -
#   第二遍: ffmpeg -y -i _merged.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=<输入I>:measured_TP=<TP>:measured_LRA=<LRA>:measured_thresh=<thresh>:linear=true" -ar 44100 -ac 2 _merged_norm.wav

# 4d) 片头 + 片尾 + 三段拼接（详见阶段 4d；片头不带念稿）
bash $SK/scripts/make_intro.sh --out $W/seg_intro.mp4 --total 5.0 \
  --title "第 3 课 · <em>事物的特征</em>"
#     片尾：$SK/assets/intro_outro/endcard.png + 告别词（与正片同倍速 atempo）
#     拼接：三段统一 30fps / -video_track_timescale 15360 / -ar 48000 -ac 2 → concat -c copy
#           → 全片 loudnorm -16 + faststart（采样率不一致的坑见 references/known_pitfalls.md §6）

# 5) 配套封面 →  $H/视频课/封面/

# 6) 切片引流（视频号 30-60s 短视频，长片发布同时产出 2~3 条）
#    a. 钩子卡/引导卡：改 $SK/assets/clip_cards_template.html（4 页：3 钩子+1 引导卡），puppeteer 截 PNG
#    b. 写 clips.json（帧号范围见剧本【第 N 帧】）→ 一键切割（句子边界对齐，不会切半句）：
python3 $SK/scripts/make_clips.py --final "$H/视频课/<课程名>_双音色成片.mp4" \
  --report $W/audio/report.json --outdir "$H/视频课/clips" --clips $W/clips.json
#    c. 标题≤16字钩子前置 + 描述带话题 + 置顶评论互动（文案模板见 L6 clips/切片文案_标题与描述.md）
#    选片三标准：自包含（不依赖前文）/ 开场即钩子 / 有过程演示（动画优势段）
```

## 路径变量（换机 / 换人只需改这里）

| 变量       | 含义                        | 本机实际值                                                                                  |
| -------- | ------------------------- | -------------------------------------------------------------------------------------- |
| `$SK`    | 本 skill 目录                | clone 后你自己的路径（如 `~/skills/dual-voice-course-video`）；或 `cd` 进 skill 目录用 `$PWD` |
| `$VC`    | 语音克隆项目（**不在教育项目目录下**）     | 运行前 `export VOICE_CLONE=/path/to/voice_clone`（脚本默认读该环境变量）|
| `$H`     | 本节课程目录                    | `…/Grades K-2. Introduction to AI Course/AI-L1. Human Senses vs Computer Sensors`      |
| `$H/视频课` | 本节全部产物                    | script / index_present.html / 素材 / 成片 / 封面                                             |
| `$W`     | 临时工作目录                    | `/tmp/<课名>`（音频、standalone、shots、成片）                                                    |
| 模板       | 蜡笔手绘风视觉基准（封面/课件统一）        | `$SK/assets/templates/crayon/preview.html`              |
| 竖版封面模板   | 视频号封面固定模板（1080×1260 对决版式） | `$SK/assets/templates/crayon/封面模板_竖版视频号_1080x1260.html` |

环境变量可覆盖：`VOICE_CLONE` / `CHROME_BIN` / `FFMPEG` / `SYS_PY`（带 PIL 的系统 python，默认 `/opt/homebrew/bin/python3`，托管版 python 没装 PIL）。

## 脚本清单（全部参数化，可直接跑）

| 脚本                                 | 作用                                                                                          | 用法                                                                            |
| ---------------------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `scripts/preflight.sh`             | 环境自检（18 项）                                                                                  | `bash preflight.sh [课目录]`                                                     |
| `scripts/verify_steps.py`          | 校验 HTML 帧/步 == 剧本帧/句                                                                        | `python3 verify_steps.py <课目录>`                                               |
| `scripts/dual_tts_dialog2audio.py` | 双音色配音（**须放在 `$VC/` 下跑**，与 `$VC/dialog2audio.py` 同内容）                                        | 见阶段 3 路由 A                                                                    |
| `scripts/dialog2audio_local.py`    | 本地 TTS 兜底配音（macOS `say`，纯标准库零依赖；输出合同与路由 A 一致，阶段 4 无缝衔接）                                     | 见阶段 3 路由 B                                                                    |
| `scripts/make_standalone.py`       | 生成 `standalone.html` + `schedule.json`（时间轴驱动）                                               | 见阶段 4a                                                                        |
| `scripts/capture.js`               | 按时间轴逐区间截图（自动找 puppeteer-core）                                                               | `node capture.js <工作目录>`                                                      |
| `scripts/capture_anim.js`          | **动效版成片渲染**（--animate 配套；逐 1/30s tick 驱动 applyTime + getAnimations 虚拟时钟同步，JPEG 落盘，约 10 帧/s） | `node capture_anim.js <standalone.html> <帧目录> [总秒数]`                          |
| `scripts/qc_frames.js`             | 放映版逐帧 QC：全展开截图 + 溢出检测 + 可选音频探测/逐 step 图                                                     | `node qc_frames.js <index_present.html> <出图目录> [audioId] [step帧号]`            |
| `scripts/contact_sheet.py`         | 截图拼总览图（需系统 python + PIL）                                                                    | `python3 contact_sheet.py <shots目录> <出图.png> 4 4`                             |
| `scripts/make_intro.sh`            | **蜡笔风动态片头一键生成**（令牌替换 → capture_anim 渲染 → 配乐 → 编码；默认 5.0s，模板见 assets/intro/，说明见「阶段 4d」）      | `bash make_intro.sh --out out.mp4 --title "第 3 课 · <em>事物的特征</em>"`           |
| `scripts/make_intro_music.py`      | 片头配乐生成（100BPM / C 大调 I–V/V–vi–IV 琶音+铺底+沙锤+混响；参数化、可复现；需 numpy+scipy）                         | `python make_intro_music.py --out m.wav --duration 5.0 [--bpm 100] [--bells]` |

## 核心约束：分阶段、每步可控

**严禁一次性自动连跑到底。** 每阶段产出中间文件后必须向用户展示并等明确确认（`AskUserQuestion` 或简短汇报），获得"继续"才进下一阶段。台词、构图、音色/语速、对齐精度、封面取向都主观且易错，连跑会浪费大量算力（双音色合成一节 40 句约 8–15 分钟，重跑成本高）。

**无人值守场景（另一个 agent 代跑）**：把确认 gate 换成「产物落盘 + 自检脚本通过 + 记录到工作日志」，可连续推进阶段 1→4；但**阶段 5 封面取向、以及成片视听验收必须留给人**。

### 阶段 1 · 演讲稿【确认 gate】

产出 `$H/视频课/script_v2_dialog.txt`（驱动 HTML 帧结构与 TTS 的唯一真相源）。

格式（被 `dual_tts_dialog2audio.py` 与 `verify_steps.py` 共同解析）：

```
【第 1 帧】开场 · 主题
小贤老师："请你仔细观察，它是什么颜色的？"[[1.2]]
学生："红色！"[[0.8]]
```

- 帧头 `【第 N 帧】`；角色行只能是 `小贤老师：` / `学生：`，台词用中文引号包裹
- `[[n]]` = 该句之后的静音秒数（学生思考/做动作的时间）
- 学生行含「哭脸/笑脸」→ 不念词，只留静音（做表情）
- **一帧内的角色行数 = 该帧 HTML 的 `.step` 数**（后续 1:1 对齐的唯一依据）
- 引号内不要出现 `"` `"`，否则解析器会漏句
- K-2 认知铁律：术语（触觉/化学/味觉传感器）只由老师说出，学生只答日常词（摄像头、麦克风）；不确定的用"不知道！/猜不到！"再让老师揭示
- 视频介质适配：线下"闭眼闻花/摸木头"要改成"看屏幕 + 听真实音频 + 回想"

**产出**：`script_v2_dialog.txt`。**确认点**：用户读稿，确认台词、角色分配、分帧节奏。

### 阶段 2 · HTML 放映版【确认 gate】

基于确认稿做 `$H/视频课/index_present.html`：每帧一个 `.stage-frame`（`id="f01"…`），帧内 `.step` 块数 = 该帧台词句数，可选 `data-hide-at="N"`（到第 N 步淡出）。

- 视觉**必须**沿用蜡笔手绘风模板：手绘抖动笔触（SVG `feTurbulence`+`feDisplacementMap`）、纸纹噪点、蜡笔 blob、贴纸卡、圆体-简/娃娃体-简；固定品牌要素（左上徽章「AI 启蒙 · 第 X 课」+ 适合年级；底部「小贤 AI 青少年教育 · 体系课程 · 实训项目 · AI 创造力」）
- 图标优先纯 SVG 简笔画；**用户给了真照片时**，做成「拍立得贴纸」：`<div class="sticker" style="padding:8px;transform:rotate(±2.5deg);position:relative"><img …118px…><span class="tape"></span></div>` + 下方 28px 标签。照片规格：方裁（对准主体/红圈）→ 360px → JPEG q86 → base64 内嵌，单文件自包含
- **改超长 base64 行时不要用 Edit 工具**（字符串匹配必然失败），用 Python `str.replace` / 正则
- 真照片贴纸（118px + 标签）比原 SVG 图标高，卡片易顶到页脚：`vis` 的 `top` 压到 566 左右，`nm` 44、`tx` 一句话不折行

**动效（按内容判断，不从上一课复制，也不用为差异化而差异化）**

- 做每帧时**先看这帧在讲什么课型**，再挑动效——不是照抄上一课的套路，也不是为了和上一课不同而硬换。判断决策表在 `$SK/assets/templates/anim-snippets/README.md`「二、按课型选动效」，必须按它走。
- 三类课型速记：① 讲概念 / 介绍特征 → `pop` 或 `blurIn`+`kenburns`；② 互动游戏 / 问答 → `slam`+`glow`+`elastic`；③ 对比 A vs B → `flyLeft`+`flyRight` 或 `iris`/`blinds`/`wipe` 转场。流程步骤用 `fadeRise`+数字步进+顺序 `glow`；总结回顾用 `fadeRise`+`slam`+`charsIn`。有真实截图/照片 → 一律 `blurIn`+`kenburns` 满幅，代码只做解释标注。
- 节奏铁律（避免被读成"翻页式 PPT"）：运动是「停住 → 猛一下 → 停住」的**脉冲节奏**，不是匀速慢推 / 全员呼吸。入场用 `MO.PULSE`（快推 `punch 0.28s`、横移 `pan 0.30s`、砸入 `slam 0.17s`）；一帧只让一个主体动，其余静止。
- 片段库两个用法：纯 CSS 课件 → `<link rel="stylesheet" href="assets/templates/anim-snippets/mo.css">` 加 class（`anim-pop`/`anim-slam`/`anim-fade-rise`/`anim-blur-in`/`anim-iris-in`/`anim-fly-left`/`anim-fly-right` + 持续 `idle-kenburns`/`idle-glow`/`idle-float`）；GSAP 时间轴渲染成片 → 引入 `mo.gsap.js` 后 `MO.entrance(tl, sel, kind, at)` / `MO.transition(tl, kind, at)` / `MO.continuous(sel, kind)`。无 GSAP 时自动降级为 CSS class，不报错。
- 开工前 / 交付前各对照一遍 `$SK/assets/templates/anim-snippets/README.md`「三、六种做坏方式」（翻页式PPT、照搬上一课、没有具体的物、死背景空画面、有真实素材却用代码画、一眼AI味拼贴）。
- 做完一支新课，效果好的动效组合**回流**进 README 第二节决策表；动效坑写进 `references/known_pitfalls.md`（§5 动效）。同课型用同一套动效完全正确，只有课型变了才换。


**QC 循环（必做）**：

```bash
node $SK/scripts/qc_frames.js "$H/视频课/index_present.html" /tmp/qc_$(basename "$H") <audioId> <要验证逐步的帧号>
bash -c '/opt/homebrew/bin/python3 '"$SK"'/scripts/contact_sheet.py /tmp/qc_xxx /tmp/总览.png 4 4'
```

逐帧看 png，溢出帧（`⚠️ 溢出帧`）按上述手法修，直到 `✅ 全部帧无溢出` + 目视构图 OK。

**确认点**：用户看 HTML 预览/截图确认构图与节奏；同时 `verify_steps.py` 必须通过。

### 阶段 3 · 双音色音频【确认 gate】

**两条路由，preflight 自动判定，产物合同完全一致**（frame_NN.wav / \_merged.wav 帧间 0.9s / report.json 顶层 list），阶段 4 无需任何改动：

**路由 A · GPT-SoVITS 克隆音色（首选，音质最佳）** —— 在 `$VC` 下跑（脚本内 `EXPS` 自动取最新权重，参考音在 `dataset/` 下，**不要手写权重路径**）：

```bash
cd "$VC"
PYTORCH_ENABLE_MPS_FALLBACK=1 ./venv/bin/python ./dialog2audio.py \
  --script "$H/视频课/script_v2_dialog.txt" --outdir $W/audio --no-cleanup
# 坏句单独重跑： --only 4,7,11
```

- 老师 `xiaoxian`（ref `dataset/xiaoxian/wavs/xiaoxian_0029.wav`）、学生 `macie`（ref `dataset/macie/wavs/macie_13.wav`）
- 参数：`--takes 3`、`--temperature 1.0`、`--gap 0.4`（帧内行距）、`--device cpu`（默认，稳）
- **必须加 `--no-cleanup`**：否则逐句 `os.remove` 会触发沙箱 bulk-delete 守卫，进程被杀（EXIT=1）
- 产出：`$W/audio/frame_NN.wav`（每帧）、`$W/audio/_merged.wav`（全课，帧间 0.9s）、**`$W/audio/report.json`**（每帧 `units:[{speaker,text,pause,dur,start}]`，`start` 是句内起始秒 —— 阶段 4 直接吃它）
- 单句成句判定：`split_units` 的过滤阈值必须是 `>=1`（旧 `>=4` 会整句丢掉「苹果！」这类 1–3 字童声，表现为"学生句消失"而不是报错）

**确认点**：抽查 2–3 帧（师生都在、短句没丢、语速自然）后进阶段 4。

**路由 B · 本地 TTS 兜底（无 GPT-SoVITS 环境时，跨平台）** —— 纯标准库脚本，零第三方依赖，按平台自动选后端：

```bash
python3 $SK/scripts/dialog2audio_local.py --script "$H/视频课/script_v2_dialog.txt" --outdir $W/audio
# 坏句单独重跑： --only 4,7,11 （CLI 与路由 A 兼容，--takes/--temperature 等被接受但忽略）
```

| 平台      | 后端                                         | 师生双音色方案                                                            |
| ------- | ------------------------------------------ | ------------------------------------------------------------------ |
| macOS   | `say`（系统自带）                                | 老师 Tingting（婷婷）/ 学生 Meijia（美佳 + `[[pbas +110]][[rate +15]]` 抬调）    |
| Windows | PowerShell + System.Speech(SAPI)（系统自带，零安装） | 自动枚举中文语音包（Huihui/Yaoyao…），师生取两个不同声音；只有一个时 SSML `pitch +25%` 抬调区分学生 |
| Linux   | `espeak-ng`（需安装，音质最差）                      | cmn 普通话，学生 pitch 抬高                                                |

- 通用约定：统一输出 32000 Hz Int16 单声道（后端采样率不符时自动 ffmpeg 重采样）；`_merged.wav` 帧间 0.9s；report.json 字段与路由 A 逐字段一致 → **阶段 4/5 全部命令原样可用**
- 声音覆盖：环境变量 `SAY_TEACHER` / `SAY_STUDENT`（所有平台通用）；Windows 中文语音包缺失时：设置 → 时间和语言 → 语言和区域 → 添加语言「中文(简体)」并勾选语音
- 音质预期管理：系统级合成，非真人克隆（Windows/Linux 明显弱于路由 A）。**升级路径**：先出片交付 → 装好 GPT-SoVITS + 训练音色后，按「无声版后悔药」流程用路由 A 重跑阶段 3→4 重合成（报告/时间轴都保留，无需改画面）
- 动作行（哭脸/笑脸）静音、`[[n]]` 停顿、AI→诶爱 清洗等解析行为与路由 A 完全一致
- ⚠️ Windows/Linux 上其余阶段（Chrome/ffmpeg 路径）需用环境变量指定（`CHROME_BIN`/`FFMPEG`）；Windows 的 SAPI 分支按标准实现，尚未真机实测，问题反馈时优先排查语音包是否含中文

### 阶段 4 · 音画整合成片【子确认点：4a 时轴 → 4b 截图 → 4c 合成 → 4d 片头片尾】

**4a 时间轴对齐**

```bash
python3 $SK/scripts/make_standalone.py \
  --present "$H/视频课/index_present.html" --report $W/audio/report.json \
  --out $W/standalone.html --sched $W/schedule.json --gap 0.9 --nf <帧数> --title "<课程名>" \
  --subtitles --srt $W/subtitles.srt --keywords "<逗号分隔关键词>"
```

- 输出 `standalone.html`（HTML 结构原样、不删任何字符；CSS 复用原 `<style>`；帧/step 显隐由 `applyTime(t)` 数据驱动）+ `schedule.json`（总时长与截图区间）
- **`--gap` 必须填 0.9**：`dialog2audio.py` 合并 `_merged.wav` 时帧间是硬编码 0.9s（旧文档写 0.25 是坑，会使末帧漂移近 10s、音画严重失步）。校验：standalone 总时长 ≈ `_merged.wav` 时长（±0.1s）
- `--subtitles`：底部蜡笔风字幕条（师生分色：老师深蓝/学生粉，`--keywords` 黄底橙字高亮，长句按标点自动切 ≤30 字短条并按字数比例分配时间），字幕条放在页脚上方（bottom:104px），**只改 standalone，不动 index_present.html，不影响老师上课用放映版**；同时会修掉"帧间空隙画面内容清空闪烁"（step 延续到 gend）
- `--srt`：同步产出 .srt（给剪辑/平台备用）
- 脚本兼容两种 frame 写法（`class` 在前或 `id` 在前），会自动剥掉内嵌 `<audio>`（成片音轨由 ffmpeg 单独混，留着会重复出声）
- `bind_delays`：step 数 == 对话行数时 1:1 锚定每句 `start`；不相等则帧内均匀分布 —— **绝不能让所有 step 堆在 0s**（画面会提前泄题）
- ⚠️ 不要用 `scripts/compose.py`（hyperframes 中间格式，脆正则 + 240s 流式限制，已弃用，仅存档）

*子确认点*：本地打开 `standalone.html` 拖 `applyTime(t)` 或试截 1 帧，确认每个 step 出现时刻与音频语义对得上。

**4b 逐帧截图**

```bash
node $SK/scripts/capture.js $W          # 读 $W/schedule.json，输出 $W/shots/shot_0000.png…；写 durations.txt
```

*子确认点*：抽查 3–5 张（含贴纸/真照片/字幕的帧），确认无空白帧、无字体回退。

**4c 合成（区间时长不同，禁止 -framerate 直读 shots）**

```bash
# 1) 按 30fps 生成硬链接帧序列（每个 tick 硬链接到所属区间的 shot，时间零误差）
python3 - <<'EOF'
import os
durs=[float(x) for x in open('durations.txt')]
os.makedirs('frames', exist_ok=True)
cum=0
for i,d in enumerate(durs):
    for k in range(round(cum*30), round((cum+d)*30)):
        os.link(f'shots/shot_{i:04d}.png', f'frames/f{k:05d}.png')
    cum+=d
EOF
ffmpeg -y -framerate 30 -i frames/f%05d.png -c:v libx264 -pix_fmt yuv420p -crf 20 video_cfr.mp4
ffmpeg -y -i video_cfr.mp4 -i audio/_merged.wav -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest 成片.mp4
```

- **已实测三种错误路径，全部会音画失步**：① `-framerate 30 -i shots/shot_%04d.png` 把每区间当 1/30s；② concat demuxer（-f concat + duration）输出 VFR，时间戳漂移实测 t=50 处错位一个区间；③ 在 concat 输入上加 `-r 30` 或 `fps=30` 滤镜，漂移更大（415s vs 398s）。**唯一可靠：硬链接帧序列**（校验方法：与 schedule 抽 3 个时刻比对显示的是哪张 shot）
- **concat PNG 时不能同时加 `-c:a`**（会被静默忽略，成片无音轨）；音轨必须第二步 `-c:v copy` 混流
- 体积：静态画面 + 纸纹噪点在真实 30fps 下 crf20 约 30MB+（VFR 单帧估算 14–15MB 已不适用）；微信轻量版可 `-crf 26 -vf scale=1280:-2`
- **画面内有真实音效时（如放映版内嵌的儿歌），成片必须额外混一层**：双音色 `_merged.wav` 里只有对白。做法：`ffmpeg -i video_cfr.mp4 -i _merged.wav -i 儿歌.mp3 -filter_complex "[2:a]volume=0.32,adelay=<帧起点ms>|<帧起点ms>[r];[1:a][r]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy ...`（儿歌起点 = 第 2 帧 gstart×1000，可从 schedule.json 算）。别指望放映版内嵌 `<audio>` 出声（standalone 已默认剥掉）。
- QC：与 schedule 抽时刻比对 shot；音频抽查首/中/尾
- **【必做】无声版归档（换音色重合成的后悔药，2026-10-03 用户要求）**：成片后立刻把中间产物复制到 `$H/视频课/`，别留在 /tmp（系统会清）：
  - `video_cfr3.mp4` → `L*_无声画面版.mp4`（无声、含烧录字幕）
  - `durations.txt` → `时间轴_durations.txt`；`schedule.json` → `时间轴_schedule.json`
  - `$A/report.json` → `音频时长_report.json`（每句真实时长，换音色后对齐用）
  - `standalone.html` → `渲染用_standalone.html`
  - ⚠️ 无声版里字幕时间是按**当前音色**时长烧进画面的：新音色若每句时长变化，直接混流会字幕错位。**正确重合成路径**：新音色跑 dialog2audio → 用新 report.json/durations 重跑 make_standalone → 重截图 → 硬链接帧 → 编码 → 混流（全链脚本化，仅时长变化无需改画面内容）；无声版视频只用于预览/对比，或新音色时长与旧版几乎一致时直接混流  
    *子确认点*：用户预览成片，确认音画同步、字幕、双音色清晰；可另出轻量版。

**4d 片头与片尾（蜡笔风动态片头，2026-10-08 定稿）**

**片头不带念稿**——只做品牌与价值主张，不念课程内容（用户 2026-10-08 定案）。5.0s / 30fps / 1920×1080。

```bash
bash $SK/scripts/make_intro.sh --out "$H/视频课/片头_5s.mp4" --title "第 3 课 · <em>事物的特征</em>"
```

- **视觉**：令牌与课件 `index_present.html` 完全一致（奶油纸底 / 点阵 / 噪点 / 藏青描边 / 圆体-简 / 娃娃体-简），末帧擦成纯奶油底，**与正片第 1 帧无缝**
- **节奏**（照 L2 `sensingandunderstanding.mp4` 前 5 秒）：logo 飞入 0.02–0.85 → 品牌名 0.60–1.25 → 主张句 1.05–1.70 → **配套三件套逐个飞入** 1.62–2.66（左/下/右三个方向、窗口交叠）→ 收尾句 2.62–3.12 → 课名贴纸 3.05–3.85 → 蜡笔擦除 4.35–4.95
- **文案全走 CLI**：`--brand / --claim / --lead / --k1 / --k2 / --k3 / --noplug / --title`（`--title` 里的 `<em>关键词</em>` 自动加黄色高亮胶囊）
- **时长**改 `--total`：模板里所有时间点都过 `K(x)=x*TOTAL/5.0` 等比缩放，不用改 JS
- **配乐** `scripts/make_intro_music.py`：100BPM、C 大调 I–V/V–vi–IV 琶音 + 铺底 pad + 轻沙锤 + 合成混响；**默认不加卡点铃铛**（用户定案，见 references/known_pitfalls.md §6）
- **资产**：`assets/intro/`（模板 + 官网 logo + README）

*确认 gate*：出片后抽 4 帧 + 完整听一遍。**片头定稿后再开正片渲染**——换音色/改文案会改时轴，画面得重渲（L3 一次 9664 帧 ≈ 12–15 分钟）。

> 片尾仍用 `assets/intro_outro/endcard.png`（静态卡 + 告别词，告别词按正片同倍速 atempo）；  
> 三段拼接（片头 / 正片 / 片尾）的采样率坑见 `references/known_pitfalls.md` §6。

### 阶段 5 · 配套封面【确认 gate】

**双模板固定制（2026-10-02 用户定稿，每课固定出这两张，不再每课另选版式）**：

| 模板      | 画布        | 模板文件（勿改结构）                                                                       | 用途            |
| ------- | --------- | -------------------------------------------------------------------------------- | ------------- |
| 横版课件封面  | 1920×1080 | `$TPL/preview.html`（第 1 页「封面」slide）                               | 课件/公众号/横版视频封面 |
| 竖版视频号封面 | 1080×1260 | `$TPL/封面模板_竖版视频号_1080x1260.html`（对决版式：左贴纸卡 + VS 圆 + 右贴纸卡 + 娃娃体批注） | 视频号竖版封面       |

- `$TPL = $SK/assets/templates/crayon`；换课只改竖版模板里 3 个【替换】点：① 徽章课号+年级 ② 主/副标题（mark.y 黄底 / mark.b 蓝底）③ 左右贴纸卡 SVG+cap 与手写批注；品牌行「小贤 AI 青少年教育 · 体系课程 · 实训项目 · AI 创造力」与徽章位置**固定不改**
- 风格铁律：蜡笔手绘风（wobble 滤镜 + 噪点纸纹 + 圆体-简/娃娃体-简 + 蜡笔色板），**不得回退旧平铺米底低对比版**
- ⚠️ 视频号信息流按 **1:1 居中裁切**（1080×1260 → 取 y=90~1170）：标题/徽章/品牌行必须全部压进该安全区（品牌行 bottom:118px 即 y≈1112，已验证在内）。自查：`ffmpeg -y -i 封面.png -vf crop=1080:1080:0:90 -q:v 3 自查_1比1裁切.png`
- 工作流：**先出 HTML 风格稿（用模板填内容）→ 用户确认 → 再 puppeteer 截图出图**；截图 1080×1260 viewport + `document.fonts.ready` + 300ms 等待
- **产出**：`$H/视频课/封面/封面_横版_*.png`（1920×1080）+ `封面_竖版_*.png`（1080×1260）+ `自查_1比1裁切_*.png`
- 实际案例（L1）：`AI-L1/视频课/封面/封面A_对决版.html|png`（即竖版模板的填内容版）；横版案例见 preview.html 第 1 页

## 关键铁律（违反必翻车）

1. 顺序不能乱：稿 → 画面 → 声音 → 整合 → 封面。**不要**把音频放到 HTML 之前，也**不要**在成片前先做封面。
2. 帧内 `.step` 数 == 台词句数（`verify_steps.py` 把关），否则对齐会错位。
3. 任何一次改稿/改画面，都要重跑 `verify_steps.py` + `qc_frames.js`。
4. 超长 base64 内容只走 Python 脚本改，不用编辑器硬改。
5. 音频必须 `--no-cleanup`；成片音轨必须二次混流。
6. 每阶段产物落到 `$H/视频课/` 或 `$W`，并把"真照片素材"另存 `$H/视频课/素材_*.jpg` 方便复用到 PPT/教材。

## 参考文档

- `references/pipeline.md`：每阶段命令与文件结构笔记
- `references/known_pitfalls.md`：通用踩坑清单（按根因/主题归类，**与课程内容无关**，动手前必读）。涵盖：吞字类（孤立拉丁字母、破折号单字短片段、童声短句）、双音色 TTS、时间轴对齐、HTML 排版版式、CSS 动效、响度/混流(loudnorm)、切片引流、合成编码、QC、封面、教学设计通用原则、路由 B 跨平台兜底。
- `references/example_schedule.json`：`schedule.json` 结构示例
