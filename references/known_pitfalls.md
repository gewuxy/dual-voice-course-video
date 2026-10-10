# 已知坑清单（真实踩坑，按根因归类）

> 更新于 L1《人类感官 vs 计算机传感器》制作之后。凡标注「已修」的，脚本里已经改好，换课直接受益。

## 1. 双音色 TTS 阶段
- **童声短句消失（不是 TTS 失败）**：`split_units` 里的中文过滤阈值写过 `>=4`，会整句丢掉「苹果！」「猫！」「数据集！」这类 1–3 字童声句，现象是"学生句凭空消失"而**不报错**。修复：阈值 `>=1`（只丢纯标点/空串）。已修。
- **全量合成被沙箱 bulk-delete 守卫杀进程（EXIT=1）**：逐句合成后脚本 `os.remove` 临时 take 文件，单轮删除数超阈值被判为批量删除。修复：**跑音频一律加 `--no-cleanup`**。已固化为默认建议。
- **语速机关枪**：短句不减速会念得飞快。脚本用 `TARGET_CPS=3.23` + 每句取样 `--takes` 取最接近目标者，再 `retempo` 兜底。
- **换课别手写权重路径**：脚本按 epoch 自动取最新（`GPT_weights/<exp>-e*.ckpt` + `SoVITS_weights/<exp>_e*_s*.pth`）。手写容易指到不存在的文件（例如文档里写过 `ref_xian.wav` / `macie-e20.ckpt`，本机实际是 `dataset/xiaoxian/wavs/xiaoxian_0029.wav` / 最高 e15）。已修。
- **产物名别记错**：实际产出是 `frame_NN.wav` + **`_merged.wav`** + **`report.json`**（没有 `lesson_final.wav` / `dialog_report.json` 了）。`report.json` 的 `units[].start` 是帧内每句起始秒，阶段 4 直接用它对齐。
- **帧数不要写死**：`NF=21` / `range(1,22)` 之类的 L12 写死值，已改为按 HTML/剧本自动识别（`make_standalone.py --nf` 可选）。

## 2. 时间轴对齐阶段
- **多 step 堆叠在 0s（"泄题"）**：早期 `bind_delays` 给多 step 帧全 0s 延迟，整帧内容在音频开始前一次性全显。修复：step 数 == 对话行数时 1:1 锚定每句 `start`；否则帧内均匀分布。已修。
- **`re.sub` 删 step 破坏 div 嵌套（致命）**：早期用非贪婪正则把 step 当 static 删掉，会掐断嵌套 div、残留孤立 `</div>`，第 2 帧之后整屏空白（曾被误判为 hyperframes worker 问题）。修复：**HTML 结构原样输出，一个字符都不删**，显隐全由 JS 数据驱动。已修。
- **frame 标签两种写法都要认**：L12 是 `<div id="f01" class="frame stage-frame">`，L1 是 `<div class="stage-frame" id="f04">`。只认一种属性顺序的脚本换课就报"缺少帧"。已修：`make_standalone.py` 用标签配对法提取，两种都吃。
- **standalone 里内嵌 `<audio>` 会重复出声**：放映版第 2 帧的儿歌音频若留在 standalone，成片音轨（`_merged.wav`）之外还会再响一遍。修复：`make_standalone.py` 默认剥掉 `<audio>`（要保留加 `--keep-audio`）。已修。

## 3. hyperframes 路线（已弃用，勿走）
- 流式编码上限 `streamingEncodeMaxDurationSeconds=240`，长课 >240s 落 disk capture；worker 竞态偶发 ENOENT。已改用自带 puppeteer + ffmpeg 管线。`scripts/compose.py` 仅存档参考。

