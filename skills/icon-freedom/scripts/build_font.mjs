#!/usr/bin/env node
// build_font.mjs — icons-src 源 SVG → 字体(woff2/woff/ttf) + css（icon-freedom skill）
//
// 用法: node build_font.mjs [--spec .icons/spec.json] [--base64]
//
// 行为:
//   1. 收集 build.src_dir 下 *.svg（跳过 _ 开头文件/目录, 如 _reference/）
//   2. codepoints.json 持久化保证码点稳定（存量图标码点永不漂移）
//   3. 首跑自动把 fantasticon 装进技能自带 node_modules（不污染项目）
//   4. 生成字体 + css 到 build.out_dir；--base64 时追加 woff2 内嵌版 @font-face
//
// 产物 css 交付后由 agent 负责接进项目现有样式管线（如 uni-app App.vue @import）。

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = path.resolve(SCRIPT_DIR, '..');

function fail(msg) {
  console.error('[build_font] FAIL: ' + msg);
  process.exit(1);
}

// ---- 参数 ----
const argv = process.argv.slice(2);
let specPath = '.icons/spec.json';
let forceBase64 = false;
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--spec') specPath = argv[++i];
  else if (argv[i] === '--base64') forceBase64 = true;
  else fail('未知参数 ' + argv[i]);
}
if (!fs.existsSync(specPath)) fail('spec 不存在: ' + specPath + '（可从 references/spec.template.json 复制定制）');
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const b = spec.build || {};
const srcDir = b.src_dir || 'src/static/icons-src';
const outDir = b.out_dir || 'src/static/font/iconfont';
const fontName = b.font_name || 'iconfont';
const prefix = (b.class_prefix || 'icon').replace(/-+$/, '');
const formats = (b.formats || ['woff2', 'woff', 'ttf']).map(s => String(s).toLowerCase());
const base64 = forceBase64 || !!b.base64;
const fontHeight = b.font_height || 1024;
const startCp = parseInt(b.start_codepoint || '0xe600', 16);

// ---- 1. 收集源 ----
if (!fs.existsSync(srcDir)) fail('源目录不存在: ' + srcDir);
const files = fs.readdirSync(srcDir)
  .filter(f => f.toLowerCase().endsWith('.svg') && !f.startsWith('_') && !f.startsWith('.'));
if (!files.length) fail('源目录无 svg: ' + srcDir);

// ---- 2. 码点稳定化 ----
const cpFile = path.join(srcDir, 'codepoints.json');
let cps = {};
if (fs.existsSync(cpFile)) {
  try { cps = JSON.parse(fs.readFileSync(cpFile, 'utf8')); } catch { fail(cpFile + ' 不是合法 JSON'); }
}
let next = startCp;
for (const f of files) {
  const name = f.replace(/\.svg$/i, '');
  if (!cps[name]) {
    while (Object.values(cps).includes(next)) next++;
    cps[name] = next;
  }
}
// 清理已删除图标的码点，防 map 无限增长
const names = new Set(files.map(f => f.replace(/\.svg$/i, '')));
for (const k of Object.keys(cps)) if (!names.has(k)) delete cps[k];
fs.writeFileSync(cpFile, JSON.stringify(cps, null, 2) + '\n');

// ---- 3. 解析 fantasticon（技能私有 node_modules, 可用环境变量覆盖） ----
function tryRequire(base) {
  if (!base) return null;
  try {
    const req = createRequire(path.join(base, '__resolve__.js'));
    req.resolve('fantasticon');
    return req('fantasticon');
  } catch { return null; }
}
let fantasticon = tryRequire(process.env.ICON_FREEDOM_NODE_DEPS)
  || tryRequire(SKILL_ROOT);
