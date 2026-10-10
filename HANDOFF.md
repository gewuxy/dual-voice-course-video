# HANDOFF · K2 视频课生产管线交接文档

> 给接手的 agent（Codex / 其他会话）：读完本文件即可继续开发，无需追问历史。
> 最后更新：2026-10-08

## 一、这是什么

「dual-voice-course-video」skill：把 K-2 AI 启蒙课的 HTML 课件批量转成**双音色（老师小贤 + 学生 Macie）讲解视频**的完整流水线，另含切片引流、片头片尾、双封面等发布物料生产。

- 课程项目根目录：（外部，你自己放置课程的位置，如 `…/Grades K-2. Introduction to AI Course/`）
- 每课视频目录：`AI-L<N> <课名>/视频课/`（含 `script_v2_dialog.txt` 台词稿、`build_l<N>.py` 课件动效、`audio_v2*/`、成片 mp4）
- 音色克隆工程：（外部依赖 `VOICE_CLONE`，GPT-SoVITS v2；含 GB 级权重，不进 git）— 运行前 `export VOICE_CLONE=/path/to/voice_clone`

## 二、五阶段管线（每课全量产出流程）

1. **稿**：`script_v2_dialog.txt`（格式：`【第N帧】老师：…[[前停]] / 学生：…[[后停]]`）
2. **画面**：`build_l<N>.py` 生成课件 HTML（动效库见 references/known_pitfalls.md §5）
3. **声音**：`voice_clone/dialog2audio.py` 按句路由情绪 ref 合成双音色 → `audio_v2/`（帧音频 + report.json）
4. **整合**：`scripts/make_standalone.py`（报告→分镜 HTML）→ 用 SKILL.md 阶段 4c 的 ffmpeg 命令混流（loudnorm -16 LUFS + faststart 必加；`compose.py` 已弃用，勿用）
5. **封面**：双封面模板（横版 1920×1080 + 竖版视频号 1080×1260），另出 1:1 裁切自查图

**扩展阶段**：
- **切片**（阶段6）：`scripts/make_clips.py` + `assets/clip_cards_template.html`，钩子/对位/预告三型
- **片头（属第 4 步「整合」的子步骤 4d，不是独立阶段）**：`scripts/make_intro.sh` + `assets/intro/`（蜡笔风动态片头 5s，2026-10-08 L3 定稿，**不带念稿**）
- **片尾**：`assets/intro_outro/endcard.png` + 告别词（`scripts/make_intro_outro.py` 的三段式仍用于片尾段）

## 三、目录速查

```
dual-voice-course-video/
├── SKILL.md                    # 管线总说明（阶段 1~6）
├── references/known_pitfalls.md # 通用踩坑清单（按根因归类，与课程内容无关），动手前必读
├── references/pipeline.md      # 管线细节
├── scripts/
│   ├── make_standalone.py      # report.json → 分镜 HTML
│   ├── capture_anim.js         # Puppeteer 逐帧截图（需 Chrome）
│   ├── make_clips.py           # 切片生产
│   ├── make_intro.sh           # 蜡笔风动态片头一键生成（2026-10-08 L3 定稿）
│   ├── make_intro_music.py     # 片头配乐生成（可复现；需 numpy+scipy）
│   ├── make_intro_outro.py     # 静态片头卡/片尾卡 + 三段拼接（片头部分已被 make_intro.sh 取代）
│   ├── dialog2audio_local.py / dual_tts_dialog2audio.py  # 旧版合成（保留）
│   └── preflight.sh / qc_frames.js / verify_steps.py     # 质检
└── assets/
    ├── intro/                          # 蜡笔风动态片头（模板 + 官网 logo + README）
    │   ├── intro_crayon_template.html  # 动画本体（令牌化，TOTAL/5.0 等比缩放）
    │   ├── logo.svg                    # 官网 https://xiaoxianai.cc/assets/logo.svg 原件
    │   └── README.md                   # 时间轴 + 已定案约束
    ├── clip_cards_template.html        # 切片钩子卡模板
    └── intro_outro/                    # 片头片尾资产
        ├── 片头卡.html / introcard.png # 独立片头（6.5s，蜡笔风）
        ├── 片尾卡.html / endcard.png   # 收尾卡（5.2s，含下集预告/B端交付行）
        ├── 片头锚句条.html / anchor_strip.png  # 旧叠加式（已弃用，保留备用）
        ├── render_cards.js             # HTML→PNG 渲染（puppeteer-core + 本机 Chrome）
        └── anchor_line.wav             # 锚句配音（v2 音色 8.98s，用前按倍速 atempo）
```

