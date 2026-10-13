---
name: dual-voice-course-video
version: 1.2.0
display_name: 主题一键成课：互动课件+讲解视频
display_name_en: Topic-to-Course — Interactive Slides and Narrated Video
description: 把一节课的主题或已有课件，产出演讲稿、互动放映版 HTML、老师/学生双音色配音讲解视频（逐帧音画对齐+字幕）与配套封面。顺序固定为写稿→放映版→双音色音频→音画整合→封面，每阶段有确认门禁。当用户要求「为一节课/一个主题生成互动课件或带配音的视频」「做双音色课程视频」「演讲稿转视频」「生成视频号封面」时使用。配音路由自动判定：有 GPT-SoVITS 用克隆音色，否则落本地系统 TTS（macOS/Windows/Linux 全平台兜底），可后续换音色重合成。不做既有视频的拆解复刻。
agent_created: true
---

# 双音色课程视频制作流水线

## 你是谁

你是这节课的编剧、分镜、美术和剪辑。画面用 HTML/CSS 画，声音用双音色 TTS 合成，成片的标准是：**每一句台词出现时，画面上对应的那个东西正好出现**。

## 先判断任务

| 用户说的 | 走哪 | 命令/格式读 |
| --- | --- | --- |
| 「给 X 主题做节课」「做个互动课件」 | 从阶段 0 取向确认开始 | 本文 SOP |
| 「已有演讲稿，转成视频」 | 从阶段 2 进 | `references/stages/2-slides.md` |
| 「只要音频」「换音色重合成」 | 阶段 3（换音色还需重跑 4a→4c） | `references/stages/3-audio.md`、`references/stages/4-compose.md` |
| 「只要封面」 | 阶段 5 | `references/stages/5-cover.md` |
| 「成片切几条短视频」 | 阶段 6（可选） | `references/stages/6-clips.md` |
| 「拆解/复刻这支视频」 | **不支持**，本 skill 是制作流水线不是拆解工具 | — |

## 门禁（硬停止，不是建议）

⛔ 严禁一次连跑到底。5 个【确认 gate】：取向、阶段 1、2、3、5；阶段 4 另有 4a/4b/4c/4d 子确认点。

1. **不得用"简短汇报一句"代替用户确认**——必须等用户明确说"继续/可以/确认"。
2. **不得为"高效/省事"合并或跳过 gate**。
3. **用户没回之前，不得预读下一阶段、不得创建/改写下一阶段产物、不得跑下一阶段命令。**

无人值守场景（另一 agent 代跑且用户已明确授权连跑）才把 gate 换成「产物落盘 + 自检通过 + 记进工作日志」；但**阶段 5 封面取向与成片视听验收必须留给人**。

## 技术铁律（违反必翻车）

1. 顺序不能乱：稿 → 画面 → 声音 → 整合 → 封面。后一步消费前一步的产物（画面按台词分步、音频按台词计时、整合按两者对轴），乱序 = 全部返工。
2. 画面与台词一一对齐：帧内 `.step` 数 == 该帧台词句数；任何一次改稿/改画面后重跑 `verify_steps.py` + `qc_frames.js`——这两处失守都是静默失败（步数错 → 均匀分布泄题；改动后不复检 → 错位/溢出进成片），不会报错。

## 窄桥：照字面做（这些没有商量余地）

- 片头节拍、视觉令牌、配乐参数的**权威在 `assets/intro/README.md`**，照它做，不复述也不自己发明。
- 音色模型与本机软件/目录路径（ffmpeg、Chrome、Python、voice_clone 目录等）​一律不写死，走 `load_config.py`（见下）。

## 开阔地：自己判断（这些是起点不是配额）

- **动效选型**：先看这帧讲什么课型，再挑——决策表在 `assets/templates/anim-snippets/README.md`「二、按课型选动效」，**必须按它走**；开工前/交付前各对一遍同文件「三、做坏方式清单」。做完效果好就把组合回流进 README 第二节。
- 视觉构图、贴纸、配色、板书呈现方式（蜡笔手绘风是基准不是牢笼）。
- 台词的口语化与节奏、钩子和人味。

## 快速开始

```bash
cd <skill 目录> && export SK=$PWD
export H="<课目录>"                                  # 取向 gate 时新建
export W=/tmp/$(basename "$H" | tr ' ' '_')          # 派生工作目录
bash $SK/scripts/preflight.sh "$H"                   # 0) 环境自检，缺件会明确报错
```