## 4. 画面（HTML 放映版）阶段
- **真照片贴纸会把卡片顶穿页脚**：真照片做成拍立得贴纸（`padding:8px` + 118px 图 + 28px 标签）比原 SVG 图标高一截，L1 的 F04/F05 用 150px 照片时卡片底到 1064（页脚线 1000）。修复：照片 118px、标签 28px、`nm` 44、`vis` 的 `top` 压到 566、`tx` 压成一句不折行。已固化为配方。
- **超长 base64 行不能用编辑器工具改**：`<img src="data:image/jpeg;base64,……">` 一行几十万字符，字符串匹配必然失败。**一律用 Python `str.replace`/正则改**，并在改前把 base64 换成 `__PLACEHOLDER__` 再注入。
- **文案折行出孤字**：中文气泡宽度略窄就会把最后一个字挤到下一行（"红圈里就／是它"）。修复：直接缩短文案（如"都藏着「电脑的眼睛」，看红圈！"），别去动字号。
- **累加式播放器要按"全部展开"排间距**：step 是累加的，同一帧里的右侧贴纸列/卡片必须按最坏情况（全部显示）留间距，否则后出现的元素会压住先出现的。L1 F02 曾出现小花贴纸与木头贴纸重叠 16px。
- **内嵌媒体后单文件体积**：儿歌 mp3（207KB base64）+ 4 张照片，HTML 从 245KB 涨到 ~417KB。可接受（放映版要自包含），但别再无脑塞高清大图。
- **emoji 组合渲染异常**：`👩‍🏫`/`🧒` 等 ZWJ 组合 emoji 在 Chrome 截图会变方块。改用纯 SVG 简笔画或色点 + 文字。
- **字体回退**：截图前必须 `document.fonts.ready`；本机可命中的中文字体是「圆体-简」(Yuanti SC) / 「娃娃体-简」(HanziPen SC)。

## 5. QC 阶段
- **逐 step 截图必须先清掉其它帧的 `.active`**：否则上一帧内容会残影叠在图上（曾误以为画面 bug）。`qc_frames.js` 每次截图前都 `frames.forEach(f => f.classList.remove('active'))`。
- **QC 脚本要等转场动画**：帧内元素有淡入/位移，切帧后立刻截图会拍到"半透明未到位"状态（曾误判为标题重复）。稳定等待 450–550ms 再截。
- **溢出阈值**：元素底边相对 1080 画布 >1000px 即会被底部品牌条裁切，必须修；`qc_frames.js` 会列出具体帧与数值。
- **截总览图用系统 python**：托管版 python 没装 PIL，用 `/opt/homebrew/bin/python3`。

## 6. 合成阶段
- **concat PNG 无音轨**：`ffmpeg -i shot_%04d.png … -c:a aac` 会静默忽略 `-c:a`（PNG 序列本身无音轨），成片无声。必须两步：先出无声 `video_silent.mp4`，再 `-c:v copy -c:a aac` 混 `_merged.wav`。
- **PSNR 量化误区**：① `crop` 与 `psnr` 不能同一条链；② 比对帧必须对齐到**同一全局时刻**，拿错帧会得到虚假 21dB 低分，对齐后 48.8dB。

## 7. 体积/画质权衡（实测 L12：9:39 / 1920×1080 / 30fps）
- `crf 20` → 14.6MB，PSNR 48.83dB（正式版）。
- `crf 16` → 35.1MB，PSNR 49.18dB，仅 +0.35dB 却体积 +140%，除非高清存档否则不值。
- 微信轻量版可降到 ~8MB。

## 8. 封面（阶段 5）
- **视频号信息流按 1:1 居中裁切** 9:16 封面（1080×1920 取 y=420~1500）。标题/品牌/年级必须压进安全区，用 `ffmpeg -vf crop=1080:1080:0:420` 生成预览自查。
- **视觉必须用已定稿的蜡笔手绘风**（`$SK/assets/templates/crayon/preview.html`）：旧版平铺米底、低对比、标题字高仅 5.4% 的排版已被用户否决，不要回退。
- 主标题字高占画面 **24–30%**；行距 ≥1.7；块间距 ≥40px（用户明确反馈"文字太拥挤"是硬伤）。

