#!/usr/bin/env python3
"""qc_divs — 放映件 div 嵌套平衡机检（排完必跑第三条）。

查每帧：
  1) foot 内嵌深度必须 = 1（.stage-frame 的直接子级）——深度异常说明帧提前闭合，
     foot/后续帧被挤出 stageWrap，foot 会变成视口宽（折行、压 HUD）。
  2) 帧内 div 开闭差必须 = 0（最后一帧允许 -1，即合法的 stageWrap 闭合）。

用法：python3 scripts/qc_divs.py <index_present*.html | preview*.html> ...
退出码：0=全绿，1=有异常（CI/流水线可直接用）。
"""
import re
import sys


def check(path: str) -> bool:
    html = open(path, encoding="utf-8").read()
    frames = list(re.finditer(r'<div class="stage-frame"[^>]*>', html))
    if not frames:
        print(f"❌ {path}: 找不到 stage-frame")
        return False
    bad = []
    for k, m in enumerate(frames):
        fid_m = re.search(r'id="([^"]+)"', m.group(0))
        fid = fid_m.group(1) if fid_m else f"frame#{k}"
        seg = html[m.start(): frames[k + 1].start() if k + 1 < len(frames) else len(html)]
        foot = seg.find('<div class="foot"')
        if foot < 0:
            bad.append(f"{fid}: 帧内无 foot")
            continue
        depth_foot = seg[:foot].count("<div") - seg[:foot].count("</div")
        diff = seg.count("<div") - seg.count("</div")
        last_ok = diff in (0, -1) if k == len(frames) - 1 else diff == 0
        if depth_foot != 1 or not last_ok:
            bad.append(f"{fid}: foot深度={depth_foot}(应1) 开闭差={diff}")
    if bad:
        print(f"❌ {path}:")
        for b in bad:
            print(f"   {b}")
        return False
    print(f"✅ {path}: {len(frames)} 帧嵌套平衡全部正常")
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    ok = all(check(p) for p in sys.argv[1:])
    sys.exit(0 if ok else 1)