if (!fantasticon) {
  console.error('[build_font] 首跑安装 fantasticon 到技能目录 ...');
  const r = spawnSync('npm', ['install', '--no-fund', '--no-audit', '--prefix', SKILL_ROOT, 'fantasticon@^4.1.0'],
    { stdio: 'inherit' });
  fantasticon = r.status === 0 ? tryRequire(SKILL_ROOT) : null;
  if (!fantasticon) fail('fantasticon 安装失败，请检查网络或手动: npm i --prefix ' + SKILL_ROOT + ' fantasticon');
}
const { generateFonts } = fantasticon;

// ---- 4. 构建 ----
fs.mkdirSync(outDir, { recursive: true });
let result;
try {
  result = await generateFonts({
    inputDir: srcDir,
    outputDir: outDir,
    name: fontName,
    fontTypes: formats,                 // 'woff2' | 'woff' | 'ttf' | 'eot' | 'svg'
    assetTypes: ['css'],
    codepoints: cps,
    fontHeight,
    normalize: true,
    prefix,
  });
} catch (e) {
  fail('fantasticon 构建失败: ' + (e && e.message || e));
}

// ---- 5. 校验产物 + css 适配 + base64 内嵌 ----
const cssFile = path.join(outDir, fontName + '.css');
if (!fs.existsSync(cssFile)) fail('css 产物缺失: ' + cssFile);
const made = formats.filter(ft => fs.existsSync(path.join(outDir, fontName + '.' + ft)));
if (!made.length) fail('无字体产物生成，检查源 svg 是否合法');
let notes = [];

// fantasticon 默认基类选择器绑死 <i> 标签（i[class^=…]），多端（uni-app <text>/Web <span>）不通用，
// 改写成标签无关的属性选择器，<i>/<text>/<span>/<view> 全适配。
{
  let css = fs.readFileSync(cssFile, 'utf8');
  const fixed = css.replace(/([\s,])i(\[class(?:\^|\*)=)/g, '$1$2');
  if (fixed !== css) {
    fs.writeFileSync(cssFile, fixed);
    notes.push('基类选择器已改为标签无关（i[class…] → [class…]）');
  }
  // 小程序 WXSS 对属性选择器无官方承诺：追加显式基类 .{prefix}-font:before（用法 class="{prefix}-font {prefix}-{name}"）
  const baseSel = `.${prefix}-font:before`;
  if (!css.includes(baseSel)) {
    const block = `\n${baseSel} {\n    font-family: "${fontName}" !important;\n    font-style: normal;\n    font-weight: normal !important;\n    font-variant: normal;\n    text-transform: none;\n    line-height: 1;\n    -webkit-font-smoothing: antialiased;\n    -moz-osx-font-smoothing: grayscale;\n}\n`;
    fs.appendFileSync(cssFile, block);
    notes.push(`已追加显式基类 ${baseSel}（小程序 WXSS 兼容兜底，用法 class="${prefix}-font ${prefix}-图标名"）`);
  }
}

if (base64) {
  const woff2 = path.join(outDir, fontName + '.woff2');
  if (!fs.existsSync(woff2)) fail('--base64 需要 woff2 格式，但未生成');
  const b64 = fs.readFileSync(woff2).toString('base64');
  let css = fs.readFileSync(cssFile, 'utf8');
  const marker = '/* icon-freedom base64 embed */';
  const block = marker + '\n@font-face {\n  font-family: "' + fontName + '";\n' +
    '  src: url(data:font/woff2;base64,' + b64 + ') format("woff2"), ' +
    "url('" + fontName + ".ttf') format('truetype');\n}\n";
  if (css.includes(marker)) {
    css = css.slice(0, css.indexOf(marker)) + block; // 重建到块尾
  } else {
    css += '\n' + block;
  }
  fs.writeFileSync(cssFile, css);
  notes.push('woff2 已 base64 内嵌进 css');
}

console.log(JSON.stringify({
  ok: true, out_dir: outDir, fonts: made, glyphs: files.length,
  css: cssFile, codepoints: cpFile, notes,
}, null, 2));