## 四、依赖环境

- **Python**：`$VOICE_CLONE/venv/bin/python`（torch/GPT-SoVITS/librosa 等全在里面；外部依赖，见上方）
- **ffmpeg**：`/opt/homebrew/bin/ffmpeg`（8.1）
- **渲染**：`node` + `puppeteer-core`（npx 缓存）+ `/Applications/Google Chrome.app`（render_cards.js 自动找）
- **ASR 复检**：必须 `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`（本地 whisper，在线校验会被代理 502 挡）
- **合成命令**：加 `PYTORCH_ENABLE_MPS_FALLBACK=1`（M3 兼容）
- **重要**：合成/重训别放后台沙箱跑（后台钩子会杀进程），用前台分段跑

## 五、当前状态（2026-10-08）

1. **音色**：`xiaoxian_v2` 已定稿投产（GPT e20 + SoVITS e12_s288）。情绪 ref 按句路由：提问→004、高兴奋/惊叹→**009**（全库音高上限最高，惊叹类必须用它）、温柔→015、悬念→017、强调→020、默认→021。Macie 学生音色不变。
2. **L3 音频**：v2 音色 + **1.5 倍速**已完成：
   - 原速 `AI-L3 Types of Perception/视频课/audio_v2/`（399.3s，16 帧）
   - 1.5x `audio_v2_fast/`（270.4s）——由 `voice_clone/speed_up.py` 逐帧 atempo 生成
   - **渲染 L3 视频必须读 `audio_v2_fast/report.json`**（时长已等比缩放），否则音画错位
3. **片头（2026-10-08 分屏改版定稿）**：蜡笔风动态片头 **7.5s、4 拍分屏、不带念稿**（参考 SkillStruck/L2 前 5 秒的极简分屏 + 呼吸拍；用户定案「内容太拥挤，课名必须单独一屏」）：拍1 logo 单独居中 → 拍2 logo+品牌名锁定 → 呼吸拍 → 拍3 主张+三件套+收尾句 → 呼吸拍 → 拍4 课名独屏 → 蜡笔擦除接正片。一键：`bash scripts/make_intro.sh --out ... --title "第 3 课 · <em>事物的特征</em>"`（默认 --total 7.5；编码已统一 -ar 48000 与拼接规范一致）。片尾不变：`endcard.png`（含下集预告/交付行）+ 告别词 atempo。

## 六、已知待办（按优先级）

1. ~~BUG｜concat 采样率不一致~~（已修：make_intro.sh 编码统一 -ar 48000；L3 三段拼接实测 334.505s = 段和+0.02s，无膨胀）。`make_intro_outro.py` 仍是旧三段式（内嵌弃用静态片头），**待改 outro-only**；本次 L3 片尾用手工 ffmpeg 生成（endcard 5.2s + 告别词 atempo 1.25，参数 30fps/15360/48k）。
2. ~~L3 正式出片~~（✅ 2026-10-08 完成）：`L3_事物的特征_双音色成片_v2_1.25x.mp4`（334.5s = 片头 7.5 + 正片 321.8 + 片尾 5.2，loudnorm -16 + faststart，23.4MB）。音效三枚按 34.00/55.06/70.62s 重混（volume 0.35 + 2s 截断淡出）；归档含无声版/字幕 srt/schedule/report（均 _v2_125 后缀）。
3. L1~L6 成片后补片头片尾（同款模板批量跑）。
4. L1 三型切片制作；L2~L5 补切片、补响度归一。
5. 视频号私信关键词自动回复还没配（校长/合作/课程/机构 → 合作介绍）。

## 七、给 agent 的操作纪律

- **每条命令保持原子性**：一条命令只做一件事。复杂长命令（多重 `$()` 嵌套、heredoc、多探测）在本项目多次出现回显错乱，拆开跑。
- **写后必验**：Write/Edit 之后用 `cat`/`md5`/`grep` 确认磁盘真实内容，回显仅供参考。
- 大文件大改动优先「整文件重写」而非多次小 Edit。
- 响度纪律：所有混流输出两遍式 `loudnorm=I=-16:TP=-1.5:LRA=11` + `+faststart`。
- 每课结束更新工作日志：（你的 agent 工作日志目录，如 `~/.workbuddy/.../memory/YYYY-MM-DD.md`，追加式）。