之后逐阶段走 SOP，**每个 gate 停下等人**。

## SOP 阶段

### 0 · 取向确认【gate】

**先问取向，再开工**——它决定阶段 2 用哪个模板、阶段 4 按什么尺寸渲染、阶段 5 要不要补竖版。横版 1920×1080（默认，课堂投影）/ 竖版 1080×1440（视频号/抖音）/ 横竖都要（阶段 3 音频只合成一次，两套共用）。

⛔ 停下，用 `AskUserQuestion` 问「横版 / 竖版 / 横竖都要」，落 `$H/视频课/course_config.json`（orientation / teacher_display_name / gap 三字段，脚本读的权威只此一份）。用户没回前不得写剧本以外的任何产物。

### 1 · 演讲稿【gate】

产出 `$H/视频课/script_v2_dialog.txt`（驱动 HTML 帧结构与 TTS 的唯一真相源）。格式与校验命令见 `references/stages/1-script.md`。

判断要点：专业名词和术语只由老师说出，学生只答日常词，不确定的用"不知道！/猜不到！"再让老师揭示；用户原始内容若按线下课堂设计（分组讨论/上台演示/实物传递），须改写成视频可呈现的形式——线下执行的动作改成"看屏幕+听音频+回想+线上 HTML 游戏"等。

⛔ 停下，呈现完整剧本 + 本课关键词表（提炼规则见 `stages/1-script.md`；字幕高亮用、横竖版共用一份）+ 问「台词/关键词表是否确认」；关键词表确认后写入 `course_config.json` 的 `subtitle_keywords`。

### 2 · HTML 放映版【gate】

基于确认稿做 `index_present.html`。结构契约、真照片配方、QC 循环见 `references/stages/2-slides.md`。

判断要点：视觉沿用蜡笔手绘风（抖动笔触 / 纸纹噪点 / 蜡笔 blob / 贴纸卡 / 圆体-简+娃娃体-简），固定品牌要素（左上徽章「AI 启蒙 · 第 X 课」+适合年级；底部「小贤 AI 青少年教育 · 体系课程 · 实训项目 · AI 创造力」）；图标优先纯 SVG 简笔画，用户给了真照片就做「拍立得贴纸」。**先逐帧定版式再动手**：跑 `python3 $SK/scripts/suggest_layout.py <剧本>` 出选型表（`dialog` 对话优先 / `visual` 图片优先，判据=这帧核心信息能否一图概括），gate 时随截图交用户确认；每帧写成 `<div class="stage-frame" id="fXX" data-layout="…">`。两套版式规格与帧骨架见 `assets/templates/crayon/README.md` §2——dialog 允许长句气泡；**visual 帧硬规则**：每步主图挂 `.fscene` 换景、对话提炼 ≤15 字/句（完整表达交字幕）、整帧画面文字 ≤40 字、字幕安全区（竖版 y≥1120 / 横版 y≥900）只放品牌行。**排版再过 2-slides.md「版式标准」**：呼吸感三查（标题带 ≥48px / 块间 ≥36px / 底部安全带 ≥32px）+ 正文 ≥32 号 + 单帧终态对话块 ≤4；塞不下按「砍内容→拆帧→降字号」处理，禁止压间距硬塞。

⛔ 呼吸感三查 + 机检（`✅ 全部帧无溢出` + `verify_steps.py` 通过）全过后停下，呈现预览/截图 + 问「构图与节奏是否确认」。

### 3 · 双音色音频【gate】

两条路由 preflight 自动判定，产物合同完全一致。命令/平台后端/参数/report.json schema 见 `references/stages/3-audio.md`。

判断要点：有 GPT-SoVITS 走路由 A（克隆音色，音质最佳），没有则落路由 B（本地系统 TTS，跨平台零依赖，先出片交付、装好环境后按「无声版后悔药」流程重合成）。

⛔ 停下，把音频文件交给用户点开听（师生都在、短句没丢、语速自然），`AskUserQuestion` 问「音频是否确认」。

### 4 · 整合出片【4a 时轴 → 4b 截图 → 4c 合成 → 4d 片头片尾】

命令与已知失步路径全部在 `references/stages/4-compose.md`，**勿手打 ffmpeg**。

