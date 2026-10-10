# 流水线实现细节（逐阶段命令与文件结构）

> 本文件是 `SKILL.md` 的**命令与产物参考（how）**。`SKILL.md` 管流程、门禁、判断、格式与写作要点（what/why/when）；本文件只放**可复制命令、参数、schema、配方、文件树**，由 agent 在执行对应阶段时按需读取。
>
> **分工边界（唯一归属，避免漂移）**：剧本格式 / 认知铁律 / 线下→线上写作要点 / 取向（横竖）/ `TEACHER_NAME` 的权威在 `SKILL.md`；本文件只在对应处用「见 SKILL.md 阶段 N」引用，不重复定义。

通用变量：

- `$SK` = 本 skill 目录（clone 后你自己的路径；或 `cd` 进 skill 目录用 `$PWD`）
- `$VC` = 语音克隆项目（外部依赖，运行前 `export VOICE_CLONE=/path/to/voice_clone`，脚本默认读 `$VOICE_CLONE` 环境变量）
- `$H` = 课程目录（**agent 在取向确认 gate 时新建并 `export $H`**；例：`~/AI课程/AI-L1.人类感官vs计算机传感器`，仅示意）
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
```

看到 `✅ 全部帧无溢出` + 逐帧目视 png 构图 OK 为止；有 `⚠️ 溢出帧` 就按上面的配方压高度。竖版把文件名换成 `index_present_portrait.html` 即可。

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

- 音色**实际定义在 `$VC/dialog2audio.py`**（老师 `xiaoxian_v2` 定稿 e20/e12_s288、含 v2 情绪路由；学生 `macie`）；`config.local.json` 的 `voices` 节是 preflight 自检源——换音色先改 dialog2audio.py，再同步 config 让自检跟上。路由 B 按平台自动选后端、师生双音色方案见 `SKILL.md` 阶段 3 路由 B 表
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

### 4c 合成（已脚本化，勿手打 ffmpeg）

**静帧版**（capture.js 产物）直接跑 `make_video.sh`——内部封装了唯一实测不失步的路径（校验数量 → 按 durations.txt 硬链接帧序列 round(dur×30) 次 → 严格 CFR 30fps 编码 → 二次混流音轨 → 自检打印）：

```bash
bash $SK/scripts/make_video.sh "$W" "$H/视频课/<课程名>_双音色成片.mp4"
```

**已实测三种错误路径，全部音画失步，禁止手打**：① `-framerate 30 -i shots/shot_%04d.png` 把每区间当 1/30s；② concat demuxer（-f concat + duration）输出 VFR，时间戳漂移实测 t=50 处错位一个区间；③ 在 concat 输入上加 `-r 30` 或 `fps=30` 滤镜，漂移更大（415s vs 398s）。唯一可靠 = 硬链接帧序列（已在脚本内）。

**动效版**（capture_anim.js 产出 `f%05d.jpg`，本身均匀 30fps，无需硬链接）：

```bash
ffmpeg -y -framerate 30 -i "$W/frames/f%05d.jpg" -c:v libx264 -pix_fmt yuv420p -crf 20 -r 30 "$W/video_anim.mp4"
ffmpeg -y -i "$W/video_anim.mp4" -i "$W/audio/_merged.wav" -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest "$H/视频课/<课程名>_双音色成片.mp4"
```

- **concat PNG 时不能同时加 `-c:a`**（会被静默忽略，成片无音轨）；音轨必须第二步 `-c:v copy` 混流（脚本已按此实现）
- 体积：静态画面 + 纸纹噪点在真实 30fps 下 crf20 约 30MB+（VFR 单帧估算 14–15MB 已不适用）；微信轻量版可 `-crf 26 -vf scale=1280:-2`
- **画面内有真实音效时（如放映版内嵌的儿歌），成片必须额外混一层**：双音色 `_merged.wav` 里只有对白。做法：`ffmpeg -i video_cfr.mp4 -i _merged.wav -i 儿歌.mp3 -filter_complex "[2:a]volume=0.32,adelay=<帧起点ms>|<帧起点ms>[r];[1:a][r]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy ...`（儿歌起点 = 第 2 帧 gstart×1000，可从 schedule.json 算）。别指望放映版内嵌 `<audio>` 出声（standalone 已默认剥掉）
- QC（PSNR，须对齐同一全局时刻）：

