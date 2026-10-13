# HTML 课件模板 · 儿童蜡笔手绘风

> 本目录唯一产物形态是**放映版**：参考成品是 `preview*.html`（见 §3.2），课程产物名是 `index_present*.html`。
> 封面是独立模板 `封面模板_竖版视频号_1080x1260.html`，不在此文件范围。

## 一、版位规律（从上往下）

| 区域 | 占画面高度位置 | 说明 |
|---|---|---|
| 页标题 | 距顶 7% ~ 20% | 顶部留白，标题独占一条 |
| 主体内容 | 距顶 25% ~ 75% | 卡片 / 列表 / 图文居中 |
| 收尾句或标签组 | 距顶 84% ~ 93% | 底部一条金句或 3 个小标签 |
| 页脚 | 距顶 ~95% | 页码 + 品牌 |

三列卡片横向位置：x ≈ 10% / 40% / 72%（不是等分，中间略偏，手绘感）。
列表页左对齐起点：x ≈ 16%~18%，右侧留给插画。

## 二、配色（蜡笔系，非自创）

黄 `#F6E360` / 绿 `#72B551` / 蓝 `#6EBAF9` / 粉 `#F4B3C4` / 米黄 `#FBEBC1`；
文字深蓝 `#1D2D49`（不是纯黑）；手绘描边统一粗描边。
**实际取值以 `preview*.html` 的 `:root` 变量为准**（放映版是唯一产物形态）。

---

## 三、放映版 · 双版式体系

### 3.1 两层：风格包 vs 版式

- **风格包**（= 本文件夹）= 视觉语言：字体、配色、贴纸、字号体系。**同一风格包下所有版式共用一套字号**，禁止衍生版式另起一套字号（L8 竖版曾私自缩 0.75 档被打回）。
- **版式**（layout）= 信息布局，**逐帧选择，允许同一课内混排**。写在帧属性上供机检识别：
  ```html
  <div class="stage-frame" id="f03" data-layout="visual">
  ```
- 产物文件名**不按版式拆分**：横版 `index_present.html`、竖版 `index_present_portrait.html`。

### 3.2 参考成品（4 件，照抄其版式骨架）

| 文件 | 取向 | 版式 |
|---|---|---|
| `preview_landscape.html` | 横版 1920×1080 | dialog 对话优先 |
| `preview_portrait.html` | 竖版 1080×1440 | dialog 对话优先 |
| `preview_landscape_visual.html` | 横版 1920×1080 | visual 图片优先 |
| `preview_portrait_visual.html` | 竖版 1080×1440 | visual 图片优先 |

（`preview.html` 是旧翻页式课件 demo，仅第 1 页封面 slide 作横版课件封面源使用，见阶段 5；不属于放映版参考件。）

四件都自带放映控制器（点击/空格步进、←返回、R 重播、F 全屏），直接打开即可翻看。

### 3.3 dialog · 对话优先（基准版式，默认）

信息主角是气泡台词；长句没问题（**不要求精简**）。字号体系（实测定档）：

| 元素 | 竖版 1080×1440 | 横版 1920×1080 |
|---|---|---|
| 帧标题 `.ftitle .title` | 88px（长标题可降到 62–72） | 88–96px |
| 气泡正文 `.bub` | 42px / 行高 1.45 | 36px / 行高 1.45（密集帧长句可降 34） |
| 说话人 `.who` | 28px | 25px |
| 关键词 chip | 40px / padding 12 28 / 边 4px | 40px（链式小 chip 28px） |
| 箭头 `.arrow` | 48px | 48px |
| 照片说明 `.pola .cap` | 27px | 27px |
| 页眉徽章 / 页脚 | 38 / 30（品牌 32） | 38 / 30 |

> 横版比竖版矮 360px，5 步以上的帧排不下 42px 气泡——横版一律按 36px 起排（`preview_landscape.html` 已内置此规格），高度富余的帧才允许升 42。

