# 动效片段库 · 使用与判断指引

本目录是 `dual-voice-course-video` skill 的**动效片段库**——**中性资产**：只按「课型 × 角色」选，**不按风格分**，蜡笔风与像素风共用同一套（`catalog.html` 直接引用 `mo.css`，换风格不影响动效）。它解决两件事：

1. **复用**：制作新课的课件时，不用从上一课的 HTML 复制动效，而是从这里挑片段。
2. **判断**：教 Agent 按"这一帧在讲什么"决定用哪种动效——**不是为差异化而差异化**，而是让每帧的运动都贴合内容语义。

---

## 一、三条总原则

> 节奏理念借鉴 `huashu-art-motion` 的 MO 库（出处注明，便于回溯）。但**别的 skill 的常量与实测数字一律不引用**——这里只写本库能落地的落点；不可复核的第三方证据不进规范。

1. **动在事件上（脉冲节奏）**：运动是"停住 → 猛地一下 → 停住"，不是匀速慢推。
   本库落点：`anim-*` 全部一次到位（`pop/slam/fade-rise/fly/rise` **0.42–0.50s**、`iris-in` 0.55s、`blur-in` 0.60s，均 `both` 填充；数值以 `mo.css` 为准），不需要额外时长参数。
   ⚠️ **不要照抄 `mo.gsap.js` 的 `MO.PULSE`（punch/pan/slam）**——那是 GSAP 侧，默认管线**抓不到**（§五）；`mo.gsap.js` 只在 HyperFrames 那一路用。
2. **持续微动只给素材层 / 聚焦层**：`idle-kenburns`（真照片）、`idle-glow`（当前格）、`idle-float`（装饰）可以一直动；**主体（卡片 / 图标 / 笑脸 / 素材外框）落定后必须停住**。
   （"不许任何持续运动"是过度解读——这三条 `idle-*` 的适用面见 §二 决策表。）
3. **风格全片统一，动效按「课型 × 角色」分**：封面 / 品牌框 / 字体 / 色板每课一致；**只有动效按内容判断**（§二决策表），**不为差异化而差异化**。
   同时守住**同步并发纪律**：同一**步**里不并发两个**同权重**主体（错峰的一排卡片算**一个**事件，用内联 `animation-delay` 逐个递增 ≈0.12s）。

## 二、按「课型 × 角色」选动效（核心决策表）

做新课某帧时，**先问两个问题**：

1. **课型**：这一帧在讲什么？（概念 / 游戏 / 对比 / 流程 / 总结）
2. **角色**：这一步在这一段里干什么？（新长出一格 / 同位替换 / 强调已有 / 收口归位 / 素材登场）

课型决定"要什么感觉"，角色决定"具体挑哪一个"。**每个角色给的是候选池（4–6 个），不是唯一解**——按这一帧的节奏、元素数量、画面密度挑最贴的；同一支课里同一角色换着用不算错，只要**同一段里不混**。

> **先看效果**：浏览器直接打开 `catalog.html`（26 条，每 5 秒自动循环；点单卡"重播"看一次完整入场）。时长/用途速查见 §七 常量表（与本目录同源生成）。

