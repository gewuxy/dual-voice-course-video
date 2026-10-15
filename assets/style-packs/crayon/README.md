# HTML 课件模板 · 儿童蜡笔手绘风


> **本文件的范围**：蜡笔风的**皮肤与度量**（配色/字体/描边/圆角/纹理/品牌行/封面/片头）。
> **中性内容不在本文件**：版式语法（间距/呼吸/热区硬线）、母题库（visual 8 + dialog 6）见 `../../layout/README.md`；
> 动效见 `../../anim-snippets/README.md`；风格包契约见 `../README.md`。
> 本文件里出现的字号/间距是**蜡笔风这一套的度量值**（作为 pack 的 tokens 基准），不是通用规范。

> 本目录唯一产物形态是**放映版**：参考成品是 `preview*.html`（见 §2.2），课程产物名是 `index_present*.html`。

## 一、配色（蜡笔系，非自创）

主色：黄 `#FFD84D` / 橙 `#FF9F45` / 红 `#FF6B6B` / 粉 `#FFB3C7` / 绿 `#7BC96F` / 青 `#4CC9B0` / 蓝 `#5AB0F5` / 紫 `#B088F9` / 棕 `#C89B6A`；
纸底 `#FFFDF4` / `#FFF6E2`，文字深棕 `#3A3226`（次级 `#7A6E5C`，不是纯黑）；手绘描边统一粗描边。
**实际取值以 `preview*.html` 的 `:root` 变量为准**（放映版是唯一产物形态）。

---

## 二、放映版 · 双版式体系

### 2.1 两层：风格包 vs 版式

- **风格包**（= 本文件夹）= 视觉语言：字体、配色、贴纸、字号体系。**同一风格包下所有版式共用一套字号**，禁止衍生版式另起一套字号。内容四件：
  - **手绘质感三板斧**：SVG `feTurbulence+feDisplacementMap` 抖动笔触、全屏噪点纸纹、蜡笔 blob 色块（配色见 §一）
  - **字体**：标题/正文 **圆体-简**，手写批注 **娃娃体-简**
  - **品牌要素（每帧固定）**：左上徽章「AI 启蒙 · 第 X 课」+ 适合年级；底部品牌行「小贤 AI 青少年教育 · 体系课程 · 实训项目 · AI 创造力」
  - **图标策略**：优先纯 SVG 简笔画；用户给了真照片就做「拍立得贴纸」
- **版式**（layout）= 信息布局，**逐帧选择，允许同一课内混排**。写在帧属性上供机检识别：
  ```html
  <div class="stage-frame" id="f03" data-layout="visual">
  ```
- 产物文件名**不按版式拆分**：横版 `index_present.html`、竖版 `index_present_portrait.html`。

### 2.2 参考成品（4 件，照抄其版式骨架）

| 文件 | 取向 | 版式 |
|---|---|---|
| `preview_landscape.html` | 横版 1920×1080 | dialog 对话优先 |
| `preview_portrait.html` | 竖版 1080×1440 | dialog 对话优先 |
| `preview_landscape_visual.html` | 横版 1920×1080 | visual 图片优先 |
| `preview_portrait_visual.html` | 竖版 1080×1440 | visual 图片优先 |

四件都自带放映控制器（点击/空格步进、←返回、R 重播、F 全屏），直接打开即可翻看。

### 2.3 dialog · 对话优先（基准版式，默认）

信息主角是气泡台词；长句没问题（**不要求精简**）。字号体系：

| 元素 | 竖版 1080×1440 | 横版 1920×1080 |
|---|---|---|
| 帧标题 `.ftitle .title` | 88px（长标题可降到 62–72） | 88–96px |
| 气泡正文 `.bub` | 42px / 行高 1.45 | 42px（密集帧内联降 34–36，L8 即此做法） |
| 说话人 `.who` | 28px | 28px |
| 关键词 chip | 40px / padding 12 28 / 边 4px | 40px（链式小 chip 28px） |
| 箭头 `.arrow` | 48px | 48px |
| 照片说明 `.pola .cap` | 27px | 27px |
| 页眉徽章 / 页脚 | 38 / 30（品牌 32） | 38 / 30 |

