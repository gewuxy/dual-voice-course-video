# known_pitfalls（通用踩坑清单）

> 本 skill 在多个课程制作中**真实踩过**的坑，已按**根因 / 主题**提炼为通用规则，**与具体课程内容无关**。换主题、换年级、换语言直接复用。
> 标注「已修」= 脚本已固化，新课题自动受益；标注「铁律 / 定案」= 设计或操作必须遵循。
> **风格基线（颜色/字重/模板/封面制式）在本文件里随仓库走**——这是保证克隆者开箱产出质量合格的默认值，可按自己偏好修改；`known_pitfalls.local.md`（gitignore）只记**个人覆盖**（品牌要素、本机字体、个人教学法），没有 local 文件时用默认即可。
> 动手前通读，可省掉大量返工。

---

## 1. 剧本与台词：吞字（TTS 丢字，最隐蔽，须重点防）

- **孤立即拉丁字母被吞（X / O 等）**：中文 TTS 前端对「夹在汉字中间的孤立拉丁字母」归一化不稳定，O 命中率最低；同一字母同课里时有时无。根因与权重 / ref / temperature / 语速**全都无关**，别去调这些。**铁律**：送进 TTS 的文本里 `X→艾克斯`、`O→欧`；画面字幕 / 棋盘符号保留 X / O 不动（只改送 TTS 的文本）。修法：只重合成坏句（写最小剧本 + `--only <帧号>` 到独立 outdir），拼回原帧时**原帧尾部已含 0.4s 行间间隔，别再插一次**，否则多 0.4s 空档；`report.json` 只改 dur/start，`text` 字段保持原文（字幕仍显示 X/O）。
- **「单字 + —— + 关键词」收尾吞字**：`clean()` 把「——」换成「，」，cut 按标点切出的末段成 2 字短片段被当句末直接收尾，破折号后面的关键词整段丢（重跑同文本必现，非 seed 运气）。**铁律**：剧本不写「单字——关键词」式收尾；写成「叫做 / 就叫 / 就叫做」。实测「叫做——操作」✅、「叫——操作」❌（只要把「叫」加成 2 字就不丢）。
- **童声短句消失**：`split_units` 中文过滤阈值原写 `>=4`，会整句丢掉「苹果！」「猫！」等 1–3 字童声句，现象是"学生句凭空消失"而**不报错**。已修（阈值 `>=1`，只丢纯标点 / 空串）。
- **句前停顿标记丢行**：`学生：[[1.5]]"答！"` 旧 parse 取首个 `[[n]]` 标记 → text 变空串、整行丢失。已修（`parse_line` 返回 4 元组含 pre 静音；动作行 dur+pre）。
- **断句「——」**：「——」整体作断点（len>=soft 时断在它后面），避免「话题——|我」硬断难看。
- **交付前丢字扫描（必做）**：全部帧跑「稿字数 vs ASR 字数」覆盖率，<82% 的帧重点复查。注意 ASR 自身对孤立字母转写也不稳（同段两次跑结果可能不同），**判断有没有丢字要看字数覆盖率 + 能量剖面，不要只信一次 ASR 文本**。本地 whisper 离线转写需传快照绝对路径并设 `HF_HUB_OFFLINE=1`，否则走网络代理 502 失败。

## 2. 双音色 TTS / 合成阶段

- **全量合成被沙箱 bulk-delete 守卫杀进程（EXIT=1）**：逐句合成后脚本 `os.remove` 临时文件，单轮删除数超阈值被判批量删除。修复：跑音频一律加 `--no-cleanup`（已固化为默认建议）。
- **语速机关枪**：短句不减速会念得飞快。脚本用 `TARGET_CPS` 目标字速 + 每句取样 `--takes` 取最接近者，再 `retempo` 兜底。
- **换课别手写权重路径**：脚本按 epoch 自动取最新权重（`GPT_weights/<exp>-e*.ckpt` + `SoVITS_weights/<exp>_e*_s*.pth`）。手写容易指到不存在的文件。已修。
- **产物名别记错**：实际产出是 `frame_NN.wav` + **`_merged.wav`** + **`report.json`**（没有 `lesson_final.wav` / `dialog_report.json`）。`report.json` 的 `units[].start` 是帧内每句起始秒，阶段 4 直接用它对齐。
- **帧数不要写死**：`NF=21` / `range(1,22)` 之类写死值已改为按 HTML / 剧本自动识别。
- **temperature 不是语气杠杆**：同 seed 同文本下 temp 1.0→1.3 用户听不出情绪变化（时长也几乎不变）；**ref 才是主杠杆**（换兴奋 ref 同句时长明显涨，听感明显）。别再花时间调 temperature，保持 1.0。
- **默认 ref 必须选情绪贴近用途的句子**：误用最平的一句语流当课程管线 ref，会导致全部配音偏朗读腔。选 ref 先问"这句的语气像不像我要合成的句子"。按句路由已实装（关键字 + 问号匹配 praise/cheer/question，未命中落默认），换音色 / 换语料只换路由表。

