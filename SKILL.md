---  
name: dual-voice-course-video  
version: 1.1.0  
display_name: 主题一键成课：互动课件+讲解视频  
display_name_en: Topic-to-Course — Interactive Slides and Narrated Video  
description_en: Give it a topic (or an old PPT) and get a full lesson package automatically — narration script -> interactive step-by-step HTML slides -> dual-voice (teacher + student) narrated video with frame-accurate alignment and subtitles -> matching cover images. Built for teachers, content creators, corporate trainers, course teams, and parents. Voice route is auto-detected — GPT-SoVITS cloned voices when available, otherwise local system TTS (macOS/Windows/Linux) — with a seamless re-synthesis path for later voice upgrades.  
description: 主题一键成课：用户给一个课程主题（或已有课件/PPT），自动产出演讲稿、互动放映版 HTML 课件、老师/学生双音色配音讲解视频（逐帧音画对齐 + 字幕）与配套封面。制作顺序为「先写演讲稿并确认 → 再做 HTML 放映版并确认 → 按稿生成双音色音频 → 把音频和 HTML 整合成最终视频 → 最后生成配套封面」。适合教师、知识博主、企业培训师、课程产品团队、家长等任何需要把知识点变成互动课件或视频课的人。配音路由自动判定：有 GPT-SoVITS 用克隆音色（音质最佳），没有则落本地系统 TTS（macOS/Windows/Linux 全平台兜底），后续可无缝换音色重合成。当用户要求"为一节课/一个主题生成 互动课件或带配音的视频""做双音色课程视频""演讲稿转视频"时使用。  
agent_created: true  
---

# 双音色课程视频制作流水线

把一节 AI 课的 **演讲稿 → HTML 放映版 → 双音色音频 → 音画整合出片 → 配套封面** 五步固化，产出画面动作精确到每一句的 mp4 与可发布的视频号封面。

## 快速开始（任何 agent / 新会话照这个跑）

```bash
SK=<本 skill 目录，你 clone 到的路径>     # 本 skill
H="<课目录>"                                                      # 例：…/AI-L1. Human Senses vs Computer Sensors
W=/tmp/$(basename "$H" | tr ' ' '_')                              # 工作目录（音频/截图/成片）

# 0) 环境自检（缺件会明确报错，不要在缺件下硬跑）
bash $SK/scripts/preflight.sh "$H"

# 制作顺序（★每阶段跑完先停下等用户确认 gate；逐阶段完整命令见 references/pipeline.md）：
# 1) 演讲稿    →  $H/视频课/script_v2_dialog.txt           （确认 gate：台词/角色/节奏）
# 2) 放映版    →  $H/视频课/index_present.html             （确认 gate：构图/节奏；取向含竖版另产 index_present_portrait.html）
# 3) 双音色音频 →  $W/audio/_merged.wav + report.json       （确认 gate：抽查 2–3 帧）
# 4) 整合出片  →  $H/视频课/<课程名>_双音色成片.mp4         （子确认点 4a→4b→4c→4d）
# 5) 封面      →  $H/视频课/封面/                          （确认 gate：取向确认后出图）
# 6) 切片引流  →  $H/视频课/clips/                          （可选；发布运营工具，非五阶段主线，见 pipeline.md 阶段 6）
```

## 路径变量（换机 / 换人只需改这里）

| 变量       | 含义                        | 你机器上的设定（示例，**真实值只写在 `config.local.json`**）                               |
| -------- | ------------------------- | --------------------------------------------------------------------------------- |
| `$SK`    | 本 skill 目录                | clone 后你自己的路径（如 `~/skills/dual-voice-course-video`）；或 `cd` 进 skill 目录用 `$PWD`     |
| `$VC`    | 语音克隆项目（**不在教育项目目录下**）     | 运行前 `export VOICE_CLONE=/path/to/voice_clone`（脚本默认读该环境变量）                         |
| `$H`     | 本节课程目录（**agent 在取向确认 gate 时新建并 `export $H`**，不写死） | `~/AI课程/AI-L1.人类感官vs计算机传感器`（仅示意，你机器自定，非固定）                       |
| `$H/视频课` | 本节全部产物                    | script / index_present.html / 素材 / 成片 / 封面                                        |
| `$W`     | 临时工作目录                    | `/tmp/<课名>`（音频、standalone、shots、成片）                                               |
| 模板       | 蜡笔手绘风视觉基准（封面/课件统一）        | `$SK/assets/templates/crayon/preview.html`                                        |
| 竖版课件模板   | 竖屏课件视觉基准（1080×1440 单栏大字号） | `$SK/assets/templates/crayon/preview_portrait.html`                               |
| 竖版封面模板   | 视频号封面固定模板（1080×1260 对决版式） | `$SK/assets/templates/crayon/封面模板_竖版视频号_1080x1260.html`                           |