| 课型 | 角色 | 候选池（挑一个） | 怎么选 |
|---|---|---|---|
| 概念 / 特征 | 主体登场 | `anim-pop` ／ `anim-drop-in` ／ `anim-flip-y` ／ `anim-wipe-right` ／ `anim-iris-in` ／ `anim-blur-in` | 抽象概念 → `pop`；把东西放上去 → `drop-in`；翻出新东西 → `flip-y`；展开信息板 → `wipe-right`；从大图钻进某处 → `iris-in`；真图 / 截图 → `blur-in` |
| 概念 / 特征 | 看全并浏览 | `idle-kenburns` ／ `idle-float`（装饰层） ／ `idle-breathe`（待机） | 大图 / 截图 → `kenburns`；飘着的小物 → `float`；待机装饰 → `breathe`；**主体别用持续类**（会显得不稳） |
| 概念 / 画图 | **揭示过程（画出来）** | `anim-write`（SVG 描线，路径需 `pathLength="1"`） ／ `anim-grow-x` | 画笑脸 / 路线 / 箭头 → `write`（真的"画"出来）；下划线 / 进度 / 连接线 → `grow-x` |
| 互动 / 问答 / 选择 | 答案落定 | `anim-slam` ／ `anim-stamp` ／ `anim-pop` ／ `anim-iris-in` | 要"命中反馈"的力度 → `slam`；√ / 确认 / 定论 → `stamp`；轻快 → `pop`；揭示式 → `iris-in` |
| 互动 / 问答 / 选择 | 当前激活项 / 聚焦 | `idle-glow` ／ `idle-ring` ／ `idle-shimmer` ／ `anim-zoom-out` | 让视线跟着走 → `glow`；"看这里"更外扩 → `ring`；推荐项（含蓄） → `shimmer`；再强调一次已在场的元素 → `zoom-out` |
| 互动 / 问答 / 选择 | 否定 / 纠错反馈 | `anim-shake`（晃两下） ／ `anim-slam` + 红色态 | 让"错了"看得见 → `shake`；硬否定 / 打回 → `slam` |
| 对比 A vs B | 两栏入场 | `anim-fly-left` + `anim-fly-right` ／ `anim-iris-in` ／ `anim-wipe-right` | 两侧同时来 → 左右飞入；"揭开另一边" → `iris-in`；逐栏擦出 → `wipe-right` |
| 流程 / 步骤 | **新长出一格** | `anim-fade-rise`（内联 `animation-delay` 逐个递增错峰） ／ `anim-rise` ／ `anim-drop-in` ／ `anim-unfold` ／ `anim-grow-x` | 一次长多格要"排队感" → `fade-rise` + 错峰；单格 → `rise`；放上去 → `drop-in`；先展开清单再逐条 → `unfold`；线 / 进度 → `grow-x` |
| 流程 / 步骤 | **同位替换 / 纠错** | `anim-slam` ／ `anim-stamp` ／ `anim-pop` ／ `anim-blur-in` ／ 旧内容 `gone` + 新内容淡入 | 强调"错了→改对" → `slam`；盖章式替换 → `stamp`；温和更新 → `blur-in` |
| 流程 / 步骤 | **强调已有格** | `idle-glow` ／ `idle-ring` ／ `idle-shimmer` ／ 静态描边 | 只引导视线 → `glow` / `ring`；怕晃 → 静态强调 |
| 流程 / 步骤 | **收口 / 归位** | `anim-fly-left` + `anim-fly-right` ／ `anim-scatter` ／ `anim-iris-in` ／ `anim-slam` | 多元素从两侧聚拢 → `fly`；碎片从四面收拢 → `scatter`；单一结论 → `iris-in` / `slam` |
| 总结 / 回顾 / 清单 | 条目依次入 | `anim-fade-rise`（错峰） ／ `anim-unfold` + 子项错峰 ／ `anim-drop-in` | 目录感、收束感；先立清单框架再逐条填 |
| 全部课型 | 素材 / 截图登场 | `anim-blur-in` + `idle-kenburns` | 有真素材就满幅放，代码只做标注 |
| 全部课型 | 装饰层 | `idle-float` ／ `idle-bob` ／ `idle-breathe` | 贴纸 / 云 / 星星可以一直动；**别给主体加** |

> **同课型 ≠ 同动效**。早前这句写作"同课型用同一套动效完全正确"，结果被当成"9 帧全 `fadeRise`"的合法依据（2026-10-14 L9 实测）。正确的说法是：**课型只是第一根轴，同一课型内部必须按"角色"分**——一支课里同一课型占多数时（如"算法=一步一步"），角色分才是动效变化的主要来源。
>
> **轮换规则（硬要求）**：
> - **相邻帧不得同角色同动效**（第 1、2 帧都是"新长出一格"，就要换候选池里的另一个：`fade-rise` ↔ `rise` ↔ `pop`）。
> - **同一动效在 visual 帧里连续出现 ≤2 帧**；整支课里任一动效占 visual 帧动效总数 **≤50%**（>50% 会被 `qc_variety.py` 报出来）。
> - 同一帧内部**允许多种**：主图 `iris-in`/`pop` + 卡片 `fade-rise` 错峰互不冲突——**"一帧一种动效"本身就是单调的来源**。

⛔ **这些 class 必须挂在 `.step.on` 门控下**（机制与例外见 §四"能力边界"）——放映版每一步默认 `opacity:0`，无条件 `animation:` 会在页面加载时就播完，点亮时只剩终态：**不报错、不丢内容，入场效果静默消失**。

