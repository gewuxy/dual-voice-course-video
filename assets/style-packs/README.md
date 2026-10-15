# 风格包契约（Style Pack）· v1

**目的**：让"内容/版式"与"长什么样"彻底分开。同一份内容 HTML，换一个 pack 就换一种风格；新增风格＝新增一个目录，**不动管线、不动母题、不动动效**。

```
assets/
  layout/                 中性层：版式语法 + 母题（visual 8 + dialog 6）+ 中性交互 demo
    README.md               四层模型 / 硬线 / 母题库 / 风格包接口
    style-demo.html         同一份内容换包自证（?style=pixel|crayon）
  style-packs/            风格层：只提供"皮肤"
    README.md               本契约
    crayon/                 蜡笔风（正式）：皮肤 + 帧骨架参考件 + 封面模板 + intro/ 片头素材
    pixel/                  像素风（正式）：皮肤 + preview.html
    _wip/watercolor/        水彩风（未达标归档，勿用于正式课）
  anim-snippets/          中性层：动效 26 条 + GSAP 轨 + catalog.html
  interactive/            交互层（规划中）
  vendor/                 第三方（gsap + 3 插件，离线内置 + 许可说明）
```

**正式支持两种风格**：`crayon`（蜡笔风）、`pixel`（像素风）。两者共用同一套中性母题、动效与管线——**换风格 = 换一个 pack 目录**。
`_wip/watercolor` 是未达标归档（对比度/字体 5 项不过），修好可复活。

## 一、分层职责

| 层 | 文件 | 能定义什么 | 禁止 |
|---|---|---|---|
| 中性·版式语法 | `neutral/*.css` | 栅格、间距梯度、安全区、热区尺寸、层级顺序 | 颜色、字体、圆角、描边、阴影、纹理 |
| 中性·母题 | `neutral/*.html` | 骨架结构与语义类名（`.bubble` / `.card` / `.btn` …） | 任何具体视觉值 |
| 中性·交互 | `neutral/*.js` | 拖拽、判定、对错、进度（只切**状态类**） | 直接写样式 |
| **风格包** | `style-packs/<pack>/pack.css` | ① 全部 tokens ② 语义类 → 皮肤 ③ 纹理/装饰 | 改动结构、改类名、写死尺寸导致溢出 |

## 二、tokens（风格包必须定义这一组）

| token | 含义 | 蜡笔风示例 | 像素风示例 | 水彩风示例 |
|---|---|---|---|---|
| `--paper` | 页面底色 | `#FFFDF4` | `#1B1B2F` | `#FBF7EF` |
| `--stage` | 舞台/卡片底 | `#FFFCF2` | `#22223B` | `#FFFDF8` |
| `--ink` | 主文字/描边 | `#3A3226` | `#F2F2F7` | `#3B3A36` |
| `--ink-2` | 次级文字 | `#7A6E5C` | `#9A9AB0` | `#7C756B` |
| `--a1 / --a2 / --a3` | 三个强调色 | 黄 / 粉 / 青 | 荧光青 / 品红 / 柠檬 | 赭 / 青 / 藤黄 |
| `--ok / --err` | 对 / 错 | 绿 / 红 | 亮绿 / 橙红 | 苔绿 / 砖红 |
| `--radius` | 圆角 | `18px` | `0` | `22px` |
| `--border-w` | 描边粗细 | `5px` | `4px` | `2px` |
| `--shadow` | 投影（可硬边） | `7px 8px 0 …` | `0 6px 0 …` | `0 10px 24px -12px …` |
| `--font-title / --font-body / --font-hand` | 字体三档 | 圆体 / 圆体 / 娃娃体 | 等宽像素感 / 系统 / 等宽 | 楷体 / 宋体 / 楷体 |
| `--texture` | 背景纹理（可空） | 点阵 | 扫描线 | 纸纹 |

## 三、语义类名（风格包按此写皮肤；改名＝破坏契约）

`.stage` `.frame` `.brand-row` `.chip` `.brand` `.title` `.bubble`＋`.bubble--t/-s` `.card`＋`.card--ok/-err/-sel/-ghost` `.pill` `.btn`＋`.btn--ghost` `.progress`＋`.seg` `.star` `.feedback`＋`.feedback--ok/-err` `.hint` `.panel` `.footer`

## 四、验收（每个新 pack 必过）

1. 打开 `style-demo.html?style=<pack>`，**内容与结构一字不改**；
2. 母题不溢出/不重叠（量 DOM 几何，不靠目测）；
3. 触摸热区 ≥88×88px；
4. 文字对比度 ≥4.5:1（浅色纸底上的次级文字最容易不达标）；
5. 反馈 ≤0.6s 内可见。
