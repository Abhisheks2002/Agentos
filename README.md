# AgentOS - AI Agent Governance Platform

A cross-platform desktop application that provides a governance layer between AI Agents and the Host OS (Windows/macOS) for enterprise deployment of AI agents.

## Features

- **Enterprise Governance**: Role-based access control, audit logging, permission management
- **AI Agent Management**: Register, configure, and monitor AI agents
- **Workflow Automation**: Visual workflow builder with drag-and-drop nodes
- **OS Bridge**: Secure file operations, command execution, and network requests
- **System Tray**: Runs in background with system tray icon
- **Cross-Platform**: Works on Windows and macOS

## Installation

### Prerequisites

- Node.js 18+
- Python 3.8+ (for backend modules)
- npm

### Setup

```bash
# Install dependencies
npm install

# Start the server (API backend)
npm run server

# Or run as desktop app (requires Electron)
npm start
```

## Quick Start

### Option 1: Run Server Only

```bash
node server.js
```

Then open http://localhost:3000 in your browser.

### Option 2: Run Desktop App

```bash
npm install electron --save-dev
npm start
```

## Architecture

```
┌─────────────────────────────────────────┐
│           AgentOS Dashboard             │
│  (HTML/JS - Browser or Electron)       │
└─────────────────┬───────────────────────┘
                  │ HTTP API
┌─────────────────▼───────────────────────┐
│           AgentOS API Server             │
│  (Node.js - REST API)                   │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐   ┌────▼────┐   ┌───▼────┐
│  OS   │   │Governance│   │Database│
│Bridge │   │  Layer   │   │(SQLite)│
└───┬───┘   └─────────┘   └────────┘
    │
┌───▼───────────────────────────┐
│      Host OS                  │
│   Windows / macOS             │
└───────────────────────────────┘
```

## API Endpoints

### Organizations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/org/register | Register organization |
| GET | /api/org/:id/stats | Get organization stats |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/agents | List agents |
| POST | /api/agents | Create agent |
| POST | /api/agents/:id | Execute agent action |

### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/workflows | List workflows |
| POST | /api/workflows | Create workflow |
| POST | /api/workflows/:id | Execute workflow |

### File Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/files/read | Read file |
| POST | /api/files/write | Write file |
| GET | /api/files/list | List directory |
| POST | /api/files/delete | Delete file |

### Other

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| GET | /api/system | System info |
| GET | /api/audit | Audit logs |
| GET | /api/permissions | Permission list |

## Organization Tiers

| Feature | Startup | Business | Enterprise |
|---------|---------|----------|-----------|
| Max Agents | 5 | 25 | Unlimited |
| Max Workflows | 10 | 100 | Unlimited |
| Rate Limit | 100/min | 1000/min | Unlimited |
| Storage | 1GB | 50GB | Unlimited |

## Governance Rules

### Auto-Blocked Actions
- System file deletion
- Registry modification
- Software installation

### Approval Required
- Elevated command execution
- System directory writes
- User account modifications

## Development

### Project Structure

```
AgentOS/
├── core/               # Python core modules
│   ├── governance.py   # Governance engine
│   ├── os_bridge.py   # OS bridge layer
│   └── database.py    # Database layer
├── assets/            # App assets
├── js/               # JavaScript files
├── css/              # Stylesheets
├── index.html        # Main dashboard
├── server.js         # API server
├── main.js          # Electron main process
├── preload.js       # Electron preload
├── package.json     # npm dependencies
├── SPEC.md          # Specification
└── README.md        # This file
```

## License

MIT
