// qc_clear.js — 清场（clear）决策检查：**放得下就不该清场，放不下才清场**（横竖同规则）
//
// 为什么不能静态估算：HTML 里的 `top` 值本身编码了清场决策（清场帧的最后一步 top 被写回顶部），
// 所以只有"用每一步的真实渲染高度重新累加一遍"，才能回答"这帧如果不清场，装得下吗"。
//
// 只判 dialog 帧（visual 帧走 .fscene 换景、步骤不累加，不适用）。
// 判据（每一步取真实 offset 高度，块间 44px）：
//   累加底沿 = 首步 top + Σ(步高) + 44×(步数-1)
//   上限     = 字幕安全区下限：横版 900 / 竖版 1120（成片字幕烧在那条线上；与 2-slides.md 同口径）
//              —— 注意别用"品牌行上沿-32"（横 947 / 竖 1306），那条更松，会让内容钻到字幕底下。
//   ① 声明了 clear 且累加底沿 ≤ 上限-24     → ⚠️ 放得下却清场
//   ② 没声明 clear 且累加底沿 > 上限        → ❌ 装不下却没清场（会压字幕/品牌行）
//   ③ 落在上限 ±24 的临界带 → 只报告不判错（清不清都说得过去）
//
// 用法：node qc_clear.js <index_present.html> [more.html ...]
// 退出码：0=无告警，1=有告警（可自行决定是否阻断）
const fs = require('fs');
const path = require('path');
const { loadPuppeteer } = require('./pptr.js');
const puppeteer = loadPuppeteer();
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const GAP = 44;

(async () => {
  let bad = 0;
  for (const SRC of process.argv.slice(2)) {
    const html = fs.readFileSync(SRC, 'utf-8');
    const m = html.match(/id="stageWrap"[^>]*style="[^"]*?width:\s*(\d+)px[^"]*?height:\s*(\d+)px/);
    const W = m ? +m[1] : 1920, H = m ? +m[2] : 1080;
    const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new',
      args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1'] });
    const page = await browser.newPage();
    await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
    await page.goto('file://' + path.resolve(SRC), { waitUntil: 'networkidle0' });
    await page.evaluate(async () => {
      document.fonts && await document.fonts.ready;
      document.querySelectorAll('.step, .step *').forEach(e => { e.style.transition = 'none'; e.style.animation = 'none'; });
      const sw = document.getElementById('stageWrap'); if (sw) sw.style.transform = 'none';   // 关缩放，量原尺寸
    });
    const LIMIT = W > H ? 900 : 1120;   // 字幕安全区下限（2-slides.md）
    const res = await page.evaluate((GAP, LIMIT) => {
      const out = [];
      document.querySelectorAll('.stage-frame').forEach(fr => {
        const steps = [...fr.querySelectorAll('.step')];
        if (!steps.length) return;
        if (steps.some(s => s.querySelector('.fscene'))) return;   // visual 帧不累加，跳过
        const hadClear = steps.some(s => s.classList.contains('clear'));
        fr.classList.add('active');
        const tops = [], heights = [];
        steps.forEach((st, k) => {
          steps.forEach((s, j) => { s.classList.remove('on', 'gone'); if (j === k) s.classList.add('on'); });
          const kids = [...st.querySelectorAll('.slot,.chips,.hero,.sticker,.mini,.panel-l,.panel-r,.guanka')];
          let top = 1e9, bot = -1e9;
          kids.forEach(e => { if (e.offsetHeight > 0) { top = Math.min(top, e.offsetTop); bot = Math.max(bot, e.offsetTop + e.offsetHeight); } });
          tops.push(top === 1e9 ? 0 : top);
          heights.push(bot === -1e9 ? 0 : bot - (top === 1e9 ? 0 : top));
        });
        const limit = LIMIT;
        const bottom = Math.round(tops[0] + heights.reduce((a, b) => a + b, 0) + GAP * (steps.length - 1));
        out.push({ id: fr.id, n: steps.length, hadClear, bottom, limit });
        fr.classList.remove('active');
      });
      return out;
    }, GAP, LIMIT);
    console.log('== ' + SRC + ' ==');
    console.log('   舞台 ' + W + '×' + H + '，块间 ' + GAP + 'px，上限 = 字幕安全区 ' + LIMIT + 'px（只判 dialog 帧）');
    for (const r of res) {
      const marg = r.bottom <= r.limit - 24, over = r.bottom > r.limit;
      if (r.hadClear && marg) { console.log('   ⚠️ 放得下却清场：' + r.id + '（' + r.n + ' 步，累加底沿 ' + r.bottom + ' ≤ 上限 ' + r.limit + '）'); bad++; }
      else if (!r.hadClear && over) { console.log('   ❌ 装不下却没清场：' + r.id + '（' + r.n + ' 步，累加底沿 ' + r.bottom + ' > 上限 ' + r.limit + '）'); bad++; }
      else if (!marg && !over) console.log('   · 临界（清不清都成立，按习惯）：' + r.id + ' 底沿 ' + r.bottom + ' / 上限 ' + r.limit);
    }
    if (!bad) console.log('   ✅ 清场决策与空间一致（放得下的不清场，放不下的才清场）');
    await browser.close();
  }
  process.exit(bad ? 1 : 0);
})();