## 3. 时间轴对齐

- **多 step 堆叠在 0s（"泄题"）**：早期 `bind_delays` 给多 step 帧全 0s 延迟，整帧内容在音频开始前一次性全显。已修：step 数 == 对话行数时 1:1 锚定每句 `start`；否则帧内均匀分布。
- **`re.sub` 删 step 破坏 div 嵌套（致命）**：非贪婪正则把 step 当 static 删，会掐断嵌套 div、残留孤立 `</div>`，第 2 帧之后整屏空白（曾被误判为渲染 worker 问题）。已修：**HTML 结构原样输出，一个字符都不删**，显隐全由 JS 数据驱动。
- **frame 标签两种写法都要认**：`<div id="f01" class="frame">` 与 `<div class="frame" id="f04">` 只认一种属性顺序的脚本换课就报"缺少帧"。已修（标签配对法提取，两种都吃）。
- **standalone 内嵌 `<audio>` 会重复出声**：放映版音频若留在 standalone，成片音轨（`_merged.wav`）之外还会再响一遍。已修（默认剥掉 `<audio>`，要保留加 `--keep-audio`）。
- **帧间 gap 曾有三个副本导致音画失步（已修，勿回退）**：`_merged.wav` 帧间静音、standalone 时间轴、`make_clips` 切点原本各自写字面量 0.9，旧文档还教人传 `--gap 0.25`，结果 standalone 总时长与音频漂移 ~9.75s、末帧整段错位。现在三者统一读 `load_config.frame_gap()`（默认 0.9，改 `defaults.frame_gap` 即可改节奏），`make_standalone` 不再接受 `--gap`，并在结尾拿 `_merged.wav` 实测时长对账，漂移 >0.15s 直接报错退出。
- **帧间空隙画面清空闪烁**：standalone 里帧显示到 `gend`（含 gap）但 step 消失时间是 `gstart+fdur`，每帧切换前有 0.9s 内容全消失。已修：非 hide-at 的 step 延续到 gend；字幕末句也延长到 gend，避免帧切换时字幕闪灭。
- **字幕切换点必须进 schedule 区间**：只把 step 显隐点写进 `changes`、字幕块时间不进轴 → 截图时整个长区间都停在区间起点的那个字幕块（表现为"某帧几十秒只有第一块字幕"）。已修：每个字幕块 t0/t1 都 `changes.update(...)`。改字幕相关代码后**必须重跑 capture→frames→encode→mux 全链**，不能只重编码。
- **standalone 重生成 = 帧已过时，必须重截（哪怕以为"没变化"）**：字幕烧在帧里，帧是唯一事实。L8 实锤：重生成 standalone（加了关键词高亮）后误信旧诊断「没生效」没重截，成片烧的还是旧画面。任何 make_standalone 重跑之后，capture→encode→mux 全链重来。

## 4. 画面 HTML / 排版版式

