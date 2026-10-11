#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""suggest_layout.py — 逐帧推荐放映版版式（dialog 对话优先 / visual 图片优先）。

用法：
    python3 suggest_layout.py <剧本.txt>
    python3 suggest_layout.py <剧本.txt> --json out.json

判据（crayon/README.md §5.7）：这帧的核心信息能不能一图概括？
  能一图概括（展示/操作/分类找宝/素材图为主）        → visual
  需要语言定义或推理（问答/概念定义/总结/作业）      → dialog（默认）

注意：台词字数**不决定**版式（dialog 版允许长句），只作信息提示——
选 visual 的帧必须把对话提炼成 ≤15 字短气泡，完整表达交给字幕。

输出选型表，在阶段 2 gate 交用户确认，可逐帧改。
"""
import json
import re
import sys

# 动作/展示信号 → visual
VISUAL_PAT = re.compile(
    r'看看|找找|找一找|找宝|哪一|哪张|放哪|放哪儿|分一分|试一试|猜一猜|猜猜|藏|'
    r'举手|摸一摸|闻一闻|尝一尝|拼一拼|排一排|连一连|圈出来|指出来|演示|变一变')
# 概念定义/推理信号 → dialog
DIALOG_PAT = re.compile(
    r'叫做|就叫|是什么意思|的意思是|为什么|因为|所以|总结|记住|学会|明白了|'
    r'想一想|如果|假如|回家|作业|任务')


def parse_script(text):
    frames = []
    for chunk in re.split(r'\n(?=【第 \d+ 帧】)', text):
        m = re.match(r'\s*【第 (\d+) 帧】\s*([^\n]*)', chunk)
        if not m:
            continue
        lines = re.findall(r'^[^\n：]*?："([^"]*)"', chunk, re.M)
        frames.append({
            'no': int(m.group(1)),
            'title': m.group(2).strip(),
            'lines': lines,
        })
    return frames


def suggest(frame):
    text = ''.join(frame['lines'])
    vis = VISUAL_PAT.findall(text)
    dia = DIALOG_PAT.findall(text)
    questions = text.count('？')
    if len(vis) >= 2 or (len(vis) >= 1 and not dia and not questions):
        layout, why = 'visual', '动作/展示信号×%d（%s）' % (len(vis), '/'.join(sorted(set(vis))[:3]))
    elif len(dia) >= 1 or questions >= 2:
        why = []
        if dia:
            why.append('定义/推理信号×%d（%s）' % (len(dia), '/'.join(sorted(set(dia))[:3])))
        if questions >= 2:
            why.append('问句×%d' % questions)
        layout, why = 'dialog', '；'.join(why)
    else:
        layout, why = 'dialog', '默认（无强信号）'
    return layout, why, {
        'lines': len(frame['lines']),
        'chars': len(text),
        'longest': max((len(l) for l in frame['lines']), default=0),
        'questions': questions,
    }


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    path = args[0]
    out_json = None
    if '--json' in args:
        out_json = args[args.index('--json') + 1]
    frames = parse_script(open(path, encoding='utf-8').read())
    if not frames:
        print('未解析到帧（需【第 N 帧】标题 + 角色："台词" 格式）')
        sys.exit(1)

    rows = []
    print('帧   标题                      推荐     台词字数(句/总/最长)  信号')
    print('-' * 96)
    for f in frames:
        layout, why, stat = suggest(f)
        rows.append({'no': f['no'], 'title': f['title'], 'layout': layout,
                     'why': why, **stat})
        print('f%-2d  %-22s  %-7s  %2d句/%3d字/最长%2d    %s'
              % (f['no'], f['title'][:20], layout, stat['lines'],
                 stat['chars'], stat['longest'], why))
    n_vis = sum(1 for r in rows if r['layout'] == 'visual')
    print('-' * 96)
    print('小计：visual %d 帧 / dialog %d 帧（默认 dialog）' % (n_vis, len(rows) - n_vis))
    print('提示：选 visual 的帧，对话提炼 ≤15 字/句，完整表达交给字幕；画面文字 ≤40 字。')
    print('确认后把每帧写成 <div class="stage-frame" id="fXX" data-layout="…">，'
          '映射：%s' % ', '.join('f%d=%s' % (r['no'], r['layout']) for r in rows))
    if out_json:
        json.dump(rows, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
