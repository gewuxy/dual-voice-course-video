# 阶段 2 · 做 HTML 放映版（命令与配方）

产出 `$H/视频课/index_present.html`。视觉风格包（手绘配方、品牌要素文字）：见 `$SK/assets/templates/crayon/README.md` §2.1（本文件不重复）。

## 结构契约（所有阶段 3/4 脚本的输入）

```html
<div id="stageWrap" style="width:1920px;height:1080px">
  <div class="stage-frame" id="f01">
    <div class="step">…</div>
    <div class="step anim-pop" data-hide-at="2">…</div>
  </div>
  …
</div>
```

- 每帧一个 `.stage-frame`（`id="f01"…`），脚本同时兼容 `class` 在前或 `id` 在前
- 帧内 `.step` 块数 = 该帧台词句数（不等会被 `verify_steps.py` 拦下）
- `.step` 上可叠动效 class（脚本按 class 分词识别，**不会漏**）；可选 `data-hide-at="N"`（到第 N 步淡出）
- 尺寸由 `#stageWrap` 读：横版 1920×1080、竖版 1080×1440 → `capture*.js` / `qc_frames.js` 自动跟随，不用手填宽高

## 模板（视觉基准，勿改结构）

| 取向 | 模板（`$SK/assets/templates/crayon/`） | 产物 |
| --- | --- | --- |
| 横版 · 对话优先 | `preview_landscape.html` | `index_present.html` |
| 竖版 · 对话优先 | `preview_portrait.html` | `index_present_portrait.html` |
| 横版 · 图片优先 | `preview_landscape_visual.html` | `index_present.html`（混排：visual 帧抄它） |
| 竖版 · 图片优先 | `preview_portrait_visual.html` | `index_present_portrait.html`（混排：visual 帧抄它） |

## 版式选择（逐帧，允许同课混排）

- **判据一句话：这帧的核心信息能不能一图概括？** 能（展示/操作演示/分类找宝/素材图为主）→ `visual`；不能（问答/概念定义/总结/作业）→ `dialog`（默认）。台词长短**不决定**版式——dialog 版允许长句。
- 自动推荐：`python3 $SK/scripts/suggest_layout.py <剧本>`，出选型表 + 每帧台词字数；**gate 时交用户确认，可逐帧改**。
- 每帧落属性：`<div class="stage-frame" id="f03" data-layout="visual">`（`qc_frames.js` 按此分管机检）。
- 规格与帧骨架：`$SK/assets/templates/crayon/README.md` §2（两版式共用同一套字号体系，**禁止衍生版式另起字号**）。
- **visual 帧硬规则**：每步主图挂 `.fscene` 整屏换景（每步都要挂，漏挂前图不清场）；对话提炼 **≤15 字/句**（完整表达交给字幕）；整帧画面文字 **≤40 字**；关键词锚点卡 ≤4 字、90–150px、一帧 1 张；主图占屏宽 ≥50%；字幕安全区（竖版 y≥1120 / 横版 y≥900）只放品牌行。

动效片段库：`$SK/assets/templates/anim-snippets/`（`mo.css` / `mo.gsap.js` / README）。class 一览与「何时用」见 `anim-snippets/README.md`，本文件不复述。

## visual 场景母题库（8 个，可混排）

做 visual 帧时先从这里挑一个骨架，再填内容。同一支课**建议至少用 3 种不同母题**，相邻 visual 帧尽量不同（**建议，不是硬约束**）。

| 母题 | 长什么样 | 适合 | 动效角色（见 anim-snippets/README §二） |
| --- | --- | --- | --- |
| **竖排流程图** | 横条卡自上而下堆，卡间短竖线连接 | 线性步骤（刷牙/出门准备/安装） | 新长出一格 → `anim-fade-rise` + `.stagger` 错峰落位 |
| **横向步骤卡** | 一排方卡 + 数字徽章（可加 `→` 连接） | 并列要点、4 步以内 | 一次性给全 → `anim-pop`；逐条 → `fade-rise` |
| **阶梯** | 格子逐级升高（左→右 / 下→上），空格用虚线 + `?` | 排序游戏、由易到难、逐级推进 | 同位替换 → `anim-slam`；当前格 → `idle-glow` |
| **时间轴** | 一条轴 + 挂在轴上的节点卡（横版横轴 / 竖版竖轴） | 先后顺序、日程、成长序列 | 收口归位 → `anim-fly-left` / `anim-fly-right` 两侧聚拢 |
| **对比双栏** | A / B 两栏各从一侧进入 | 概念辨析、对错、前后 | 两栏入场 → `anim-fly-left` + `anim-fly-right` |
| **找错批改** | 原图/卡片 + 红圈 / `✗` / 正确项并排 | 纠错、顺序反例 | 错误项 → `anim-slam`（红），正确项 → `fade-rise` |
| **逐步生长主视觉** | 内联 SVG 分步长出（圆→眼睛→嘴、树→枝→叶） | 过程演示、从无到有 | 每步只给新长出的部分挂动画（别整图重弹） |
| **大素材帧** | 真照片/截图满幅（`object-fit:cover`）+ 拍立得白边 | 实物、场景、课件原图 | `anim-blur-in` 登场 + `idle-kenburns` 持续微动 |