- **每帧必须有具体的物**：抽象概念不能只写文字和图标——写出具体的物（猫/狗/网格/传感器）和它的动作。这条原是 anim-snippets README「做坏方式」之一，与动效无关，迁来此处归口。
- **真照片贴纸会把卡片顶穿页脚**：真照片做成拍立得贴纸比原 SVG 图标高一截，卡片底会超页脚线（1080 画布中页脚 ~1000）。配方：照片 118px、标签 28px、`top` 压低、标签文案一句不折行。
- **超长 base64 行不能用编辑器工具改**：`<img src="data:image/jpeg;base64,……">` 一行几十万字符，字符串匹配必然失败。**一律用 Python `str.replace` / 正则改**，并在改前把 base64 换成 `__PLACEHOLDER__` 再注入。
- **文案折行出孤字**：中文气泡宽度略窄会把最后一个字挤到下一行。修复：直接缩短文案，别去动字号。
- **累加式播放器要按"全部展开"排间距**：step 是累加的，同一帧里的右侧贴纸列 / 卡片必须按最坏情况（全部显示）留间距，否则后出现的元素会压住先出现的。
- **emoji ZWJ 组合渲染异常**：`👩‍🏫` / `🧒` 等组合 emoji 在 Chrome 截图会变方块。改用纯 SVG 简笔画或色点 + 文字。
- **字体回退**：截图前必须 `document.fonts.ready`；本机可命中的中文字体清单见 `known_pitfalls.local.md`。
- **内嵌媒体后单文件体积**：自包含可接受，但别再无脑塞高清大图。
- **ftitle 重叠根因**：`.ftitle{top:150px}`，96px 标题文字底 ≈254px——任何帧内元素 `top<260` 都会压标题。卡片一律 `top≥262`，或删图内自带标题。ftitle 必须放 step 外（帧级常显），放 step 1 里会让每帧开场全屏空白，且同一帧两步不能各有一个 ftitle（累加后会叠标题）。
- **透明 SVG 多步叠加透字**：主视觉 SVG 无底色时，前面步骤的 plain 版文字会从后面 lit 版底下透出来（两图同位叠加）。凡多状态复用同一 SVG，禁止在某状态里加独有文字，或给 SVG 加不透明底。
- **pola 标注 ≤10 字**：手写体 29px、宽 350 时超 10 字必折行。
- **自建 class 必须「先定义再引用」**：构建器凭空引用未定义类 → 所有照片退化成无样式流式 div（left/top 失效、flex 里叠出屏），且溢出检测照样通过（无样式 div 不超界）——**QC 溢出全绿 ≠ 版式正确，必须目检**。
- **视觉默认风格基线（随仓库 assets/templates/crayon/ 走，可按偏好改，勿无据弃用）**：彩色蜡笔+手绘贴纸+儿童画风；主标题字高占画面 **24–30%**、行距 ≥1.7、块间距 ≥40px（「文字太拥挤」是硬伤）。旧版平铺米底低对比排版已实测否决（标题字高仅 5.4%），勿回退。

## 5. 动效（CSS 动画）

- **容器淡入是同位卡片重影的根因**：同位替换的卡片（决策树逐步点亮、过程演示图）淡入时旧卡会透过半透明新卡显形。正确做法：容器即时切换（`transition:none`），动效全部下放到子元素。
- **带内联旋转的元素动画必须用 CSS 变量保角度**：`--pr` / `--gr`，keyframes 终帧写 `rotate(var(--pr))`，否则动画 `fill:both` 会把旋转永久抹平。
- **演示页全幅绝对定位层会静默吃掉按钮点击**：`.body{position:absolute;inset:0}` 盖满整帧，static 定位的按钮被压在下面，点击全落在透明层上——表现为「按钮点了没反应/动画不播」，且无任何报错。修法：全幅层加 `pointer-events:none`（或按钮加 `position:relative;z-index:1`）。判定演示页动效是否生效必须用无头浏览器实测点击（`document.getAnimations()` 看动画名），页面无报错 ≠ 交互正常。
- **`animation-direction:reverse` 做「从另一侧飞入」会把元素播飞**：reverse 是倒放整条动画，`fill:both` 下落定停在 0% 帧——若 0% 帧是 `opacity:0; translateX(120px)`，元素不是飞入而是飞出并**永久消失**（catalog 的 flyRight 实测落定 op=0）。正确做法：两侧各写一条 keyframes（`mo-fly-l` 从 -120、`mo-fly-r` 从 +120），都用正方向。CSS class 与 GSAP `MO.entrance` 的 kind 表方向必须逐条对账（曾出现 CSS/GSAP 两侧 x 方向都反了还不一致）。
- **转场 demo「黑层扫过黑底」全不可见**：catalog 转场卡片若 stage 是纯黑空底，`#0b0b0e` 覆盖层扫过去等于没动；且 demo 只做了「扫入」半段，`forwards` 让层永远留着。正确语义对齐 GSAP 版：stage 里放可见帧内容 → 覆盖扫入 → 末尾淡出（`.mo-trans.out` opacity 过渡）→ 移除 DOM，露出新帧。判定标准：中途截图能看到覆盖层在帧上运动、结束后层计数归零。
- **循环飞行不算「过程」**：装饰 infinite 飞行 ≠ 整理过程；要演过程就每颗元素单独一次动画（`fill:both` + 内联 `--d` 错峰 delay），落位后留在终点，堆上肉眼可见变空。台词时长必须 ≥ 最后一颗落位时间。
- **opacity 隐藏的容器里动画会提前跑完**：容器用 `opacity:0` 隐藏时，子元素 CSS 动画页面加载即开始、点亮时早已结束。所有入场 / 过程动画必须挂在 `.step.on 子元素` 选择器下，点亮才启动。
- **animation-delay 要进 shorthand**：`animation:flyOnce .85s cubic-bezier(...) var(--d,0s) both`——单独写 `--d` 变量不接 delay 位则错峰失效。
- **累积式步进的同位场景叠影**：用 `.fscene` 类 + `.step.on:has(~ .step.on .fscene) .fscene{visibility:hidden}`——注意限定「后面的 step 也带场景」才隐藏，否则无场景的收尾步会把最后场景藏光（终态开天窗）。`:has()` 需 Chrome 105+。
- **逐步生长的主视觉用内联 SVG 而非 base64 img**：内联 SVG 元素真实 DOM，页面 CSS 能选中内部类 → 只给「本步新长的部分」挂动画，已长出部分静止；base64 `<img>` 只能整图弹（等于每步全部重来）。
- **SVG 视口裁切伪装成「卡片挡图」**：无 viewBox 的 SVG 按属性尺寸裁切，被裁元素贴别的卡片时看起来像被挡。排查：算 `max(cy+r、文字 y)` 是否 > 画布高；修法加高画布并重算 img 显示高度（img 高 = 宽 × 画布高 / 画布宽）避免压到下方气泡。
- **path 画线动画**：`pathLength="100"` 归一化，`stroke-dasharray:100;stroke-dashoffset:100`，keyframes `to{stroke-dashoffset:0}` 即可通用画线，不用算真实路径长度。
- **CSS 入场动画 + `.sticker::before` 白底盖彩色背景**：动效模板下 `.sticker` 成层叠上下文后其 `::before(z-index:-1)` 会绘在元素背景之上。动效模板下必须 `.sticker::before{display:none}`。排查：computed style 是绿的但截图是米白 → 层叠上下文问题。
- **过程类演示要有起点**：分类 / 排序演示必须先给"混乱的一堆"起点帧，再逐层出现分类结果，不能只给最终结果。
- **截图前必须等动画完成**：capture 在 applyTime 后只等 90ms 截图 → 新 step 拍在渐入 ~20% 处（视频里"先置灰、下个区间才正常"）。冻结视频版所有 transition/animation（`transition:none !important`），或把等待提到 ≥500ms。

