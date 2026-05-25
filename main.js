/**
 * AgentOS - Electron Main Process
 * System tray, window management, and native OS integration
 */

const { app, BrowserWindow, Tray, Menu, ipcMain, dialog, shell, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

// App configuration
const APP_NAME = 'AgentOS';
const APP_VERSION = '1.0.0';
const SERVER_PORT = 3000;

// Global references
let mainWindow = null;
let tray = null;
let serverProcess = null;
let isQuitting = false;

// Determine if running in development
const isDev = !app.isPackaged;

// Get resource paths
function getAssetPath(...paths) {
  if (isDev) {
    return path.join(__dirname, ...paths);
  }
  return path.join(process.resourcesPath, ...paths);
}

// Create the main window
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1200,
    minHeight: 700,
    title: APP_NAME,
    backgroundColor: '#0a0a0f',
    show: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // Load the app
  const startUrl = isDev
    ? `http://localhost:${SERVER_PORT}`
    : `file://${path.join(__dirname, 'index.html')}`;

  mainWindow.loadURL(startUrl);

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    console.log('AgentOS window ready');
  });

  // Handle close to tray
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow.hide();
      return false;
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
}

// Create system tray
function createTray() {
  // Create a simple tray icon (16x16 for tray)
  const iconPath = isDev
    ? path.join(__dirname, 'assets', 'tray-icon.png')
    : path.join(process.resourcesPath, 'assets', 'tray-icon.png');

  // Create a default icon if file doesn't exist
  let trayIcon;
  if (fs.existsSync(iconPath)) {
    trayIcon = nativeImage.createFromPath(iconPath);
  } else {
    // Create a simple colored icon
    trayIcon = nativeImage.createEmpty();
  }

  tray = new Tray(trayIcon.isEmpty() ? createDefaultIcon() : trayIcon);

  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open AgentOS Dashboard',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: 'Server Status',
      enabled: false,
      id: 'server-status'
    },
    { type: 'separator' },
    {
      label: 'Start Server',
      click: () => startServer()
    },
    {
      label: 'Stop Server',
      click: () => stopServer()
    },
    { type: 'separator' },
    {
      label: 'Open Logs',
      click: () => {
        const logPath = path.join(app.getPath('userData'), 'logs');
        shell.openPath(logPath);
      }
    },
    {
      label: 'Settings',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.webContents.send('navigate', 'settings');
        }
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]);

  tray.setToolTip(`${APP_NAME} v${APP_VERSION}`);
  tray.setContextMenu(contextMenu);

  // Double-click to show window
  tray.on('double-click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });
}

// Create default tray icon
function createDefaultIcon() {
  // Create a 16x16 icon programmatically
  const size = 16;
  const canvas = Buffer.alloc(size * size * 4);

  // Fill with cyan color (#00d4ff)
  for (let i = 0; i < size * size; i++) {
    canvas[i * 4] = 0x00;     // R
    canvas[i * 4 + 1] = 0xd4; // G
    canvas[i * 4 + 2] = 0xff; // B
    canvas[i * 4 + 3] = 0xff; // A
  }

  return nativeImage.createFromBuffer(canvas, { width: size, height: size });
}

// Start the backend server
function startServer() {
  if (serverProcess) {
    console.log('Server already running');
    return;
  }

  console.log('Starting AgentOS server...');

  const serverPath = path.join(__dirname, 'server.js');
  serverProcess = spawn('node', [serverPath], {
    env: { ...process.env, PORT: SERVER_PORT },
    stdio: 'pipe'
  });

  serverProcess.stdout.on('data', (data) => {
    console.log(`Server: ${data}`);
    updateTrayMenu();
  });

  serverProcess.stderr.on('data', (data) => {
    console.error(`Server Error: ${data}`);
  });

  serverProcess.on('close', (code) => {
    console.log(`Server closed with code ${code}`);
    serverProcess = null;
    updateTrayMenu();
  });

  updateTrayMenu();
}

// Stop the backend server
function stopServer() {
  if (serverProcess) {
    console.log('Stopping AgentOS server...');
    serverProcess.kill();
    serverProcess = null;
    updateTrayMenu();
  }
}

// Update tray menu with current status
function updateTrayMenu() {
  if (!tray) return;

  const status = serverProcess ? 'Running' : 'Stopped';
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open AgentOS Dashboard',
      click: () => {
        if (mainWindow) {
          mainWindow.show();
          mainWindow.focus();
        }
      }
    },
    {
      label: `Server: ${status}`,
      enabled: false
    },
    { type: 'separator' },
    {
      label: 'Start Server',
      enabled: !serverProcess,
      click: () => startServer()
    },
    {
      label: 'Stop Server',
      enabled: !!serverProcess,
      click: () => stopServer()
    },
    { type: 'separator' },
    {
      label: 'Open Logs Folder',
      click: () => {
        const logPath = path.join(app.getPath('userData'), 'logs');
        if (!fs.existsSync(logPath)) {
          fs.mkdirSync(logPath, { recursive: true });
        }
        shell.openPath(logPath);
      }
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true;
        stopServer();
        app.quit();
      }
    }
  ]);

  tray.setContextMenu(contextMenu);
}