## 9. 音画整合成片（2026-10-02 L1 实测新增）
- **make_standalone 的 `--gap` 必须 = 0.9**：`dialog2audio.py` 合并 `_merged.wav` 时帧间硬编码 0.9s。旧文档写 `--gap 0.25`，导致 standalone 总时长 388s vs 音频 397.7s，末帧漂移 9.75s。校验：两者时长差 ≤0.1s。
- **帧间空隙画面清空闪烁**：standalone 里帧显示到 `gend`（含 gap）但 step 的消失时间是 `gstart+fdur`，每帧切换前有 0.9s 内容全消失。已修：非 hide-at 的 step 延续到 gend；字幕末句也延长到 gend，避免帧切换时字幕闪灭。
- **三种 ffmpeg 时间轴错误路径（全部实测翻车）**：① `-framerate 30 -i shots/shot_%04d.png`（42 张变 1.4s）；② concat demuxer + duration 输出 VFR，t=50 实测错位一个区间；③ concat 输入加 `-r 30` → 总长被拉到 415s（应为 398s），`fps=30` 滤镜也漂。**唯一可靠：按 30fps 生成硬链接帧序列 frames/f%05d.png 再 `-framerate 30` 读入**。
- **对齐 QC 正确姿势**：拿成片在 t 抽帧，与 schedule 判定的 shot 比对 RMS（应 <3），两个视频互相比没有意义——可能"错得一致"。本次就是 VFR 版错、CFR 版对。
- **体积重估**：纸纹噪点让每帧都不同，真实 30fps crf20 实测 32MB/6'38"（旧估算 14–15MB 是 VFR 单帧的假象）。轻量版 `-crf 26 -vf scale=1280:-2`。
- **字幕条（make_standalone --subtitles）**：放在页脚上方 bottom:104px；老师深蓝/学生粉边框分色；关键词黄底橙字 1.18em；长句按标点切 ≤30 字、按字数比例分配时间（帧 1 的 100 字长句不切会变成 408px 高的大块挡住画面）。只改 standalone，**index_present.html（老师上课用）完全不动**。
- **字幕切换点必须进 schedule 区间**（2026-10-02 用户验收发现）：make_standalone 只把 step 显隐点写进 `changes`，字幕块时间不进轴 → 截图时整个长区间都停在区间起点的那个字幕块（表现为"第 1 帧 25 秒只有第一块字幕"）。已修：每个字幕块 t0/t1 都 `changes.update(...)`，区间数从 42 涨到 113 属正常。改字幕相关代码后**必须重跑 capture→frames→encode→mux 全链**，不能只重编码。
- **断句「——」**：破折号中间硬断很难看（"话题——|我"），chunk_text 已把「——」整体作断点（len>=soft 时断在它后面）。
- **step 入场渐入被截在半路（2026-10-02 用户验收发现，L2 起生效）**：课件原生 `.step.on` 有 0.45s 渐入+上移动画（课堂点击的加分设计），但 capture.js 在 applyTime 后只等 90ms 就截图 → 新 step 出现的那个区间拍在渐入 ~20% 处，视频里表现为"先置灰半透明、下个区间才正常"。已在 make_standalone OVERRIDE_CSS 冻结视频版所有 transition/animation（`transition:none !important`），放映版不受影响。若以后想保留入场动画，需把 capture.js 的等待提到 ≥500ms。