骨架（直接抄改，这是验证过的成品结构）：

```html
<!-- 竖排流程图：每行一个 step；行内错峰靠容器 .stagger -->
<div class="step"><div class="fscene" style="position:absolute;inset:0">
  <div class="flow stagger" style="position:absolute;left:460px;top:300px">
    <div class="frow anim-fade-rise"><span class="fnum">1</span>…<span class="flab">拿起牙刷</span></div>
    <div class="fconn"></div>
    <div class="frow anim-fade-rise"><span class="fnum">2</span>…<span class="flab">挤上牙膏</span></div>
  </div>
  <div class="mini say" style="left:…;top:…"><div class="who">小贤老师</div><div class="bub">按顺序，一步一步来</div></div>
</div></div>

<!-- 阶梯：空格用 .pending，当前格用 .slam-glow（砸入 + 发光） -->
<div class="ladder">
  <div class="lcell slam-glow"><span class="lnum">1</span>…<div class="llab">倒面粉</div></div>
  <div class="lcell pending"><div class="lq">?</div></div>
</div>

<!-- 时间轴（横版）：轴 + 节点卡；左半 anim-fly-left、右半 anim-fly-right -->
<div class="tl" style="width:1240px;height:380px">
  <div class="tline" style="left:40px;right:40px;top:196px;height:8px"></div>
  <div class="tnode anim-fly-left" style="left:195px;top:8px;width:250px;transform:translateX(-50%)">
    <div class="tcard">…<div class="tlabel">穿好衣服</div></div>
    <div class="tdot" style="margin:14px auto 0"></div>
  </div>
</div>

<!-- 大素材帧：base64 注入只走 Python str.replace（见下方真照片配方） -->
<div class="photo anim-blur-in" style="width:1000px;height:430px;display:flex;flex-direction:column">
  <div class="ph"><img src="data:image/jpeg;base64,__B64_CAKE__"></div>
  <div class="cap">真的蛋糕出炉啦</div>   <!-- .step.on .photo img 上跑 kenburns -->
</div>
```

- 母题之间允许同帧混用（例如"时间轴 + 末尾一排放好的方卡"），但**每一步只留一个主角**。
- 逐帧 QC 时顺手记一下用了哪些母题；`python3 $SK/scripts/qc_variety.py <html>` 会打出分布（**只提示不阻断**）。
- 让统计更准：在帧属性上标母题即可，`<div class="stage-frame" id="f06" data-layout="visual" data-scene="ladder">`（取值用上面的母题名：`flow / cards / ladder / timeline / compare / findwrong / grow / photo`；不标也能跑，脚本退回按结构识别）。

## 动效清单表（阶段 2 产出，防单一化）

**动手前先拉一张表**：逐帧逐步写"这一帧在讲什么课型 / 这一步是什么角色 / 用哪个动效"。这张表本身就是照妖镜——9 帧全填同一个动效，表格一眼就露。

| 帧 | 步 | 课型 | 角色 | 动效（候选池第几选） |
| --- | --- | --- | --- | --- |
| 2 | 1 | 概念 | 主体登场 | `pop` |
| 2 | 2 | 对比 | 两物入场 | `fly-left` + `fly-right` |
| 2 | 3 | 流程 | 新长出一格 | `fade-rise`（错峰） |
| 2 | 4 | 流程 | 同位替换/纠错 | `slam` |

落盘 `$H/视频课/动效清单_<课号>.md`，与 HTML 一起过阶段 2 gate。**边写边查**：每做完 2–3 帧跑一次 `node $SK/scripts/qc_variety.py <html>`，别等全做完（那时改动成本最高——HTML 一改，成片就得重截）。

**三条硬线**（其余按 `anim-snippets/README.md` §二 的候选池挑）：
1. 相邻帧不得同角色同动效；
2. 同一动效在 visual 帧里连续 ≤2 帧、整支课占比 ≤50%；
3. 一帧内允许多种动效（主图 `iris-in`/`pop` + 卡片 `fade-rise` 错峰），"一帧一种"本身就是单调。

## 版式标准（呼吸感）

**主体呼吸（三条硬线，`qc_overlap.js` 主体呼吸段机检）**：

1. **图形↔标注 ≥24px（目标 28–32px）**——42px 的标注字号配 14px 间距就是"贴在一起"；间距要跟着图形大小走，不是固定值。
2. **主体（含标注）↔下方气泡 ≥28px**——负值=重叠，直接红。
3. **图形尺寸按"场景盒可用高度"算，不许只按 ratio 拍**：`可用高 = 场景盒高 − 2×场景呼吸 − 标注高 − 图形↔标注间距`（只按 ratio 拍必然溢出，见 `known_pitfalls.md` §4）。


