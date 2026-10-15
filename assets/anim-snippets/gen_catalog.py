#!/usr/bin/env python3
# 生成 anim-snippets/catalog.html：覆盖 mo.css 里全部 class，真实渲染 + 自动循环
# 用法：python3 gen_catalog.py <anim-snippets 目录>
import re, sys, os

DIR = sys.argv[1] if len(sys.argv) > 1 else "."
CARD = 'class="sample card"'; PILL = 'class="sample pill"'; STK = 'class="sample sticker"'

# (class, 名称, 何时用, 时长, 分组, 样例类型, 样例文字)
D = [
 ("anim-pop","pop · 缩放弹出","答案卡、贴纸、重点词出现（带过冲）",".50s","入场 · 弹出 / 砸落",CARD,"答案 B"),
 ("anim-slam","slam · 砸入","金句、大数字、主词落定（猛一下回弹）",".42s","入场 · 弹出 / 砸落",CARD,"特征！"),
 ("anim-stamp","stamp · 盖章","√ / 确认 / 结论落定（又快又硬，带一点歪）",".34s","入场 · 弹出 / 砸落",PILL,"√ 就这样"),
 ("anim-drop-in","drop-in · 落下回弹","把一格或一枚贴纸放上去、归位",".52s","入场 · 弹出 / 砸落",CARD,"第 3 步"),
 ("anim-zoom-out","zoom-out · 收拢聚焦","强调已经在场上的元素（镜头收回来）",".48s","入场 · 弹出 / 砸落",CARD,"看这里"),
 ("anim-swing-in","swing-in · 摆动落定","挂着的贴纸或招牌甩两下停住",".62s","入场 · 弹出 / 砸落",STK,"挂个小牌子"),
 ("anim-fade-rise","fade-rise · 上浮淡入","要点、列表、老师或学生气泡（两端停稳）",".50s","入场 · 浮现 / 揭示",STK,"老师：我们来看看"),
 ("anim-rise","rise · 位移浮现","单格内容落位（比 fade-rise 更轻）",".50s","入场 · 浮现 / 揭示",CARD,"单格"),
 ("anim-iris-in","iris-in · 中心揭开","从大图钻进某处、揭开另一半",".55s","入场 · 浮现 / 揭示",CARD,"揭开"),
 ("anim-wipe-right","wipe-right · 左擦揭示","像掀纸一样展开信息板或答案区",".55s","入场 · 浮现 / 揭示",CARD,"答案区"),
 ("anim-unfold","unfold · 向下展开","清单、卷轴、菜单从顶边撑开",".45s","入场 · 浮现 / 揭示",CARD,"清单"),
 ("anim-blur-in","blur-in · 模糊浮出","真实截图、照片、课件大图登场（像对焦）",".60s","入场 · 浮现 / 揭示",'class="sample photo"',"真照片"),
 ("anim-write","write · 手写描线","SVG 线条画出来：笑脸的圆、路线、箭头（需 pathLength=1）",".75s","入场 · 浮现 / 揭示","SVG_WRITE",""),
 ("anim-grow-x","grow-x · 从左生长","下划线、连接线、进度条伸出来",".50s","入场 · 浮现 / 揭示",'class="sample bar2"',""),
 ("anim-fly-left","fly-left · 左侧飞入","两物对比的左件、从左边归位",".50s","入场 · 位移 / 方向",CARD,"左"),
 ("anim-fly-right","fly-right · 右侧飞入","两物对比的右件、从右边归位",".50s","入场 · 位移 / 方向",CARD,"右"),
 ("anim-flip-y","flip-y · 翻面","翻出一张新卡、换个选项看看",".55s","入场 · 位移 / 方向",CARD,"翻过来"),
 ("anim-scatter","scatter · 多碎片聚拢","一组碎片从四个方向收到位（容器类）",".50s","入场 · 位移 / 方向","SCATTER",""),
 ("anim-shake","shake · 否定抖动","错了、不行（左右晃两下；别用来表达惊讶）",".42s","入场 · 位移 / 方向",'class="sample bad"',"✗ 错了"),
 ("idle-kenburns","kenburns · 缓慢推近","真照片、大图（主体别用，会显得不稳）","9s","持续微动（只给素材 / 聚焦 / 装饰层）",'class="sample photo"',"真照片"),
 ("idle-glow","glow · 呼吸发光","让视线跟着走的当前格","1.6s","持续微动（只给素材 / 聚焦 / 装饰层）",CARD,"当前格"),
 ("idle-ring","ring · 光圈扩散","看这里的聚焦提示（比 glow 更外扩）","1.8s","持续微动（只给素材 / 聚焦 / 装饰层）",PILL,"看这里"),
 ("idle-shimmer","shimmer · 光泽扫过","推荐项、当前项（比 glow 含蓄）","2.6s","持续微动（只给素材 / 聚焦 / 装饰层）",CARD,"推荐"),
 ("idle-float","float · 漂浮","飘着的贴纸、云、星星（装饰层）","4s","持续微动（只给素材 / 聚焦 / 装饰层）",STK,"飘一下"),
 ("idle-bob","bob · 上下轻晃","小物件上下晃（比 float 快）","2.8s","持续微动（只给素材 / 聚焦 / 装饰层）",STK,"晃一晃"),
 ("idle-breathe","breathe · 轻微呼吸","待机的装饰物（主体别用）","3.4s","持续微动（只给素材 / 聚焦 / 装饰层）",STK,"待机"),
]

