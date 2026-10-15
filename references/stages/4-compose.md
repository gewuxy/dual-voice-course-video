# 阶段 4 · 音画整合出片（命令与已知失步路径）

顺序 4a 时轴 → 4b 截图 → 4c 合成 → 4d 片头与拼接，**连续执行不中断**；各步自检见下文，**唯一确认点在 4d 末尾**（片头+正片拼完 → 「成片是否确认」，门禁规则见 `SKILL.md` 阶段 4）。

## 4a 时间轴对齐

```bash
python3 $SK/scripts/make_standalone.py \
  --present "$H/视频课/index_present.html" --report "$W/audio/report.json" \
  --out "$W/standalone.html" --sched "$W/schedule.json" --title "<课程名>" --animate
```

- ⛔ **`--animate` 是默认必带项，不是可选参数**：成片一律动效版（虚拟时钟逐帧渲染，HTML 动效完整进片）。只有课件完全无动效**且用户明确要求**才允许去掉它走静帧版——静帧版会把 `.step.on` 后代上的入场动画拍在半路定格整段区间。
- **帧间静音走 config，不是命令行参数**：不传 `--gap`；`frame_gap` 默认 0.9（`config.local.json` 的 `defaults.frame_gap`），与阶段 3 拼 `_merged.wav` 同源。脚本结尾自动与 `_merged.wav` 对账，漂移 >0.15s 报错退出，无需人工校验。
- **GSAP 轨（源页用到 GSAP 时）**：`make_standalone` 会自动**内联**内置 gsap（`assets/vendor/`，离线）+ `mo.gsap.js` + 页面里 `<script id="mo-timeline">` 那段脚本，并在生成的 `applyTime(t)` 末尾调 `MO.seek(t)`——抓帧时 GSAP 时间轴被冻结在 t，与 CSS 轨同步进片。**时间轴必须用 `MO.timeline()` 建、代码必须写在 `id="mo-timeline"` 的 `<script>` 里**，否则不会带进 standalone（生成时会打 ⚠️）。强制开关：`--gsap` / `--no-gsap`（默认自动检测）。
- **竖版 / 横竖都要**：把 4a 命令的三处路径加 `_portrait`（`index_present_portrait.html` / `standalone_portrait.html` / `schedule_portrait.json`）再跑一次；尺寸自动 1080×1440，`--report` 复用同一份；后续 `capture*.js`、`qc_frames.js` 同样指向 `_portrait` 那份
- 其它参数：`--subtitles`（蜡笔风字幕条，师生分色；分句上限、样式与机制见 `known_pitfalls.md` §8）、`--srt`、`--keywords`（**一般不用传**，词表唯一权威是 `course_config.json` 的 `subtitle_keywords`，横竖版共用；实际生效参数见 `视频课/build_log.jsonl`）
- 脚本兼容两种 frame 写法（`class` 在前或 `id` 在前），自动剥掉内嵌 `<audio>`（成片音轨由 ffmpeg 单独混，留着会重复出声）
- `bind_delays`：step 数 == 对话行数时 1:1 锚定每句 `start`；不相等则帧内均匀分布并打印提示
- ⚠️ 不要用 `scripts/compose.py`（hyperframes 中间格式，脆正则 + 240s 流式限制，已弃用，仅存档）

产出：

- `standalone.html`：frame 原样嵌套 + 末尾注入 `var HF_DATA={f01:{gstart,gend,steps:[{ap,di}]}}` 与 `applyTime(t)`
- `schedule.json`：`{total, intervals:[{t,dur}]}`（只在视觉变化边界截一张）
- 自检打印：`div 不配平(应为空): 无`、`step 总数:`、`总时长`

**自检（不停）**：本地打开 `standalone.html` 拖 `applyTime(t)`，确认每个 step 的出现时刻与音频语义对得上；不对就回 4a 重生成，不要带疑问往下走。

## 4b 截图

**成片一律动效版（默认，无需询问）**：4a 已带 `--animate`，此处直接：

```bash
node $SK/scripts/capture_anim.js "$W/standalone.html" "$W/frames" [总秒数]
```

（逐 1/30s tick 驱动 `applyTime` + `getAnimations` 虚拟时钟，JPEG 落盘，约 15–25 帧/s，7 分钟片 ≈ 1.4 万帧 ≈ 10–20 分钟。）
**先看磁盘**：单版帧序列约 1.3GB（`capture_anim.js` 的 JPEG `quality` 82 时；调高会近倍数增长），横竖两版别同时存——**一版截完就编码，然后删帧**（`rm -rf $W/frames`）再截另一版。4a 后抽中间帧确认动画在播：任选一句台词边界 +0.1~0.3s 的帧，元素应呈半透明/位移入场中——全就位 = 动画没进片。

**静帧版是显式降级**，仅当课件完全无动效**且用户明确要求**才走；4a 需去掉 `--animate` 重生成：

```bash
node $SK/scripts/capture.js "$W"
```

