# 流水线实现细节（逐阶段命令与文件结构）

通用变量：
- `$SK` = 本 skill 目录（clone 后你自己的路径；或 `cd` 进 skill 目录用 `$PWD`）
- `$VC` = 语音克隆项目（外部依赖，运行前 `export VOICE_CLONE=/path/to/voice_clone`，脚本默认读 `$VOICE_CLONE` 环境变量）
- `$H` = 课程目录（例：`…/Grades K-2. Introduction to AI Course/AI-L1. Human Senses vs Computer Sensors`）
- `$W` = 工作目录（例：`/tmp/l1`；放音频、standalone、shots、成片）

制作顺序：**① 写稿 → ② 做 HTML → ③ 生成音频 → ④ 整合出片 → ⑤ 配套封面**（顺序不可换）。

---

## 阶段 1 · 写演讲稿

产出 `$H/视频课/script_v2_dialog.txt`（单文件即"真相源"：帧结构与台词同时驱动 HTML 与 TTS）。

格式：
```
【第 1 帧】开场 · 主题
小贤老师："同学们好，我是小贤老师。……"[[1.5]]
学生："红色！"[[1.2]]
```
**约束（三处必须一致）**：一帧内的角色行数 = 该帧 HTML 的 `.step` 数 = 该帧 TTS 句子数。
**校验**：阶段 1、2 各做完都跑一次
```bash
python3 $SK/scripts/verify_steps.py "$H"
```

写作要点（K-2 已验证）：
- 术语只由老师说出，学生只答日常词；不确定的用"不知道！/猜不到！"→ 老师揭示
- 线下不可执行的动作（闻花、摸木头）改成"看屏幕 + 听真实音频 + 回想"
- 视频化的动手环节用 `[[1.5]]` 停顿留操作时间，不强制出画面

---

## 阶段 2 · 做 HTML 放映版

产出 `$H/视频课/index_present.html`：每帧 `<div class="stage-frame" id="fNN">…</div>`，
帧内 `.step` 块数 = 该帧台词句数，可选 `data-hide-at="N"`。

视觉：沿用 `$SK/assets/templates/crayon/preview.html`（手绘抖动 SVG 滤镜、纸纹噪点、蜡笔 blob、贴纸卡、圆体-简/娃娃体-简、固定品牌要素）。

**真照片替换配方**（用户给图时）：
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

**QC 循环**：
```bash
node $SK/scripts/qc_frames.js "$H/视频课/index_present.html" /tmp/qc_x <audioId> <帧号>
/opt/homebrew/bin/python3 $SK/scripts/contact_sheet.py /tmp/qc_x /tmp/预览_总览.png 4 4
```
看到 `✅ 全部帧无溢出` + 目视构图 OK 为止；有 `⚠️ 溢出帧` 就按上面的配方压高度。

---

## 阶段 3 · 双音色 TTS

```bash
cd "$VC"
PYTORCH_ENABLE_MPS_FALLBACK=1 ./venv/bin/python ./dialog2audio.py \
  --script "$H/视频课/script_v2_dialog.txt" --outdir "$W/audio" --no-cleanup
# 坏句重跑： --only 4,7,11
```
- 老师 `xiaoxian`（ref `dataset/xiaoxian/wavs/xiaoxian_0029.wav`）、学生 `macie`（ref `dataset/macie/wavs/macie_13.wav`）
- 权重自动取最新 epoch；参数 `--takes 3 --temperature 1.0 --gap 0.4 --device cpu`
- **必加 `--no-cleanup`**（否则被 bulk-delete 守卫杀）

产物：
```
$W/audio/
  f1_老师_0.wav …            # 逐句（--no-cleanup 时保留，方便单独替换坏句）
  frame_01.wav …             # 每帧拼接（帧内行距 --gap 0.4s）
  _merged.wav                # 全课拼接（帧间 0.9s 静音）→ 阶段4混音用这个
  report.json                # 时间轴：{frame, dur, units:[{speaker,text,pause,dur,start}]}
```
`report.json` 结构：
```json
{"frame": 1, "dur": 12.34,
 "units": [{"speaker":"老师","text":"…","pause":1.5,"dur":3.1,"start":0.0},
           {"speaker":"学生","text":"红色！","pause":1.2,"dur":1.0,"start":3.5}]}
```
`units[].start` 是**帧内**起始秒 —— 阶段 4 的 1:1 对齐直接吃它。

---

## 阶段 4 · 整合出片

### 4a 时间轴对齐
```bash
python3 $SK/scripts/make_standalone.py \
  --present "$H/视频课/index_present.html" --report "$W/audio/report.json" \
  --out "$W/standalone.html" --sched "$W/schedule.json" --gap 0.25 --title "<课程名>"
```
产出：
- `standalone.html`：frame 原样嵌套 + 末尾注入 `var HF_DATA={f01:{gstart,gend,steps:[{ap,di}]}}` 与 `applyTime(t)`；默认剥掉内嵌 `<audio>`
- `schedule.json`：`{total, intervals:[{t,dur}]}`（只在视觉变化边界截一张）
- 自检打印：`div 不配平(应为空): 无`、`step 总数:`、`总时长`

### 4b 截图
```bash
node $SK/scripts/capture.js "$W"
```
产出 `$W/shots/shot_0000.png …` + `durations.txt`。
抽查：最小 png >32KB（空白帧会 <10KB），随机 diff 相邻帧确认互异。

### 4c 合成（两步法，关键）
```bash
ffmpeg -y -framerate 30 -i "$W/shots/shot_%04d.png" -c:v libx264 -pix_fmt yuv420p -crf 20 -r 30 "$W/video_silent.mp4"
ffmpeg -y -i "$W/video_silent.mp4" -i "$W/audio/_merged.wav" -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k -ar 44100 -ac 2 -shortest "$H/视频课/<课程名>_双音色成片.mp4"
```
QC（PSNR，`crop` 与 `psnr` 分链，且必须对齐同一全局时刻）：
```bash
ffmpeg -y -ss <该截图对应秒> -i 成片.mp4 -frames:v 1 /tmp/ab_a.png
cp "$W/shots/shot_00XX.png" /tmp/ab_b.png
ffmpeg -y -i /tmp/ab_a.png -i /tmp/ab_b.png -filter_complex psnr -f null -   # ≥45dB 合格
```

---

## 阶段 5 · 配套封面

- 视觉沿用已定稿蜡笔风模板；固定要素：logo + 品牌、课程标题（字高占画面 24–30%）、完整 slogan、年级徽章、底部固定行
- 主推 9:16（1080×1920）+ 横版（1920×1080）备用；每课 3 版取向（点题/悬念/对话）
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
  index_present.html          # 阶段2
  素材_*.jpg                  # 阶段2 收集的真照片
  预览_*帧总览.png / 逐步.png  # 阶段2 QC 留档
  <课程名>_双音色成片.mp4      # 阶段4 最终交付
  封面/视频号封面_*.jpg        # 阶段5

$W/                            # 例 /tmp/l1
  audio/  frame_NN.wav  _merged.wav  report.json
  standalone.html  schedule.json
  shots/shot_0000.png …  durations.txt
  video_silent.mp4
```
