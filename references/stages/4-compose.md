# 阶段 4 · 音画整合出片（命令与已知失步路径）

子确认点顺序 4a 时轴 → 4b 截图 → 4c 合成 → 4d 片头片尾；各确认点与「片头不带念稿」等判断：见 `SKILL.md` 阶段 4。

## 4a 时间轴对齐

```bash
python3 $SK/scripts/make_standalone.py \
  --present "$H/视频课/index_present.html" --report "$W/audio/report.json" \
  --out "$W/standalone.html" --sched "$W/schedule.json" --title "<课程名>"
```

- **帧间静音不是参数**：`make_standalone` 不接 `--gap`，直接读 `load_config.frame_gap()`（默认 0.9，改 `config.local.json` 的 `defaults.frame_gap`），与阶段 3 拼 `_merged.wav` 同源，不可能错配。脚本结尾自动拿 `_merged.wav` 实测对账，漂移 >0.15s 报错退出——不用人工校验。
  （坑史：旧文档教人传 `--gap 0.25`，末帧漂移近 10s。另注 `dialog2audio --gap` 是另一个东西：帧内行距 0.4）
- **竖版 / 横竖都要**：对 `index_present_portrait.html` 再跑一次（加 `--present …portrait` `--out $W/standalone_portrait.html` `--sched $W/schedule_portrait.json`），尺寸自动按 1080×1440；`--report` 复用同一份 `report.json`（阶段 3 音频只合成一次，两套共用）。后续 `capture*.js` / `qc_frames.js` 各自指向 `_portrait` 那份即可
- 其它参数：`--subtitles`（蜡笔风字幕条，师生分色，长句按标点切 ≤30 字；字幕条 bottom:104px，只改 standalone 不动放映版）、`--srt`、--`keywords`（黄底橙字高亮）、`--animate`（动效版）
- 脚本兼容两种 frame 写法（`class` 在前或 `id` 在前），自动剥掉内嵌 `<audio>`（成片音轨由 ffmpeg 单独混，留着会重复出声）
- `bind_delays`：step 数 == 对话行数时 1:1 锚定每句 `start`；不相等则帧内均匀分布并打印提示
- ⚠️ 不要用 `scripts/compose.py`（hyperframes 中间格式，脆正则 + 240s 流式限制，已弃用，仅存档）

产出：

- `standalone.html`：frame 原样嵌套 + 末尾注入 `var HF_DATA={f01:{gstart,gend,steps:[{ap,di}]}}` 与 `applyTime(t)`
- `schedule.json`：`{total, intervals:[{t,dur}]}`（只在视觉变化边界截一张）
- 自检打印：`div 不配平(应为空): 无`、`step 总数:`、`总时长`

## 4b 截图

**管线选型是用户决策点，必须过 gate（L8 教训：静默选静帧版 → 动画全消失被用户打回）**。课件有入场动效（`.step.on` 后代选择器上的 animation）→ 一律动效版（L7 即此管线）；课件纯静态/用户明确要静帧版才走静帧版。

```bash
node $SK/scripts/capture.js "$W"        # 静帧版（需 make_standalone 不加 --animate）
```

产出 `$W/shots/shot_0000.png …` + `durations.txt`。抽查：最小 png >32KB（空白帧会 <10KB），随机 diff 相邻帧确认互异。
动效版用 `capture_anim.js "$W/standalone.html" "$W/frames" [总秒数]`（`make_standalone` 必须加 `--animate`；逐 1/30s tick 驱动 `applyTime` + `getAnimations` 虚拟时钟，JPEG 落盘，约 10 帧/s，7 分钟片 ≈ 1.1 万帧 ≈ 15–20 分钟）。

## 4c 合成（已脚本化，勿手打 ffmpeg）

**静帧版**直接跑（内部：校验数量 → 按 `durations.txt` 硬链接帧序列 `round(dur×30)` 次 → 严格 CFR 30fps 编码 → 二次混流 → 自检打印）：

```bash
bash $SK/scripts/make_video.sh "$W" "$H/视频课/<课程名>_双音色成片.mp4"
```

**已实测三种错误路径，全部音画失步，禁止手打**：① `-framerate 30 -i shots/shot_%04d.png` 把每区间当 1/30s；② concat demuxer（`-f concat` + duration）输出 VFR，时间戳漂移实测 t=50 处错位一个区间；③ 在 concat 输入上加 `-r 30` 或 `fps=30` 滤镜，漂移更大（415s vs 398s）。唯一可靠 = 硬链接帧序列。