环境变量可覆盖（**优先级高于配置文件**，适合临时覆盖）：`VOICE_CLONE` / `CHROME_BIN` / `FFMPEG` / `SYS_PY` / `TEACHER_NAME` / `FAREWELL_WAV`。**机器相关路径与音色的权威来源是 `config.local.json`**（由 `config.example.json` 复制而来，已 gitignore），详见下方「本地配置」。

## 本地配置（配置与代码分离，禁止写死路径/模型名）

所有机器相关路径、音色模型名、`gap`、老师显示名只在一处定义，脚本/流水线不再写死。共两层：

- **环境配置（skill 级，机器相关）**：复制 `config.example.json` → `config.local.json`（gitignore），改 `paths.voice_clone_dir` 等为你的机器值。`voices` 节是 **preflight 自检源 + 路由 B 参考**；⚠️ 路由 A（GPT-SoVITS）的**实际音色定义在 `$VC/dialog2audio.py`**（`EXPS` + 情绪路由表）——换音色先改那边，再同步 config 让自检跟上（后续可把路由 A 接到 config 消除双源）。
- **课程配置（每课一份，`$H/视频课/course_config.json`）**：取向确认 gate 时由 agent 写入，记录本课 `orientation` / `teacher_display_name` / `gap` / `keywords`；阶段 2/3/4/5 直接读它。
- **老师显示名**（默认 `老师`，纯展示层）：优先级 `TEACHER_NAME` 环境变量 > 课程配置 > 环境配置；**只改 HTML 气泡署名，剧本角色行固定 `老师：` 不变**（TTS 路由只认角色标签判声线，兼容细节见 pipeline.md 阶段 3）。
- **合并优先级**：环境变量 > 课程配置 > 环境配置（`scripts/load_config.py` 统一加载；CLI `python3 load_config.py --get paths.voice_clone_dir` / `--course "$H/视频课" --json`）。

> 设计对齐最佳实践：skill 只持判断/命令/模板，所有可变参数外置为配置；换机只改 `config.local.json`，不再碰任何脚本里的绝对路径。

## 脚本清单（全部参数化，可直接跑）

