// pptr.js — 共享 puppeteer-core 加载器（capture.js / capture_anim.js / qc_frames.js 三处合一）
//
// 查找顺序：常规 require（NODE_PATH / 本地 node_modules）
//         → ~/.npm/_npx/*/node_modules（npx 缓存）
//         → 全局 npm 根（Intel: /usr/local/lib/node_modules；Apple Silicon: /opt/homebrew/lib/node_modules）
const fs = require('fs');
const path = require('path');
const os = require('os');

function loadPuppeteer() {
  try { return require('puppeteer-core'); } catch (e) {}
  const npxRoot = path.join(os.homedir(), '.npm', '_npx');
  let dirs = [];
  try { dirs = fs.readdirSync(npxRoot); } catch (e) {}
  for (const d of dirs) {
    const p = path.join(npxRoot, d, 'node_modules', 'puppeteer-core');
    if (fs.existsSync(p)) { try { return require(p); } catch (e) {} }
  }
  for (const g of ['/usr/local/lib/node_modules', '/opt/homebrew/lib/node_modules']) {
    const p = path.join(g, 'puppeteer-core');
    if (fs.existsSync(p)) { try { return require(p); } catch (e) {} }
  }
  console.error('找不到 puppeteer-core。装一个：cd ~/.workbuddy/binaries/node/workspace && npm i puppeteer-core');
  process.exit(2);
}

module.exports = { loadPuppeteer };
