# AgentOS - AI Agent Governance Platform Specification

## 1. Project Overview

**Project Name:** AgentOS
**Project Type:** Cross-platform Desktop Application / System Service
**Core Feature Summary:** A governance layer between AI Agents and the Host OS (Windows/macOS) that provides enterprise-grade security, audit logging, workflow automation, and system resource management for deploying AI agents in business environments.
**Target Users:** Enterprise, Business, and Startup organizations that need to deploy and manage AI agents for workflow automation with security and compliance.

---

## 2. UI/UX Specification

### 2.1 Layout Structure

**Multi-Window Model:**
- **Main Window:** Dashboard with tabs for Overview, Agents, Workflows, Permissions, Governance, Audit Log
- **System Tray:** Background service indicator with context menu (Start/Stop, Open Dashboard, Settings, Exit)
- **Settings Dialog:** Modal window for configuration
- **Notification Popups:** Toast notifications for security alerts and approvals

**OS-Native Style:**
- Windows: Uses native title bar, follows Windows 11 design language
- macOS: Uses system title bar with traffic light buttons

**Major Layout Areas:**
- **Header:** Logo, organization badge, system status indicators, user profile, logout
- **Navigation:** Tab-based navigation (Overview, Agents, Workflows, Permissions, Governance, Audit)
- **Content:** Dynamic content area based on selected tab
- **Status Bar:** Connection status, service status, version info

### 2.2 Visual Design

**Color Palette:**
- Primary: `#00d4ff` (Cyan - action elements)
- Secondary: `#7b2ff7` (Purple - accents)
- Background Dark: `#0a0a0f` (Main background)
- Surface: `#12121a` (Cards, panels)
- Border: `#2a2a3a` (Dividers, borders)
- Text Primary: `#ffffff`
- Text Secondary: `#888888`
- Success: `#2ed573`
- Warning: `#ffa502`
- Error: `#ff4757`

**Typography:**
- Font Family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif
- Headings: 24px (h1), 20px (h2), 16px (h3)
- Body: 14px
- Small: 12px

**Spacing System:**
- Base unit: 4px
- Component padding: 12px-16px
- Section margins: 20px-30px
- Card padding: 20px-24px

**Visual Effects:**
- Card shadows: `0 4px 12px rgba(0, 0, 0, 0.3)`
- Hover transitions: 200ms ease
- Gradient accents on buttons and badges
- Border radius: 8px (buttons), 12px (cards), 16px (modals)

### 2.3 Components

**Dashboard Components:**
- Stats Cards (4-column grid, shows Active Agents, Workflows, API Calls, Blocked Actions)
- Agent Cards (grid layout, shows name, type, status, task count, actions)
- Permission Matrix (toggle switches for each permission)
- Governance Controls (rate limit bars, auto-block rules, approval workflow)
- Audit Log Table (filterable, sortable entries)

**Component States:**
- Default, Hover (lighter background), Active (primary color border), Disabled (50% opacity)
- Status badges: Active (green), Paused (orange), Error (red)

---

## 3. Functional Specification

### 3.1 Core Features

**Organization Management:**
- Create organizations with tier selection (Startup, Business, Enterprise)
- Tier-based limits: Agent count, workflow count, storage, rate limits
- Organization-specific governance rules

**AI Agent Management:**
- Register and configure AI agents
- Assign permissions per agent (file read/write, command execution, network, registry)
- Start, pause, stop, delete agents
- Monitor agent activity and errors
- Agent types: Data Processing, File Management, Communication, Automation, Analysis

**Workflow Automation:**
- Visual workflow builder with drag-and-drop nodes
- Node types: Trigger, Condition, Action, Approval, Notify, Loop, Log
- Execute workflows manually or on schedule
- Track workflow execution status and results

**Governance & Security:**
- Permission-based access control (RBAC)
- Auto-block dangerous operations (system file deletion, registry modification, software installation)
- Require approval for elevated commands
- Rate limiting per organization tier
- Real-time security monitoring

**Audit & Compliance:**
- Comprehensive audit logging of all agent actions
- Filter logs by status (allowed, blocked, warning), agent, time range
- Export audit logs (JSON format)
- Compliance reporting

### 3.2 OS Integration (OS Bridge Layer)

**File System Operations:**
- Read files from allowed directories
- Write/create/modify files
- Delete files (with safety checks)
- List directories
- File metadata operations

**Process Management:**
- Execute shell commands (with governance approval)
- Get process information
- Terminate processes (with restrictions)

