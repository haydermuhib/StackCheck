#!/usr/bin/env node
// StackCheck Launch Video deterministic renderer.
// CLI Contract: node src/render.js --from 0 --to 3 --fps 30 --scale 1 --out renders/previews --name "Preview v1" [--audio mix.wav] [--jpg]
import http from 'node:http';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { readFile, stat, mkdir, writeFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = process.cwd();
const src = path.dirname(fileURLToPath(import.meta.url));
const a = process.argv.slice(2);
const opt = (k, d) => { const i = a.indexOf('--' + k); return i < 0 ? d : a[i + 1]; };

const { DURATION, W, H, scenes } = await import('./data.js');
const from = Number(opt('from', 0));
const to = Number(opt('to', DURATION));
const fps = Number(opt('fps', 30));
const scale = Number(opt('scale', 1));

if (![from, to, fps, scale].every(Number.isFinite) || from < 0 || to <= from || fps <= 0 || scale <= 0 || scale > 1) {
  throw Error('Invalid range, fps or scale');
}

const count = Math.ceil((to - from) * fps - 1e-8);
const out = path.resolve(opt('out', 'cache/smoke'));
const jpg = a.includes('--jpg');
const name = String(opt('name', 'Preview v1'));
if (!name || /[\\/:*?"<>|]/.test(name)) throw Error('Use a plain output name without path separators');

const dest = path.join(out, name + '.mp4');
const audio = opt('audio');
if (audio && !existsSync(path.resolve(audio))) throw Error('Audio file not found: ' + audio);
if (!jpg && existsSync(dest)) throw Error('Output exists; use a new version name: ' + dest);

await mkdir(out, { recursive: true });
if (jpg && (await readdir(out)).some(f => /^\d{5}\.(jpg|png)$/.test(f))) {
  throw Error('Frame output already exists; choose a fresh cache directory: ' + out);
}

const ffmpeg = process.env.MVD_FFMPEG || 'ffmpeg';
const defaultChrome = '/home/haider/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome';
const browserPath = process.env.MVD_CHROMIUM || (existsSync(defaultChrome) ? defaultChrome : 'google-chrome');

// Serve only render resources on loopback
const mime = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.mjs': 'text/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.mp4': 'video/mp4'
};

const srcUrl = '/' + path.relative(root, src).split(path.sep).join('/');
const server = http.createServer(async (request, response) => {
  try {
    const u = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
    if (u.split('/').some(s => s.startsWith('.')) || !['/src/', '/assets/', '/plan/'].some(s => u.startsWith(s))) {
      throw Error('Forbidden');
    }
    const localF = path.resolve(root, '.' + u);
    const parentF = path.resolve(root, '..' + u);
    const f = existsSync(localF) ? localF : (existsSync(parentF) ? parentF : localF);
    if ((await stat(f)).isDirectory()) throw Error('Forbidden');
    response.writeHead(200, { 'Content-Type': mime[path.extname(f)] || 'application/octet-stream' });
    response.end(await readFile(f));
  } catch {
    response.writeHead(404);
    response.end('Not found');
  }
});

let chromeProcess, encoder, encodeResult, ws;

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 1;
    this.pending = new Map();
  }
  async connect() {
    await new Promise((res, rej) => {
      this.ws.onopen = res;
      this.ws.onerror = rej;
    });
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        if (msg.error) reject(new Error(msg.error.message));
        else resolve(msg.result);
      }
    };
  }
  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = this.id++;
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expression, awaitPromise = false) {
    const res = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise
    });
    if (res.exceptionDetails) {
      throw new Error(res.exceptionDetails.text || 'JS Evaluation Exception');
    }
    return res.result?.value;
  }
  close() {
    try { this.ws.close(); } catch {}
  }
}

