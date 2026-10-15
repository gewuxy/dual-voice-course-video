# 版式层（layout）· 中性资产 · 与风格无关

**这一层的所有内容不随风格变化**。换风格只换 `assets/style-packs/<pack>/`，本层一行不动。
分层职责（四层模型）：

| 层 | 是什么 | 例子 | 住哪 | 随风格变？ |
|---|---|---|---|---|
| **L0 结构契约** | 帧/步/DOM、时间轴接口、数据属性 | `.stage-frame > .step`、`applyTime(t)`、`data-layout` / `data-scene` | `references/stages/2-slides.md`（结构契约）+ 管线脚本 | 否 |
| **L1 版式语法** | 栅格、间距梯度、呼吸硬线、触摸热区、断行 | 间距 6/10/16/24/36/52、块间距 44、图形↔标注 ≥28、主体↔气泡 ≥28、热区 ≥88 | **本文件 §二** | 否（数值由 tokens 落地） |
| **L2 版式母题** | 画面骨架（含 dialog） | 竖排流程图 / 步骤卡 / 阶梯 / 时间轴 / 对比 / 找错 / 母视觉 / 大素材 / dialog×6 | **本文件 §三** | 否 |
| **L3 风格皮肤** | 色板、字体、描边、圆角、纹理、品牌、封面 | 蜡笔风、像素风 | `assets/style-packs/<pack>/` | **是** |
| **L4 动效** | 入场/持续动效 + GSAP 时间轴 | `anim-*` / `idle-*` / `MO.*` | `assets/anim-snippets/` | 否（按课型×角色，不按风格） |

**切分原则**：**母题的骨架与规则中性；具体度量由风格包以 tokens 注入**。
（因为二者耦合：蜡笔风 7px 描边让内容天然大一档、圆体-简的字宽决定每行几个字——所以不是"母题属于风格"，而是"中性母题 + 风格 tokens"。）

---

## 一、资产索引

```
assets/
  layout/                  ← 本层：版式语法 + 母题 + 中性交互 demo
    style-demo.html           中性演示页（?style=pixel|crayon 实时换包 = 架构自证）
  style-packs/             ← 皮肤层（每个 pack 只定义 tokens + 语义类皮肤）
    README.md                 风格包契约（tokens 清单 / 语义类名 / 验收五条）
    crayon/                   蜡笔风（正式）：皮肤 + 帧骨架参考件 + 封面模板 + intro/ 片头素材
    pixel/                    像素风（正式）：皮肤
    _wip/watercolor/          水彩风（未达标归档：对比度/字体 5 项不过，勿用于正式课）
  anim-snippets/           ← 动效层（中性）：26 条 CSS + GSAP 轨 + catalog.html 预览
  interactive/             ← 交互层（规划中，见其 README）
  vendor/                  ← 第三方（gsap 3.15.0 + 3 插件，离线内置，含许可说明）
  sfx/                     ← 音效素材（中性）
```

## 二、版式语法（L1 硬线，**权威定义在此**）

| 规则 | 数值 | 机检 |
|---|---|---|
| 间距梯度 | 6 / 10 / 16 / 24 / 36 / 52 px（`--sp-1..6`） | 目视 |
| 同屏块间距 | ≥44px（低于 30 报警） | `qc_overlap.js` |
| 图形 ↔ 其标注 | ≥24px（目标 28–32） | `qc_overlap.js`「主体呼吸」段 |
| 主体（含标注）↔ 气泡 | ≥28px（负值=重叠） | 同上 |
| 内容底沿 ↔ 品牌行 | ≥32px | `qc_overlap.js` |
| 字幕安全区 | 横版 900px / 竖版 1120px 以下只放品牌行 | `qc_frames.js` |
| 触摸热区 | ≥88×88px（K-2 手指粗、动作大） | 交互层验收 |
| 文字对比度 | ≥4.5:1（小字）、≥3:1（≥22px 粗体） | 风格包验收第 4 条 |
| 画面文字预算 | visual 帧按 `data-layout` 分管，≤2 行短句 | `qc_frames.js` |
| 图形尺寸 | **按场景盒可用高度算**：`可用 = 场景盒高 − 2×呼吸 − 标注高 − 间距` | 只按 ratio 拍必然溢出（known_pitfalls §4） |

母题排完的检查流程（命令、清场、动效清单表）在 `references/stages/2-slides.md`。

## 三、母题库（L2）

### 3.1 visual 母题（8 个，可混排）

做 visual 帧时先挑一个骨架再填内容；同一支课**建议至少用 3 种**，相邻帧尽量不同（建议，不是硬约束）。

