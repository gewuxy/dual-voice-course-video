# 阶段索引与通用约定（how 层入口）

> 本目录是 `SKILL.md` 的**命令与产物参考（how）**。分工边界（唯一归属，避免漂移）：
> `SKILL.md` = 判断 / 门禁 / 路由 / 红线（what/why/when）；本目录 = 可复制命令、参数、schema、配方、文件树。
> 两侧都不重复定义对方的内容——`SKILL.md` 只写「见 stages/N.md」，本目录只写「见 SKILL.md 阶段 N」。

## 命令里的变量（不手写路径）

| 变量 | 怎么得到 | 说明 |
| --- | --- | --- |
| `$SK` | `cd` 进 skill 目录后取 `$PWD` | **脚本自己知道自己的位置**：`preflight.sh:19` 用 `SKILL_DIR="$(dirname "$SCRIPT_DIR")"` 推导，模板路径也由此拼出（`:40`） |
| `$VC` / `FFMPEG` / `SYS_PY` / `CHROME_BIN` | `python3 $SK/scripts/load_config.py --get paths.ffmpeg` | 机器相关值只认 `config.local.json` + 环境变量，**禁止在文档或命令里写死** |
| `$H` | 取向确认 gate 时新建并 `export H="<课目录>"` | 运行时用户输入，不是配置 |
| `$W` | `export W=/tmp/$(basename "$H" \| tr ' ' '_')` | 派生工作目录（音频 / standalone / shots / 成片） |

优先级：环境变量 > 课程配置（`course_config.json`）> `config.local.json`。完整合并结果：`load_config.py --json`。

制作顺序 **① 写稿 → ② 做 HTML → ③ 生成音频 → ④ 整合出片 → ⑤ 配套封面**（为什么不可换是红线，见 `SKILL.md` 技术铁律）。

## 阶段文件

| 阶段 | 文件 | 含 |
| --- | --- | --- |
| 1 演讲稿 | [1-script.md](1-script.md) | 剧本格式示例、`[[n]]`、校验命令 |
| 2 放映版 | [2-slides.md](2-slides.md) | `.stage-frame` / `.step` 结构、真照片 base64 配方、QC 循环 |
| 3 双音色音频 | [3-audio.md](3-audio.md) | 路由 A/B 命令、平台后端表、参数、产物与 report.json schema |
| 4 整合出片 | [4-compose.md](4-compose.md) | 4a 时轴 / 4b 截图 / 4c 合成 / 4d 片头片尾、三种失步路径、无声版归档 |
| 5 封面 | [5-cover.md](5-cover.md) | 双模板路径、1:1 裁切自查命令、截图参数 |
| 6 切片引流（可选） | [6-clips.md](6-clips.md) | `make_clips.py` 命令与 clips.json |

配套：`../known_pitfalls.md`（踩过的坑，按根因归类）、`../positive-patterns.md`（做对了的做法，开工前看）。

## 文件结构总览

```
$H/视频课/
  course_config.json          # 阶段0建(orientation/teacher_display_name/gap)+阶段1补(subtitle_keywords)；阶段4只读
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