呼吸感五条（硬指标）：标题底沿→首元素 ≥48px；块间 ≥36px；内容底沿→品牌行 ≥32px；正文 ≥32 号/行距 ≥1.6；终态密度上限 横版 ≤4 块、竖版单列 ≤5、双列 ≤6。

### 3.4 visual · 图片 / 概念可视化优先

**画面主角是大图、照片或概念卡；对话退居其次，且必须提炼成短气泡（≤15 字/句），完整表达交给字幕**（成片管线已有字幕）。

| # | 规则 | 数值 |
|---|---|---|
| 1 | 整屏换景 | 每步主图挂 `.fscene`（见 3.5） |
| 2 | 字幕安全区 | 竖版 y≥1120、横版 y≥900 只放品牌行，不放任何内容块 |
| 3 | 关键词锚点卡 | 只放 ≤4 字核心词，90–150px，一帧最多 1 张 |
| 4 | 主图占屏 | 宽 ≥50%，水平居中 |
| 5 | 对话（若有） | 短气泡 ≤15 字/句，整帧画面文字 ≤40 字 |
| 6 | 密度上限 | 单步主视觉元素 1 个（不要同屏塞 2 张主图） |
| 7 | 答案/物品展示一律「黄金贴纸卡」 | 宽 横版 300px / 竖版 280px，卡间距 横 40 / 竖 30，emoji 130px，标签娃娃体 34px，白描边 6px + 微旋转（±2°）。定稿样例：`preview_landscape_visual` f03s4、`preview_portrait_visual` f03s4。**禁止用小 chips（字号 ≤48px）展示关键词/答案**——字太小、页面空；chips 只允许用于流程链（A→B→C）等 ≤6 字短词序列 |

### 3.5 fscene · 整屏换景机制（三行 CSS）

```css
.fscene{visibility:hidden}                                   /* 默认隐藏 */
.step.on .fscene{visibility:visible}                         /* 当前激活步显示 */
.step.on:has(~ .step.on .fscene) .fscene{visibility:hidden}  /* 后面还有已激活的 fscene → 自己隐藏 */
```

语义：**后一步挂了 fscene 且被激活时，前一步的图自动清场**。因此——

- 想让某步的图在第 N 步消失，**第 N 步也必须挂 fscene**（漏挂 = 图赖着不走，这是踩过的坑）；
- 最后一步后面没人了，天然常驻；
- 想让两张图**并排共存**（不同位置），不要用 fscene，用普通 `div`（fscene 只用于同位替换/换景）。

### 3.6 帧骨架（照抄填空）

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

### 3.7 逐帧选型判据

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

### 3.8 排完必跑的机检（三条命令）

```bash
node $SK/scripts/qc_frames.js   <index_present*.html> /tmp/qc    # 溢出 + visual 文字预算/安全区
node $SK/scripts/qc_overlap.js  <index_present*.html>            # 块重叠 + 块间<36px + 压品牌行
python3 $SK/scripts/qc_divs.py   <index_present*.html> ...       # div 嵌套平衡（帧提前闭合检测）
```

- `qc_overlap` 在**关动画、舞台原尺寸**下量真实包围盒；同一步内的叠放算设计手段不报，**跨步重叠必报**。
- `qc_divs` 查每帧 foot 内嵌深度=1、帧内 div 开闭差=0（末帧允许 -1 的 stageWrap 闭合）。帧提前闭合时后续帧会掉出 stageWrap 失去缩放，foot 变视口宽（折行、压 HUD），而 qc_frames/qc_overlap 未必能报出来——**必须三条都跑**。
- **塞不下时的动作顺序（硬规则）**：砍内容 → 拆帧/拆步 → 字号降一档 → 最后才允许压间距，且不得低于下限。
- 「砍内容」在放映版的落地方式：**该句留空 `<div class="step"></div>`（保留步数与音段对齐），画面不新增卡片，完整表达交给字幕**——附和句、与 chips/阶梯图重复的回答、纯欢呼句优先隐藏。隐藏处留 HTML 注释说明是哪句。
- 禁止目测估高一次排完：绝对 top 手摆的帧，必须跑 `qc_overlap` 实测渲染高，再回填 top。