产出 `$W/shots/shot_0000.png …` + `durations.txt`。抽查：最小 png >32KB（空白帧会 <10KB），随机 diff 相邻帧确认互异。

**自检（不停）**：动效版抽查 3–5 张（贴纸 / 真照片 / 字幕各一），无空白帧、无字体回退。

## 4c 合成（已脚本化，勿手打 ffmpeg）

**静帧版**直接跑（内部：校验数量 → 按 `durations.txt` 硬链接帧序列 `round(dur×30)` 次 → 严格 CFR 30fps 编码 → 二次混流 → 自检打印）：

```bash
bash $SK/scripts/make_video.sh "$W" "$H/视频课/<课程名>_双音色成片.mp4"
```

⛔ **禁止手打 ffmpeg**：三条错误路径（PNG 帧率、concat demuxer + duration、concat 再加 `-r`/`fps`）都会音画失步，**唯一可靠 = 硬链接帧序列**（证据见 `known_pitfalls.md` §8）。

**动效版**（`f%05d.jpg` 本身均匀 30fps，无需硬链接）。

（帧间硬切，不做转场；能力边界与注入方式见 `anim-snippets/README.md` §五）

```bash
ffmpeg -y -framerate 30 -i "$W/frames/f%05d.jpg" -c:v libx264 -pix_fmt yuv420p -crf 20 -r 30 "$W/video_anim.mp4"
ffmpeg -y -i "$W/video_anim.mp4" -i "$W/audio/_merged.wav" -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest "$H/视频课/<课程名>_双音色成片.mp4"
```

- **concat PNG 时不能同时加 `-c:a`**（会被静默忽略，成片无音轨）；音轨必须第二步 `-c:v copy` 混流
- 体积：静态画面 + 纸纹噪点在真实 30fps 下 crf20 约 30MB+；微信轻量版可 `-crf 26 -vf scale=1280:-2`
**可选：音效层**——`_merged.wav` 里只有对白。画面事件需要声音强调时（笑声、雷声、环境音、内嵌儿歌），在 4c 混流时叠加音效：

- **素材**：通用音效放 `$SK/assets/sfx/`（`<名>.wav`）；课程专属素材放课程目录。放映版内嵌 `<audio>` 不会出声（standalone 已默认剥掉），必须走混流
- **落位（自动）**：跑 `make_sfx.py`，输入阶段 1 确认的 `sfx_plan.txt`，自动输出时刻表与混流命令：

```bash
python3 $SK/scripts/make_sfx.py --script "$H/视频课/script_v2_dialog.txt" \
  --plan "$H/视频课/sfx_plan.txt" --audio "$W/音频_v2_125" \
  --sfx-dir "$SK/assets/sfx" --intro 7.5 --out "$H/视频课/音效时刻.txt"
```

  工具自动对齐：帧起点读 `report.json`、帧内细切后合并到台词行数、表情行跳过、台词前缀校验（不符即 `exit 1`）。**必须对最终采用的变速版本音频跑**（做法与实测见 `positive-patterns.md`）。
- **混流**（多音效，在 4c 第二步混流命令上加输入与链）：

```bash
ffmpeg -i video_cfr.mp4 -i _merged.wav -i "$SK/assets/sfx/笑.wav" -i 雷.wav \
  -filter_complex "[2:a]volume=0.85,adelay=41400|41400[s1];[3:a]volume=0.85,adelay=62400|62400[s2];[1:a][s1][s2]amix=inputs=3:duration=first:normalize=0[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest 成片.mp4
```

  adelay 毫秒按**成片时间轴**（含片头时 = 正片秒 + 7500）；音量：内容型音效 0.85（必须听清），氛围型 0.32
- **联动**：时刻按最终采用的变速倍率时间轴计算；换倍率或换音色重合成后，音效时刻整体重测，并随最终混流重新叠加
- **试听备选**： 生成带播放器的试听页（自动抓 Mixkit 各分类候选，含【在用】标记），用户在页上选编号后转 wav 入库
- **换音效零重合成**：TTS 音频、视频渲染、字幕烧录都不受影响——换掉 `assets/sfx/` 里同名 wav（或改 plan 音效名）→ 重跑 `make_sfx.py`（秒级）→ 重跑最后一步混流（`-c:v copy` 视频直拷，只编码音轨，分钟内）。试听阶段可先只混音频（`_merged.wav` + 音效，不挂视频）快速审听，满意再出完整成片
- QC（PSNR，须对齐同一全局时刻）。阈值按管线分：**PNG 静帧管线 ≥45dB**；动效管线（`capture_anim.js` 落 JPEG → crf20 两段有损）明显低于此，**以该脚本当前 quality 实测为准，不要照 45dB 追**。

```bash
ffmpeg -y -ss <该截图对应秒> -i 成片.mp4 -frames:v 1 /tmp/ab_a.png
cp "$W/shots/shot_00XX.png" /tmp/ab_b.png
ffmpeg -y -i /tmp/ab_a.png -i /tmp/ab_b.png -filter_complex psnr -f null -   # ≥45dB 合格
```