判断要点：**成片一律动效版**——`make_standalone` 必带 `--animate`、4b 用 `capture_anim.js` 虚拟时钟逐帧渲染（L1/L2 静帧版时代动画全丢，L8 误走静帧版被打回；静帧版仅当课件完全无动效**且用户明确要求**才可用）。**片头不带念稿**（只做品牌与价值主张，2026-10-08 定案），默认 7.5s；片尾用 `make_intro_outro.py` 三段式。

- *4a 后*：本地打开 `standalone.html` 拖 `applyTime(t)`，确认每个 step 出现时刻与音频语义对得上。
- *4b 后*：抽查 3–5 张（含贴纸/真照片/字幕的帧），无空白帧、无字体回退。
- *4c 后*：用户预览成片，确认音画同步、字幕、双音色清晰。
- ⛔ **4d 片头渲染完停下**，呈现抽 4 帧 + 请完整听一遍 + 问「片头是否定稿」——**片头定稿后再开正片渲染**（换音色/改文案会改时轴，L3 一次 9664 帧 ≈ 12–15 分钟）。

### 5 · 配套封面【gate】

双模板固定制、命令与安全区自查见 `references/stages/5-cover.md`。**先出 HTML 风格稿 → 用户确认 → 再截图出图**。

⛔ 停下，用 `AskUserQuestion` 确认取向（主副标题/贴纸卡/批注）后再截图；成片视听验收必须留给人，不得自动定稿发布。

### 6 · 切片引流（可选，发布运营工具）

从成片切 30–60s 短视频，命令见 `references/stages/6-clips.md`。不属于五阶段主线。

## 路径与配置（一律不手写）

```bash
python3 $SK/scripts/load_config.py --get paths.ffmpeg      # 机器相关值只认 config + 环境变量
python3 $SK/scripts/load_config.py --json                  # 完整合并结果
```

- 首次使用：复制 `config.example.json` → `config.local.json`（已 gitignore），填 `paths` 与 `voices`。
- 优先级：环境变量 > 课程配置 `course_config.json` > `config.local.json`。
- `$SK` 脚本自己知道（`SKILL_DIR` 由 `dirname` 推导）；`$H` 取向 gate 时 `export`；`$W` 默认 `/tmp/<课名>`。
- 老师显示名（默认 `老师`）只改 HTML 气泡署名，剧本角色行固定 `老师：`——TTS 只认标签判声线。

## 脚本入口

```bash
bash  $SK/scripts/preflight.sh "$H"                 # 环境自检（缺件明确报错）
python3 $SK/scripts/verify_steps.py "$H"            # 帧/步 vs 帧/句 一致性（exit 1 拦截）
node  $SK/scripts/capture_anim.js "$W/standalone.html" "$W/frames"  # 阶段 4b 动效版（默认管线）
```

动效版 4c 用 `ffmpeg -framerate 30 -i f%05d.jpg`（命令见 4-compose.md）；`make_video.sh` 仅静帧版降级用。其余脚本（`make_standalone` / `capture` / `qc_frames` / `dialog2audio_local` / `make_intro` / `make_intro_music` / `make_intro_outro` / `make_clips`）在各阶段文件里给完整命令；参数以 `--help` 为准。

## Response Style

- 每个 gate 停下时用 `AskUserQuestion`，给 2–3 个具体选项，推荐项放第一个并一句话说为什么。
- 汇报只说「本阶段产出了什么、下一步在等什么确认」，不复述整份文档。
- 命令失败先读报错和 `known_pitfalls.md` 对应根因，不要盲改参数重试。
- 给用户看的成片路径单独成行，不加粗、不加代码块、不加表格。

## 参考文档

- `references/stages/00-overview.md`：阶段索引、变量取法、文件结构总览（**命令层入口**）
- `references/stages/1-script.md` … `6-clips.md`：逐阶段命令、参数、schema、配方
- `references/known_pitfalls.md`：踩过的坑 + **风格默认基线**（按根因归类，动手前必读）；`references/known_pitfalls.local.md`：个人覆盖（品牌/本机字体/个人教学法，gitignore；缺失时用默认即可）
- `references/positive-patterns.md`：**做对了的做法**（做法+证据+为什么+何时用，开工前看）
- `references/example_schedule.json`：`schedule.json` 结构示例