## 6. 音频响度 / 混流

- **成片混流一律用官方 `_merged.wav` 原样，禁加单遍 loudnorm（L8 v2 定案）**：单遍 loudnorm 是**动态压缩**，会把语音压平压闷——L8 竖版 v1「听着发闷」的真凶就是它，返工实锤。横竖版共用同一份 `_merged.wav` 时响度天然一致（实测 -23 LUFS），成对发布听感统一。（历史背景：GPT-SoVITS 直出约 -19 LUFS 偏小，旧流程曾用两遍式 loudnorm 归一到 -16；**若确需响度归一只允许两遍式**：第一遍 `loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json` 测 input_i/TP/LRA/thresh，第二遍带 measured_* + `linear=true` 线性归一不压动态——且横竖版必须同参。诊断链不变：`volumedetect`（有没有声）→ `ebur128`（LUFS）→ 定量判断，不要凭文件存在就认为正常。）
- **配乐音轨数必须 = 1**：`ffprobe -select_streams a -show_entries stream=index` 数 =2 说明配乐和复用件一起混进去了。配乐生成器必须可复现（固定 seed + 固定峰值归一），否则每次重做音乐都不同，没法做 A/B 也没法定稿。
- **不要卡点铃铛**：在动画卡点各加一声铃铛，听感是"音乐之外还多了一层叮叮声"。节奏交给画面，不要用音效打点。
- **音效 / 字幕等精确落位一律用 silencedetect 实测静音窗口**：`report.json` 的 `units` 时刻偏差可达 6s+（dur 疑似把句后停顿计入），只用于粗对齐，别据此落音效。
- **内容型音效要大音量**（如 0.85），别沿用背景乐的 0.32。

## 7. 切片引流

- **切割必须按 report.json 帧边界**：帧时间 = Σ前面帧dur + frame_gap×帧序（gap 取 `load_config.frame_gap()`，与 `_merged.wav` 同源），切段 = 帧N起点 → 帧N+1起点减一个 gap，天然句子边界对齐；直接凭感觉 `-ss` 会切半句。
- **一条 ffmpeg 命令别抽两帧**：`-ss A -i x -frames:v 1 f1.jpg -ss B ... f2.jpg` 两个输出会自动映射错乱（可能都取第一个输入）。QC 抽帧一律一条命令一帧。
- **concat 卡片音频用 aevalsrc 静音段**：钩子 / 引导卡无声，正片有声，各段必须等长同格式（stereo 44100）；钩子卡静置即首帧可当封面，正片第一句即入题（黄金 3 秒）。