**动效版**（`f%05d.jpg` 本身均匀 30fps，无需硬链接）：

```bash
ffmpeg -y -framerate 30 -i "$W/frames/f%05d.jpg" -c:v libx264 -pix_fmt yuv420p -crf 20 -r 30 "$W/video_anim.mp4"
ffmpeg -y -i "$W/video_anim.mp4" -i "$W/audio/_merged.wav" -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest "$H/视频课/<课程名>_双音色成片.mp4"
```

- **concat PNG 时不能同时加 `-c:a`**（会被静默忽略，成片无音轨）；音轨必须第二步 `-c:v copy` 混流
- 体积：静态画面 + 纸纹噪点在真实 30fps 下 crf20 约 30MB+；微信轻量版可 `-crf 26 -vf scale=1280:-2`
- **画面内有真实音效时（如放映版内嵌儿歌），必须额外混一层**：`_merged.wav` 里只有对白

```bash
ffmpeg -i video_cfr.mp4 -i _merged.wav -i 儿歌.mp3 \
  -filter_complex "[2:a]volume=0.32,adelay=<帧起点ms>|<帧起点ms>[r];[1:a][r]amix=inputs=2:duration=first:normalize=0[a]" \
  -map 0:v -map "[a]" -c:v copy …
```

  儿歌起点 = 第 2 帧 `gstart×1000`（从 `schedule.json` 算）。别指望放映版内嵌 `<audio>` 出声（standalone 已默认剥掉）
- QC（PSNR，须对齐同一全局时刻）：

```bash
ffmpeg -y -ss <该截图对应秒> -i 成片.mp4 -frames:v 1 /tmp/ab_a.png
cp "$W/shots/shot_00XX.png" /tmp/ab_b.png
ffmpeg -y -i /tmp/ab_a.png -i /tmp/ab_b.png -filter_complex psnr -f null -   # ≥45dB 合格
```

### 【必做】无声版归档（换音色重合成的后悔药，2026-10-03 用户要求）

成片后立刻把中间产物复制到 `$H/视频课/`，别留在 /tmp（系统会清）：

- `video_cfr.mp4` → `L*_无声画面版.mp4`（无声、含烧录字幕）
- `durations.txt` → `时间轴_durations.txt`；`schedule.json` → `时间轴_schedule.json`
- `$W/audio/report.json` → `音频时长_report.json`
- `standalone.html` → `渲染用_standalone.html`

⚠️ 无声版里字幕时间是按**当前音色**时长烧进画面的：新音色若每句时长变化，直接混流会字幕错位。
**正确重合成路径**：新音色跑 dialog2audio → 用新 `report.json`/durations 重跑 `make_standalone` → 重截图 → `make_video.sh` → 混流（全链脚本化，仅时长变化无需改画面内容）。无声版只用于预览/对比，或新音色时长与旧版几乎一致时直接混流。

## 4d 片头与片尾

**动态片头一键生成**（默认 7.5s / 30fps / 1920×1080）：

```bash
bash $SK/scripts/make_intro.sh --out "$H/视频课/片头_5s.mp4" --title "第 3 课 · <em>事物的特征</em>"
```

- 文案全走 CLI：`--brand / --claim / --lead / --k1 / --k2 / --k3 / --noplug / --title`（`--title` 里的 `<em>关键词</em>` 自动加黄色高亮胶囊）
- 时长改 `--total`：模板内所有时间点过 `K(x)=x*TOTAL/7.5` 等比缩放，不用改 JS
- **节拍表、视觉令牌、配乐参数、设计约束的权威在 `assets/intro/README.md`**（分屏时间轴 / 已定案的设计约束），改之前必读，本文件不复述
- 配乐：`python3 $SK/scripts/make_intro_music.py --out m.wav --duration 7.5 [--bpm 100] [--bells]`（默认不加卡点铃铛，用户定案）

**片尾**：`python3 $SK/scripts/make_intro_outro.py --video 正片.mp4 --out 成片.mp4`（三段式，尺寸自适应，正片不再被压成 1920×1080；告别词按正片同倍速 atempo）。其 16:9 片头卡资产为 legacy，动态片头已由 `make_intro.sh` 取代。三段拼接（片头/正片/片尾）的采样率坑见 `known_pitfalls.md` §6。