// Setup IPC handlers
function setupIPC() {
  // Get app info
  ipcMain.handle('get-app-info', () => {
    return {
      name: APP_NAME,
      version: APP_VERSION,
      platform: process.platform,
      serverRunning: !!serverProcess
    };
  });

  // Get logs path
  ipcMain.handle('get-logs-path', () => {
    return path.join(app.getPath('userData'), 'logs');
  });

  // Open folder dialog
  ipcMain.handle('open-folder-dialog', async () => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openDirectory']
    });
    return result.filePaths[0] || null;
  });

  // Open file dialog
  ipcMain.handle('open-file-dialog', async (event, options) => {
    const result = await dialog.showOpenDialog(mainWindow, {
      properties: ['openFile'],
      filters: options?.filters || []
    });
    return result.filePaths[0] || null;
  });

  // Save dialog
  ipcMain.handle('show-save-dialog', async (event, options) => {
    const result = await dialog.showSaveDialog(mainWindow, {
      defaultPath: options?.defaultPath,
      filters: options?.filters || []
    });
    return result.filePath || null;
  });

  // Show notification
  ipcMain.handle('show-notification', (event, { title, body }) => {
    const { Notification } = require('electron');
    if (Notification.isSupported()) {
      new Notification({ title, body }).show();
    }
  });

  // Server control
  ipcMain.handle('control-server', (event, action) => {
    if (action === 'start') {
      startServer();
    } else if (action === 'stop') {
      stopServer();
    }
    return { running: !!serverProcess };
  });

  // Shell operations
  ipcMain.handle('open-external', (event, url) => {
    // Only allow http/https URLs
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
      return { success: true };
    }
    return { success: false, error: 'Only http/https URLs allowed' };
  });

  // Show item in folder
  ipcMain.handle('show-in-folder', (event, filePath) => {
    shell.showItemInFolder(filePath);
    return { success: true };
  });

  // Open path in default app
  ipcMain.handle('open-path', (event, filePath) => {
    shell.openPath(filePath);
    return { success: true };
  });

  // Get platform info
  ipcMain.handle('get-platform', () => {
    return {
      platform: process.platform,
      arch: process.arch,
      version: process.getSystemVersion(),
      electron: process.versions.electron,
      node: process.versions.node
    };
  });

  // Window controls
  ipcMain.handle('window-minimize', () => {
    if (mainWindow) mainWindow.minimize();
    return { success: true };
  });

  ipcMain.handle('window-maximize', () => {
    if (mainWindow) {
      if (mainWindow.isMaximized()) {
        mainWindow.unmaximize();
      } else {
        mainWindow.maximize();
      }
    }
    return { success: true, isMaximized: mainWindow?.isMaximized() };
  });

  ipcMain.handle('window-close', () => {
    if (mainWindow) mainWindow.hide();
    return { success: true };
  });

  ipcMain.handle('window-is-maximized', () => {
    return { isMaximized: mainWindow?.isMaximized() || false };
  });

  // Clipboard operations
  ipcMain.handle('clipboard-write', (event, text) => {
    const { clipboard } = require('electron');
    clipboard.writeText(text);
    return { success: true };
  });

  ipcMain.handle('clipboard-read', () => {
    const { clipboard } = require('electron');
    return { text: clipboard.readText() };
  });

  // App paths
  ipcMain.handle('get-path', (event, name) => {
    // Valid path names: home, appData, userData, temp, desktop, documents, downloads, music, pictures, videos
    const validPaths = ['home', 'appData', 'userData', 'temp', 'desktop', 'documents', 'downloads', 'music', 'pictures', 'videos'];
    if (validPaths.includes(name)) {
      return { path: app.getPath(name) };
    }
    return { error: 'Invalid path name' };
  });
}

// App ready
app.whenReady().then(() => {
  console.log('AgentOS starting...');

  // Create logs directory
  const logsPath = path.join(app.getPath('userData'), 'logs');
  if (!fs.existsSync(logsPath)) {
    fs.mkdirSync(logsPath, { recursive: true });
  }

  // Setup IPC
  setupIPC();

  // Create window and tray
  createWindow();
  createTray();

  // Auto-start server in background
  setTimeout(() => startServer(), 1000);

  console.log('AgentOS ready');
});

// Handle all windows closed
app.on('window-all-closed', () => {
  // On macOS, keep app running in background
  if (process.platform !== 'darwin') {
    // On Windows, minimize to tray instead of quitting
  }
});

// Handle activate (macOS)
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  } else if (mainWindow) {
    mainWindow.show();
  }
});

// Handle before quit
app.on('before-quit', () => {
  isQuitting = true;
  stopServer();
});

// Handle quit
app.on('quit', () => {
  console.log('AgentOS shutting down');
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  const logPath = path.join(app.getPath('userData'), 'logs', 'error.log');
  fs.appendFileSync(logPath, `${new Date().toISOString()} - Uncaught Exception: ${error.stack}\n`);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection:', reason);
  const logPath = path.join(app.getPath('userData'), 'logs', 'error.log');
  fs.appendFileSync(logPath, `${new Date().toISOString()} - Unhandled Rejection: ${reason}\n`);
});