## 8. 合成 / 编码

- **concat PNG 无音轨**：`ffmpeg -i shot_%04d.png … -c:a aac` 会静默忽略 `-c:a`（PNG 序列本身无音轨），成片无声。必须两步：先出无声 `video_silent.mp4`，再 `-c:v copy -c:a aac` 混 `_merged.wav`。
- **PSNR 量化误区**：① `crop` 与 `psnr` 不能同一条链；② 比对帧必须对齐到**同一全局时刻**，拿错帧会得到虚假 21dB 低分，对齐后 48.8dB。
- **ffmpeg 时间轴错误路径（全部实测翻车）**：① `-framerate 30 -i shot_%04d.png`（帧数变 1.4s）；② concat demuxer + duration 输出 VFR，时刻错位；③ concat 输入加 `-r 30` → 总长被拉偏。**唯一可靠：按 30fps 生成硬链接帧序列 `frames/f%05d.png` 再 `-framerate 30` 读入**。
- **crf 体积 / 画质权衡**：`crf 20` → 约 15MB / 48.8dB（正式版）；`crf 16` → +140% 体积仅 +0.35dB，除非高清存档否则不值；微信轻量版 `-crf 26 -vf scale=1280:-2`。
- **字幕条机制与默认样式（默认值=代码 SUB_CSS，克隆即得；改样式进 local 记录偏离）**：放页脚上方 `bottom:104px`（竖版）/ `bottom:26px`（横版）；老师默认横版 `#1D2D49` 深蓝 700 / 竖版 `#C17F59` 暖陶棕 400（与米黄纸感背景统一）、学生 `#C2255C` 粉；关键词 `.kw` 黄底 `#F6E360` 橙字 `#D9480F`、1.12em（词表来源见下条）；**单行 nowrap，不折行、不缩字**，长句由分句器分段显示。只改 standalone，**`index_present.html`（老师上课用）完全不动**。
- **分句长度上限由最窄版型决定，横竖版同用一套（勿只改一边）**：可用宽 = 版宽 −120px（竖版 1080−120=960px、横版 1920−120=1800px）。上限 = 可用宽÷34px 再留关键词放大（1.12em）与内边距余量 → **竖版卡死在 26 字**（26×34=884<960）；横版虽然放得下约 50 字，仍同用 26——单行过长低龄读不了，且横竖版共用分句器、字幕节奏一致好维护。**超限硬断必须回退到最近的弱标点（，、：；）处切，禁止切在词中间**（横版旧版「…什么特 / 征」断词实锤，还顺带吞掉一次关键词高亮）。改分句相关任何代码后，standalone 重生成即变 → **必须重截帧再重编码，不能只重编码**（烧帧字幕，帧是唯一事实）。

## 9. QC

- **逐 step 截图必须先清掉其它帧的 `.active`**：否则上一帧内容残影叠在图上（曾误以为画面 bug）。
- **QC 脚本要等转场动画**：帧内元素有淡入 / 位移，切帧后立刻截图会拍到"半透明未到位"状态。稳定等待 450–550ms 再截。
- **溢出阈值**：元素底边相对 1080 画布 >1000px 即会被底部品牌条裁切，必须修；脚本会列出具体帧与数值。
- **截总览图用系统 python**：托管版 python 没装 PIL。
- **QC 溢出全绿 ≠ 版式正确，必须目检**（见 §4 自建 class 坑）。
- **grep 查 JSON 内嵌 HTML 必用宽模式**：SUBS 等数据经 `json.dumps` 注入，引号是转义的 `class=\"kw\"`——`grep 'class="kw"'` 或单 `.` 通配都匹配不到，误报 0（L8 曾据此误判「高亮机制没生效」）。用 `class=..kw` 这类多点宽模式，或直接用 Python 按真实转义形式匹配。同理：**对"没生效"的下结论前，先换一种匹配方式复核一次**。

## 10. 封面（阶段 5）——默认制式随仓库模板走，个人品牌要素在 local