```bash
ffmpeg -y -ss <该截图对应秒> -i 成片.mp4 -frames:v 1 /tmp/ab_a.png
cp "$W/shots/shot_00XX.png" /tmp/ab_b.png
ffmpeg -y -i /tmp/ab_a.png -i /tmp/ab_b.png -filter_complex psnr -f null -   # ≥45dB 合格
```

- 与 schedule 抽 3 个时刻比对显示的是哪张 shot；音频抽查首/中/尾
- **【必做】无声版归档（换音色重合成的后悔药，2026-10-03 用户要求）**：成片后立刻把中间产物复制到 `$H/视频课/`，别留在 /tmp（系统会清）：
  - `video_cfr.mp4` → `L*_无声画面版.mp4`（无声、含烧录字幕）
  - `durations.txt` → `时间轴_durations.txt`；`schedule.json` → `时间轴_schedule.json`
  - `$A/report.json` → `音频时长_report.json`（每句真实时长，换音色后对齐用）
  - `standalone.html` → `渲染用_standalone.html`
  - ⚠️ 无声版里字幕时间是按**当前音色**时长烧进画面的：新音色若每句时长变化，直接混流会字幕错位。**正确重合成路径**：新音色跑 dialog2audio → 用新 report.json/durations 重跑 make_standalone → 重截图 → `make_video.sh` → 混流（全链脚本化，仅时长变化无需改画面内容）；无声版视频只用于预览/对比，或新音色时长与旧版几乎一致时直接混流

---

## 阶段 5 · 配套封面

- 视觉沿用已定稿蜡笔风模板；固定要素、双模板（横版 1920×1080 / 竖版视频号 1080×1260）、风格铁律、1:1 裁切安全区：见 `SKILL.md` 阶段 5
- 取向 = both 时横竖封面都出
- 截屏用 `qc_frames.js` 同源的 puppeteer 能力（Chrome + 自动找 puppeteer-core）
- ⚠️ 视频号信息流 **1:1 居中裁切**自查（1080×1260 → 取 y=90~1170）：

```bash
ffmpeg -y -i "$H/视频课/封面/封面_竖版_*.png" -vf crop=1080:1080:0:90 -q:v 3 "$H/视频课/封面/自查_1比1裁切_竖版.png"
```

- 产出（口径与 `SKILL.md` 阶段 5 一致）：`$H/视频课/封面/封面_横版_*.png`（1920×1080）+ `封面_竖版_*.png`（1080×1260）+ `自查_1比1裁切_*.png`

---

## 阶段 6 · 切片引流（可选，发布运营工具，不属于五阶段主线）

从成片按帧号切 30–60s 引流短视频（钩子/对位/预告三型）：

```bash
python3 $SK/scripts/make_clips.py \
  --final "$H/视频课/<课程名>_双音色成片.mp4" \
  --report "$H/视频课/音频时长_report.json" \
  --outdir "$H/视频课/clips" --clips clips.json
```

- `clips.json` 格式见 `scripts/make_clips.py` 文件头注释（帧号取剧本【第 N 帧】的 N；`hook` 为 1920×1080 钩子卡 PNG，模板 `assets/clip_cards_template.html`；片尾自动找同目录 `endcard.png`）
- 帧时间换算内置 gap=0.9（与 `_merged.wav` 一致）；报告用阶段 4c 归档的 `音频时长_report.json`
- 实例：L6 切出 3 条（54.6s / 44.9s / 33.3s）+ 切片文案

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
  L*_无声画面版.mp4 / 时间轴_*.txt|json / 音频时长_report.json / 渲染用_standalone.html
                              # 阶段4c 无声版归档（换音色后悔药，必做）
  封面/封面_横版_*.png  封面_竖版_*.png  自查_1比1裁切_*.png   # 阶段5
  clips/*.mp4 + 切片文案      # 阶段6（可选）

$W/                            # 例 /tmp/l1
  audio/  frame_NN.wav  _merged.wav  report.json
  standalone.html  standalone_portrait.html  schedule.json  schedule_portrait.json
  shots/shot_0000.png …  durations.txt
  seq/                         # make_video.sh 硬链接帧序列（可删）
  video_cfr.mp4                # make_video.sh 无声 CFR 中间产物
```