**Network Operations:**
- HTTP/HTTPS requests (governance-controlled)
- DNS resolution
- Port scanning prevention

**System Operations (Windows):**
- Registry read/write (blocked by default)
- Service management
- Windows Management Instrumentation (WMI)

**System Operations (macOS):**
- System Preferences access
- LaunchAgent management
- Keychain access (read only)

### 3.3 Data Flow & Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AgentOS Client                        │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │  Dashboard  │  │ System Tray │  │ Settings UI     │   │
│  │   (HTML/JS) │  │   (Electron) │  │   (Electron)   │   │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘   │
│         │                │                   │            |
│         └────────────────┼───────────────────┘            │
│                          │                                │
│                   ┌──────▼──────┐                        │
│                   │  API Server │                        │
│                   │  (Node.js)  │                        │
│                   └──────┬──────┘                        │
└──────────────────────────┼───────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌────▼────┐ ┌────▼─────┐
        │ Governance│ │   OS    │ │ Database │
        │   Layer   │ │  Bridge │ │ (SQLite) │
        └─────┬─────┘ └────┬────┘ └──────────┘
              │            │
              │     ┌──────▼──────┐
              │     │ Host OS      │
              │     │ Win/macOS    │
              │     └──────────────┘
              │
        ┌─────▼─────┐
        │   AI      │
        │  Agents   │
        └───────────┘
```

**Key Modules:**

1. **Governance Layer** (`governance.py`)
   - `check_permission(agent_id, permission)` - Validate agent permissions
   - `apply_governance_rules(action, params)` - Apply auto-block and approval rules
   - `get_rate_limit_status(org_id)` - Check rate limits

2. **OS Bridge** (`os_bridge.py`)
   - `read_file(path)` - Safe file read with path validation
   - `write_file(path, content)` - Safe file write
   - `execute_command(cmd, shell)` - Governed command execution
   - `make_request(url, method, headers)` - Network request handler
   - `get_system_info()` - OS information

3. **Database** (`database.py`)
   - `init_db()` - Initialize SQLite database
   - `save_organization(org)` - Persist organization
   - `save_agent(agent)` - Persist agent
   - `log_audit(entry)` - Save audit log

4. **System Service** (`service.py`)
   - `start_service()` - Start as Windows Service/macOS LaunchAgent
   - `stop_service()` - Stop the service
   - `get_service_status()` - Get running status

### 3.4 Edge Cases

- **Permission Denied:** Agent attempts action without permission → Block with audit log
- **Rate Limit Exceeded:** Agent exceeds API calls → Queue requests, return 429
- **File Not Found:** Agent requests missing file → Return 404 with audit
- **Dangerous Path:** Agent attempts system directory access → Auto-block
- **Network Timeout:** External API call fails → Retry with backoff, log warning
- **Database Error:** SQLite fails → Fallback to in-memory, alert user
- **Service Crash:** Service stops unexpectedly → Auto-restart, log error

---

## 4. Acceptance Criteria

### 4.1 Success Conditions

1. **System Service:**
   - [ ] AgentOS runs as a background service on Windows (Service) and macOS (LaunchAgent)
   - [ ] Service starts automatically on system boot
   - [ ] System tray icon shows service status (running/stopped)
   - [ ] Service can be started/stopped from tray menu

2. **Dashboard:**
   - [ ] Login screen with organization tier selection
   - [ ] Dashboard displays all 6 sections (Overview, Agents, Workflows, Permissions, Governance, Audit)
   - [ ] Real-time stats update
   - [ ] Agent CRUD operations work
   - [ ] Workflow builder functional

3. **Governance:**
   - [ ] Permission checks work before any action
   - [ ] Dangerous actions auto-blocked
   - [ ] Rate limiting enforced
   - [ ] All actions logged to audit

4. **OS Bridge:**
   - [ ] File read/write operations work with path validation
   - [ ] Command execution with safety checks
   - [ ] Network requests go through governance
   - [ ] Cross-platform path handling (Windows/macOS)

5. **Persistence:**
   - [ ] Organizations saved to SQLite database
   - [ ] Agents persist across restarts
   - [ ] Audit logs persist
   - [ ] Settings saved

### 4.2 Visual Checkpoints

1. Login screen shows gradient logo and tier selector
2. Dashboard header shows organization badge and system status
3. Stats cards display with colored values
4. Agent cards show status badges (green/orange/red)
5. Permission toggles animate smoothly
6. Audit log entries have colored left borders (green/orange/red)
7. System tray icon visible with context menu