| 脚本                              | 作用                                                                                          | 用法                                                                            |
| ------------------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `scripts/preflight.sh`          | 环境自检（18 项）                                                                                  | `bash preflight.sh [课目录]`                                                     |
| `scripts/verify_steps.py`       | 校验 HTML 帧/步 == 剧本帧/句                                                                        | `python3 verify_steps.py <课目录>`                                               |
| `scripts/load_config.py`        | 统一配置加载器（合并 环境变量>课程config>config.local.json；CLI `--get/--json/--course`）                     | `python3 load_config.py --get paths.voice_clone_dir`                          |
| `scripts/dialog2audio_local.py` | 本地 TTS 兜底配音（macOS `say`，纯标准库零依赖；输出合同与路由 A 一致，阶段 4 无缝衔接）                                     | 见阶段 3 路由 B                                                                    |
| `scripts/make_standalone.py`    | 生成 `standalone.html` + `schedule.json`（时间轴驱动）                                               | 见阶段 4a                                                                        |
| `scripts/capture.js`            | 按时间轴逐区间截图（自动找 puppeteer-core）                                                               | `node capture.js <工作目录>`                                                      |
| `scripts/capture_anim.js`       | **动效版成片渲染**（--animate 配套；逐 1/30s tick 驱动 applyTime + getAnimations 虚拟时钟同步，JPEG 落盘，约 10 帧/s） | `node capture_anim.js <standalone.html> <帧目录> [总秒数]`                          |
| `scripts/qc_frames.js`          | 放映版逐帧 QC：全展开截图 + 溢出检测 + 可选音频探测/逐 step 图                                                     | `node qc_frames.js <index_present.html> <出图目录> [audioId] [step帧号]`            |
| `scripts/make_video.sh`         | **阶段 4c 静帧版合成（唯一实测不失步路径）**：校验 → 硬链接帧序列 → CFR 编码 → 二次混流 → 自检                      | `bash make_video.sh <工作目录> <输出.mp4> [merged音频]`                            |
| `scripts/make_intro.sh`         | **蜡笔风动态片头一键生成**（令牌替换 → capture_anim 渲染 → 配乐 → 编码；默认 5.0s，模板见 assets/intro/，说明见「阶段 4d」）      | `bash make_intro.sh --out out.mp4 --title "第 3 课 · <em>事物的特征</em>"`           |
| `scripts/make_intro_music.py`   | 片头配乐生成（100BPM / C 大调 I–V/V–vi–IV 琶音+铺底+沙锤+混响；参数化、可复现；需 numpy+scipy）                         | `python make_intro_music.py --out m.wav --duration 5.0 [--bpm 100] [--bells]` |
| `scripts/make_intro_outro.py`   | 片尾三段式拼接（**尺寸自适应**，正片不再被压扁；动态片头已由 make_intro.sh 取代，其 16:9 片头卡资产为 legacy）                | `python make_intro_outro.py --video 正片.mp4 --out 成片.mp4`                  |
| `scripts/make_clips.py`         | **可选 · 阶段 6 切片引流**（发布运营工具，非五阶段主线）：按帧号切 30–60s 短视频 + 钩子卡                              | `python make_clips.py --final 成片.mp4 --report report.json --outdir clips/ --clips clips.json` |
| `scripts/read_config.js` + `scripts/pptr.js` | node 侧内部模块：统一配置读取（env>config.local>example）/ 共享 puppeteer 加载器（被 3 个截图脚本引用）                  | 被引用，不单独调用                                                          |

## 核心约束与铁律（⛔ 门禁是硬停止，不是建议）

**严禁一次性自动连跑到底。** 本流水线有 5 个【确认 gate】：阶段 1（剧本）、阶段 2（放映版）、阶段 3（双音色音频）、阶段 5（封面），阶段 4 含 4a/4b/4c 子确认点。**每个 gate 是硬停止（hard stop）**：完成该阶段产出后，**必须停下**，主动用 `AskUserQuestion` 工具把本阶段产出 + 一个「确认后再继续」的问题抛给用户，实实在在等到用户回"继续/确认"或具体修改意见，才能开始下一阶段的任何文件写入或命令。台词、构图、音色/语速、对齐精度、封面取向都主观且易错，连跑会浪费大量算力（双音色合成一节 40 句约 8–15 分钟，重跑成本高）。

**⛔ 门禁三铁律（任何模式/任何会话都生效，不可绕过）：**

1. **不得用"简短汇报一句"代替用户确认**——汇报完不自动继续，必须等用户明确说"继续 / 可以 / 确认"才算过 gate。
2. **不得为"高效/省事"合并或跳过 gate**——每个 gate 单独停下，逐关过。
3. **用户没回之前，不得预读下一阶段、不得创建/改写下一阶段产物文件、不得跑下一阶段命令**。这三点违反任一条都算流程事故。

**无人值守场景（另一个 agent 代跑，且用户已明确授权连跑）**：才把确认 gate 换成「产物落盘 + 自检脚本通过 + 记录到工作日志」连续推进阶段 1→4；但**阶段 5 封面取向、以及成片视听验收必须留给人**。未获明确授权时，一律逐 gate 停下等人。

### 技术铁律（违反必翻车）

1. 顺序不能乱：稿 → 画面 → 声音 → 整合 → 封面。**不要**音频先于 HTML，也**不要**成片前先做封面。
2. 帧内 `.step` 数 == 台词句数（`verify_steps.py` 把关），否则对齐错位。
3. 任何一次改稿/改画面，重跑 `verify_steps.py` + `qc_frames.js`。
4. 超长 base64 只走 Python 脚本改，不用编辑器硬改。
5. 音频必须 `--no-cleanup`；成片音轨必须二次混流。
6. 每阶段产物落 `$H/视频课/` 或 `$W`；真照片素材另存 `$H/视频课/素材_*.jpg` 供 PPT/教材复用。

### 取向确认 · 横版 / 竖版【确认 gate】

用户创建课程时**先问取向，再开工**。取向决定阶段 2 用哪个模板、阶段 4 按什么尺寸渲染、阶段 5 封面要不要补竖版。

