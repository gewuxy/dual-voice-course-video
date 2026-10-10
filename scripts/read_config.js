// read_config.js — node 侧统一配置读取（零依赖，与 python 的 load_config.py 对齐）
//
// 优先级：环境变量 > config.local.json > config.example.json（都缺失返回空对象）
// 用法（模块）：
//   const { resolve } = require('./read_config.js');
//   resolve('chrome_bin')   // env CHROME_BIN > config.paths.chrome_bin > ''
//   resolve('ffmpeg')       // env FFMPEG     > config.paths.ffmpeg     > ''
// 用法（CLI）：
//   node read_config.js                 # 打印完整合并配置 JSON
//   node read_config.js chrome_bin      # 打印单个值（找不到打印空行）
const fs = require('fs');
const path = require('path');

const SKILL_DIR = path.resolve(__dirname, '..');

function loadConfig() {
  for (const f of ['config.local.json', 'config.example.json']) {
    try {
      return JSON.parse(fs.readFileSync(path.join(SKILL_DIR, f), 'utf-8'));
    } catch (e) { /* 下一个 */ }
  }
  return {};
}

const ENV_MAP = { chrome_bin: 'CHROME_BIN', ffmpeg: 'FFMPEG' };

function resolve(tool) {
  const envKey = ENV_MAP[tool];
  if (envKey && process.env[envKey]) return process.env[envKey];
  const v = (loadConfig().paths || {})[tool];
  return (typeof v === 'string' && v) ? v : '';
}

module.exports = { loadConfig, resolve };

if (require.main === module) {
  const k = process.argv[2];
  if (!k) {
    console.log(JSON.stringify(loadConfig(), null, 2));
  } else {
    console.log(resolve(k.replace(/^paths\./, '')));
  }
}
