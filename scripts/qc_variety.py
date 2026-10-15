#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qc_variety — 版式母题 / 动效分布统计（**只提示，不阻断**）。

为什么有它：
  visual 帧只有"能不能一图概括"的判据、没有母题清单时，agent 会一路用最省事的那一种
  （典型症状：整支课 6 帧都是同一排方形步骤卡）。这个脚本把"看多了腻"变成可观察的数字，
  在阶段 2 gate 时一眼能看到"9 个 visual 帧里 6 个同母题"。

它统计：
  · 每帧 data-layout（dialog / visual；缺省按 dialog）
  · visual 帧的画面母题（按结构识别：flow / ladder / timeline / cards / photo / fscene / icon）
    —— 也认显式标记 data-scene="steps|compare|…"，有就用它
  · 每帧用到的动效 class（anim-* / idle-*，含自建同名类）
  · 连续同母题最长串、母题占比

提示阈值（不阻断，仅供阶段 2 gate 参考）：
  · 同一母题 > 50% 的 visual 帧
  · 同一母题连续出现 ≥3 帧
  · visual 帧 ≥4 帧却只用了 1 种母题

用法：
  python3 qc_variety.py <index_present.html> [more.html ...] [--strict]
  --strict：有提示时退出码 1（默认恒为 0，不阻断流水线）
"""
import re
import sys
from collections import Counter

FRAME_RE = re.compile(r'<div class="stage-frame"([^>]*)>')
MOTHER = [("flow", r'class="frow'), ("ladder", r'class="lcell'), ("timeline", r'class="tnode'),
          ("photo", r'class="photo'), ("cards", r'class="scard'), ("steps_arrows", r'class="arrow"'),
          ("hero", r'class="hero')]
ANIM_RE = re.compile(r'\b((?:anim|idle)-[a-z-]+|slam-glow)\b')
SCENE_RE = re.compile(r'data-scene="([^"]+)"')


def analyze(path):
    html = open(path, encoding="utf-8").read()
    frames = list(FRAME_RE.finditer(html))
    print("== %s ==" % path)
    print("   帧 %d" % len(frames))
    layouts, mothers, anims = [], [], []
    rows = []
    for k, fm in enumerate(frames):
        seg = html[fm.start(): frames[k + 1].start() if k + 1 < len(frames) else len(html)]
        fid = (re.search(r'id="([^"]+)"', fm.group(0)) or [None, "f%02d" % (k + 1)])[1]
        lm = re.search(r'data-layout="([^"]+)"', fm.group(1))
        layout = lm.group(1) if lm else "dialog"
        sm = SCENE_RE.search(fm.group(1))
        mom = sm.group(1) if sm else next((n for n, pat in MOTHER if re.search(pat, seg)), "text-only")
        as_ = sorted(set(ANIM_RE.findall(seg)))
        layouts.append(layout)
        if layout == "visual":
            mothers.append(mom)
        anims += as_ or (["—"] if layout == "dialog" else [])
        rows.append((fid, layout, mom, ",".join(as_) or "—"))
    print("   版式：visual %d / dialog %d" % (layouts.count("visual"), layouts.count("dialog")))
    print("   %-6s %-8s %-14s %s" % ("帧", "版式", "画面母题", "动效 class"))
    for r in rows:
        print("   %-6s %-8s %-14s %s" % r)
    warn = []
    if mothers:
        c = Counter(mothers)
        print("   visual 母题分布：%s" % "，".join("%s×%d" % (k, v) for k, v in c.most_common()))
        top, n = c.most_common(1)[0]
        if n / len(mothers) > 0.5:
            warn.append("同一母题 %s 占 visual 帧 %d/%d（>50%）——建议按 anim-snippets/README §二 换角色或换母题" % (top, n, len(mothers)))
        if len(mothers) >= 4 and len(c) == 1:
            warn.append("visual 帧 %d 帧只用 1 种母题——视觉重复风险最高" % len(mothers))
        run, best = 1, 1
        for a, b in zip(mothers, mothers[1:]):
            run = run + 1 if a == b else 1
            best = max(best, run)
        if best >= 3:
            warn.append("同一母题连续出现 %d 帧" % best)
    if anims:
        ca = Counter(a for a in anims if a != "—")
        if ca:
            print("   动效分布：%s" % "，".join("%s×%d" % (k, v) for k, v in ca.most_common()))
            top, n = ca.most_common(1)[0]
            if len(ca) == 1 and sum(ca.values()) >= 6:
                warn.append("全片只用 1 种动效（%s）——按课型×角色候选池换一换" % top)
    # visual 帧专项：整体分布好看，也可能"每个 visual 帧内部都只有一种动效"（L9 实翻车）
    vis = [(r[0], [a for a in r[3].split(",") if a and a != "—"]) for r in rows if r[1] == "visual"]
    vis = [(fid, a) for fid, a in vis if a]
    if vis:
        agg = Counter(a for _, lst in vis for a in lst)
        total = sum(agg.values())
        top, n = agg.most_common(1)[0]
        if total >= 6 and n / total > 0.5:
            warn.append("visual 帧内 %s 占 %d/%d（>50%%）——同一角色（如「新长出一格」）换用候选池里的另一个" % (top, n, total))
        doms = [(fid, Counter(lst).most_common(1)[0][0]) for fid, lst in vis]
        run, best = 1, 1
        for i in range(1, len(doms)):
            run = run + 1 if doms[i][1] == doms[i - 1][1] else 1
            best = max(best, run)
        if best >= 3:
            topdom = Counter(d for _, d in doms).most_common(1)[0][0]
            chain = [f for f, d in doms if d == topdom]
            warn.append("连续 %d 个 visual 帧的主变动效相同（%s，涉及 %s）——相邻帧换候选池里的另一个" % (best, topdom, "、".join(chain[:6])))
        single = [fid for fid, lst in vis if len(set(lst)) == 1]
        if len(single) >= max(2, len(vis) // 2):
            warn.append("这些 visual 帧内部只用了 1 种动效：%s——一帧多元素时可混（主图 iris/pop + 卡片 rise 错峰）" % "、".join(single[:6]))
        print("   visual 帧动效覆盖：%d 帧 / %d 种（每帧动效种类：%s）"
              % (len(vis), len(agg), "，".join("%s:%d" % (f, len(set(l))) for f, l in vis)))
    for w in warn:
        print("   ⚠️ %s" % w)
    if not warn:
        print("   ✅ 母题/动效分布未见明显重复")
    return not warn


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    strict = "--strict" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(2)
    ok = all(analyze(p) for p in args)
    sys.exit(1 if (strict and not ok) else 0)