| 母题 | 长什么样 | 适合 | 动效角色（`anim-snippets/README.md` §二） |
| --- | --- | --- | --- |
| **竖排流程图** | 横条卡自上而下堆，卡间短竖线连接 | 线性步骤（刷牙/出门准备/安装） | 新长出一格 → `anim-fade-rise` + 内联 delay 错峰 |
| **横向步骤卡** | 一排方卡 + 数字徽章（可加 `→` 连接） | 并列要点、4 步以内 | 一次给全 → `anim-pop`；逐条 → `fade-rise` |
| **阶梯** | 格子逐级升高（左→右 / 下→上），空格用虚线 + `?` | 排序游戏、由易到难、逐级推进 | 同位替换 → `anim-slam`；当前格 → `idle-glow` |
| **时间轴** | 一条轴 + 挂在轴上的节点卡（横版横轴 / 竖版竖轴） | 先后顺序、日程、成长序列 | 收口归位 → `anim-fly-left` / `anim-fly-right` |
| **对比双栏** | A / B 两栏各从一侧进入 | 概念辨析、对错、前后 | 两栏入场 → `anim-fly-left` + `anim-fly-right` |
| **找错批改** | 原图/卡片 + 红圈 / `✗` / 正确项并排 | 纠错、顺序反例 | 错误项 → `anim-slam`（红）；正确项 → `fade-rise` |
| **母视觉 + 分解** | 中央大主体（脸/机器人/图），四周标注逐步长出 | 讲结构、逐步揭示 | 主体 → `anim-iris-in` / `anim-pop`；标注 → `fade-rise` |
| **大素材帧** | 真照片/截图满幅 + 一句标注 | 有真素材时（蛋糕、地图、实拍） | `anim-blur-in` + `idle-kenburns` |

**画出来（`anim-write`）**：任何"过程要画出来"的母题（笑脸、路线、下划线）用 SVG 描线（路径带 `pathLength="1"`）。

### 3.2 dialog 母题（6 个）——**dialog 也是版式母题**

`data-layout="dialog"` 决定的是「**两个角色轮流说话**」的信息结构（谁在说、几轮、气泡先后、留白在哪），属版式；气泡的粉/蓝、圆角、描边属皮肤。

| 子母题 | 结构 | 动效角色 | 用在 |
| --- | --- | --- | --- |
| `dialog-single` | 一问一答（气泡贴合内容，不拉满宽） | 气泡 → `fade-rise` | 引入、确认 |
| `dialog-chase` | 递进追问（"最后一步呢？"） | 追问气泡 → `fade-rise`；提示 → `idle-glow` | 引导孩子往下想 |
| `dialog-correct` | 错误 → 纠正（带 `✗` 态） | 错→`shake`/`slam`；改正→`stamp` | 纠错、找错 |
| `dialog-chorus` | 齐读 / 跟读重复 | 重复句 → `fade-rise` | 记忆点、口令 |
| `dialog-with-hero` | 气泡 + 主视觉并置（不遮挡） | 主体 → `pop`/`iris-in` | 讲 + 看同时 |
| `dialog-clear` | 清场式收尾（旧气泡淡出） | 清场只在**放不下**时用（横竖同规则） | 帧尾、告别 |

**排完必检**：`node scripts/qc_clear.js <两版 html>`（放得下却清场/装不下却没清场）、`qc_overlap.js`（重叠 + 主体呼吸）。

## 四、风格包接口（L3）

风格包＝一个目录，只允许出现：**tokens（CSS 变量）+ 语义类皮肤 + 纹理/装饰 + 该风格的素材与封面**。
契约（tokens 清单、语义类名、验收五条）见 `style-packs/README.md`。

- **正式支持**：`crayon`（蜡笔风）、`pixel`（像素风）
- **归档**：`_wip/watercolor`（未达标：ink-2 4.08:1、名标签 2.35:1、卡片分离 ~3:1、按钮 ~3.5:1、全站楷体——修好可复活）

**新增一种风格的完整动作**：① 复制一个 pack 目录改 tokens；② 跑 `style-demo.html?style=<新包>` 看母题是否都成立；③ 过验收五条；④ 在 `style-packs/README.md` 登记。
**不需要**改母题、动效、管线、脚本——这是这套分层的目的。

## 五、中性验证入口

```bash
# 同一份内容、两个皮肤（内容与结构一字不改）
open assets/layout/style-demo.html                     # 默认 pack
open "assets/layout/style-demo.html?style=crayon"
open assets/style-packs/pixel/preview.html             # 自包含预览（双击可看）
```