### 【必做】无声版归档（换音色重合成的后悔药）

成片后立刻把中间产物复制到 `$H/视频课/`，别留在 /tmp（系统会清）：

- `video_cfr.mp4` → `L*_无声画面版.mp4`（无声、含烧录字幕）
- `durations.txt` → `时间轴_durations.txt`；`schedule.json` → `时间轴_schedule.json`
- `$W/audio/report.json` → `音频时长_report.json`
- `standalone.html` → `渲染用_standalone.html`

⚠️ 无声版里字幕时间是按**当前音色**时长烧进画面的：新音色若每句时长变化，直接混流会字幕错位。
**正确重合成路径**：新音色跑 dialog2audio → 用新 `report.json`/durations 重跑 `make_standalone` → 重截图 → `make_video.sh` → 混流（全链脚本化，仅时长变化无需改画面内容）。无声版只用于预览/对比，或新音色时长与旧版几乎一致时直接混流。

## 4d 片头拼接

**片头无念稿**：只有配乐（`make_intro_music.py`），不要把 TTS 台词塞进片头——片头是品牌展示，不是课程内容。

**动态片头一键生成**（默认 7.5s / 30fps / 1920×1080）：

```bash
bash $SK/scripts/make_intro.sh --out "$H/视频课/片头_5s.mp4" --title "第 3 课 · <em>事物的特征</em>"
```

- 文案全走 CLI：`--brand / --claim / --lead / --k1 / --k2 / --k3 / --noplug / --title`（`--title` 里的 `<em>关键词</em>` 自动加黄色高亮胶囊）
- 时长改 `--total`：模板内所有时间点过 `K(x)=x*TOTAL/7.5` 等比缩放，不用改 JS
- **片头已定稿**：出片头只跑上面的命令，不要改模板与配乐参数（模板 `intro_crayon_template.html`、配乐器 `make_intro_music.py`、`logo.svg` 官网原件均在 `assets/style-packs/crayon/intro/`）
- **竖版片头**：加 `--portrait` 出 1080×1440 片头（同一套 4 拍时间轴/令牌），**两段尺寸必须同向**——横版片头配横版正片、竖版片头配竖版正片，然后走下面同一套 concat（`-r 30 -video_track_timescale 15360 -ar 48000`）：
  ```bash
  bash $SK/scripts/make_intro.sh --portrait --out "$H/视频课/片头_竖版.mp4" --title "第 9 课 · <em>推理 · 算法</em>"
  ```
- **配乐前置**：跑 `make_intro.sh` 前先 `export VOICE_CLONE=<voice_clone 目录>`（脚本自动用其 venv）或 `export MUSIC_PY=<带 numpy+scipy 的 python>`；帧已渲完时可加 `--work <上次 work 目录>` 复用，不重渲。
- 配乐：`python3 $SK/scripts/make_intro_music.py --out m.wav --duration 7.5 [--bpm 100] [--bells]`（默认不加卡点铃铛）

**片头与正片拼接**：两段编码参数必须统一（30fps + video_track_timescale 15360 + 48kHz），否则 `concat -c copy` 静默截断/失步（见 known_pitfalls §6）：

```bash
# 1) 两段统一编码（片头出自 make_intro.sh 已对齐，正片 4c 音轨是 44.1kHz 必须重编码）
ffmpeg -y -i 片头.mp4 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p" \
  -r 30 -video_track_timescale 15360 -c:v libx264 -crf 20 -preset medium \
  -ar 48000 -ac 2 -c:a aac -b:a 192k /tmp/intro_u.mp4
ffmpeg -y -i 正片.mp4 -vf "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p" \
  -r 30 -video_track_timescale 15360 -c:v libx264 -crf 20 -preset medium \
  -ar 48000 -ac 2 -c:a aac -b:a 192k /tmp/body_u.mp4
# 2) 无损拼接 + loudnorm + faststart
printf "file '/tmp/intro_u.mp4'\nfile '/tmp/body_u.mp4'\n" > /tmp/list.txt
ffmpeg -y -f concat -safe 0 -i /tmp/list.txt -c copy /tmp/joined.mp4
ffmpeg -y -i /tmp/joined.mp4 -af "loudnorm=I=-16:TP=-1.5:LRA=11" -ar 48000 -ac 2 \
  -c:v copy -c:a aac -b:a 192k -movflags +faststart 成片.mp4
```

**自检（不停）**：抽 4 帧看片头画面 + 完整听一遍配乐；画面/配乐有问题就重渲染片头，不要带疑问往下走。

⛔ **阶段 4 唯一确认点（停下 + `AskUserQuestion`）**：片头与正片拼接完成后，交**完整成片**请用户看一遍 → 问「成片是否确认」（音画同步、字幕、双音色、片头衔接一并确认）。取向=both 时两版各自确认或一并确认。
