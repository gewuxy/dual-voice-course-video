// 按 schedule.json 的全局时间轴驱动 standalone.html 截图（只在视觉变化区间截一张）
//
// 用法：
//   node capture.js <工作目录> [chrome路径]
//   <工作目录> 下需有 standalone.html 与 schedule.json；截图落到 <工作目录>/shots/
// 依赖：puppeteer-core（自动搜索 npx 缓存 / 全局 node_modules），Chrome（可用 CHROME_BIN 覆盖）
const fs = require('fs');
const path = require('path');
const os = require('os');

function loadPuppeteer() {
  // 1) 常规 require（NODE_PATH / 本地 node_modules）
  try { return require('puppeteer-core'); } catch (e) {}
  // 2) 搜 ~/.npm/_npx/*/node_modules 下的缓存安装
  const roots = [path.join(os.homedir(), '.npm', '_npx')];
  for (const root of roots) {
    let dirs = [];
    try { dirs = fs.readdirSync(root); } catch (e) { continue; }
    for (const d of dirs) {
      const p = path.join(root, d, 'node_modules', 'puppeteer-core');
      if (fs.existsSync(p)) { try { return require(p); } catch (e) {} }
    }
  }
  // 3) 全局 npm 根
  for (const g of ['/usr/local/lib/node_modules', '/opt/homebrew/lib/node_modules']) {
    const p = path.join(g, 'puppeteer-core');
    if (fs.existsSync(p)) { try { return require(p); } catch (e) {} }
  }
  console.error('找不到 puppeteer-core。装一个：cd ~/.workbuddy/binaries/node/workspace && npm i puppeteer-core');
  process.exit(2);
}

const puppeteer = loadPuppeteer();
const CHROME = process.env.CHROME_BIN || process.argv[3] ||
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DIR = process.argv[2] || process.env.WORK_DIR;
if (!DIR) { console.error('用法：node capture.js <工作目录> [chrome路径]'); process.exit(2); }

const sched = JSON.parse(fs.readFileSync(path.join(DIR, 'schedule.json'), 'utf-8'));
const shotsDir = path.join(DIR, 'shots');
fs.mkdirSync(shotsDir, { recursive: true });

// 从 standalone 的 <meta name="hf-size"> 读取舞台尺寸（竖版 1080×1440 / 横版 1920×1080），缺省回退横版
function readSize(file) {
  try {
    const h = fs.readFileSync(file, 'utf-8');
    const m = h.match(/name="hf-size"\s+content="(\d+)x(\d+)"/);
    if (m) return { width: +m[1], height: +m[2] };
  } catch (e) {}
  return { width: 1920, height: 1080 };
}
const SIZE = readSize(path.join(DIR, 'standalone.html'));

(async () => {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--force-device-scale-factor=1',
           '--hide-scrollbars', '--disable-dev-shm-usage'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: SIZE.width, height: SIZE.height, deviceScaleFactor: 1 });
  await page.goto('file://' + path.join(DIR, 'standalone.html'),
                  { waitUntil: 'networkidle0', timeout: 90000 });
  await page.evaluate(() => document.fonts && document.fonts.ready);

  const intervals = sched.intervals;
  const durations = [];
  for (let i = 0; i < intervals.length; i++) {
    const { t, dur } = intervals[i];
    await page.evaluate((tt) => window.applyTime(tt), t);
    await new Promise(r => setTimeout(r, 90));   // 等布局/字体绘制稳定
    await page.screenshot({
      path: path.join(shotsDir, 'shot_' + String(i).padStart(4, '0') + '.png'), type: 'png' });
    durations.push(dur);
    if (i % 20 === 0) console.log('captured', i + 1, '/', intervals.length, 't=', t);
  }
  fs.writeFileSync(path.join(DIR, 'durations.txt'), durations.map(d => d.toFixed(3)).join('\n'));
  await browser.close();
  console.log('DONE shots=', intervals.length, 'total=', sched.total);
})().catch(e => { console.error('CAPTURE ERROR', e); process.exit(1); });