排版好坏的量化定义，**写 HTML 时就照此分配空间**，不是渲染完再补：

| # | 项目 | 标准 | 依据 |
| --- | --- | --- | --- |
| 1 | 标题呼吸带 | 标题底沿 → 首个内容元素 **≥48px** | 实测校准 |
| 2 | 块间呼吸 | 相邻气泡/卡片块间 **≥36px** | 沿用封面模板 ≥40px 档 |
| 3 | 底部安全带 | 内容底沿 → 品牌行徽章上沿 **≥32px** | 品牌行不可遮挡 |
| 4 | 字号下限 | 正文气泡 **≥32 号**、行距 ≥1.6 | 系列现用 34–38 |
| 5 | 密度上限 | 单帧**终态**对话块：横版 **≤4**；竖版单列 **≤5**、对话+侧卡双列 **≤6**（同一套间距下限下的推算容量） | 按前四条推算 |

**清场（`clear`）只看空间，不分横竖**：先按**累加式**排一遍，**该版装得下就不清场，装不下才让 `clear` 生效**——横竖同规则，不得把一版的清场决策照搬到另一版。机检 `node $SK/scripts/qc_clear.js <两版 html>`（实测每步渲染高度重算累加底沿，报"放得下却清场"与"装不下却没清场"）。

**空间不够时的动作顺序（硬规则）**：砍内容 → 拆帧/拆步 → 字号降一档 → 最后才允许压间距，且**任何一条不得低于下限**。砍内容在放映版=该句改 clear 清空步（步数不变、音段对齐，前序淡出、画面变化可见），完整表达交字幕；**禁止留空 step（死点击）**。禁止目测估高一次排完——排完必跑机检：`node $SK/scripts/qc_frames.js <html> /tmp/qc`（溢出/visual 预算）+ `node $SK/scripts/qc_overlap.js <html>`（同屏跨步重叠 / 块间<30px 提示 / 压品牌行；按 clear 分段只测同屏步骤对），有报警回填 top 再复测。另加两条轻量检查：`node $SK/scripts/qc_clear.js <两版 html>`（清场 vs 空间）+ `python3 $SK/scripts/qc_variety.py <html>`（母题/动效分布提示，不阻断）。

## 素材采集（**可选**，有源课件才做）

**不是每课都有现成课件**——用户可能只给一个主题。规则：

- **有 PPT / 教材 PDF / 图片素材时**：动手前先把配图抽出来（`python-pptx` 遍历 `slide.shapes` 取 `shape.image.blob`；PDF 用 `pdfimages`），存 `$H/视频课/素材_<名字>.jpg`，**建议**每课至少 2 帧用真素材（`anim-blur-in` + `idle-kenburns`）。
- **只有主题时**：跳过，全套 SVG 简笔画重画即可，**不构成 gate 不通过**。
- 抽出来的图先目检：纯白底 icon 组、示意线稿这类"PPT 拼图"不如自己重画；实拍照片、地图、界面截图才值得进片。

## 真照片配方（用户给图时）

```python
# 1) 方裁对准主体（有红圈就对准红圈中心）→ 2) 缩 360px → 3) JPEG q86 → 4) base64 内嵌
#    ↳ 360px 是「拍立得贴纸」尺寸；**大素材帧**（母题 8）用 900–1000px 宽、q86。
#      显示用 object-fit:cover 填满场景盒（横版约 1000×430、竖版约 880×560），容器要显式宽度，别让 flex 把图压小。
```

```html
<div class="sticker" style="padding:8px;transform:rotate(±2.5deg);position:relative">
  <img src="data:image/jpeg;base64,__B64__" style="width:118px;height:118px;object-fit:cover;border-radius:10px;display:block">
  <span class="tape"></span>
</div>
<div class="title" style="text-align:center;font-size:28px;margin-top:4px">手机</div>
```

- 卡片紧凑化（否则顶穿页脚）：`vis` 的 `top:566px`、`nm` 44px、`tx` 一句话不折行
- 素材另存 `$H/视频课/素材_<名字>.jpg` 供 PPT / 教材复用
- **base64 注入只走 Python `str.replace`**，不要用编辑器改那一行（字符串匹配必然失败）

## QC 循环（逐帧溢出检测）

```bash
node $SK/scripts/qc_frames.js "$H/视频课/index_present.html" /tmp/qc_x <audioId> <帧号>
```

看到 `✅ 全部帧无溢出` + 逐帧目视 png 构图 OK 为止；有 `⚠️ 溢出帧` 就按上面的配方压高度。竖版把文件名换成 `index_present_portrait.html`。

机检已覆盖画布底溢出 + **主体呼吸**（图形↔标注、主体↔气泡，见上）；剩下的**三查靠目视**（对照上面版式标准逐帧过）：① 标题底沿到首元素 ≥48px；② 块间距 ≥36px、无叠压；③ 尾元素到品牌行 ≥32px。三查不过 = gate 不过，压间距解决不了就回到动作顺序（砍内容/拆帧）。
