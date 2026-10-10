#!/usr/bin/env node
/**
 * capture_anim.js — 动效版成片截图管线（确定性 30fps）
 *
 * 原理：
 *   1. 加载 make_standalone.py --animate 产出的 standalone.html
 *   2. 逐 1/30s tick 驱动 window.applyTime(t)
 *   3. 用 document.getAnimations() 把所有 CSS 动画/过渡同步到虚拟时钟：
 *      动画首次出现时记下虚拟起点 __vstart，此后每 tick 强制
 *      pause() + currentTime = (t - __vstart)*1000 —— 动画进度与
 *      截图耗时完全解耦，任何机器上都产出严格一致的 30fps 序列
 *   4. CDP Page.captureScreenshot (jpeg) 逐帧落盘 f%05d.jpg
 *
 * 用法: node capture_anim.js <standalone.html> <输出帧目录> [总秒数]
 * 输出: <输出帧目录>/f00000.jpg ...（约 120KB/帧，1.5GB/7min）
 */
const fs = require('fs'), path = require('path'), os = require('os');
function loadP() {
  try { return require('puppeteer-core'); } catch (e) {
    const r = path.join(os.homedir(), '.npm', '_npx');
    for (const d of fs.readdirSync(r)) {
      try { return require(path.join(r, d, 'node_modules', 'puppeteer-core')); } catch (e) {}
    }
  }
  throw new Error('puppeteer-core not found');
}
const puppeteer = loadP();

(async () => {
  const html = path.resolve(process.argv[2]);
  const outDir = path.resolve(process.argv[3]);
  const forceTotal = process.argv[4] ? parseFloat(process.argv[4]) : null;
  fs.mkdirSync(outDir, { recursive: true });

  const b = await puppeteer.launch({
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--force-device-scale-factor=1', '--hide-scrollbars',
           '--disable-gpu', '--font-render-hinting=none']
  });
  const p = await b.newPage();
  await p.setViewport({ width: 1920, height: 1080 });
  await p.goto('file://' + html, { waitUntil: 'networkidle0' });
  await p.evaluate(async () => {
    document.fonts && await document.fonts.ready;
    // 无用覆盖层（若存在）
    ['intro', 'hint', 'hud'].forEach(id => { const e = document.getElementById(id); if (e) e.style.display = 'none'; });
    // 预解码全部图片
    await Promise.all(Array.from(document.images).map(im =>
      im.complete ? 0 : new Promise(r => { im.onload = im.onerror = r; })));
  });

  const TOTAL = forceTotal || await p.evaluate(() => {
    if (window.HF_DATA) return Math.max(...Object.values(window.HF_DATA).map(d => d.gend));
    return window.__TOTAL || window.TOTAL || null;
  });
  if (!TOTAL) { console.error('无法确定总时长，请用第 3 个参数传入'); process.exit(1); }
  const FPS = 30, N = Math.round(TOTAL * FPS);
  console.log(`TOTAL=${TOTAL}s -> ${N} 帧 @${FPS}fps`);

  const cdp = await p.createCDPSession();
  await cdp.send('Page.enable');

  // 初始化虚拟时钟 + 重置到 t=0
  await p.evaluate(() => {
    window.__vt = 0;
    window.applyTime(0);
    document.getAnimations().forEach(a => { a.__vstart = 0; try { a.pause(); a.currentTime = 0; } catch (e) {} });
  });

  let lastPct = -10;
  for (let k = 0; k < N; k++) {
    const t = k / FPS;
    await p.evaluate((t) => {
      window.applyTime(t);
      for (const a of document.getAnimations()) {
        if (a.__vstart === undefined) a.__vstart = window.__vt;
        let lt = (t - a.__vstart) * 1000;
        try {
          const timing = a.effect.getTiming();
          if (timing.iterations !== Infinity) {
            const dur = (timing.duration || 0) * (timing.iterations || 1) + (timing.delay || 0);
            if (lt > dur) lt = dur;
          }
          a.pause();
          a.currentTime = lt;
        } catch (e) {}
      }
      window.__vt = t;
    }, t);
    const shot = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 82 });
    fs.writeFileSync(path.join(outDir, `f${String(k).padStart(5, '0')}.jpg`), Buffer.from(shot.data, 'base64'));
    const pct = Math.floor(k / N * 100);
    if (pct >= lastPct + 10) { lastPct = pct; console.log(`${pct}% (t=${t.toFixed(1)}s)`); }
  }
  await b.close();
  console.log(`DONE ${N} 帧 -> ${outDir}`);
})().catch(e => { console.error(e); process.exit(1); });
