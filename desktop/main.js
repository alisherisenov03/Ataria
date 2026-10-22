const { app, BrowserWindow, globalShortcut, Tray, Menu, ipcMain, session, safeStorage, nativeImage } = require('electron');
const fs = require('fs');
const path = require('path');

const HOTKEY = 'Control+Shift+J';
const cfgPath = () => path.join(app.getPath('userData'), 'config.json');
let win, tray;

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

function createWindow() {
  win = new BrowserWindow({
    width: 340, height: 300, frame: false, alwaysOnTop: true, resizable: false,
    skipTaskbar: true, show: false, backgroundColor: '#0f1117',
    webPreferences: { preload: path.join(__dirname, 'preload.js'), contextIsolation: true, nodeIntegration: false },
  });
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
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

app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((_wc, permission, cb) => cb(permission === 'media'));
  ipcMain.handle('config:get', loadConfig);
  ipcMain.handle('config:save', (_e, c) => { saveConfig(c); });
  ipcMain.on('hide', () => win.hide());
  createWindow();
  tray = new Tray(nativeImage.createFromPath(path.join(__dirname, 'icon.png')));
  tray.setToolTip(`Jarvis (${HOTKEY})`);
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Открыть', click: toggle },
    { label: 'Выход', click: () => { app.isQuitting = true; app.quit(); } },
  ]));
  tray.on('click', toggle);
  if (!globalShortcut.register(HOTKEY, toggle)) console.error('hotkey unavailable');
});

app.on('will-quit', () => globalShortcut.unregisterAll());
app.on('window-all-closed', (e) => e.preventDefault());