> 横版 CSS 基准与竖版同为 42px，只有排不下的高密帧才内联降档——**不许整帧预设小字号**。

**两种收尾惯用法（都可，机检都认）**：
- **清场式**（横版 dialog 惯用）：收尾总结步加 `clear` 类，亮起时之前步骤整体淡出、新内容顶上。前后段允许共享位置——机检按段测量，只查同屏步骤对。
- **累加式**（竖版 dialog 惯用）：全程不清场，步骤自上而下堆叠。不用 `clear`。

呼吸感硬指标：**标题底沿 + ≥44px = 首步最小 top**（横版 ≈288、竖版 290，两份参考件已达标）；**同列块间排版目标 ≥44px**，<30px 机检提示（不阻断）；内容底沿→品牌行 ≥32px（机检 FAIL）；正文 ≥32 号 / 行距 ≥1.6；终态密度上限（清场帧按段计）横版 ≤4 块、竖版单列 ≤5、双列 ≤6。

### 2.4 visual · 图片 / 概念可视化优先

**画面主角是大图、照片或概念卡；对话退居其次，且必须提炼成短气泡（≤15 字/句），完整表达交给字幕**（成片管线已有字幕）。

| # | 规则 | 数值 |
|---|---|---|
| 1 | 整屏换景 | 每步主图挂 `.fscene`（见 2.5） |
| 2 | 字幕安全区 | 竖版 y≥1120、横版 y≥900 只放品牌行，不放任何内容块 |
| 3 | 关键词锚点卡 | 只放 ≤4 字核心词，90–150px，一帧最多 1 张 |
| 4 | 主图占屏 | 宽 ≥50%，水平居中 |
| 5 | 对话（若有） | 短气泡 ≤15 字/句，整帧画面文字 ≤40 字 |
| 6 | 密度上限 | 单步主视觉元素 1 个（不要同屏塞 2 张主图） |
| 7 | 答案/物品展示一律「黄金贴纸卡」 | 宽 横版 300px / 竖版 280px，卡间距 横 40 / 竖 30，emoji 130px，标签娃娃体 34px，白描边 6px + 微旋转（±2°）。定稿样例：`preview_landscape_visual` f03s4、`preview_portrait_visual` f03s4。**禁止用小 chips（字号 ≤48px）展示关键词/答案**——字太小、页面空；chips 只允许用于流程链（A→B→C）等 ≤6 字短词序列 |

### 2.5 fscene · 整屏换景机制（三行 CSS）

```css
.fscene{visibility:hidden}                                   /* 默认隐藏 */
.step.on .fscene{visibility:visible}                         /* 当前激活步显示 */
.step.on:has(~ .step.on .fscene) .fscene{visibility:hidden}  /* 后面还有已激活的 fscene → 自己隐藏 */
```

语义：**后一步挂了 fscene 且被激活时，前一步的图自动清场**。因此——

- 想让某步的图在第 N 步消失，**第 N 步也必须挂 fscene**（漏挂 = 图赖着不走，这是踩过的坑）；
- 最后一步后面没人了，天然常驻；
- 想让两张图**并排共存**（不同位置），不要用 fscene，用普通 `div`（fscene 只用于同位替换/换景）。

### 2.6 帧骨架（照抄填空）

版位锚点（实测自参考件，竖版 / 横版）：页眉 `.hdr` top 58 / 56；帧标题 `.ftitle` top 140 / 150；
首步 top ≥290 / ≥288（=标题底沿+44，见 2.3 呼吸感）；内容底沿红线 =品牌行上沿-32（横版 947，机检会报）；
页脚 `.foot` bottom 36 / 40。

