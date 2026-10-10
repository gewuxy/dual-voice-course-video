// index_present.html 逐帧 QC：全展开截图 + 溢出检测（+ 可选音频播放探测 / 逐 step 截图）
//
// 用法：
//   node qc_frames.js <index_present.html> <输出目录> [audio元素id] [逐step帧号]
// 例：
//   node qc_frames.js ./index_present.html /tmp/qc l1rhyme 2
//
// 输出：<输出目录>/f01.png ... ；逐 step 图 <输出目录>/step_<帧>_<k>.png
// 检测：每帧全展开后元素底部相对舞台画布的位置，超出「画布高-80px」视为被页脚裁切（需修布局）。
//       舞台尺寸自动从 #stageWrap 读取（竖版 1080×1440 / 横版 1920×1080）。
//
// ⚠️ 关键坑：截「逐步」图前必须先移除**所有**帧的 .active，否则上一帧内容会残影叠加。
const fs = require('fs');
const path = require('path');
const { loadPuppeteer } = require('./pptr.js');
const { resolve } = require('./read_config.js');

const puppeteer = loadPuppeteer();
// Chrome：env CHROME_BIN > config.paths.chrome_bin > macOS 默认
const CHROME = resolve('chrome_bin') ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const SRC = process.argv[2];
const OUT = process.argv[3] || '/tmp/qc_frames';
const AUDIO_ID = process.argv[4] || null;
const STEP_FRAME = process.argv[5] ? parseInt(process.argv[5], 10) : null;
if (!SRC) { console.error('用法：node qc_frames.js <index_present.html> <输出目录> [audioId] [stepFrameNo]'); process.exit(2); }
fs.mkdirSync(OUT, { recursive: true });

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME, headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--force-device-scale-factor=1', '--hide-scrollbars',
           '--disable-dev-shm-usage', '--autoplay-policy=no-user-gesture-required'],
  });
  const page = await browser.newPage();
  // 舞台尺寸自动从源 #stageWrap 读取（竖版 1080×1440 / 横版 1920×1080），缺省回退横版
  let STAGE = { width: 1920, height: 1080 };
  try {
    const h = fs.readFileSync(path.resolve(SRC), 'utf-8');
    let m = h.match(/id="stageWrap"[^>]*style="[^"]*?width:\s*(\d+)px[^"]*?height:\s*(\d+)px/);
    if (!m) m = h.match(/#stageWrap\s*\{[^}]*?width:\s*(\d+)px[^}]*?height:\s*(\d+)px/);
    if (m) STAGE = { width: +m[1], height: +m[2] };
  } catch (e) {}
  await page.setViewport({ width: STAGE.width, height: STAGE.height, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(SRC), { waitUntil: 'networkidle0', timeout: 90000 });
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.evaluate(() => {
    ['intro', 'hint', 'hud'].forEach(id => { const e = document.getElementById(id); if (e) e.style.display = 'none'; });
  });

  // —— 可选：内嵌音频播放探测（确认放映版里真的会响）——
  if (AUDIO_ID) {
    const audio = await page.evaluate(async (aid) => {
      const a = document.getElementById(aid);
      if (!a) return { found: false };
      const root = document.getElementById('root');
      root.click(); root.click();                 // 跳到第 2 帧第 1 步
      await new Promise(r => setTimeout(r, 1600));
      return { found: true, dur: Math.round((a.duration || 0) * 10) / 10, ready: a.readyState,
               paused: a.paused, t: Math.round(a.currentTime * 100) / 100 };
    }, AUDIO_ID);
    console.log('AUDIO', JSON.stringify(audio));
  }

  const n = await page.evaluate(() => document.querySelectorAll('.stage-frame').length);
  const report = [];
  for (let i = 1; i <= n; i++) {
    const info = await page.evaluate((idx) => {
      const frames = document.querySelectorAll('.stage-frame');
      frames.forEach(f => f.classList.remove('active'));       // 关键：先关掉其它帧
      const f = frames[idx - 1]; f.classList.add('active');
      f.querySelectorAll('.step').forEach(s => { s.classList.add('on'); s.classList.remove('gone'); });
      let maxBottom = 0; const over = [];
      const root = (document.getElementById('root') || document.getElementById('stageWrap'));
      const rootRect = root.getBoundingClientRect();
      const refH = rootRect.height || 1080;   // 实际画布高（竖版 1440 / 横版 1080）
      f.querySelectorAll('.sticker,.card,.ask,.reply,.say,.vis, div[style*="background"]').forEach(el => {
        const r = el.getBoundingClientRect();
        const bottomRel = (r.bottom - rootRect.top) / (rootRect.height / refH);
        if (bottomRel > maxBottom) maxBottom = bottomRel;
        if (bottomRel > refH - 80) over.push(Math.round(bottomRel));
      });
      return { maxBottom: Math.round(maxBottom), over };
    }, i);
    await new Promise(r => setTimeout(r, 450));
    report.push({ f: i, ...info });
    await page.screenshot({ path: path.join(OUT, 'f' + String(i).padStart(2, '0') + '.png'), type: 'png' });
  }
  console.log('QC', JSON.stringify(report));
  const bad = report.filter(r => r.over.length);
  console.log(bad.length ? '⚠️ 溢出帧：' + bad.map(r => `f${r.f}(${r.over.join('/')})`).join(' ') : '✅ 全部帧无溢出');

  // —— 可选：某一帧的逐 step 截图（验证逐步出现顺序）——
  if (STEP_FRAME) {
    const cnt = await page.evaluate((idx) => document.querySelectorAll('.stage-frame')[idx - 1].querySelectorAll('.step').length, STEP_FRAME);
    for (let k = 1; k <= cnt; k++) {
      await page.evaluate(({ idx, kk }) => {
        const frames = document.querySelectorAll('.stage-frame');
        frames.forEach(f => f.classList.remove('active'));   // 同样先清干净
        const f = frames[idx - 1]; f.classList.add('active');
        f.querySelectorAll('.step').forEach((el, i) => el.classList.toggle('on', i < kk));
      }, { idx: STEP_FRAME, kk: k });
      await new Promise(r => setTimeout(r, 550));
      await page.screenshot({ path: path.join(OUT, `step_${STEP_FRAME}_${k}.png`), type: 'png' });
    }
    console.log(`逐步截图 ${cnt} 张 -> ${OUT}/step_${STEP_FRAME}_*.png`);
  }

  await browser.close();
  console.log('DONE', n, '->', OUT);
})().catch(e => { console.error('ERR', e); process.exit(1); });
