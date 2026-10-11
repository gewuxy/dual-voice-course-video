# 阶段 3 · 双音色音频（命令与产物 schema）

**两条路由，preflight 自动判定，产物合同完全一致**（`frame_NN.wav` / `_merged.wav` 帧间 0.9s / `report.json` 顶层 list），阶段 4 无需任何改动。路由选择原则与确认点：见 `SKILL.md` 阶段 3。

## 路由 A · GPT-SoVITS 克隆音色（首选）

在 `$VC` 下跑（脚本内 `EXPS` 自动取最新权重，参考音在 `dataset/` 下，**不要手写权重路径**）：

```bash
cd "$VC"
PYTORCH_ENABLE_MPS_FALLBACK=1 ./venv/bin/python ./dialog2audio.py \
  --script "$H/视频课/script_v2_dialog.txt" --outdir $W/audio --no-cleanup
# 坏句单独重跑： --only 4,7,11
```

## 路由 B · 本地 TTS 兜底（跨平台，零第三方依赖）

```bash
python3 $SK/scripts/dialog2audio_local.py --script "$H/视频课/script_v2_dialog.txt" --outdir $W/audio
# 坏句重跑： --only 4,7,11 （CLI 与路由 A 兼容）
```

| 平台 | 后端 | 师生双音色方案 |
| --- | --- | --- |
| macOS | `say`（系统自带） | 老师 Tingting（婷婷）/ 学生 Meijia（美佳 + `[[pbas +110]][[rate +15]]` 抬调） |
| Windows | PowerShell + System.Speech(SAPI)（零安装） | 自动枚举中文语音包（Huihui/Yaoyao…），师生取两个不同声音；只有一个时 SSML `pitch +25%` 抬调区分学生 |
| Linux | `espeak-ng`（需安装，音质最差） | cmn 普通话，学生 pitch 抬高 |

- 声音覆盖：环境变量 `SAY_TEACHER` / `SAY_STUDENT`（全平台通用）
- 统一输出 32000 Hz Int16 单声道（后端采样率不符时自动 ffmpeg 重采样）
- Windows 中文语音包缺失时：设置 → 时间和语言 → 语言和区域 → 添加「中文(简体)」并勾选语音
- Windows / Linux 上其余阶段需用环境变量指定 `CHROME_BIN` / `FFMPEG`

## 变速（可选，倍率 = 阶段 3 gate 用户决策点）

```bash
cd "$VC" && ./venv/bin/python speed_up.py --src "$W/audio" --speed 1.25
mv "$W/audio_fast" "$W/音频_v2_125"    # 命名惯例：音频_v2_<倍率去掉点>，如 音频_v2_125 / 音频_v2_11
```

- 帧内语速 ×倍速（atempo 保音高），**帧间 0.9s 间隙不变速**（保留场景切换呼吸感）
- 产物 `report.json` 的帧长已按实测 wav 回写（脚本内置 2b 步骤；atempo 编码每帧比理论短 ~24ms，不回写会累计漂移撞 4a 的 0.15s 对账红线）
- **阶段 4 之后一律读变速后的 `report.json` 与 `_merged.wav`**，读原速的会音画错位
- **倍率不是技术默认值**：K-2 受众（5-8 岁）偏慢，1.0x 原速也完全可交；同倍率给用户出 2–3 帧对比样本再定

## 参数与坑（两条路由通用）

- 音色**实际定义在 `$VC/dialog2audio.py`**（老师 `xiaoxian_v2` 定稿 e20/e12_s288、含 v2 情绪路由；学生 `macie`）；`config.local.json` 的 `voices` 节是 preflight 自检源——换音色先改 `dialog2audio.py`，再同步 config 让自检跟上
- 参数：`--takes 3 --temperature 1.0 --gap 0.4 --device cpu`（`--gap` 是**帧内行距** 0.4，与帧间静音 `frame_gap` 0.9 是两个东西，别混）
- **必加 `--no-cleanup`**（否则逐句 `os.remove` 触发沙箱 bulk-delete 守卫，进程被杀 EXIT=1）
- 单句成句判定阈值必须 `>=1`（旧 `>=4` 会整句丢掉「苹果！」这类 1–3 字童声，表现为"学生句消失"而非报错）
- 角色标签：剧本固定 `老师：`/`学生：`（TTS 只认标签判声线）。路由 A 同时认旧剧本 `小贤老师：`（L1–L7 旧课无需改剧本）；路由 B 认 `老师：`/`小贤老师：`/自定义 `TEACHER_NAME`。`report.json` 的 `speaker` 统一为通用 `老师`/`学生`，字幕不与显示名耦合
- 动作行（哭脸/笑脸）静音、`[[n]]` 停顿、"AI→诶爱"清洗：两条路由行为一致

## 产物（`--no-cleanup` 时保留逐句，方便单独替换坏句）

```
$W/audio/
  f1_老师_0.wav …            # 逐句
  frame_01.wav …             # 每帧拼接（帧内行距 --gap 0.4s）
  _merged.wav                # 全课拼接（帧间 0.9s 静音）→ 阶段4混音用这个
  report.json                # 时间轴
```

`report.json`：

```json
{"frame": 1, "dur": 12.34,
 "units": [{"speaker":"老师","text":"…","pause":1.5,"dur":3.1,"start":0.0},
           {"speaker":"学生","text":"红色！","pause":1.2,"dur":1.0,"start":3.5}]}
```

`units[].start` 是**帧内**起始秒——阶段 4 的 1:1 对齐直接吃它。路由 A/B 字段逐字一致 → 阶段 4/5 全部命令原样可用。