- **视频号信息流按 1:1 居中裁切**：竖版封面 **1080×1260 取 y=90~1170**（与 SKILL.md 阶段 5 / stages/5-cover.md 同口径；旧稿 1080×1920 取 y=420 已作废，对 1260 高的图执行会越界失败）。标题 / 品牌 / 年级必须压进安全区，自查图 `ffmpeg -vf crop=1080:1080:0:90`。
- **双封面固定制**：横版 1920×1080 课件封面 + 竖版 1080×1260 对决版式（模板 `assets/templates/crayon/` 同目录配套文件），每课另出 1:1 裁切自查图。品牌徽章/标语文案属个人品牌 → 见 local。

## 11. 教学设计原则（用户定案）→ 已移至 `known_pitfalls.local.md`

- 通用版不含教学偏好；与互动课教学法相关的定案全部在 local。

## 12. 路由 B 本地 TTS 跨平台兜底

- **起因**：初版兜底只支持 macOS `say`，其他平台用户会卡死在阶段 3。重构为 `dialog2audio_local.py` 平台后端抽象：darwin→say / win32→PowerShell+System.Speech(SAPI) / linux→espeak-ng。
- **Windows 编码坑**：中文文本绝不能走命令行参数或 .ps1 文件（GBK 控制台 / 编码损坏），必须用 `powershell -EncodedCommand`（UTF-16LE base64）+ SSML here-string 传递。SSML 失败时 Python 层自动重试纯文本 Speak + Rate。
- **师生双声差异化（三平台）**：macOS 两个声音 + 抬调；Windows 枚举中文声音取两个不同 voice，仅一个时 SSML pitch+25%；espeak 学生 -p 80 vs 老师 -p 50。
- **采样率合同**：统一重采样到 32k（ffmpeg 是流水线硬依赖）。
- **实测状态**：macOS 分支已真机实测；**Windows SAPI 与 Linux espeak 分支尚未真机实测**，首个对应平台用户反馈时优先排查中文语音包是否安装。preflight 路由 B 检测也要按平台分支（uname -s）。

## 13. 静帧截图拍到入场动画中间态（L8 实翻车）

- **现象**：成片里元素半透明+位移定格整段区间（say 气泡悬在半空盖住徽章/标题、chips 级联延迟的后几颗几乎不可见），且机检全绿（PSNR 对的是同源 shots，抓不住）。
- **根因**：动效全挂在 `.step.on` 的**后代选择器**上（`.step.on .slot.say` / `.step.on .chips>*` …），standalone 冻结块只覆盖 `.step`/`.stage-frame`/`#subtitle`/`#subbar` 容器自身——animation 不继承，子元素动画照跑；capture 在 applyTime 切类后仅等 90ms，0.45–0.68s 的入场动画全被拍在半路，而该截图要静止挂满整个区间（数秒）。
- **为什么后来才爆**：冻结块与 90ms 自 skill 打包初始版就有；L7 出片在打包之前（其存档 standalone 无冻结块可证），L8 是第一个全流程走打包版流水线的课。不是 2026-10-11 两次重构引入（均未碰 capture.js/OVERRIDE_CSS）。
- **修法（勿回退）**：OVERRIDE_CSS 冻结选择器必须连后代一起冻：`.step *, .stage-frame *`。安全性依据：所有入场动画 fill-mode:both 且 100% 关键帧=自然末态，基态=末态（唯一基态 opacity:0 的是 `.step` 包装层自身，显隐仍由 `.on` 控制）；`--animate` 实时渲染管线不受影响（该分支不加冻结块）。

## 14. fscene 换景：每步都要挂，漏挂前图不清场（L8 实翻车）

- 机制：`.fscene{visibility:hidden}` + `.step.on .fscene{visible}` + `.step.on:has(~ .step.on .fscene) .fscene{hidden}`——**后一步挂了 fscene 且激活时，前一步的图才消失**。
- 坑 1：想让第 N 步的图在第 M 步消失，**第 M 步也必须挂 fscene**；漏挂 = 图赖着不走（F9 两张插画没挂，该消失时不消失）。
- 坑 2：想**并排共存**的两张图别用 fscene（它只管同位替换/换景），用普通 div。
- 坑 3：最后一步天然常驻（后面没人触发隐藏），别再给它叠隐藏逻辑。

## 15. base64 照片提取：按 cap 文本建 map，别按文档序对位