> ⛔ **取向门禁（硬停止）**：开工前**停下**，用 `AskUserQuestion` 问用户本节课要「横版 / 竖版 / 横竖都要」，并把选择记进本课（例如 `$H/视频课/取向.txt` 写 `landscape` / `portrait` / `both`）。用户没回前不得写剧本以外的任何产物。

- **横版**（默认）：1920×1080，课堂投影 / 横版视频号封面，阶段 2 用 `preview.html`，产出 `index_present.html`
- **竖版**：1080×1440，视频号/抖音/Shorts 原生竖视频，阶段 2 用 `preview_portrait.html`（单栏大字号版式），产出 `index_present_portrait.html`
- **横竖都要**：同一内容两套，阶段 2 出 `index_present.html` + `index_present_portrait.html`；阶段 3 音频**只合成一次**；阶段 4 两套各按尺寸渲染、复用同一份音频；阶段 5 封面横竖都出
- 尺寸全自动：`make_standalone.py` 从源 `#stageWrap` 读尺寸（1920×1080 / 1080×1440），`capture*.js` / `qc_frames.js` 跟着源尺寸走，不用手填宽高；竖版 `.stage-frame` 结构、`.step` 数 == 台词句数 的约束与横版完全一致

### 阶段 1 · 演讲稿【确认 gate】

产出 `$H/视频课/script_v2_dialog.txt`（驱动 HTML 帧结构与 TTS 的唯一真相源）。

格式（被 `verify_steps.py` 解析）：

```
【第 1 帧】开场 · 主题
老师："请你仔细观察，它是什么颜色的？"[[1.2]]
学生："红色！"[[0.8]]
```

- 帧头 `【第 N 帧】`；角色行老师固定 `老师：`（通用角色标签，TTS 只认它判声线；显示名是纯展示层、只改 HTML 气泡，见「本地配置」），学生 `学生：`，台词用中文引号包裹
- `[[n]]` = 该句之后的静音秒数（学生思考/做动作的时间）
- 学生行含「哭脸/笑脸」→ 不念词，只留静音（做表情）
- **一帧内的角色行数 = 该帧 HTML 的 `.step` 数**（后续 1:1 对齐的唯一依据）
- 引号内不要出现 `"` `"`，否则解析器会漏句
- 认知铁律：专业名词和术语（触觉/化学/味觉传感器）只由老师说出，学生只答日常词（摄像头、麦克风）；不确定的用"不知道！/猜不到！"再让老师揭示
- 视频介质适配：用户原始内容若按线下课堂设计（分组讨论/上台演示/实物传递/动手实验），须改写为视频可呈现形式——① 线下不可执行的动作（闻花、摸木头）改成"看屏幕 + 听真实音频 + 回想"；② 动手/互动环节用 `[[1.5]]` 停顿留操作时间代替"当场做"，不强制出画面，并加一句"小朋友在家也可以跟着做"的邀请


**产出**：`script_v2_dialog.txt`。

> ⛔ **阶段 1 门禁（硬停止）**：写完后**停下**，用 `AskUserQuestion` 向用户完整呈现剧本（或分帧摘要）+「台词 / 角色分配 / 分帧节奏是否确认？确认后进入阶段 2 做放映版」。在用户明确回"继续"前，**不得开始阶段 2 的 `index_present.html` 任何写入或 preflight 之外的命令**。用户要改就按意见改完，再二次确认。

### 阶段 2 · HTML 放映版【确认 gate】

基于确认稿做 `$H/视频课/index_present.html`：每帧一个 `.stage-frame`（`id="f01"…`），帧内 `.step` 块数 = 该帧台词句数，可选 `data-hide-at="N"`（到第 N 步淡出）。

