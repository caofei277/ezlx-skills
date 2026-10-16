// stroke SVG → 高分辨率栅格 → potrace 描摹 → 填充轮廓 SVG（供 fantasticon 吃）
// 首跑自举：技能目录缺 potrace/sharp 时自动 npm install（与 build_font.mjs 的 fantasticon 同模式）
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const SKILL_ROOT = path.resolve(SCRIPT_DIR, '..');

function requireOrInstall(mod) {
  try {
    return createRequire(path.join(SKILL_ROOT, '__resolve__.js'))(mod);
  } catch {
    console.error(`[trace] 首跑安装 ${mod} 到技能目录 ...`);
    const r = spawnSync('npm', ['install', '--no-fund', '--no-audit', '--prefix', SKILL_ROOT, mod],
      { stdio: 'inherit' });
    if (r.status !== 0) {
      console.error(`[trace] FAIL: ${mod} 安装失败，请手动: npm install --prefix ${SKILL_ROOT}`);
      process.exit(1);
    }
    return createRequire(path.join(SKILL_ROOT, '__resolve__.js'))(mod);
  }
}

const potrace = requireOrInstall('potrace');
const sharp = requireOrInstall('sharp');

const [,, inFile, outFile, pxArg] = process.argv;
const PX = Number(pxArg || 960); // 24 grid × 40
const png = await sharp(Buffer.from(fs.readFileSync(inFile, 'utf8')), { density: 72 * (PX / 24) })
  .resize(PX, PX, { fit: 'contain', background: { r: 255, g: 255, b: 255, alpha: 1 } })
  .flatten({ background: '#ffffff' })
  .toBuffer();
const pt = new potrace.Potrace({ threshold: 128, blackOnWhite: true, turdSize: 2, optTolerance: 0.2, turnPolicy: potrace.Potrace.TURNPOLICY_MINORITY });
await new Promise((res, rej) => pt.loadImage(png, e => e ? rej(e) : res()));
const traced = pt.getSVG();
// 提取 potrace 输出的 path d，包回 960 viewBox 的纯填充 SVG
const d = [...traced.matchAll(/d="([^"]+)"/g)].map(m => m[1]).join(' ');
const out = `<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${PX} ${PX}" fill="currentColor"><path d="${d}" fill-rule="evenodd"/></svg>`;
fs.writeFileSync(outFile, out);
console.log('ok', outFile, out.length, 'bytes, paths:', traced.match(/d="/g).length);