## 10. L2 实测新增（2026-10-03）
- **剧本句前停顿 `学生：[[1.5]]"答！"[[1.5]]`**：旧 parse_line 用 `PAUSE_RE.search` 取第一个标记 → text 变空串、学生回答整行丢失。已给 voice_clone/dialog2audio.py 打补丁（parse_line 返回 4 元组 speaker,text,pause,pre；synth_line 支持 pre=句前静音；动作行 dur+pre）。备份在 /tmp/dialog2audio.py.bak。
- **自建 class 必须「先定义再引用」**：L1 放映版根本没有 .pola 类（L1 照片用 `.sticker` + 内联 padding/rotate 实现）。L2 构建器凭空引用 .pola 且未定义 → 所有照片退化成无样式流式 div（left/top 失效、flex 里叠出屏）。而且溢出检测照样通过（无样式 div 不超界）——**QC 溢出全绿 ≠ 版式正确，必须目检**。修复：builder 往 head 注入 .pola/.chips/.chip/.arrow CSS；flex 容器内的 pola 必须加 `position:static`。
- **QC 探测内嵌音频的点击次数**：qc_frames.js 的 AUDIO 探测固定 root.click()×2，只到 F1S2；F1 有 3 步的课程探测不到 F2S1（误报 paused）。按 F1 步数补点。
- **内嵌音效混流**：L2 铃声音效（非背景音乐）volume=0.85、adelay=第2帧起点(=frame_01.wav时长+0.9gap)。内容型音效要大音量，别沿用儿歌的 0.32。
- **累加式播放器布局铁律（2026-10-03 L2 返工，L2 v2 重写全 16 帧）**：放映版 JS 是累加式（旧 step 永不消失），builder 曾把「答句」「定义卡」放在与「问句」完全相同的坐标（replace 式设计）→ 新卡 0.45s 淡入期间新旧文字叠加，用户感知为「后面的卡片被前面的挡住一小会」。**v2 布局规范**：① 左栏对话槽位流（3 步帧 y=320/540/760，5 步帧 y≈292/420/548/676/804，每槽 ≤2 行）；② 右栏视觉区 x≥1180，视觉元素只在第 1 步出现；③ 格子游戏状态（撞障碍/出界/路线/眼罩）用同 viewBox 透明 SVG 叠加层锚在底图上，绝不换底图；④ 画面只留 ≤2 行短气泡+关键词公式卡，整句旁白交给配音和字幕（用户明确反馈「画面和字幕重复度过高」）；⑤ `.sticker.crayon` 组合的 `--fill` 会被 `.sticker::before` 白底覆盖（白底白字不可读）——彩色贴纸直接 `background:{fill}` 不用 crayon；⑤b **ftitle 必须放 step 外（帧级常显，L1 规范）**，放 step 1 里会让每帧开场全屏空白（2026-10-03 用户验收指出），且同一帧两步不能各有一个 ftitle（累加后会叠标题）；⑤c 同一信息只出现一次（如 F1 曾同时有大贴纸「不够！」和学生气泡「不够！」，用户质疑）；⑥ 单句长独白帧必须拆 2-3 个视觉节拍（每步一个槽位卡），不能整帧 1 步。构建脚本存档：/tmp/l2_build/build_l2_v2.py（QC：qc_v2.js 全步展开截图+溢出检测，ftitle 的 left:0/right:1920 是居中标题误报）。
- **无声版视频必须归档（2026-10-03 用户要求，L1/L2 已补归档）**：`video_cfr3.mp4`（无声含烧录字幕）+ durations.txt + schedule.json + report.json + standalone.html 都要复制进 `$H/视频课/`，不能只留在 /tmp（系统会清，且访达不可见）。用途：换音色重合成。⚠️ 无声版字幕时间是按旧音色烧进画面的，新音色每句时长若变，直接混流会字幕错位——正确路径是用新 report/durations 重跑 make_standalone→截图→帧→编码全链（脚本化，几分钟）；直接混流仅当新音色时长与旧版几乎一致时可用。

## 11. 动效版坑（2026-10-03，L3 起）

- **CSS 入场动画 + `.sticker::before` 白底盖彩色背景**：popIn 等动画使 `.sticker` 成为层叠上下文后，其 `::before(z-index:-1)` 会绘制在元素自身背景**之上**（无动画时落在祖先上下文、被背景盖住）。动效模板下必须 `.sticker::before{display:none}`（已在 build_l3.py 固化）。排查手段：computed style 是绿的但截图是米白 → 层叠上下文问题。
- **verify_steps.py 曾不认句前停顿**：`学生：[[1.5]]"羽毛！"` 这种 `[[n]]` 在引号前的行会被丢掉，导致"剧本句数少 1"。已修：正则允许前后各一个可选 `[[n]]`。
- **make_standalone.py 加了 `--animate`**：跳过冻结动画 CSS，供实时渲染管线使用；静帧截图管线仍用默认冻结。
- **动效成片管线（新）**：静帧截图法拍不到 CSS 动画 → 改用「实时驱动 applyTime + CDP screencast」逐 tick 抓帧。要点：rAF 循环驱动 `window.applyTime(t)`，Page.startScreencast(jpeg q85) 收帧+必须及时 Ack，按 1/30s tick 映射"最近一帧"，再 ffmpeg 合成。音频轨照旧 ffmpeg 混流（对白 _merged.wav + 内容音效 adelay）。
- **polas 旋转变换**：动效模板下照片旋转用 `--pr` 变量（`transform:rotate(var(--pr))`），动画 polaIn 的关键帧引用同一变量，避免动画结束后旋转角被覆盖。

