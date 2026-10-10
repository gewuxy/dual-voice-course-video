#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把截图目录拼成总览图（contact sheet），方便一次性过目全片。

用法：
  /opt/homebrew/bin/python3 contact_sheet.py <shots目录> <输出png> [列数] [行数] [缩略宽] [缩略高]
例：
  /opt/homebrew/bin/python3 contact_sheet.py /tmp/l1_qc /tmp/预览_总览.png 4 4 480 270

说明：需要 PIL。托管版 python 没装 PIL，用系统 python（/opt/homebrew/bin/python3）。
"""
import os, sys
from PIL import Image

d = sys.argv[1] if len(sys.argv) > 1 else "."
out = sys.argv[2] if len(sys.argv) > 2 else "/tmp/contact.png"
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
rows = int(sys.argv[4]) if len(sys.argv) > 4 else 4
tw = int(sys.argv[5]) if len(sys.argv) > 5 else 480
th = int(sys.argv[6]) if len(sys.argv) > 6 else 270
pad = 10

files = sorted(f for f in os.listdir(d) if f.lower().endswith(".png") and not f.startswith("step_"))
if not files:
    sys.exit("目录里没有 png")

n = min(len(files), cols * rows)
W, H = cols * tw + (cols + 1) * pad, rows * th + (rows + 1) * pad
sheet = Image.new("RGB", (W, H), "#DDD6C6")
for i, f in enumerate(files[:n]):
    im = Image.open(os.path.join(d, f)).convert("RGB").resize((tw, th), Image.LANCZOS)
    r, c = divmod(i, cols)
    sheet.paste(im, (pad + c * (tw + pad), pad + r * (th + pad)))
sheet.save(out, quality=90)
print(f"{n} 张 -> {out} {sheet.size}")