try {
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const serverPort = server.address().port;

  // Launch headless browser with CDP
  const cdpPort = 9222 + Math.floor(Math.random() * 500);
  const homeDir = path.join(root, 'cache/home');
  await mkdir(homeDir, { recursive: true });

  chromeProcess = spawn(browserPath, [
    '--headless',
    '--no-sandbox',
    '--disable-gpu',
    `--remote-debugging-port=${cdpPort}`,
    `--user-data-dir=${path.join(homeDir, 'cdp_profile')}`,
    'about:blank'
  ], {
    env: { ...process.env, HOME: homeDir },
    stdio: 'ignore'
  });

  // Wait for CDP readiness
  let targetWsUrl = null;
  for (let attempt = 0; attempt < 30; attempt++) {
    await new Promise(r => setTimeout(r, 200));
    try {
      const r = await fetch(`http://127.0.0.1:${cdpPort}/json/version`);
      const v = await r.json();
      if (v.webSocketDebuggerUrl) {
        targetWsUrl = v.webSocketDebuggerUrl;
        break;
      }
    } catch {}
  }
  if (!targetWsUrl) throw Error('Could not connect to browser CDP port ' + cdpPort);

  // Create a new target page
  const newTargetRes = await fetch(`http://127.0.0.1:${cdpPort}/json/new?http://127.0.0.1:${serverPort}/src/index.html?scale=${scale}`, { method: 'PUT' });
  const targetJson = await newTargetRes.json();
  const pageWsUrl = targetJson.webSocketDebuggerUrl;

  const cdp = new CDPClient(pageWsUrl);
  await cdp.connect();
  await cdp.send('Page.enable');
  await cdp.send('Runtime.enable');

  // Wait for window.__ready === true
  let ready = false;
  for (let i = 0; i < 150; i++) {
    try {
      ready = await cdp.evaluate('window.__ready === true');
      if (ready) break;
    } catch {}
    await new Promise(r => setTimeout(r, 100));
  }
  if (!ready) throw Error('Renderer index.html timed out waiting for window.__ready');

  // Setup FFmpeg encoder if not writing individual frames
  if (!jpg) {
    const args = ['-hide_banner', '-n', '-f', 'image2pipe', '-framerate', String(fps), '-i', 'pipe:0'];
    if (audio) args.push('-ss', String(from), '-t', String(to - from), '-i', path.resolve(audio));
    args.push('-map', '0:v:0');
    if (audio) args.push('-map', '1:a:0', '-af', 'apad', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000');
    args.push('-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-frames:v', String(count), '-t', String(count / fps), '-movflags', '+faststart', dest);

    encoder = spawn(ffmpeg, args, { stdio: ['pipe', 'inherit', 'inherit'] });
    encodeResult = new Promise((resolve, reject) => {
      encoder.once('error', reject);
      encoder.once('close', code => code === 0 ? resolve() : reject(Error('FFmpeg exited ' + code)));
    });
    encodeResult.catch(() => {});
    encoder.stdin.on('error', () => {});
  }

  console.log(`Starting render: frames ${count} | from ${from}s to ${to}s | scale ${scale} | fps ${fps}`);
  const startTime = Date.now();

  for (let i = 0; i < count; i++) {
    const t = from + i / fps;
    await cdp.evaluate(`window.renderFrame(${t})`, true);
    const dataUrl = await cdp.evaluate(`window.grab("${jpg ? 'image/jpeg' : 'image/png'}")`, false);
    const bytes = Buffer.from(dataUrl.slice(dataUrl.indexOf(',') + 1), 'base64');

    if (jpg) {
      await writeFile(path.join(out, String(i).padStart(5, '0') + '.jpg'), bytes);
    } else {
      if (!encoder.stdin.write(bytes)) {
        await Promise.race([
          once(encoder.stdin, 'drain'),
          encodeResult.then(() => { throw Error('Encoder ended early'); })
        ]);
      }
    }

    if ((i + 1) % 30 === 0 || i === count - 1) {
      process.stdout.write(`Rendered ${i + 1}/${count} frames (${Math.round((i + 1) / count * 100)}%)\r`);
    }
  }

  if (encoder) {
    encoder.stdin.end();
    await encodeResult;
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  console.log(`\nRender complete in ${elapsed}s -> ${jpg ? out : dest}`);
  cdp.close();

} finally {
  if (encoder && encoder.exitCode === null) encoder.kill();
  if (chromeProcess) chromeProcess.kill();
  await new Promise(resolve => server.close(resolve));
}