### 入场动效选型表（每条都写了何时用）

| 片段 | class / MO.entrance(kind) | 何时用 | 别用 |
|---|---|---|---|
| 缩放弹出 | `anim-pop` / `pop` | 答案卡、贴纸、重点词出现 | 大段正文（太跳） |
| 砸入 | `anim-slam` / `slam` | 金句、大数字、主词落定 | 普通要点 |
| 上浮淡入 | `anim-fade-rise` / `fadeRise` | 要点、列表、老师/学生气泡 | 需要冲击的强调物 |
| 模糊浮出 | `anim-blur-in` / `blurIn` | 真实截图/照片/课件大图登场 | 文字卡 |
| 向内溶解 | `anim-iris-in` / `irisIn` | 从大图钻进某细节、揭示卡片内容 | 整屏换景 |
| 飞入 | `anim-fly-left/right` / `flyLeft/flyRight` | 对比两栏、两角色/两选项 | 单一主体 |
| 逐字上浮 | `MO.charsIn(el)` | 标题、关键词 | 长句（拆太碎） |

### 转场选型表（帧间切换）

| 转场 | MO.transition(kind) | 何时用 |
|---|---|---|
| 向内溶解 | `iris` | 聚焦/进入下一步，最柔和 |
| 百叶窗 | `blinds` | 揭幕感、节奏明快 |
| 擦除 | `wipe` | 左→右推进，像翻页 |
| 飞入 | `fly` | 新画面从下升起 |
| 淡入 | `fade` | 安静过渡，不抢戏 |

### 持续微动（落定后停住；只给素材/装饰层）

| 微动 | class / MO.continuous(kind) | 何时用 | 别用 |
|---|---|---|---|
| Ken Burns | `idle-kenburns` / `kenburns` | 大截图/课件总览"看全并浏览"（F1 类） | 要点卡（不稳） |
| 闪烁渐变 | `idle-glow` / `glow` | 状态 chip / 当前激活卡 / 正在说话的一方 | 满屏元素全加（晃眼） |
| 漂浮 | `idle-float` / `float` | 背景装饰、环境层 | 主体 |

---

## 三、做坏方式清单（开工前、交付前各对一遍）

1. **翻页式 PPT**：固定页眉页码、要点逐条匀速淡入、每镜匀速慢推、结尾落回居中金句卡。→ 去掉页框，一帧一个视觉事件，入场用脉冲（pop/slam），不是匀速推。
2. **照搬上一课**：直接复制上一课 HTML 改台词，动效套路化。→ 只学做法，动效按本帧课型从本库挑。
3. **死背景、空画面**：大块纯色底一直不变，只有中间一小块动。→ 主体放大占画面一半以上，背景跟着内容换。
4. **有真实素材却用代码画**：截图/照片满幅放，代码只解释标注。→ 真实素材当主画面（`blurIn`+`kenburns`）。
5. **一眼 AI 味 / 每课拼贴**：每课换一套画风拼贴。→ 全片一套风格（当前默认蜡笔风）；动效可以因课型不同，但画风不变。
6. **直接 `<link>` mo.css 就加 class**：库里的 `animation` 是无条件声明；分步放映/分步渲染必须在你自己那层写 `.step.on .anim-pop{...}` 门控，否则动画在加载时就跑完、点亮时只剩终态（静默失败）。要开箱即用就把需要的 keyframes 与规则复制进你的 CSS 并改写选择器。
7. **一刀切兜底动效**：写一条 `.step.on .hero .hv{animation:zoomPop}`（或任何"所有未标注主体都用同一种"的兜底）——漏标动效的元素**照样会动、但全动成一样**，把单一化藏到交付都看不出来。**兜底只允许用于装饰层**；主体（卡片/图标/笑脸/素材）必须显式声明动效。生成器/组件同理：**动效参数的默认值不许是一个会被一路复制的具体值**——要么 `None` 强制显式填，要么按角色表选（L9 的 `cards()` 默认 `rise` 就是反例）。
8. **`clear` 不按空间判（或把一版的决策照搬另一版）**：清场只有一个依据——**这一步起，页面还装得下吗**；装得下就不清场，横竖同规则。用一份帧数据生成两版时要**分别按该版空间重判**（判定用真实渲染高度，别用文字估算：估算与渲染 padding 不一致会误判），否则会出现"底部明明够、却把刚读过的内容收走"（老四台机检都不会报，用 `qc_clear.js`）。

