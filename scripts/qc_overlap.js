// qc_overlap.js — 放映版逐帧「终态重叠」检测
//
// 用法：node qc_overlap.js <index_present.html>
// 检测：每帧全展开（关动画、按舞台原尺寸），不同 step 的内容块两两求交，
//       重叠面积 >150px² 记一处。同一步内的叠放是设计手段，不报。
// 顺带报：内容块底沿侵入品牌行（内容底沿→品牌行 <32px 呼吸感红线）。
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
  let bad = 0;
  for (let i = 1; i <= n; i++) {
    const { pairs, footHit, tight } = await page.evaluate((idx) => {
      const frames = document.querySelectorAll('.stage-frame');
      frames.forEach(f => f.classList.remove('active'));
      const f = frames[idx - 1]; f.classList.add('active');
      f.querySelectorAll('.step').forEach(s => { s.classList.add('on'); s.classList.remove('gone'); });
      // 内容块 = 可见的「原子盒」：气泡/贴纸/chip/照片/面板/svg/带底色的块
      // 注意：只能取原子盒——像「只装绝对定位子元素的零尺寸容器」量出来是 0，会漏检
      const SEL = '.slot, .chip, .sticker, .pola, .guanka, .panel-l, .panel-r, svg, [style*="background"], [style*="border"]';
      const blocks = [];
      f.querySelectorAll('.step').forEach((step, si) => {
        const seen = new Set();
        step.querySelectorAll(SEL).forEach(k => {
          if (seen.has(k)) return; seen.add(k);
          if (k.closest('.hdr') || k.closest('.foot') || k.closest('.ftitle')) return;
          const r = k.getBoundingClientRect();
          if (r.width < 8 || r.height < 8) return;
          const cs = getComputedStyle(k);
          if (cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) return;
          blocks.push({ si: si + 1, r, tag: (k.className || 'div').toString().slice(0, 24),
                        txt: (k.innerText || '').replace(/\s+/g, '').slice(0, 10) });
        });
      });
      const res = [], tight = [];
      for (let a = 0; a < blocks.length; a++) for (let b = a + 1; b < blocks.length; b++) {
        if (blocks[a].si === blocks[b].si) continue;
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
      bad++;
      console.log(`f${String(i).padStart(2, '0')} 块间过近（<30px，呼吸线 36px）:`);
      tight.forEach(x => console.log(`   step${x.s1}×step${x.s2} 间距${x.gap}px  ${x.a} ↔ ${x.b}`));
    }
    if (footHit.length) {
      bad++;
      console.log(`f${String(i).padStart(2, '0')} 侵入品牌行呼吸区:`);
      footHit.forEach(x => console.log('   ' + x));
    }
  }
  console.log(bad ? `⚠️ ${bad} 帧有问题` : '✅ 全帧无重叠、无品牌行侵入');
  console.log('DONE');
  await browser.close();
})().catch(e => { console.error('ERR', e); process.exit(1); });
