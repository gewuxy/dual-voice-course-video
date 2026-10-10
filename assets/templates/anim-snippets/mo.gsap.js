/* ============================================================================
 * mo.gsap.js — 双音色课程视频 · 动效片段库（GSAP 时间轴版）
 * 在课件 HTML 里 <script src="mo.gsap.js"></script> 后，window.MO 提供：
 *   MO.ease       缓动预设（每条都写了"何时用"，见下方注释）
 *   MO.PULSE      脉冲节奏时长常量（快推/横移/砸入；改这里统一改节奏）
 *   MO.entrance(tl, sel, kind, at, opts)   给一条时间轴在 at 秒加一个入场
 *   MO.transition(tl, kind, at, opts)      加一个帧间转场覆盖层
 *   MO.continuous(sel, kind, opts)         对元素起一个循环微动（落定后停住不用这个）
 *
 * 设计哲学（直接来自 huashu-art-motion 的 MO 库）：
 *   - 动效是"时间→数值"的纯函数，确定性，可重复。
 *   - 入场是脉冲：停住 → 一下 → 停住。不用匀速慢推凑运动。
 *   - 每条缓动带"何时用"一句说明，让 Agent 按内容判断，而非为差异化而差异化。
 *
 * 没有 GSAP 时（比如纯浏览器看课件）本文件只挂 MO.ease / MO.PULSE / MO.entranceCSS，
 * 入场改走 CSS class（mo.css 已定义），不报错。
 * ========================================================================== */