- **取向分支**：取向为「横版」→ 基于 `$SK/assets/templates/crayon/preview.html` 做 `index_present.html`；「竖版」→ 基于 `preview_portrait.html`（1080×1440 单栏大字号版式）做 `index_present_portrait.html`；「横竖都要」→ 两套都做（同一剧本，版式各自适配）。竖版 `.stage-frame` 结构、`.step` 数 == 台词句数 的约束与横版完全一致；竖版用 `mo.css` 的 `anim-fade-rise`/`anim-pop` 等 class 与横版同一套动效判断逻辑（见下方「动效」）。
- 视觉**必须**沿用蜡笔手绘风模板：手绘抖动笔触（SVG `feTurbulence`+`feDisplacementMap`）、纸纹噪点、蜡笔 blob、贴纸卡、圆体-简/娃娃体-简；固定品牌要素（左上徽章「AI 启蒙 · 第 X 课」+ 适合年级；底部「小贤 AI 青少年教育 · 体系课程 · 实训项目 · AI 创造力」）
- 图标优先纯 SVG 简笔画；**用户给了真照片时**，做成「拍立得贴纸」（方裁→360px→JPEG q86→base64 内嵌，118px + 28px 标签，单文件自包含）。完整 base64 配方代码与压高度参数见 `references/pipeline.md` 阶段 2
- **改超长 base64 行时不要用 Edit 工具**（字符串匹配必然失败），用 Python `str.replace` / 正则
- 真照片贴纸（118px + 标签）比原 SVG 图标高，卡片易顶到页脚：`vis` 的 `top` 压到 566 左右，`nm` 44、`tx` 一句话不折行

**动效（按内容判断，不从上一课复制，也不用为差异化而差异化）**

- 做每帧时**先看这帧在讲什么课型**，再挑动效——不是照抄上一课的套路，也不是为了和上一课不同而硬换。判断决策表在 `$SK/assets/templates/anim-snippets/README.md`「二、按课型选动效」，必须按它走。
- 三类课型速记：① 讲概念 / 介绍特征 → `pop` 或 `blurIn`+`kenburns`；② 互动游戏 / 问答 → `slam`+`glow`+`elastic`；③ 对比 A vs B → `flyLeft`+`flyRight` 或 `iris`/`blinds`/`wipe` 转场。流程步骤用 `fadeRise`+数字步进+顺序 `glow`；总结回顾用 `fadeRise`+`slam`+`charsIn`。有真实截图/照片 → 一律 `blurIn`+`kenburns` 满幅，代码只做解释标注。
- 节奏铁律（避免被读成"翻页式 PPT"）：运动是「停住 → 猛一下 → 停住」的**脉冲节奏**，不是匀速慢推 / 全员呼吸。入场用 `MO.PULSE`（快推 `punch 0.28s`、横移 `pan 0.30s`、砸入 `slam 0.17s`）；一帧只让一个主体动，其余静止。
- 片段库两个用法：纯 CSS 课件 → `<link rel="stylesheet" href="assets/templates/anim-snippets/mo.css">` 加 class（`anim-pop`/`anim-slam`/`anim-fade-rise`/`anim-blur-in`/`anim-iris-in`/`anim-fly-left`/`anim-fly-right` + 持续 `idle-kenburns`/`idle-glow`/`idle-float`）；GSAP 时间轴渲染成片 → 引入 `mo.gsap.js` 后 `MO.entrance(tl, sel, kind, at)` / `MO.transition(tl, kind, at)` / `MO.continuous(sel, kind)`。无 GSAP 时自动降级为 CSS class，不报错。
- 开工前 / 交付前各对照一遍 `$SK/assets/templates/anim-snippets/README.md`「三、六种做坏方式」（翻页式PPT、照搬上一课、没有具体的物、死背景空画面、有真实素材却用代码画、一眼AI味拼贴）。
- 做完一支新课，效果好的动效组合**回流**进 README 第二节决策表；动效坑写进 `references/known_pitfalls.md`（§5 动效）。同课型用同一套动效完全正确，只有课型变了才换。

**QC 循环（必做）**：命令见 `references/pipeline.md` 阶段 2（`qc_frames.js`）。逐帧看 png，溢出帧（`⚠️ 溢出帧`）按上述贴纸/卡片压高度手法修，直到 `✅ 全部帧无溢出` + 目视构图 OK。

**确认点**：用户看 HTML 预览/截图确认构图与节奏；同时 `verify_steps.py` 必须通过。

> ⛔ **阶段 2 门禁（硬停止）**：QC 通过（`✅ 全部帧无溢出` + `verify_steps.py` 通过）后**停下**，用 `AskUserQuestion` 向用户呈现 HTML 预览/截图 +「构图与节奏是否确认？确认后进入阶段 3 合成双音色音频」。用户明确回"继续"前，**不得跑阶段 3 的音频合成命令**（路由 A 的 `dialog2audio.py` / 路由 B 的 `dialog2audio_local.py`）。

