const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvis', {
  getConfig: () => ipcRenderer.invoke('config:get'),
  saveConfig: (c) => ipcRenderer.invoke('config:save', c),
  hide: () => ipcRenderer.send('hide'),
  onStart: (fn) => ipcRenderer.on('start', fn),
  onStop: (fn) => ipcRenderer.on('stop', fn),
});