(function () {
  const hasGSAP = typeof window !== 'undefined' && window.gsap;
  const MO = (window.MO = window.MO || {});

  // ---------- 缓动预设：每条都写"何时用" ----------
  // 讲解/概念（两端停稳，像 3b1b/白板）：smooth / sineInOut
  MO.ease = {
    smooth:    'power2.inOut',                 // 默认；两端速度、加速度都为 0，最稳
    sineInOut: 'sine.inOut',                   // 同上，轻一点
    // 强调出现（发布会/大数字）：快出慢停
    expoOut:   'expo.out',                      // 入场最常用；"快出慢停"
    back:      'back.out(1.7)',                // 带 ~17% 过冲的弹出（卡片/答案）
    backSoft:  'back.out(1.2)',                // 轻过冲（10%）
    // 砸入（主词/金句落定）：先猛再回
    slam:      'cubic.in',                      // 前 60% 砸下
    elastic:   'elastic.out(1, 0.5)',          // 弹性落定（贴纸"啪"地落下、命中反馈）
    // 苹果/发布会过渡
    apple:     'cubic-bezier(0.25,0.1,0.25,1)',// 长尾减速
    // 通用强调缓动
    emphasized:'cubic-bezier(0.2,0,0,1)',
  };

  // ---------- 脉冲节奏时长（秒），改这里统一全片节奏 ----------
  // 出处：一支被判"像放 PPT"（每镜匀速推 7.5%）的片，换成脉冲后被认可。
  MO.PULSE = { punch: 0.28, pan: 0.30, slam: 0.17, k: 0.25, kMin: 0.18, kMax: 0.32 };

  // 入场：kind → GSAP fromTo 配置。at=出现时刻(秒)；opts 可覆盖 duration/ease/delay/stagger
  const ENTRANCE = {
    pop:      { from: { opacity: 0, scale: 0.82 }, to: { opacity: 1, scale: 1 },    dur: 0.50, ease: MO.ease.back },
    slam:     { from: { opacity: 0, scale: 1.5 },  to: { opacity: 1, scale: 1 },     dur: 0.42, ease: MO.ease.emphasized },
    fadeRise: { from: { opacity: 0, y: 26 },       to: { opacity: 1, y: 0 },         dur: 0.50, ease: MO.ease.sineInOut },
    blurIn:   { from: { opacity: 0, filter: 'blur(14px)', scale: 1.04 }, to: { opacity: 1, filter: 'blur(0px)', scale: 1 }, dur: 0.60, ease: 'power1.out' },
    irisIn:   { from: { opacity: 0, clipPath: 'circle(0% at 50% 50%)' }, to: { opacity: 1, clipPath: 'circle(75% at 50% 50%)' }, dur: 0.55, ease: MO.ease.sineInOut },
    flyLeft:  { from: { opacity: 0, x: 120 },      to: { opacity: 1, x: 0 },         dur: 0.50, ease: MO.ease.sineInOut },
    flyRight: { from: { opacity: 0, x: -120 },     to: { opacity: 1, x: 0 },         dur: 0.50, ease: MO.ease.sineInOut },
  };

  // 转场：kind → 一个覆盖层元素 + 出现动画。at=转场开始时刻。
  // 用法：MO.transition(tl, 'iris', 24.95) 会在 at 时刻插入一个全屏覆盖层做向内溶解。
  const TRANSITION = {
    iris:  { cls: 'mo-trans-iris',  dur: 0.5 },
    blinds:{ cls: 'mo-trans-blinds',dur: 0.55, strips: 8 },
    wipe:  { cls: 'mo-trans-wipe',  dur: 0.45 },
    fly:   { cls: 'mo-trans-fly',   dur: 0.5 },
    fade:  { cls: 'mo-trans-fade',  dur: 0.5 },
  };

  // 持续微动：kind → GSAP 循环配置（yoyo）。仅素材/装饰层用。
  const CONTINUOUS = {
    kenburns: { to: { scale: 1.12, x: -12, y: -10 }, dur: 9,  ease: 'sine.inOut', yoyo: true, repeat: -1, repeatDelay: 0 },
    glow:     { to: { boxShadow: '0 0 26px rgba(123,201,111,.55)' }, dur: 0.8, ease: 'sine.inOut', yoyo: true, repeat: -1 },
    float:    { to: { y: -8 }, dur: 4, ease: 'sine.inOut', yoyo: true, repeat: -1 },
  };

  // ---------- 入场 ----------
  MO.entrance = function (tl, sel, kind, at, opts) {
    opts = opts || {};
    const def = ENTRANCE[kind] || ENTRANCE.pop;
    const dur = opts.duration || def.dur;
    const ease = opts.ease || def.ease;
    const els = typeof sel === 'string' ? (tl && tl.targets ? null : document.querySelectorAll(sel)) : sel;
    if (!hasGSAP) { // 退化：直接加 CSS class
      const nodes = typeof sel === 'string' ? document.querySelectorAll(sel) : (sel.length ? sel : [sel]);
      nodes.forEach((n, i) => {
        const c = 'anim-' + (kind === 'flyRight' ? 'fly-right' : kind === 'irisIn' ? 'iris-in' : kind === 'blurIn' ? 'blur-in' : kind === 'fadeRise' ? 'fade-rise' : kind === 'slam' ? 'slam' : 'pop');
        n.classList.remove(c); void n.offsetWidth; n.classList.add(c);
        if (opts.stagger) n.style.animationDelay = (i * opts.stagger) + 's';
      });
      return;
    }
    const targets = typeof sel === 'string' ? sel : sel;
    if (opts.stagger) {
      tl.fromTo(targets, def.from, Object.assign({ duration: dur, ease: ease, stagger: opts.stagger }, def.to), at);
    } else {
      tl.fromTo(targets, def.from, Object.assign({ duration: dur, ease: ease }, def.to), at);
    }
  };

  // ---------- 转场 ----------
  MO.transition = function (tl, kind, at, opts) {
    opts = opts || {};
    const def = TRANSITION[kind] || TRANSITION.fade;
    if (!hasGSAP) { console.warn('[MO] 无 GSAP，转场需手动控制覆盖层'); return; }
    const layer = document.createElement('div');
    layer.className = 'mo-trans ' + def.cls;
    if (kind === 'blinds') {
      for (let i = 0; i < (def.strips || 8); i++) {
        const s = document.createElement('i');
        s.style.animationDelay = (i * 0.03) + 's';
        layer.appendChild(s);
      }
    }
    const root = (opts.parent && document.querySelector(opts.parent)) || document.querySelector('#stage, .stage, body');
    if (root) root.appendChild(layer);
    tl.set(layer, { opacity: 1 }, at);
    tl.to(layer, { opacity: 0, duration: 0.3, ease: 'power1.inOut' }, at + def.dur - 0.3);
    tl.set(layer, { opacity: 0 }, at + def.dur + 0.05);
    // 转场结束后移除 DOM
    setTimeout(() => { if (layer.parentNode) layer.parentNode.removeChild(layer); }, (at + def.dur + 0.2) * 1000);
  };

  // ---------- 持续微动 ----------
  MO.continuous = function (sel, kind, opts) {
    opts = opts || {};
    const def = CONTINUOUS[kind] || CONTINUOUS.float;
    if (!hasGSAP) { // 退化：加 CSS class
      const c = 'idle-' + (kind === 'kenburns' ? 'kenburns' : kind === 'glow' ? 'glow' : 'float');
      const nodes = typeof sel === 'string' ? document.querySelectorAll(sel) : (sel.length ? sel : [sel]);
      nodes.forEach((n) => n.classList.add(c));
      return;
    }
    const targets = typeof sel === 'string' ? sel : sel;
    return window.gsap.to(targets, Object.assign({}, def, opts));
  };

  // 逐字上浮：把文字拆成 span 再 stagger 升起（标题/关键词用）。
  // 返回被拆的节点列表，方便后续接时间轴。
  MO.charsIn = function (el, opts) {
    opts = opts || {};
    const text = el.textContent;
    el.textContent = '';
    const frag = document.createDocumentFragment();
    const spans = [];
    for (const ch of text) {
      const s = document.createElement('span');
      s.textContent = ch;
      s.style.display = 'inline-block';
      s.style.opacity = '0';
      frag.appendChild(s); spans.push(s);
    }
    el.appendChild(frag);
    if (hasGSAP) {
      window.gsap.to(spans, { opacity: 1, y: 0, duration: opts.duration || 0.4, ease: MO.ease.expoOut, stagger: opts.stagger || 0.04,
        from: { y: 18 } });
    } else {
      spans.forEach((s, i) => { s.style.animation = 'mo-rise .4s ' + (i * 0.04) + 's both'; });
    }
    return spans;
  };

  if (!hasGSAP) console.info('[MO] GSAP 未加载，已降级为 CSS class（mo.css）入场/微动。');
})();