```html
<!-- dialog 帧 -->
<div class="stage-frame" id="f01" data-layout="dialog">
<div class="hdr">…</div>
  <div class="ftitle"><div class="title" style="font-size:88px">__标题__</div></div>
  <div class="step"><div class="slot say" style="top:300px"><div class="who">小贤老师</div><div class="bub">__台词__</div></div></div>
  <div class="step"><div class="slot reply" style="top:484px">…</div></div>
<div class="foot">…</div>
</div>

<!-- visual 帧：每步一个 fscene，短气泡只作点缀 -->
<div class="stage-frame" id="f03" data-layout="visual">
<div class="hdr">…</div>
  <div class="ftitle"><div class="title" style="font-size:88px">__标题__</div></div>
  <div class="step"><div class="fscene" style="position:absolute;left:300px;top:340px">__大图/概念卡__</div></div>
  <div class="step"><div class="fscene" style="position:absolute;left:90px;top:460px;width:900px">__换景图__</div>
    <div class="slot say" style="top:1020px;width:420px"><div class="bub" style="font-size:36px">__≤15字短句__</div></div></div>
<div class="foot">…</div>
</div>
```

### 2.7 逐帧选型判据

一句话：**这帧的核心信息能不能一图概括？**

| 判断 | 版式 | 典型帧 |
|---|---|---|
| 能一图概括（展示、操作演示、分类/找宝、素材图为主） | `visual` | 卡片分组、搜索找宝、实物展示 |
| 不能，需要语言定义或推理（问答、概念定义、总结、作业布置） | `dialog` | 概念讲解、比一比、闯关问答、作业 |
| 判断不了 | `dialog`（默认，已验证基准） | — |

自动推荐：`node/python $SK/scripts/suggest_layout.py <剧本>` 出选型表，**在阶段 2 gate 交用户确认**后可逐帧改。

**步级自检（visual 帧逐步过一遍，帧级判据管不到这里）**：

1. 每步先问「**这一步的画面主角是什么**」——答不出来（只有一段台词）= 该步实际在用 dialog 排版：要么给它配图，要么整帧改回 dialog。判据错到步级就是假 visual（L8 f08 教训：帧级标 visual，步级却是长气泡链）。
2. visual 帧内**禁止 dialog 式长气泡链**（多句台词逐条堆叠、上一句还挂着）。visual 帧的每一页 = 一图 + 至多一句 ≤15 字短气泡；上一句要退场就用 clear 清空步。
3. 同一场景跨步复制（孪生换景）时，各步的 fscene 位置/尺寸必须**逐字一致**——要改就整帧一起改，只改一步场景会在翻页时跳位。
4. 完整台词不删：缩写气泡时，原句放 HTML 注释（`<!-- 完整台词（字幕/音频用）：… -->`），完整表达交给字幕。

### 2.8 排完必跑的机检（三条命令）

```bash
node $SK/scripts/qc_frames.js   <index_present*.html> /tmp/qc    # 溢出 + visual 文字预算/安全区
node $SK/scripts/qc_overlap.js  <index_present*.html>            # 同屏块重叠(FAIL) + 间距<30px(提示) + 压品牌行(FAIL)
python3 $SK/scripts/qc_divs.py   <index_present*.html> ...       # div 嵌套平衡（帧提前闭合检测）
```

- `qc_overlap` 在**关动画、舞台原尺寸**下量真实包围盒；按 clear 分段只测**同屏步骤对**（清场式共享位置不报），同段跨步重叠必报，裸 SVG 底板不参与配对。
- `qc_divs` 查每帧 foot 内嵌深度=1、帧内 div 开闭差=0（末帧允许 -1 的 stageWrap 闭合）。帧提前闭合时后续帧会掉出 stageWrap 失去缩放，foot 变视口宽（折行、压 HUD），而 qc_frames/qc_overlap 未必能报出来——**必须三条都跑**。
- **塞不下时的动作顺序（硬规则）**：砍内容 → 拆帧/拆步 → 字号降一档 → 最后才允许压间距，且不得低于下限。
- 「砍内容」在放映版的落地方式：**该句改为 clear 清空步（`<div class="step clear">…</div>`，保留步数与音段对齐）——亮起时前序内容整体淡出，画面变化可见，完整表达交给字幕**。**禁止留空 `<div class="step"></div>`：交互放映里是死点击，观众点了没反馈**。附和句、与 chips/阶梯图重复的回答、纯欢呼句优先砍。clear 步后如还有步骤，后续画面必须自立（前序已被清掉）。砍掉处留 HTML 注释说明是哪句。
- 禁止目测估高一次排完：绝对 top 手摆的帧，必须跑 `qc_overlap` 实测渲染高，再回填 top。