### 阶段 3 · 双音色音频【确认 gate】

**两条路由，preflight 自动判定，产物合同完全一致**（frame_NN.wav / \_merged.wav 帧间 0.9s / report.json 顶层 list），阶段 4 无需任何改动：

**路由 A · GPT-SoVITS 克隆音色（首选，音质最佳）** —— 在 `$VC` 下跑（脚本内 `EXPS` 自动取最新权重，参考音在 `dataset/` 下，**不要手写权重路径**）。命令见 `references/pipeline.md` 阶段 3 路由 A（`dialog2audio.py --script … --outdir $W/audio --no-cleanup`，`--only 4,7,11` 重跑坏句）。

- 音色**实际定义在 `$VC/dialog2audio.py`**（老师 `xiaoxian_v2` 定稿 e20/e12_s288、含 v2 情绪路由表；学生 `macie`）；`config.local.json` 的 `voices` 节是 preflight 自检源——换音色先改 dialog2audio.py，再同步 config
- 参数：`--takes 3`、`--temperature 1.0`、`--gap 0.4`（帧内行距）、`--device cpu`（默认，稳）
- **必须加 `--no-cleanup`**：否则逐句 `os.remove` 会触发沙箱 bulk-delete 守卫，进程被杀（EXIT=1）
- 产出：`$W/audio/frame_NN.wav`（每帧）、`$W/audio/_merged.wav`（全课，帧间 0.9s）、**`$W/audio/report.json`**（每帧 `units:[{speaker,text,pause,dur,start}]`，`start` 是句内起始秒 —— 阶段 4 直接吃它）
- 单句成句判定：`split_units` 的过滤阈值必须是 `>=1`（旧 `>=4` 会整句丢掉「苹果！」这类 1–3 字童声，表现为"学生句消失"而不是报错）

**确认点**：抽查 2–3 帧（师生都在、短句没丢、语速自然）后进阶段 4。

> ⛔ **阶段 3 门禁（硬停止）**：音频合成完**停下**，用 `AskUserQuestion` 向用户呈现抽查 2–3 帧音频（师生都在、短句没丢、语速自然）+「音频是否确认？确认后进入阶段 4 音画整合」。用户明确回"继续"前，**不得跑阶段 4 的 `make_standalone.py` / `capture.js` / `capture_anim.js` / 合成命令**。

**路由 B · 本地 TTS 兜底（无 GPT-SoVITS 环境时，跨平台）** —— 纯标准库脚本，零第三方依赖，按平台自动选后端。命令见 `references/pipeline.md` 阶段 3 路由 B（`dialog2audio_local.py --script … --outdir $W/audio`，`--only 4,7,11` 重跑坏句）。

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

命令见 `references/pipeline.md` 阶段 4a（`make_standalone.py --present … --report … --gap 0.9 --title …`；`--subtitles`/`--srt`/`--keywords`/`--animate` 等参数同文件）。

- 输出 `standalone.html`（HTML 结构原样、不删任何字符；CSS 复用原 `<style>`；帧/step 显隐由 `applyTime(t)` 数据驱动）+ `schedule.json`（总时长与截图区间）
- **竖版 / 横竖都要**：取向含竖版时，对 `$H/视频课/index_present_portrait.html` 再跑一次同样的 `make_standalone.py`（加 `--present ...portrait` `--out $W/standalone_portrait.html` `--sched $W/schedule_portrait.json`），尺寸自动按 1080×1440。`--report` 复用同一份 `report.json`（阶段 3 音频只合成一次，两套共用）。后续 `capture*.js` / `qc_frames.js` 各自指向 `_portrait` 的那份 standalone 即可，无需改任何宽高参数
- **`--gap` 必须填 0.9**：`dialog2audio.py` 合并 `_merged.wav` 时帧间是硬编码 0.9s（旧文档写 0.25 是坑，会使末帧漂移近 10s、音画严重失步）。校验：standalone 总时长 ≈ `_merged.wav` 时长（±0.1s）
- `--subtitles`：底部蜡笔风字幕条（师生分色：老师深蓝/学生粉，`--keywords` 黄底橙字高亮，长句按标点自动切 ≤30 字短条并按字数比例分配时间），字幕条放在页脚上方（bottom:104px），**只改 standalone，不动 index_present.html，不影响老师上课用放映版**；同时会修掉"帧间空隙画面内容清空闪烁"（step 延续到 gend）
- `--srt`：同步产出 .srt（给剪辑/平台备用）
- 脚本兼容两种 frame 写法（`class` 在前或 `id` 在前），会自动剥掉内嵌 `<audio>`（成片音轨由 ffmpeg 单独混，留着会重复出声）
- `bind_delays`：step 数 == 对话行数时 1:1 锚定每句 `start`；不相等则帧内均匀分布 —— **绝不能让所有 step 堆在 0s**（画面会提前泄题）
- ⚠️ 不要用 `scripts/compose.py`（hyperframes 中间格式，脆正则 + 240s 流式限制，已弃用，仅存档）

