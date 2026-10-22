const { app, BrowserWindow, Tray, Menu, ipcMain, session, safeStorage, nativeImage } = require('electron');
const fs = require('fs');
const http = require('http');
const path = require('path');

const { uIOhook, UiohookKey } = require('uiohook-napi');

// Right Ctrl pressed and released on its own (no other key in between) toggles Jarvis.
const MAX_TAP_MS = 500;
const cfgPath = () => path.join(app.getPath('userData'), 'config.json');
let win, tray, localUrl = '';

function loadConfig() {
  try {
    const c = JSON.parse(fs.readFileSync(cfgPath(), 'utf8'));
    const token = c.token && safeStorage.isEncryptionAvailable()
      ? safeStorage.decryptString(Buffer.from(c.token, 'base64')) : '';
    return { backendUrl: c.backendUrl || '', token };
  } catch { return { backendUrl: '', token: '' }; }
}

function saveConfig({ backendUrl, token }) {
  const enc = safeStorage.isEncryptionAvailable()
    ? safeStorage.encryptString(token).toString('base64') : '';
  fs.writeFileSync(cfgPath(), JSON.stringify({ backendUrl, token: enc }));
}

// The renderer is served from a tiny local server (127.0.0.1 only). From file:// the browser
// refuses to load the audio worklet that the voice SDK needs for the microphone.
function serveRenderer() {
  const dir = path.join(__dirname, 'renderer');
  const files = { '/': 'index.html', '/index.html': 'index.html', '/renderer.js': 'renderer.js' };
  const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8' };
  return new Promise((resolve) => {
    const srv = http.createServer((req, res) => {
      const name = files[(req.url || '/').split('?')[0]];
      if (!name) { res.writeHead(404); return res.end(); }
      fs.readFile(path.join(dir, name), (err, data) => {
        if (err) { res.writeHead(500); return res.end(); }
        res.writeHead(200, { 'Content-Type': types[path.extname(name)] });
        res.end(data);
      });
    });
    srv.listen(0, '127.0.0.1', () => resolve(srv.address().port));
  });
}

// The UI comes from the backend (`<backendUrl>/app/`), so UI updates need no new download.
// The bundled local page is only for first-run setup and for when the backend is unreachable.
function remoteUrl() {
  const { backendUrl } = loadConfig();
  return backendUrl ? backendUrl.replace(/\/$/, '') + '/app/' : '';
}

function originOf(url) {
  try { return new URL(url).origin; } catch { return ''; }
}

function trusted(url) {
  const o = originOf(url);
  return !!o && (o === originOf(localUrl) || o === originOf(remoteUrl()));
}

function loadUi() {
  const remote = remoteUrl();
  win.loadURL(remote || localUrl);
}

async function createWindow() {
  win = new BrowserWindow({
    width: 340, height: 300, frame: false, alwaysOnTop: true, resizable: false,
    skipTaskbar: true, show: false, backgroundColor: '#0f1117',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false },
  });
  const port = await serveRenderer();
  localUrl = `http://127.0.0.1:${port}/index.html`;
  win.webContents.on('did-fail-load', (_e, _code, _desc, url, isMainFrame) => {
    if (isMainFrame && url !== localUrl) win.loadURL(localUrl + '?offline=1');
  });
  win.webContents.on('will-navigate', (e, url) => { if (!trusted(url)) e.preventDefault(); });
  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  loadUi();
  win.on('close', (e) => { if (!app.isQuitting) { e.preventDefault(); win.hide(); } });
}

function toggle() {
  if (win.isVisible()) { win.webContents.send('stop'); win.hide(); return; }
  const { screen } = require('electron');
  const d = screen.getPrimaryDisplay().workArea;
  win.setPosition(d.x + d.width - 360, d.y + d.height - 320);
  win.show(); win.focus();
  win.webContents.send('start');
}

app.whenReady().then(async () => {
  session.defaultSession.setPermissionRequestHandler((_wc, permission, cb) => cb(permission === 'media'));
  // Only our own pages (local setup page or the backend's /app/) may read the saved token.
  ipcMain.handle('config:get', (e) => (trusted(e.senderFrame.url) ? loadConfig() : { backendUrl: '', token: '' }));
  ipcMain.handle('config:save', (e, c) => {
    if (!trusted(e.senderFrame.url)) return;
    saveConfig(c);
    setTimeout(loadUi, 300);
  });
  ipcMain.on('hide', () => win.hide());
  await createWindow();
  tray = new Tray(nativeImage.createFromPath(path.join(__dirname, 'icon.png')).resize({ width: 16, height: 16 }));
  tray.setToolTip('Jarvis (правый Ctrl)');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Открыть', click: toggle },
    { label: 'Выход', click: () => { app.isQuitting = true; app.quit(); } },
  ]));
  tray.on('click', toggle);
  let down = 0, clean = false;
  uIOhook.on('keydown', (e) => {
    if (e.keycode === UiohookKey.CtrlRight) { if (!down) { down = Date.now(); clean = true; } }
    else clean = false;
  });
  uIOhook.on('keyup', (e) => {
    if (e.keycode !== UiohookKey.CtrlRight) return;
    if (down && clean && Date.now() - down < MAX_TAP_MS) toggle();
    down = 0;
  });
  uIOhook.start();
});

app.on('will-quit', () => uIOhook.stop());
app.on('window-all-closed', (e) => e.preventDefault());
