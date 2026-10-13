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

## 版式标准（呼吸感）

排版好坏的量化定义，**写 HTML 时就照此分配空间**，不是渲染完再补：

| # | 项目 | 标准 | 依据 |
| --- | --- | --- | --- |
| 1 | 标题呼吸带 | 标题底沿 → 首个内容元素 **≥48px** | 实测校准 |
| 2 | 块间呼吸 | 相邻气泡/卡片块间 **≥36px** | 沿用封面模板 ≥40px 档 |
| 3 | 底部安全带 | 内容底沿 → 品牌行徽章上沿 **≥32px** | 品牌行不可遮挡 |
| 4 | 字号下限 | 正文气泡 **≥32 号**、行距 ≥1.6 | 系列现用 34–38 |
| 5 | 密度上限 | 单帧**终态**对话块：横版 **≤4**；竖版单列 **≤5**、对话+侧卡双列 **≤6**（同一套间距下限下的推算容量） | 按前四条推算 |

**空间不够时的动作顺序（硬规则）**：砍内容 → 拆帧/拆步 → 字号降一档 → 最后才允许压间距，且**任何一条不得低于下限**。砍内容在放映版=该句改 clear 清空步（步数不变、音段对齐，前序淡出、画面变化可见），完整表达交字幕；**禁止留空 step（死点击）**。禁止目测估高一次排完——排完必跑机检：`node $SK/scripts/qc_frames.js <html> /tmp/qc`（溢出/visual 预算）+ `node $SK/scripts/qc_overlap.js <html>`（同屏跨步重叠 / 块间<30px 提示 / 压品牌行；按 clear 分段只测同屏步骤对），有报警回填 top 再复测。

## 真照片配方（用户给图时）

```python
# 1) 方裁对准主体（有红圈就对准红圈中心）→ 2) 缩 360px → 3) JPEG q86 → 4) base64 内嵌
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

机检只查画布底溢出，**呼吸感三查靠目视**（对照上面版式标准逐帧过）：① 标题底沿到首元素 ≥48px；② 块间距 ≥36px、无叠压；③ 尾元素到品牌行 ≥32px。三查不过 = gate 不过，压间距解决不了就回到动作顺序（砍内容/拆帧）。
