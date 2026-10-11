# 阶段 6 · 切片引流（可选，发布运营工具，非五阶段主线）

从成片按帧号切 30–60s 引流短视频（钩子 / 对位 / 预告三型）。何时该切、切几条的判断：见 `SKILL.md` 阶段 6。

```bash
python3 $SK/scripts/make_clips.py \
  --final "$H/视频课/<课程名>_双音色成片.mp4" \
  --report "$H/视频课/音频时长_report.json" \
  --outdir "$H/视频课/clips" --clips clips.json
```

- `clips.json` 格式见 `scripts/make_clips.py` 文件头注释（帧号取剧本【第 N 帧】的 N；`hook` 为 1920×1080 钩子卡 PNG，模板 `assets/clip_cards_template.html`；片尾自动找同目录 `endcard.png`）
- 帧时间换算的 gap 读 `load_config.frame_gap()`（默认 0.9，与 `_merged.wav` 同源）；报告用阶段 4c 归档的 `音频时长_report.json`
- 实例：L6 切出 3 条（54.6s / 44.9s / 33.3s）+ 切片文案