css = open(os.path.join(DIR, "mo.css"), encoding="utf-8").read()
have = {m.lstrip(".") for m in re.findall(r'^\.(?:anim|idle)-[a-z-]+', css, re.M)}
listed = {d[0] for d in D}
assert not (have - listed), "目录漏了：%s" % (have - listed)
assert not (listed - have), "目录多了不存在的类：%s" % (listed - have)
print("完整性 OK：%d 个 class 全覆盖" % len(have))


def sample(d):
    cls, sp = d[0], d[5]
    if sp == "SVG_WRITE":
        inner = ('<svg viewBox="0 0 220 120" width="196" height="107">'
                 '<circle cx="70" cy="60" r="42" fill="none" stroke="#3A3226" stroke-width="7" pathLength="1"/>'
                 '<path d="M46 52 q10 10 20 0" fill="none" stroke="#3A3226" stroke-width="6" pathLength="1"/>'
                 '<path d="M78 52 q10 10 20 0" fill="none" stroke="#3A3226" stroke-width="6" pathLength="1"/>'
                 '<path d="M48 78 q22 20 44 0" fill="none" stroke="#FF6B6B" stroke-width="7" pathLength="1"/></svg>')
        return '<div class="%s" id="s-%s">%s</div>' % (cls, cls, inner)
    if sp == "SCATTER":
        chips = "".join('<span class="chip">%s</span>' % t for t in ("1", "2", "3", "4"))
        return '<div class="%s scatter-box" id="s-%s">%s</div>' % (cls, cls, chips)
    return '<div %s id="s-%s">%s</div>' % (sp, cls, d[6])


groups = []
for d in D:
    if d[4] not in groups:
        groups.append(d[4])
