#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验放映版 HTML 的 .step 数 == 演讲稿每帧角色行数（1:1 才能做音画对齐）。

用法：
  python3 verify_steps.py <课目录>
  # 默认读 <课目录>/视频课/script_v2_dialog.txt + <课目录>/视频课/index_present.html

输出：逐帧对照表 + 总计；不一致时列出差异帧并以非 0 退出。
阶段 1/2 任何一次改稿或改画面后都应先跑这个再往下走。
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load_config import teacher_prefixes

# 剧本老师角色标签（通用「老师：」+ 旧「小贤老师：」+ 可选 TEACHER_NAME），统一定义在 load_config
TEACHER_PREFIXES = teacher_prefixes()

H = sys.argv[1] if len(sys.argv) > 1 else "."
SCRIPT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(H, "视频课", "script_v2_dialog.txt")
HTML = sys.argv[3] if len(sys.argv) > 3 else os.path.join(H, "视频课", "index_present.html")

# 角色行：老师（可配置名）或学生；兼容全角/半角冒号
ROLE_RE = re.compile(
    r'^(?:' + "|".join(re.escape(p) for p in TEACHER_PREFIXES) + r'|学生)\s*[:：]\s*'
    r'(?:\[\[(\d+\.?\d*)\]\])?\s*["“]([^"”]+)["”]\s*'
    r'(?:\[\[(\d+\.?\d*)\]\])?\s*$')
FRAME_RE = re.compile(r'^【第\s*(\d+)\s*帧】')

frames, cur = [], None
for ln in open(SCRIPT, encoding="utf-8"):
    ln = ln.rstrip("\n")
    if FRAME_RE.match(ln):
        cur = []; frames.append(cur); continue
    if cur is not None and ROLE_RE.match(ln):
        cur.append(1)
exp = [len(f) for f in frames]

html = open(HTML, encoding="utf-8").read()
counts = [len(re.findall(r'<div class="step"', p))
          for p in re.split(r'<div[^>]*class="[^"]*stage-frame[^"]*"', html)[1:]]

print(f"剧本：{len(exp)} 帧 / {sum(exp)} 句    HTML：{len(counts)} 帧 / {sum(counts)} 步")
diff = []
for i in range(max(len(counts), len(exp))):
    a = counts[i] if i < len(counts) else None
    b = exp[i] if i < len(exp) else None
    flag = "" if a == b else "   <<< 不一致"
    if a != b:
        diff.append((i + 1, a, b))
    print(f"  第{i+1:>2}帧  HTML step={a}  剧本句={b}{flag}")

if len(frames) != len(counts):
    print(f"❌ 帧数不一致：剧本 {len(frames)} / HTML {len(counts)}")
if diff:
    print("❌ 存在不一致帧：", diff)
    sys.exit(1)
print("✅ 逐帧一致（每帧 step 数 = 该帧台词句数），可以做音画对齐")
