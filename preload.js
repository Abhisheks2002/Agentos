/**
 * AgentOS - Preload Script
 * Secure bridge between renderer and main process
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
  getLogsPath: () => ipcRenderer.invoke('get-logs-path'),

  // Dialogs
  openFolderDialog: () => ipcRenderer.invoke('open-folder-dialog'),
  openFileDialog: (options) => ipcRenderer.invoke('open-file-dialog', options),
  showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),

  // Notifications
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', { title, body }),

  // Server control
  controlServer: (action) => ipcRenderer.invoke('control-server', action),

  // Shell operations
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  showInFolder: (path) => ipcRenderer.invoke('show-in-folder', path),
  openPath: (path) => ipcRenderer.invoke('open-path', path),

  // Platform info
  getPlatform: () => ipcRenderer.invoke('get-platform'),

  // Window controls
  minimizeWindow: () => ipcRenderer.invoke('window-minimize'),
  maximizeWindow: () => ipcRenderer.invoke('window-maximize'),
  closeWindow: () => ipcRenderer.invoke('window-close'),
  isWindowMaximized: () => ipcRenderer.invoke('window-is-maximized'),

  // Clipboard
  clipboardWrite: (text) => ipcRenderer.invoke('clipboard-write', text),
  clipboardRead: () => ipcRenderer.invoke('clipboard-read'),

  // App paths
  getPath: (name) => ipcRenderer.invoke('get-path', name),

  // Event listeners
  onNavigate: (callback) => {
    ipcRenderer.on('navigate', (event, section) => callback(section));
  },

  onServerStatus: (callback) => {
    ipcRenderer.on('server-status', (event, status) => callback(status));
  },

  // Platform info (synchronous)
  platform: process.platform
});

// Log that preload is loaded
console.log('AgentOS preload script loaded');

// Expose additional APIs
contextBridge.exposeInMainWorld('systemAPI', {
  // Shell operations
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  showInFolder: (path) => ipcRenderer.invoke('show-in-folder', path),
  openPath: (path) => ipcRenderer.invoke('open-path', path),

  // Platform info
  getPlatform: () => ipcRenderer.invoke('get-platform'),

  // Window controls
  minimize: () => ipcRenderer.invoke('window-minimize'),
  maximize: () => ipcRenderer.invoke('window-maximize'),
  close: () => ipcRenderer.invoke('window-close'),
  isMaximized: () => ipcRenderer.invoke('window-is-maximized'),

  // Clipboard
  writeClipboard: (text) => ipcRenderer.invoke('clipboard-write', text),
  readClipboard: () => ipcRenderer.invoke('clipboard-read'),

  // App paths
  getPath: (name) => ipcRenderer.invoke('get-path', name),

  // Listen for window state changes
  onMaximizeChange: (callback) => {
    ipcRenderer.on('window-maximized-changed', (event, isMaximized) => callback(isMaximized));
  }
});