cards = []
for g in groups:
    cards.append('<h2>%s</h2>\n<div class="grid">' % g)
    for d in [x for x in D if x[4] == g]:
        cards.append('''  <div class="cardbox" data-cls="{cls}" data-tgt="s-{cls}">
    <div class="stage">{sample}</div>
    <div class="meta"><b>{name}</b><span class="dur">{dur}</span>
      <div class="when">{when}</div>
      <button class="replay">重播</button></div>
  </div>'''.format(cls=d[0], sample=sample(d), name=d[1], dur=d[3], when=d[2]))
    cards.append('</div>')

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>动效片段库 · 预览目录（__N__ 条）</title>
<link rel="stylesheet" href="mo.css">
<style>
  :root{--ink:#3A3226;--ink-2:#7A6E5C;--yellow:#FFD84D;--green:#7BC96F;--red:#FF6B6B;}
  *{box-sizing:border-box}
  body{margin:0;padding:26px 32px 60px;color:var(--ink);font-family:"圆体-简","Yuanti SC","PingFang SC",sans-serif;
       background:radial-gradient(120% 90% at 12% 8%,#FFFDF6,#FFF9EC 45%,#FFF4E0)}
  h1{font-size:29px;margin:0 0 6px}
  .lead{color:var(--ink-2);font-size:15px;line-height:1.75;margin:0 0 12px;max-width:1020px}
  code{background:#F3EADA;border-radius:6px;padding:0 5px}
  .toolbar{position:sticky;top:0;z-index:9;background:rgba(255,253,244,.95);padding:10px 0;border-bottom:2px dashed #E3D9C4;margin-bottom:8px}
  .toolbar button{font:inherit;font-size:14px;padding:7px 16px;border:3px solid var(--ink);border-radius:999px;background:#FFFDF8;box-shadow:3px 4px 0 rgba(58,50,38,.16);cursor:pointer;margin-right:10px}
  .toolbar .st{font-size:13px;color:var(--ink-2)}
  h2{font-size:19px;margin:26px 0 10px;padding-left:12px;border-left:8px solid var(--yellow)}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(272px,1fr));gap:16px}
  .cardbox{background:#FFFDF8;border:4px solid var(--ink);border-radius:20px;box-shadow:7px 8px 0 rgba(58,50,38,.13);overflow:hidden;display:flex;flex-direction:column}
  .stage{height:170px;display:flex;align-items:center;justify-content:center;overflow:hidden;
    background:radial-gradient(circle at 22px 22px,#EFE7D6 2px,transparent 2.5px) 0 0/44px 44px,#FFFCF2}
  .meta{padding:9px 12px 12px;border-top:3px dashed #E9DFC9;font-size:13px}
  .meta b{font-size:15px}
  .meta .dur{float:right;color:#8A5A2B;background:var(--yellow);border-radius:999px;padding:1px 9px;font-size:12px}
  .meta .when{color:var(--ink-2);margin:5px 0 9px;line-height:1.5}
  .replay{font:inherit;font-size:13px;padding:4px 13px;border:3px solid var(--ink);border-radius:999px;background:#FFFDF8;cursor:pointer;box-shadow:2px 3px 0 rgba(58,50,38,.15)}
  .sample{display:flex;align-items:center;justify-content:center;font-weight:700}
  .card{width:196px;height:96px;background:#FFF7E0;border:5px solid var(--ink);border-radius:18px;font-size:22px}
  .pill{background:var(--green);border:5px solid var(--ink);border-radius:999px;padding:9px 18px;font-size:20px}
  .sticker{background:#FFFDF8;border:5px solid var(--ink);border-radius:16px;padding:10px 16px;font-size:16px}
  .photo{width:210px;height:118px;border:5px solid var(--ink);border-radius:14px;color:#3A3226;font-size:15px;
    background:linear-gradient(135deg,#8ED0E8,#F6C87A 55%,#9AD98B)}
  .bar2{width:190px;height:16px;background:var(--red);border-radius:999px;border:4px solid var(--ink)}
  .bad{background:#FFE0E0;border:5px solid var(--red);color:#B2402F;border-radius:18px;padding:9px 18px;font-size:20px}
  .scatter-box{display:flex;gap:9px}
  .scatter-box .chip{width:44px;height:44px;border:4px solid var(--ink);border-radius:12px;background:var(--yellow);display:flex;align-items:center;justify-content:center;font-size:19px}
</style></head><body>
<h1>动效片段库 · 预览目录</h1>
<p class="lead">__N__ 条，全部是 <code>mo.css</code> 里真实可用的 class（做课件时复制对应片段并挂 <code>.step.on</code> 门控；直接引入 mo.css 会加载即播完）。<br>
入场类演示该出现的时刻猛地动一下然后落定；持续类演示可以一直动的素材 / 聚焦 / 装饰层。<b>别拿它们做帧间转场</b>——4 个 <code>mo-trans-*</code> 在默认管线里没有落点（见 README §五）。</p>
<div class="toolbar"><button id="all">全部重播</button><button id="auto">自动循环：开</button><span class="st">每 5 秒自动把全部重播一遍；点单卡重播看一次完整入场</span></div>
__CARDS__
<script>
const boxes=[...document.querySelectorAll('.cardbox')];
function play(b){const cls=b.dataset.cls, el=document.getElementById(b.dataset.tgt);
  el.classList.remove(cls); void el.offsetWidth; el.classList.add(cls);}
boxes.forEach(b=>{b.querySelector('.replay').onclick=()=>play(b);});
function playAll(){boxes.forEach((b,i)=>setTimeout(()=>play(b), i*90));}
document.getElementById('all').onclick=playAll;
let auto=true; setInterval(()=>{ if(auto) playAll(); }, 5200);
document.getElementById('auto').onclick=e=>{auto=!auto; e.target.textContent='自动循环：'+(auto?'开':'关');};
setTimeout(playAll,300);
</script>
</body></html>'''

out = HTML.replace("__CARDS__", "\n".join(cards)).replace("__N__", str(len(D)))
open(os.path.join(DIR, "catalog.html"), "w", encoding="utf-8").write(out)
print("✅ catalog.html：%d 条 / %d 字节" % (len(D), len(out.encode())))

# ---- 同步 README §七 常量表（放在标记之间，保证文档与库不漂）----
readme = os.path.join(DIR, "README.md")
rows = ["| class | 时长 | 类型 | 用途 |", "|---|---|---|---|"]
for d in D:
    rows.append("| `%s` | %s | %s | %s |" % (d[0], d[3], "持续" if d[0].startswith("idle-") else "入场", d[2]))
table = "\n".join(rows)
block = ("<!-- 常量表:start（由 gen_catalog.py 生成，勿手改）-->\n\n"
         "本表与 `catalog.html` 同源（%d 条）：要看效果直接开目录页，要查时长/用途看这里。\n\n%s\n\n"
         "<!-- 常量表:end -->" % (len(D), table))
s = open(readme, encoding="utf-8").read()
if "<!-- 常量表:start" in s:
    a = s.index("<!-- 常量表:start")
    b = s.index("<!-- 常量表:end -->") + len("<!-- 常量表:end -->")
    s = s[:a] + block + s[b:]
else:
    s = s.rstrip("\n") + "\n\n## 七、常量表（class / 时长 / 类型 / 用途）\n\n" + block + "\n"
open(readme, "w", encoding="utf-8").write(s)
print("✅ README §七 常量表已同步（%d 行）" % len(rows))