*子确认点*：本地打开 `standalone.html` 拖 `applyTime(t)` 或试截 1 帧，确认每个 step 出现时刻与音频语义对得上。

**4b 逐帧截图**

命令见 `references/pipeline.md` 阶段 4b（`capture.js $W`，读 `schedule.json` 输出 `shots/` + `durations.txt`；动效版用 `capture_anim.js`）。

*子确认点*：抽查 3–5 张（含贴纸/真照片/字幕的帧），确认无空白帧、无字体回退。

**4c 合成（已脚本化，勿手打 ffmpeg）**

静帧版直接跑 `bash $SK/scripts/make_video.sh "$W" "$H/视频课/<课程名>_双音色成片.mp4"`——内部 = 硬链接帧序列 → 严格 CFR 30fps 编码 → 二次混流 → 自检打印。动效版（capture_anim 产物，均匀 30fps）命令不同：见 `references/pipeline.md` 阶段 4c。

- **三种错误路径全部实测音画失步，禁止手打**：`-framerate` 直读 shots / concat demuxer / concat 上加 `-r`·`fps` 滤镜。唯一可靠 = 硬链接帧序列（脚本已封装）
- concat PNG 时不能同加 `-c:a`（被静默忽略）；音轨必须第二步 `-c:v copy` 混流
- 画面内有真实音效（如内嵌儿歌）须额外混层；体积/轻量版参数；**【必做】无声版归档清单与换音色重合成路径**：均见 `references/pipeline.md` 阶段 4c
- QC：与 schedule 抽时刻比对 shot（PSNR ≥45dB）；音频抽查首/中/尾

*子确认点*：用户预览成片，确认音画同步、字幕、双音色清晰；可另出轻量版。

**4d 片头与片尾（蜡笔风动态片头，2026-10-08 定稿）**

**片头不带念稿**——只做品牌与价值主张，不念课程内容（用户 2026-10-08 定案）。5.0s / 30fps / 1920×1080。

**片头命令**（见 `references/pipeline.md` 阶段 4d）：`bash $SK/scripts/make_intro.sh --out "$H/视频课/片头_5s.mp4" --title "第 3 课 · <em>事物的特征</em>"`

- **视觉**：令牌与课件 `index_present.html` 完全一致（奶油纸底 / 点阵 / 噪点 / 藏青描边 / 圆体-简 / 娃娃体-简），末帧擦成纯奶油底，**与正片第 1 帧无缝**
- **节奏**（照 L2 `sensingandunderstanding.mp4` 前 5 秒）：logo 飞入 0.02–0.85 → 品牌名 0.60–1.25 → 主张句 1.05–1.70 → **配套三件套逐个飞入** 1.62–2.66（左/下/右三个方向、窗口交叠）→ 收尾句 2.62–3.12 → 课名贴纸 3.05–3.85 → 蜡笔擦除 4.35–4.95
- **文案全走 CLI**：`--brand / --claim / --lead / --k1 / --k2 / --k3 / --noplug / --title`（`--title` 里的 `<em>关键词</em>` 自动加黄色高亮胶囊）
- **时长**改 `--total`：模板里所有时间点都过 `K(x)=x*TOTAL/5.0` 等比缩放，不用改 JS
- **配乐** `scripts/make_intro_music.py`：100BPM、C 大调 I–V/V–vi–IV 琶音 + 铺底 pad + 轻沙锤 + 合成混响；**默认不加卡点铃铛**（用户定案，见 references/known_pitfalls.md §6）
- **资产**：`assets/intro/`（模板 + 官网 logo + README）

