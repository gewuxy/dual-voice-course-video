// qc_overlap.js — 放映版逐帧「同屏重叠」检测
//
// 用法：node qc_overlap.js <index_present.html>
// 放映语义：步骤按 clear 分段——clear 步亮起时之前所有步骤整体淡出（清场式），
//           因此只有同段步骤会同屏。**只测同段步骤对**；跨段在真实放映中永不同屏，
//           位置共享是清场式的设计本体，不构成重叠。
// 阈值：同段步骤对重叠面积 >150px² 记 FAIL；同列间距 <30px 记提示（不阻断）；
//       内容底沿→品牌行 <32px 呼吸线侵入记 FAIL（任何步骤亮起时都不可侵入）。
// 豁免：裸 SVG（场景底板/插画/动物墙）不参与配对——贴纸、拍立得压在底板上是设计手段；
//       同一步内的叠放不报。
const fs = require('fs');
const path = require('path');
const { loadPuppeteer } = require('./pptr.js');
const puppeteer = loadPuppeteer();
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const SRC = process.argv[2];

// 舞台尺寸从源码读（竖版 1080×1440 / 横版 1920×1080）
let STAGE = { width: 1920, height: 1080 };
try {
  const h = fs.readFileSync(path.resolve(SRC), 'utf-8');
  let m = h.match(/id="stageWrap"[^>]*style="[^"]*?width:\s*(\d+)px[^"]*?height:\s*(\d+)px/);
  if (m) STAGE = { width: +m[1], height: +m[2] };
} catch (e) {}

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars'] });
  const page = await browser.newPage();
  await page.setViewport({ width: STAGE.width, height: STAGE.height, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(SRC), { waitUntil: 'networkidle0', timeout: 90000 });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.evaluate(() => {
    ['intro', 'hint', 'hud'].forEach(id => { const e = document.getElementById(id); if (e) e.style.display = 'none'; });
    // 关动画：入场动画进行中测量会把位移误判成重叠/漏判
    const s = document.createElement('style');
    s.textContent = '*,*::before,*::after{animation:none!important;transition:none!important}';
    document.head.appendChild(s);
  });
  const n = await page.evaluate(() => document.querySelectorAll('.stage-frame').length);
  let bad = 0, tightTotal = 0;
  for (let i = 1; i <= n; i++) {
    const { pairs, footHit, tight } = await page.evaluate((idx) => {
      const frames = document.querySelectorAll('.stage-frame');
      frames.forEach(f => f.classList.remove('active'));
      const f = frames[idx - 1]; f.classList.add('active');
      f.querySelectorAll('.step').forEach(s => { s.classList.add('on'); s.classList.remove('gone'); });
      // clear 分段：clear 步开启新段（它亮起时前段整体淡出），段号相同的步骤才会同屏
      const steps = Array.prototype.slice.call(f.querySelectorAll('.step'));
      const segOf = []; let cur = 0;
      steps.forEach((s, k) => { if (s.classList.contains('clear')) cur++; segOf[k] = cur; });
      // 内容块 = 可见的「原子盒」：气泡/贴纸/chip/照片/面板/带底色的块
      // 注意：① 只能取原子盒——像「只装绝对定位子元素的零尺寸容器」量出来是 0，会漏检
      //       ② 裸 svg（场景底板/插画）不收——贴纸压底板是设计手段，且 svg 常是纯装饰
      const SEL = '.slot, .chip, .sticker, .pola, .guanka, .panel-l, .panel-r, [style*="background"], [style*="border"]';
      const blocks = [];
      steps.forEach((step, si) => {
        const seen = new Set();
        step.querySelectorAll(SEL).forEach(k => {
          if (seen.has(k)) return; seen.add(k);
          if (k.closest('.hdr') || k.closest('.foot') || k.closest('.ftitle')) return;
          const r = k.getBoundingClientRect();
          if (r.width < 8 || r.height < 8) return;
          const cs = getComputedStyle(k);
          if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) return;
          blocks.push({ si: si + 1, seg: segOf[si], r, tag: (k.className || 'div').toString().slice(0, 24),
                        txt: (k.innerText || '').replace(/\s+/g, '').slice(0, 10) });
        });
      });
      const res = [], tight = [];
      for (let a = 0; a < blocks.length; a++) for (let b = a + 1; b < blocks.length; b++) {
        if (blocks[a].si === blocks[b].si) continue;
        if (blocks[a].seg !== blocks[b].seg) continue;         // 跨段：放映时永不同屏，不构成重叠
        const A = blocks[a].r, B = blocks[b].r;
        const w = Math.min(A.right, B.right) - Math.max(A.left, B.left);
        const h = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
        if (w <= 0) continue;                                  // 不同列，互不相干
        if (h > 2 && w * h > 150) {
          res.push({ s1: blocks[a].si, s2: blocks[b].si, area: Math.round(w * h),
            a: blocks[a].tag + '「' + blocks[a].txt + '」', b: blocks[b].tag + '「' + blocks[b].txt + '」',
            r1: [Math.round(A.left), Math.round(A.top), Math.round(A.right), Math.round(A.bottom)],
            r2: [Math.round(B.left), Math.round(B.top), Math.round(B.right), Math.round(B.bottom)] });
        } else if (h <= 2) {
          // 同列且没叠上：查呼吸感（块间 ≥36px）
          const gap = (A.bottom <= B.top) ? (B.top - A.bottom) : (A.top - B.bottom);
          if (gap >= 0 && gap < 30) tight.push({ s1: blocks[a].si, s2: blocks[b].si, gap: Math.round(gap),
            a: blocks[a].tag + '「' + blocks[a].txt + '」', b: blocks[b].tag + '「' + blocks[b].txt + '」' });
        }
      }
      // 品牌行顶沿
      const foot = f.querySelector('.foot');
      const footTop = foot ? Math.round(foot.getBoundingClientRect().top) : null;
      const hits = [];
      if (foot) blocks.forEach(bl => {
        if (bl.r.bottom > footTop - 32) hits.push(`step${bl.si} ${bl.tag}「${bl.txt}」 bottom:${Math.round(bl.r.bottom)} (品牌行顶 ${footTop})`);
      });
      return { pairs: res, footHit: hits, tight: tight };
    }, i);
    if (pairs.length) {
      bad++;
      console.log(`f${String(i).padStart(2, '0')} 重叠 ${pairs.length} 处:`);
      pairs.forEach(p => console.log(`   step${p.s1}×step${p.s2} 面积${p.area}px²  ${p.a}@${JSON.stringify(p.r1)} ↔ ${p.b}@${JSON.stringify(p.r2)}`));
    }
    if (tight.length) {
      tightTotal += tight.length;
      console.log(`f${String(i).padStart(2, '0')} 间距过近提示 ${tight.length} 处（<30px，呼吸目标 44px，不阻断）:`);
      tight.forEach(x => console.log(`   step${x.s1}×step${x.s2} 间距${x.gap}px  ${x.a} ↔ ${x.b}`));
    }
    if (footHit.length) {
      bad++;
      console.log(`f${String(i).padStart(2, '0')} 侵入品牌行呼吸区:`);
      footHit.forEach(x => console.log('   ' + x));
    }
  }
  // ③ 主体呼吸：图形↔标注 ≥24px；主体↔气泡 ≥28px
  //    （2026-10-14 L9 f08/f09 实测：图形按 ratio 算尺寸时溢出场景盒、压到气泡 −9px；标注只隔固定 14px）
  let breathe = 0;
  for (let i = 1; i <= n; i++) {
    const issues = await page.evaluate((idx) => {
      const fr = document.querySelectorAll('.stage-frame')[idx - 1];
      const steps = [...fr.querySelectorAll('.step')];
      if (!steps.some(s => s.querySelector('.fscene'))) return [];      // 只看 visual 帧
      const out = [];
      const R = e => e.getBoundingClientRect();
      fr.classList.add('active');
      steps.forEach((st, k) => {
        steps.forEach((s, j) => { s.classList.remove('on', 'gone'); if (j === k) s.classList.add('on'); });
        const hvs = [...st.querySelectorAll('.hero .hv')];
        if (!hvs.length) return;
        // 逐个"最内层 .hv"量图形↔标注（render_hero 与 hero_block 各包一层，成排时每个主体各有一层）
        [...st.querySelectorAll('.hero .hv')].filter(e => !e.querySelector('.hv')).forEach((hv, hi) => {
          const cap = hv.querySelector('.hcaption,.hlabel,.cap');
          const gfx = [...hv.querySelectorAll('svg,img,.ph')].map(R).sort((a, b) => b.height - a.height)[0];
          if (gfx && cap) {
            const g = Math.round(R(cap).top - gfx.bottom);
            if (g < 24) out.push(`step${k + 1} 主体${hi + 1} 图形↔标注 仅 ${g}px（目标 ≥28px）`);
          }
        });
        const bub = st.querySelector('.mini,.slot');
        if (bub) {
          const hvB = Math.max(...hvs.map(e => R(e).bottom));
          const g = Math.round(R(bub).top - hvB);
          if (g < 28) out.push(`step${k + 1} 主体↔气泡 仅 ${g}px（目标 ≥28px${g < 0 ? '，负值=重叠' : ''}）`);
        }
      });
      fr.classList.remove('active');
      return out;
    }, i);
    if (issues.length) {
      breathe++;
      console.log(`f${String(i).padStart(2, '0')} 呼吸不足：`);
      issues.forEach(x => console.log('   ' + x));
    }
  }
  console.log(bad || breathe
    ? `⚠️ ${bad} 帧重叠/侵入，${breathe} 帧呼吸不足`
    : `✅ 全帧无重叠、无品牌行侵入、主体呼吸达标${tightTotal ? `（另有 ${tightTotal} 处间距过近提示）` : ''}`);
  console.log('DONE');
  await browser.close();
})().catch(e => { console.error('ERR', e); process.exit(1); });
