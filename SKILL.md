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

你是这节课的编剧、导演、教研总监和设计师。画面用 HTML/CSS 画，声音用双音色 TTS 合成，成片的标准是：观众看得懂每一帧在讲什么，愿意看下去，**每一句台词出现时，画面上对应的那个东西正好出现**。

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

⛔ 严禁一次连跑到底。6 个【确认 gate】：取向、阶段 1、2、3、**4（片头+正片完整出完后一次）**、5。

1. **不得用"简短汇报一句"代替用户确认**——必须等用户明确说"继续/可以/确认"。
2. **不得为"高效/省事"合并或跳过 gate**。
3. **用户没回之前，不得预读下一阶段、不得创建/改写下一阶段产物、不得跑下一阶段命令。**

无人值守场景（另一 agent 代跑且用户已明确授权连跑）才把 gate 换成「产物落盘 + 自检通过 + 记进工作日志」；但**阶段 5 封面取向与成片视听验收必须留给人**。

## 技术铁律（违反必翻车）

1. 顺序不能乱：稿 → 画面 → 声音 → 整合 → 封面。后一步消费前一步的产物（画面按台词分步、音频按台词计时、整合按两者对轴），乱序 = 全部返工。
2. 画面与台词一一对齐：帧内 `.step` 数 == 该帧台词句数；任何一次改稿/改画面后重跑 `verify_steps.py` + `qc_frames.js`——这两处失守都是静默失败（步数错 → 均匀分布泄题；改动后不复检 → 错位/溢出进成片），不会报错。

## 窄桥：照字面做（这些没有商量余地）

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

取向=both 时：**两版各自判空间与排版**（清场/字号/间距/片头/封面横竖各一套），不得把一版的决策直接复制到另一版；命中判据见阶段 2/4d/5。

### 1 · 演讲稿【gate】

产出 `$H/视频课/script_v2_dialog.txt`（驱动 HTML 帧结构与 TTS 的唯一真相源）。格式、校验命令与判断要点（角色分配铁律、视频介质改写）见 `references/stages/1-script.md`。

⛔ 停下，呈现完整剧本 + 本课关键词表 + 音效提案 `sfx_plan.txt`（判定表见 `stages/1-script.md`；关键词表字幕高亮用、横竖版共用一份）+ 问「台词/关键词表/音效是否确认」；关键词表确认后写入 `course_config.json` 的 `subtitle_keywords`。

### 2 · HTML 放映版【gate】

基于确认稿做 `index_present.html`。**版式选型、visual 帧硬规则、排版标准、结构契约、QC 循环一律见 `references/stages/2-slides.md`**（视觉风格包配方与品牌要素见 `assets/templates/crayon/README.md` §2.1）。

⛔ 呼吸感三查 + 机检（`qc_frames` 全部帧无溢出 + `verify_steps.py` + `qc_divs.py` + `qc_clear.js` 清场 vs 空间 + `qc_variety.py` 母题/动效分布）全过后停下，把 HTML 放映版呈现给用户预览 + 问「内容、排版和动效是否确认」。

### 3 · 双音色音频【gate】

两条路由 preflight 自动判定，产物合同完全一致。路由选择原则、命令/平台后端/参数/report.json schema 见 `references/stages/3-audio.md`。

⛔ 停下，把音频文件交给用户点开听，`AskUserQuestion` 问「音频是否确认」。

### 4 · 整合出片【gate】

命令、各步自检项与已知失步路径全部在 `references/stages/4-compose.md`，**勿手打 ffmpeg**。

**4a → 4b → 4c → 4d 连续执行，中途不停**（各步只做自检，不过就回上一步重跑，不要带着疑问往下走）。⛔ **片头与正片拼接完成后停下**，交完整成片请用户看一遍 + `AskUserQuestion` 问「成片是否确认」。取向=both 时两版都拼片头，尺寸必须同向。

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
node    $SK/scripts/qc_clear.js "$H/视频课/"index_present*.html   # 清场决策 vs 空间（只提示）
python3 $SK/scripts/qc_variety.py "$H/视频课/index_present.html"  # 母题/动效分布（只提示不阻断）
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