*确认 gate*：出片后抽 4 帧 + 完整听一遍。**片头定稿后再开正片渲染**——换音色/改文案会改时轴，画面得重渲（L3 一次 9664 帧 ≈ 12–15 分钟）。

> ⛔ **4d 门禁（硬停止）**：片头渲染完**停下**，用 `AskUserQuestion` 向用户呈现抽 4 帧 + 请完整听一遍 +「片头是否定稿？定稿后再开正片渲染」。用户明确回"继续"前，**不得开始正片（阶段 4a→4c）的渲染**。

> 片尾用 `scripts/make_intro_outro.py` 的三段式（**尺寸自适应**，正片不再被强制压成 1920×1080；其 16:9 片头卡资产为 legacy，动态片头已由 make_intro.sh 取代）+ 告别词按正片同倍速 atempo；  
> 三段拼接（片头 / 正片 / 片尾）的采样率坑见 `references/known_pitfalls.md` §6。

### 阶段 5 · 配套封面【确认 gate】

**双模板固定制（2026-10-02 用户定稿，每课固定出这两张，不再每课另选版式）**：

| 模板      | 画布        | 模板文件（勿改结构）                                                        | 用途            |
| ------- | --------- | ----------------------------------------------------------------- | ------------- |
| 横版课件封面  | 1920×1080 | `$TPL/preview.html`（第 1 页「封面」slide）                               | 课件/公众号/横版视频封面 |
| 竖版视频号封面 | 1080×1260 | `$TPL/封面模板_竖版视频号_1080x1260.html`（对决版式：左贴纸卡 + VS 圆 + 右贴纸卡 + 娃娃体批注） | 视频号竖版封面       |

- `$TPL = $SK/assets/templates/crayon`；换课只改竖版模板里 3 个【替换】点：① 徽章课号+年级 ② 主/副标题（mark.y 黄底 / mark.b 蓝底）③ 左右贴纸卡 SVG+cap 与手写批注；品牌行「小贤 AI 青少年教育 · 体系课程 · 实训项目 · AI 创造力」与徽章位置**固定不改**
- 风格铁律：蜡笔手绘风（wobble 滤镜 + 噪点纸纹 + 圆体-简/娃娃体-简 + 蜡笔色板），**不得回退旧平铺米底低对比版**
- ⚠️ 视频号信息流按 **1:1 居中裁切**（1080×1260 → 取 y=90~1170）：标题/徽章/品牌行必须全部压进该安全区（品牌行 bottom:118px 即 y≈1112，已验证在内）。自查：`ffmpeg -y -i 封面.png -vf crop=1080:1080:0:90 -q:v 3 自查_1比1裁切.png`
- 工作流：**先出 HTML 风格稿（用模板填内容）→ 用户确认 → 再 puppeteer 截图出图**；截图 1080×1260 viewport + `document.fonts.ready` + 300ms 等待
- **产出**：`$H/视频课/封面/封面_横版_*.png`（1920×1080）+ `封面_竖版_*.png`（1080×1260）+ `自查_1比1裁切_*.png`

> ⛔ **阶段 5 门禁（硬停止）**：横版/竖版 HTML 风格稿填内容后**停下**，用 `AskUserQuestion` 向用户确认取向（主副标题 / 贴纸卡 / 批注）后再 puppeteer 截图出图；出图后用户要调就改 HTML 重截，不反复猜。成片视听验收也必须留给人，不得自动定稿发布。

- 实际案例（L1）：`AI-L1/视频课/封面/封面A_对决版.html|png`（即竖版模板的填内容版）；横版案例见 preview.html 第 1 页

## 参考文档

- `references/pipeline.md`：**逐阶段完整命令与文件结构（how）**——`make_standalone`/`capture`/`ffmpeg`/`dialog2audio` 参数、`report.json` schema、贴纸 base64 配方、文件树都在这里；执行某阶段时按需读取。流程/格式/写作要点/门禁的权威在本文（SKILL.md）
- `references/known_pitfalls.md`：通用踩坑清单（按根因/主题归类，**与课程内容无关**，动手前必读）。涵盖：吞字类（孤立拉丁字母、破折号单字短片段、童声短句）、双音色 TTS、时间轴对齐、HTML 排版版式、CSS 动效、响度/混流(loudnorm)、切片引流、合成编码、QC、封面、教学设计通用原则、路由 B 跨平台兜底。
- `references/example_schedule.json`：`schedule.json` 结构示例
