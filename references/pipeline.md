# 流水线实现细节（逐阶段命令与文件结构）

> 本文件是 `SKILL.md` 的**命令与产物参考（how）**。`SKILL.md` 管流程、门禁、判断、格式与写作要点（what/why/when）；本文件只放**可复制命令、参数、schema、配方、文件树**，由 agent 在执行对应阶段时按需读取。
>
> **分工边界（唯一归属，避免漂移）**：剧本格式 / 认知铁律 / 线下→线上写作要点 / 取向（横竖）/ `TEACHER_NAME` 的权威在 `SKILL.md`；本文件只在对应处用「见 SKILL.md 阶段 N」引用，不重复定义。

通用变量：

- `$SK` = 本 skill 目录（clone 后你自己的路径；或 `cd` 进 skill 目录用 `$PWD`）
- `$VC` = 语音克隆项目（外部依赖，运行前 `export VOICE_CLONE=/path/to/voice_clone`，脚本默认读 `$VOICE_CLONE` 环境变量）
- `$H` = 课程目录（例：`…/Grades K-2. Introduction to AI Course/AI-L1. Human Senses vs Computer Sensors`）
- `$W` = 工作目录（例：`/tmp/l1`；放音频、standalone、shots、成片）

制作顺序：**① 写稿 → ② 做 HTML → ③ 生成音频 → ④ 整合出片 → ⑤ 配套封面**（顺序不可换，见 `SKILL.md`「关键铁律」）。

---

## 阶段 1 · 写演讲稿

**格式（`【第 N 帧】` / 角色行 / `[[n]]` 含义）、认知铁律、线下→线上改写、`.step` 数 == 台词句数 约束、老师显示名 `TEACHER_NAME`**：全部见 `SKILL.md` 阶段 1 与「老师显示名可配置」（本文件不重复，避免两处漂移）。

**校验（阶段 1、2 各做完都跑一次）**：

```bash
python3 $SK/scripts/verify_steps.py "$H"
```

打印每帧 `.step` 数 vs 该帧台词句数，不一致即报错（这是阶段 4 能 1:1 对齐的前提）。

---

## 阶段 2 · 做 HTML 放映版

产出 `$H/视频课/index_present.html`：每帧 `<div class="stage-frame" id="fNN">…</div>`，帧内 `.step` 块数 = 该帧台词句数，可选 `data-hide-at="N"`。

- **取向含竖版时另产 `index_present_portrait.html`**（同 `.stage-frame` 结构、1080×1440，版式见 `SKILL.md` 取向确认）；本阶段所有命令对竖版只差源文件名，尺寸自动按 1080×1440。
- 视觉与版式规则、动效判断（按课型选片段）：见 `SKILL.md` 阶段 2。

**真照片替换配方（用户给图时，命令级细节）**：

```python
# 1) 方裁对准主体（有红圈就对准红圈中心）→ 2) 缩 360px → 3) JPEG q86 → 4) base64 内嵌
<div class="sticker" style="padding:8px;transform:rotate(±2.5deg);position:relative">
  <img src="data:image/jpeg;base64,__B64__" style="width:118px;height:118px;object-fit:cover;border-radius:10px;display:block">
  <span class="tape"></span>
</div>
<div class="title" style="text-align:center;font-size:28px;margin-top:4px">手机</div>
```

- 卡片紧凑化（否则顶穿页脚）：`vis` 的 `top:566px`、`nm` 44px、`tx` 一句话不折行
- 素材另存 `$H/视频课/素材_<名字>.jpg` 供 PPT/教材复用
- **base64 注入只走 Python replace**，不要用编辑器改那一行

**QC 循环（逐帧溢出检测）**：

```bash
node $SK/scripts/qc_frames.js "$H/视频课/index_present.html" /tmp/qc_x <audioId> <帧号>
python3 $SK/scripts/contact_sheet.py /tmp/qc_x /tmp/预览_总览.png 4 4
```