- 提取 `<img src="data:image/jpeg;base64,…">` 时：丢闭合引号会产出损坏标签（渲染侥幸正常、DOM 已坏）；按文档序对位到 cap 会**错位**（发光卡可能排第一）。
- 正确姿势：正则只取 `[A-Za-z0-9+/=]` 字符集，按其后 `class="cap">文本<` 建 dict 再取；重建标签时写完整 `<img src="data:image/jpeg;base64,…">`。
- 注入仍只走 Python `str.replace`（见 2-slides.md 真照片配方）。

## 16. visual 帧：字幕安全区与文字预算（机检按 data-layout 分管）

- visual 帧的画面主角是大图/概念卡，**对话必须提炼 ≤15 字/句**，完整表达交给字幕；整帧画面文字 ≤40 字（不含标题/页眉页脚）。
- 字幕安全区：竖版 y≥1120、横版 y≥900 **只放品牌行**，内容块压进来会被字幕盖住。
- 每帧必须写 `data-layout="visual|dialog"`，`qc_frames.js` 才能分管检查；漏写按 dialog 处理（不查文字预算）。
- 关键词锚点卡 ≤4 字、一帧最多 1 张——锚点卡里塞整句 = 又回到文字过载。

## 17. 绝对 top 手摆布局：重叠/压行必须机检，塞不下就 hide 台词

- 放映版每步都是写死的绝对 `top`，而气泡行数 / chips 高度 / 照片高度随字体与文案浮动——目测排完必出「卡片叠卡片、内容压品牌行」（L8 竖版 13 帧里 8 帧中招，用户打回）。
- 量几何必须**关动画 + 舞台原尺寸**：入场动画进行中量包围盒，位移会被误判（`qc_overlap.js` 已内置）。
- 机检两条（排完必跑，报警回填 top 再复测）：
  `node $SK/scripts/qc_frames.js <html> /tmp/qc`（溢出）；
  `node $SK/scripts/qc_overlap.js <html>`（同屏跨步重叠 / 同列块间 <30px 提示 / 压品牌行呼吸区；按 clear 分段只测同屏步骤对，清场式共享位置不报）。
- 塞不下时的正解（用户定档）：**hide 掉冗余对话**——该句留空 `<div class="step"></div>`（步数不变、音段对齐），完整表达交给字幕；优先隐藏附和句、与 chips/阶梯图重复的回答、纯欢呼句。**不改字号、不改左右双列对话流、不压间距硬塞。**
- 与图重复的文字优先隐藏图那一侧：chips / 线索阶梯 / 标签墙已经表达的内容，气泡再念一遍就是双份。

## 18. 返修时先确认用户看的是哪个文件；成品修复的三条工程教训

- **先定位文件再动手**：参考件（$SK/assets/templates/crayon/preview*.html）与成品（课程目录 index_present*.html）是两套文件。L8 返修前两轮只修了参考件，用户看的是成品——白干两轮。用户报「第 N 帧有问题」时先问/查他打开的是哪套（成品 13 帧 vs 参考 6 帧）。
- **测量必须用 offsetTop/offsetHeight**：成品页面带 fit-scale transform，getBoundingClientRect 受缩放污染（style top:470 量出 426）；offset* 不受 transform 影响，且与 qc_overlap 口径一致。
- **源码级 hide 的结构安全**：①「清空步」必须保留 step 的闭合 </div>，否则 div 失衡、后续帧全部嵌套进前帧（机检表现为跨帧 slot 串台）；②帧内**最后一个 step** 里删视觉块时，绝不能吞掉 `.foot` 与帧闭合；③删完必跑 div 平衡自检 + 浏览器逐帧验证。
- **hide 后做全量链式重排**（首气泡保持原位，后续每个 = 前底 + 36px，可上移可下移），比只推重叠对更能利用 hide 腾出的空间；重排只动左列 slot（offsetLeft < 右列界），右列贴纸/chips 不跟动。
- fscene 帧的终态截图上半空是正常的（前步换景被隐藏），别当 bug 修。

## 19. 生成器 chips 行内联双闭合：帧提前闭合掉出 stageWrap（参考件打回第 N 轮的真凶）