---

## 四、怎么用

### 方式 A：纯 CSS（静态课件 / 浏览器预览）
在课件 HTML `<head>` 引入：
```html
<link rel="stylesheet" href="$SK/assets/anim-snippets/mo.css">
```
给元素加 class 即生效：
```html
<div class="sticker anim-pop">答案是 B</div>
<div class="hero-img idle-kenburns">…截图…</div>
```
要重播：移除再添加 class（catalog.html 的"重播"按钮即此原理）。

⚠️ 分步放映/分步渲染（本 skill 默认管线）**不能只用 `<link>` 方案**：必须改写成 `.step.on .anim-pop{...}` 门控，见 §五。

### 方式 B：GSAP 时间轴（HyperFrames 渲染成片）
在课件 HTML 引入 GSAP 后引入：
```html
<script src="$SK/assets/anim-snippets/mo.gsap.js"></script>
```
在构建时间轴时用：
```js
const tl = window.__timelines["root"];
MO.entrance(tl, "#answer", "slam", 12.4);          // 12.4s 砸入答案
MO.entrance(tl, ".point", "fadeRise", 13.0, {stagger:0.15}); // 要点依次浮现
MO.transition(tl, "iris", 24.95);                   // 24.95s 向内溶解转场
MO.continuous("#hero", "kenburns");                // 大图持续浏览
```
无 GSAP 时 `MO.entrance` / `MO.continuous` 自动降级为 CSS class，不报错。

### 预览本库
打开 `catalog.html` 可逐条看每个片段的效果并"重播"；某帧该配哪些片段，先查第二节的课型决策表。

---

## 五、能力边界（两条轨：CSS 与 GSAP，都能进片）

默认管线 = `make_standalone.py`（把 report.json 变成分步时间轴）+ `capture_anim.js`（虚拟时钟逐帧抓图）。抓帧走 `document.getAnimations()`，它只认 **CSS 动画 / WAAPI**；**GSAP 走另一条注入的路**（2026-10-15 打通）：

| 能力 | 状态 | 说明 |
|---|---|---|
| `mo.css` 全部 26 条（`anim-*` / `idle-*`） | ✅ 进片 | 但必须自己写 `.step.on` 门控（§三.6） |
| `MO.entrance / MO.transition / MO.continuous / MO.charsIn`（GSAP 轨） | ✅ 进片（**需按下面三步接**） | ① 时间轴用 `MO.timeline()` 建（或 `MO.register(tl)` 登记）；② 页面自己的时间轴代码写在 **`<script id="mo-timeline">`** 里；③ `make_standalone.py` 自动内联内置的 gsap + `mo.gsap.js` + 那段脚本，并在生成的 `applyTime(t)` 里调 `MO.seek(t)` 把时间冻结在 t |
| GSAP 插件：**DrawSVG（描线）/ MorphSVG（形变）/ MotionPath（路径）** | ✅ 进片 | 内置在 `assets/vendor/`（离线）；白板 / 手绘风格的底座。用时在页面里按需 `<script src>` 引入即可 |
| `mo-trans-iris/blinds/wipe/fly`（帧间转场） | ⛔ 无落点 | `make_standalone` 不注入转场覆盖层 → **默认管线不做帧间转场**；要用得自己给 4a 加注入点 |
| GSAP 直接 `gsap.to()` 不登记时间轴 | ⚠️ 会退化为 globalTimeline seek | 能生效但不受控：登记过的 `MO.timeline()` 才逐个精确 seek |

> 一句话：**CSS 写在 `.step.on` 选择器下的动画、或经 `MO.timeline()` 登记并由 `MO.seek(t)` 驱动的时间轴**，才进得了成片。
> 两条轨可以混用（同一帧：主图走 GSAP 路径，卡片走 CSS 错峰），但**同一元素别同时挂 CSS class 和 GSAP tween**（会互相覆盖）。
> **离线**：gsap 全家（core + 三个插件，v3.15.0）已内置在 `assets/vendor/`，`make_standalone` 会内联进 standalone，课堂放映不依赖网络。许可与出处见 `assets/vendor/gsap.LICENSE.txt`。

### GSAP 轨最小用法