看到 `✅ 全部帧无溢出` + 目视构图 OK 为止；有 `⚠️ 溢出帧` 就按上面的配方压高度。竖版把文件名换成 `index_present_portrait.html` 即可。

---

## 阶段 3 · 双音色 TTS

**路由 A（GPT-SoVITS 克隆音色，首选，音质最佳）** —— 在 `$VC` 下跑（脚本内 `EXPS` 自动取最新权重，参考音在 `dataset/` 下，**不要手写权重路径**）：

```bash
cd "$VC"
PYTORCH_ENABLE_MPS_FALLBACK=1 ./venv/bin/python ./dialog2audio.py \
  --script "$H/视频课/script_v2_dialog.txt" --outdir $W/audio --no-cleanup
# 坏句单独重跑： --only 4,7,11
```

**路由 B（本地 TTS 兜底，无 GPT-SoVITS 环境时，跨平台零依赖）**：

```bash
python3 $SK/scripts/dialog2audio_local.py --script "$H/视频课/script_v2_dialog.txt" --outdir $W/audio
# 坏句重跑： --only 4,7,11 （CLI 与路由 A 兼容）
```

- 音色见 `config.local.json` 的 `voices` 节（默认 老师 `xiaoxian_v2` 定稿 e20/e12_s288、含 v2 情绪路由；学生 `macie`）；改模型只改配置。路由 B 按平台自动选后端、师生双音色方案见 `SKILL.md` 阶段 3 路由 B 表
- 权重自动取最新 epoch；参数 `--takes 3 --temperature 1.0 --gap 0.4 --device cpu`
- **必加 `--no-cleanup`**（否则逐句 `os.remove` 触发沙箱 bulk-delete 守卫，进程被杀 EXIT=1）
- 单句成句判定阈值必须 `>=1`（旧 `>=4` 会整句丢掉「苹果！」这类 1–3 字童声，表现为"学生句消失"而非报错）

产物（`--no-cleanup` 时保留逐句，方便单独替换坏句）：

```
$W/audio/
  f1_老师_0.wav …            # 逐句
  frame_01.wav …             # 每帧拼接（帧内行距 --gap 0.4s）
  _merged.wav                # 全课拼接（帧间 0.9s 静音）→ 阶段4混音用这个
  report.json                # 时间轴
```

`report.json` 结构：

```json
{"frame": 1, "dur": 12.34,
 "units": [{"speaker":"老师","text":"…","pause":1.5,"dur":3.1,"start":0.0},
           {"speaker":"学生","text":"红色！","pause":1.2,"dur":1.0,"start":3.5}]}
```

`units[].start` 是**帧内**起始秒 —— 阶段 4 的 1:1 对齐直接吃它。`report.json` 顶层为 list，路由 A/B 字段逐字一致 → 阶段 4/5 全部命令原样可用。

---

## 阶段 4 · 整合出片

### 4a 时间轴对齐

```bash
python3 $SK/scripts/make_standalone.py \
  --present "$H/视频课/index_present.html" --report "$W/audio/report.json" \
  --out "$W/standalone.html" --sched "$W/schedule.json" --gap 0.9 --title "<课程名>"
```

- `--gap` 必须 = 0.9（与 `_merged.wav` 帧间硬编码一致；旧文档写 0.25 是坑，会使末帧漂移近 10s、音画严重失步）。校验：standalone 总时长 ≈ `_merged.wav` 时长（±0.1s）
- **竖版 / 横竖都要**：对 `index_present_portrait.html` 再跑一次同样的 `make_standalone.py`（加 `--present …portrait` `--out $W/standalone_portrait.html` `--sched $W/schedule_portrait.json`），尺寸自动按 1080×1440；`--report` 复用同一份 `report.json`（阶段 3 音频只合成一次，两套共用）。后续 `capture*.js` / `qc_frames.js` 各自指向 `_portrait` 那份 standalone 即可，无需改任何宽高参数
- 其它参数（`--subtitles` / `--srt` / `--keywords` / `--animate` 动效版）、`bind_delays` 规则、字幕条位置、弃用 `compose.py` 等：见 `SKILL.md` 阶段 4a