- 症状：某帧起画面失去缩放（按视口宽渲染）、底部品牌行折行、HUD 控制条压住品牌行——但出问题的帧本身内容看起来"差不多对"，极难目检发现。
- 根因：生成器写 chips 行时把 `</div></div>`（内层 div + fscene）内联闭合了，模板又保留后两行 `</div>`（fscene + step 闭合）——**每个 chips 步多出一个 `</div>`**。HTML 解析器照单全收：f03 的多余闭合把帧和 stageWrap 提前关掉，f04 起整帧掉到 body 层，`.stage-frame` 的 `inset:0` 变成相对视口 → foot 宽=视口宽。
- 诊断金标准：**量 foot 的 offsetWidth，不等于 STAGE_W 就是嵌套断了**（参考件 660 vs 1080 一眼定位）。逐行跑 div 深度能精确到行。
- 机检已固化：`python3 $SK/scripts/qc_divs.py <html>...`（foot 深度=1 + 开闭差=0），与 qc_frames/qc_overlap 并列第三条，排完必跑。注意 qc_frames/qc_overlap **报不出这个 bug**（掉出舞台的帧其内容互不重叠、不溢出）。
- 末帧段会连带 stageWrap 闭合一起统计（差=-1 属正常），机检已放行；另注意 dialog 13 帧版 f13 末尾同类多余闭合（被解析器忽略，无害但要清）。

## 20. 帧级 fscene 提升：会被 `.fscene{visibility:hidden}` 藏掉，且 sim_verify 量不到
- **现象**：把累积式场景（动物墙/分类墙）从 step 提升为 frame 直接子元素后，页面整体通过机检，但场景**整块消失**——CSS 里 `.fscene{visibility:hidden}.step.on .fscene{visibility:visible}` 只对 step 内的 fscene 生效，帧级 fscene 永远 hidden。L8 三件成品 f07 动物墙集体中招（横版重排时发现，竖版是上轮遗留回归）。
- **修法**：CSS 追加 `.stage-frame>.fscene{visibility:visible}`（放在 `.fscene{visibility:hidden}` 之后、`.step.on .fscene` 之前或之后均可）。
- **防再犯**：① sim_verify 只量 `:scope > .step` 的 children，**帧级元素不参与任何检查**——凡是做「提升到帧级」的结构手术，必须配截图目检该帧最后一页；② sim 的成对重叠检查不建模 `.step.on:has(~ .step.on .fscene)` 累积隐藏规则，链式（无 clear）帧报出的「前场景×后场景重叠」先截图实证再动手，多半是误报（L8 竖版 f03 即此类）。

## 21. standalone 竖版：四角布局 CSS 只适用横版；applyTime 必须实现 clear 语义
- **坑 A（页脚打架）**：make_standalone 的 SUB_CSS 曾无条件注入「四角布局」（标语→右上 top:52/right:44、品牌→右下、字幕 bottom:26）。横版 1920 宽放得下；竖版 1080 宽下右上标语与 .hdr 的「适合…小朋友」直接重叠、字幕压品牌胶囊。**修法（已进代码）**：H>W 时跳过四角覆盖，保持放映版页脚（标语+品牌居中一行 bottom:36），字幕条 bottom:104 避让。判据：**竖版成片四角布局一律照搬用户已定稿的竖版放映版，不沿用横版视频的排法**。
- **坑 B（气泡叠罗汉）**：applyTime 只按时间窗 toggle `.on`，不实现 clear——放映版控制器在 clear 步会把之前的步骤加 `.gone`，standalone 没有这段，导致 clear 分页帧所有步骤同时可见（L8 f02 四气泡叠印实测）。**修法（已进代码）**：applyTime 先算 cur（时间窗命中的最大步号），再对每个 i 判断「(i,cur] 里是否存在 clear 步」→ 是则 .gone；与控制器语义逐字对齐（clear 隐藏它之前**所有**步，后续非 clear 步正常亮）。
- **坑 C（var 遮蔽死循环，capture 卡死真凶）**：给 applyTime 加 clear 判断时，内层循环写了 `for(var k=i+1;k<=cur;k++)`——`var` 函数级作用域，内层 `var k` 直接覆盖外层帧循环的 `k`：活动帧处理完 k 被重置为 i+1，外层 k++ 后重新处理同一帧，**applyTime 无限循环**（L8 竖版 f03 入口 t=61.7 精确卡死，capture_anim 每 tick 都调 applyTime → 整条截图管线挂死）。applyTime(0) 恰好不触发（首帧 cur=0 内层初始化即退），所以加载/首屏全正常，极难察觉。**修法**：内层变量一律换名（k2）。教训：applyTime 里所有循环变量必须唯一命名；改完先用「跨帧时刻」(t=帧边界±0.2s) 各跑一次 applyTime 冒烟，别只测 t=0。
- **教训**：放映版控制器每新增一种显隐语义（clear/gone/…），standalone 的 applyTime 必须同步实现，否则「HTML 定稿通过 ≠ 成片通过」。竖版出片前必抽 3 个时刻截图：首帧、任一 clear 帧中段、末帧。