```html
<script src="../../../assets/vendor/gsap.min.js"></script>
<script src="../../../assets/vendor/MotionPathPlugin.min.js"></script>
<script src="../../../assets/anim-snippets/mo.gsap.js"></script>
...
<script id="mo-timeline">           <!-- ← 必须用这个 id：make_standalone 原样带进 standalone -->
  gsap.registerPlugin(MotionPathPlugin);
  var tl = MO.timeline();                                  // 建 + 登记（浏览器里照常自动播放）
  MO.entrance(tl, '#card', 'pop', 1.0);                    // 复用 CSS 同款入场（脉冲）
  tl.to('#dot', { x: -360, y: -200, rotation: 360,         // GSAP 独有：曲线位移 / 旋转 / 形变
                  duration: 1.2, ease: 'power2.inOut' }, 2.0);
</script>
```

## 六、回流

每做完一支新课：哪种课型用了哪种动效效果好，写进本文件第二节的决策表（做法＋何时用）；踩到的动效坑写进 `references/known_pitfalls.md`（§5 动效）。**不要为了和上一课不同而非要不同**——同课型用同一套动效完全正确，只有课型变了才换。

## 七、常量表（class / 时长 / 类型 / 用途）

> **新增动效后跑**：`python3 gen_catalog.py .`（在本目录下）——它会重生成 `catalog.html` 与本表，
> 并断言 **`mo.css` 里每个 `.anim-*` / `.idle-*` 都必须出现在目录里**（漏了就报错），顺带同步名称/用途。

<!-- 常量表:start（由 gen_catalog.py 生成，勿手改）-->

本表与 `catalog.html` 同源（26 条）：要看效果直接开目录页，要查时长/用途看这里。

| class | 时长 | 类型 | 用途 |
|---|---|---|---|
| `anim-pop` | .50s | 入场 | 答案卡、贴纸、重点词出现（带过冲） |
| `anim-slam` | .42s | 入场 | 金句、大数字、主词落定（猛一下回弹） |
| `anim-stamp` | .34s | 入场 | √ / 确认 / 结论落定（又快又硬，带一点歪） |
| `anim-drop-in` | .52s | 入场 | 把一格或一枚贴纸放上去、归位 |
| `anim-zoom-out` | .48s | 入场 | 强调已经在场上的元素（镜头收回来） |
| `anim-swing-in` | .62s | 入场 | 挂着的贴纸或招牌甩两下停住 |
| `anim-fade-rise` | .50s | 入场 | 要点、列表、老师或学生气泡（两端停稳） |
| `anim-rise` | .50s | 入场 | 单格内容落位（比 fade-rise 更轻） |
| `anim-iris-in` | .55s | 入场 | 从大图钻进某处、揭开另一半 |
| `anim-wipe-right` | .55s | 入场 | 像掀纸一样展开信息板或答案区 |
| `anim-unfold` | .45s | 入场 | 清单、卷轴、菜单从顶边撑开 |
| `anim-blur-in` | .60s | 入场 | 真实截图、照片、课件大图登场（像对焦） |
| `anim-write` | .75s | 入场 | SVG 线条画出来：笑脸的圆、路线、箭头（需 pathLength=1） |
| `anim-grow-x` | .50s | 入场 | 下划线、连接线、进度条伸出来 |
| `anim-fly-left` | .50s | 入场 | 两物对比的左件、从左边归位 |
| `anim-fly-right` | .50s | 入场 | 两物对比的右件、从右边归位 |
| `anim-flip-y` | .55s | 入场 | 翻出一张新卡、换个选项看看 |
| `anim-scatter` | .50s | 入场 | 一组碎片从四个方向收到位（容器类） |
| `anim-shake` | .42s | 入场 | 错了、不行（左右晃两下；别用来表达惊讶） |
| `idle-kenburns` | 9s | 持续 | 真照片、大图（主体别用，会显得不稳） |
| `idle-glow` | 1.6s | 持续 | 让视线跟着走的当前格 |
| `idle-ring` | 1.8s | 持续 | 看这里的聚焦提示（比 glow 更外扩） |
| `idle-shimmer` | 2.6s | 持续 | 推荐项、当前项（比 glow 含蓄） |
| `idle-float` | 4s | 持续 | 飘着的贴纸、云、星星（装饰层） |
| `idle-bob` | 2.8s | 持续 | 小物件上下晃（比 float 快） |
| `idle-breathe` | 3.4s | 持续 | 待机的装饰物（主体别用） |

<!-- 常量表:end -->
