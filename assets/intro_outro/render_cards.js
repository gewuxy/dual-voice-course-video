// 渲染片头锚句条(透明底)与片尾卡 → PNG
// 用法: node render_cards.js <assets目录>
const fs = require('fs'), path = require('path'), os = require('os');
function loadPuppeteer() {
  try { return require('puppeteer-core'); } catch (e) {}
  const roots = [path.join(os.homedir(), '.npm', '_npx')];
  for (const root of roots) {
    let dirs = [];
    try { dirs = fs.readdirSync(root); } catch (e) { continue; }
    for (const d of dirs) {
      const p = path.join(root, d, 'node_modules', 'puppeteer-core');
      if (fs.existsSync(p)) { try { return require(p); } catch (e) {} }
    }
  }
  for (const g of ['/usr/local/lib/node_modules', '/opt/homebrew/lib/node_modules']) {
    const p = path.join(g, 'node_modules/puppeteer-core');
    if (fs.existsSync(p)) { try { return require(p); } catch (e) {} }
  }
  console.error('找不到 puppeteer-core'); process.exit(2);
}
const puppeteer = loadPuppeteer();
const CHROME = process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const DIR = process.argv[2];

(async () => {
  const browser = await puppeteer.launch({ executablePath: CHROME, headless: 'new',
    args: ['--no-sandbox', '--force-device-scale-factor=1'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });

  // 片尾卡（不透明）
  await page.goto('file://' + path.join(DIR, '片尾卡.html'));
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(DIR, 'endcard.png') });
  console.log('endcard.png 完成');

  // 片头卡（不透明，独立片头）
  await page.goto('file://' + path.join(DIR, '片头卡.html'));
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(DIR, 'introcard.png') });
  console.log('introcard.png 完成');

  // 片头锚句条（透明底）
  await page.goto('file://' + path.join(DIR, '片头锚句条.html'));
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 400));
  await page.screenshot({ path: path.join(DIR, 'anchor_strip.png'), omitBackground: true });
  console.log('anchor_strip.png 完成');

  await browser.close();
})();