产出：

- `standalone.html`：frame 原样嵌套 + 末尾注入 `var HF_DATA={f01:{gstart,gend,steps:[{ap,di}]}}` 与 `applyTime(t)`；默认剥掉内嵌 `<audio>`
- `schedule.json`：`{total, intervals:[{t,dur}]}`（只在视觉变化边界截一张）
- 自检打印：`div 不配平(应为空): 无`、`step 总数:`、`总时长`

### 4b 截图

```bash
node $SK/scripts/capture.js "$W"
```

产出 `$W/shots/shot_0000.png …` + `durations.txt`。竖版指向 `standalone_portrait.html` 同理。抽查：最小 png >32KB（空白帧会 <10KB），随机 diff 相邻帧确认互异。动效版用 `capture_anim.js`（逐 1/30s tick 驱动 `applyTime` + 虚拟时钟，JPEG 落盘，约 10 帧/s），见 `SKILL.md` 阶段 4a 说明。

### 4c 合成（两步法，关键）

```bash
ffmpeg -y -framerate 30 -i "$W/shots/shot_%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 20 -r 30 "$W/video_silent.mp4"
ffmpeg -y -i "$W/video_silent.mp4" -i "$W/audio/_merged.wav" -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest "$H/视频课/<课程名>_双音色成片.mp4"
```

- 静帧版须先按 30fps **硬链接帧序列**（区间时长不同，禁止 `-framerate` 直读 shots）：脚本见 `SKILL.md` 阶段 4c；三种错误路径（直接 `-framerate 30 -i shots` / concat demuxer VFR / 加 `-r 30`）全部会音画失步，唯一可靠是硬链接帧序列
- QC（PSNR，须对齐同一全局时刻）：

```bash
ffmpeg -y -ss <该截图对应秒> -i 成片.mp4 -frames:v 1 /tmp/ab_a.png
cp "$W/shots/shot_00XX.png" /tmp/ab_b.png
ffmpeg -y -i /tmp/ab_a.png -i /tmp/ab_b.png -filter_complex psnr -f null -   # ≥45dB 合格
```

- 真实音效混层（双音色 `_merged.wav` 只有对白）、无声版归档（换音色后悔药）、体积/轻量版、concat PNG 不能同加 `-c:a` 等坑：见 `SKILL.md` 阶段 4c

---

## 阶段 5 · 配套封面

- 视觉沿用已定稿蜡笔风模板；固定要素、双模板（横版 1920×1080 / 竖版视频号 1080×1260）、风格铁律、1:1 裁切安全区：见 `SKILL.md` 阶段 5
- 取向 = both 时横竖封面都出
- 截屏用 `qc_frames.js` 同源的 puppeteer 能力（Chrome + 自动找 puppeteer-core）
- ⚠️ 视频号信息流 1:1 居中裁切自查：

```bash
ffmpeg -y -i 封面.jpg -vf crop=1080:1080:0:420 -q:v 3 预览_信息流裁切.jpg
```

- 产出：`$H/视频课/封面/视频号封面_*.jpg` + `预览_信息流裁切_*.jpg`

---

## 文件结构总览

```
$H/视频课/
  script_v2_dialog.txt        # 阶段1
  index_present.html          # 阶段2（横版）
  index_present_portrait.html # 阶段2（竖版，取向含竖版时）
  素材_*.jpg                  # 阶段2 收集的真照片
  预览_*帧总览.png / 逐步.png  # 阶段2 QC 留档
  <课程名>_双音色成片.mp4      # 阶段4 最终交付
  封面/视频号封面_*.jpg        # 阶段5

$W/                            # 例 /tmp/l1
  audio/  frame_NN.wav  _merged.wav  report.json
  standalone.html  standalone_portrait.html  schedule.json  schedule_portrait.json
  shots/shot_0000.png …  durations.txt
  video_silent.mp4
```