## 12. L4 实测新增（2026-10-03，全 emoji 课 / 封面卡折行）

- **无照片课程默认视觉 = 蜡笔风 emoji 图标卡**：机器/食物等无实拍素材时，`img()` 生成 SVG 数据 URI（米底圆 + 大 emoji + 蜡笔点缀点），Chrome headless 渲染 Apple emoji 正常。L4 全课 12 个主体全 emoji，用户验收通过，"icon 即最终样式"已固化。
- **横版封面三贴纸卡的 label 折行会撑高卡片盖住品牌行**：娃娃体实际字宽 >32px 估算，"扫地机器人 · 自己拿主意" 折两行后中卡 bottom 达 ~1000，直接压住 `.foot`（y≈990-1040）。修复三板斧：卡区 top 620→570、label 统一 32px、需要两行时用显式 `<br>` 控制断点（如 "扫地机器人<br>自己拿主意"）而非让浏览器自由折行。三卡 img 高 240/235/240 已验证安全。
- **左栏槽位卡字号量化规则（y=760 三步帧末位 card）**：文本 >22 字必然两行，42px 两行 bottom≈1006 溢出（QC 阈值 1000），**38px 两行是 L3 验证的安全上限**。42px 只允许 ≤20 字单行。
- **五步帧槽位 Y 定值**：292/420/548/676/804（沿 L2 F13 实测），末槽 y=804 时 card 必须 ≤1 行（size 36 + ≤21 字）。
- **抽帧 QC 踩帧间边界会误判**：t 恰好落在帧尾 gap（如 t=100.0 帧边界）时字幕隐藏+旧帧内容是正常现象，抽非边界时刻（帧中段）验证。
- **L4 全链耗时参考**：音频 49 句 4m10s；capture_anim 11148 帧 21m35s；编码+混流 1m06s；全程（含两轮 QC + 封面三轮修复）约 55 分钟。

## 13. 路由 B 本地 TTS 跨平台兜底（2026-10-03 用户要求）

- **起因**：初版兜底只支持 macOS `say`，Windows 用户会卡死在阶段 3。重构为 `dialog2audio_local.py` 平台后端抽象：darwin→say / win32→PowerShell+System.Speech(SAPI) / linux→espeak-ng。
- **Windows 编码坑**：中文文本绝不能走命令行参数或 .ps1 文件（GBK 控制台/编码损坏），必须用 `powershell -EncodedCommand`（UTF-16LE base64）+ SSML here-string 传递。SSML SpeakSsml 失败时 Python 层自动重试纯文本 Speak + Rate 属性（SAPI 对 prosody 支持不完整）。
- **师生双声差异化策略（三平台）**：macOS 两个声音 + pbas 抬调；Windows 枚举中文声音取两个不同 voice，仅一个时 SSML pitch+25%；espeak 学生 -p 80 vs 老师 -p 50。
- **采样率合同**：say 用 `--data-format=LEI16@32000` 直出；SAPI/ESpeak 输出可能是 22050Hz，统一 ffmpeg 重采样到 32k（ffmpeg 本来就是流水线硬依赖）。
- **实测状态**：macOS 分支已真机实测（L4 第 1 帧 3 句 23.5s，report 合同校验通过）；**Windows SAPI 分支与 Linux espeak 分支尚未真机实测**，首个 Windows 用户反馈时优先排查中文语音包是否安装。
- **preflight 路由 B 检测也要按平台分支**：uname -s 三分支（say+zh_CN 声音 / espeak-ng / powershell）。
