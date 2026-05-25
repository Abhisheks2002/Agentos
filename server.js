/**
 * AgentOS - API Server
 * REST API for AgentOS governance and operations
 */

const http = require('http');
const { URL } = require('url');
const fs = require('fs');
const path = require('path');
const { spawn, execSync } = require('child_process');

// Import Day 51-60 Advanced Features
const { ChainOfThoughtReasoning } = require('./core/reasoning/chain_of_thought');
const { ToolRegistry } = require('./core/tools/tool_registry');
const { MultiAgentCoordinator } = require('./core/multi_agent_coordinator');
const { TaskScheduler } = require('./core/task_scheduler');
const { WebhookSystem } = require('./core/webhook_system');
const { MetricsSystem } = require('./core/metrics');

const PORT = process.env.PORT || 3000;

// Initialize Advanced Systems
const reasoningEngine = new ChainOfThoughtReasoning();
const toolRegistry = new ToolRegistry();
const agentCoordinator = new MultiAgentCoordinator();
const taskScheduler = new TaskScheduler();
const webhookSystem = new WebhookSystem();
const metricsSystem = new MetricsSystem();

// Update metrics periodically
setInterval(() => {
  metricsSystem.updateSystemMetrics();
}, 30000);

// Platform detection
const isWindows = process.platform === 'win32';
const isMac = process.platform === 'darwin';

function getDefaultWorkspace() {
  if (isWindows) {
    return path.join(process.env.USERPROFILE || 'C:\\', 'AgentOS_Workspace');
  }
  return path.join(process.env.HOME || '/tmp', 'AgentOS_Workspace');
}

const WORKSPACE_DIR = process.env.WORKSPACE_DIR || getDefaultWorkspace();

// Ensure workspace exists
if (!fs.existsSync(WORKSPACE_DIR)) {
  fs.mkdirSync(WORKSPACE_DIR, { recursive: true });
}

// ============ In-Memory Storage (Replaces Python modules) ============

class MemoryStore {
  constructor() {
    this.vectorStore = new Map();
    this.semanticFacts = new Map();
    this.episodes = new Map();
    this.sessions = new Map();
    this.counter = 0;
  }

  storeKnowledge(fact, concepts = [], metadata = {}) {
    const id = `fact_${++this.counter}`;
    this.semanticFacts.set(id, { id, fact, concepts, metadata, createdAt: new Date().toISOString() });
    return id;
  }

  recallKnowledge(query, topK = 5) {
    // Simple text search
    const results = [];
    const queryLower = query.toLowerCase();
    for (const [id, data] of this.semanticFacts) {
      const score = data.fact.toLowerCase().includes(queryLower) ? 0.8 : 0.2;
      if (score > 0.3) {
        results.push({ id, fact: data.fact, concepts: data.concepts, score });
      }
    }
    return results.slice(0, topK);
  }

  startSession(agentId, context = {}) {
    const sessionId = `session_${Date.now()}`;
    this.sessions.set(sessionId, { id: sessionId, agentId, context, episodes: [], createdAt: new Date().toISOString() });
    return sessionId;
  }

  addInteraction(sessionId, type, content, metadata = {}) {
    const episodeId = `ep_${Date.now()}_${++this.counter}`;
    this.episodes.set(episodeId, { id: episodeId, type, content, metadata, timestamp: new Date().toISOString() });
    const session = this.sessions.get(sessionId);
    if (session) session.episodes.push(episodeId);
    return episodeId;
  }

  getHistory(agentId, limit = 50) {
    const session = [...this.sessions.values()].find(s => s.agentId === agentId);
    if (!session) return [];
    return session.episodes.slice(-limit).map(id => this.episodes.get(id)).filter(Boolean);
  }

  getStats() {
    return {
      semantic: { totalFacts: this.semanticFacts.size },
      episodic: { totalEpisodes: this.episodes.size, activeSessions: this.sessions.size }
    };
  }
}

const memoryStore = new MemoryStore();

// Agent Runtime (in-memory)
const agents = new Map();
const tasks = [];
const toolRegistry = [
  { name: 'file_read', description: 'Read file contents', params: [{ name: 'path', type: 'string' }] },
  { name: 'file_write', description: 'Write file contents', params: [{ name: 'path', type: 'string' }, { name: 'content', type: 'string' }] },
  { name: 'list_directory', description: 'List directory', params: [{ name: 'path', type: 'string' }] },
  { name: 'execute_command', description: 'Execute shell command', params: [{ name: 'command', type: 'string' }] },
  { name: 'web_request', description: 'Make HTTP request', params: [{ name: 'url', type: 'string' }] },
  { name: 'search_memory', description: 'Search memory', params: [{ name: 'query', type: 'string' }] },
  { name: 'store_knowledge', description: 'Store knowledge', params: [{ name: 'fact', type: 'string' }] }
];

function createAgent(name, type, config = {}, permissions = []) {
  const id = `agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  agents.set(id, { id, name, type, config, permissions, status: 'idle', createdAt: new Date().toISOString(), tasksCompleted: 0 });
  return id;
}

function submitTask(agentId, taskType, payload = {}, priority = 2) {
  const id = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  tasks.push({ id, agentId, type: taskType, payload, priority, status: 'pending', createdAt: new Date().toISOString() });
  return id;
}

// ============ AgentOS Core ============

class AgentOS {
  constructor() {
    this.organizations = new Map();
    this.auditLog = [];
    this.permissions = new Map();
    this.tiers = {
      startup: { maxAgents: 5, maxWorkflows: 10, rateLimit: 100, storage: '1GB' },
      business: { maxAgents: 25, maxWorkflows: 100, rateLimit: 1000, storage: '50GB' },
      enterprise: { maxAgents: -1, maxWorkflows: -1, rateLimit: -1, storage: 'Unlimited' }
    };
    this.initPermissions();
    this.loadOrganizations();
  }

  initPermissions() {
    const defaultPerms = [
      { name: 'file_read', description: 'Read files from allowed directories', enabled: true },
      { name: 'file_write', description: 'Create or modify files', enabled: true },
      { name: 'file_delete', description: 'Delete files', enabled: false },
      { name: 'execute_commands', description: 'Run shell commands', enabled: false },
      { name: 'network_access', description: 'Make external requests', enabled: true },
      { name: 'registry_access', description: 'Modify system registry', enabled: false },
      { name: 'install_software', description: 'Install applications', enabled: false }
    ];
    defaultPerms.forEach(p => this.permissions.set(p.name, p));
  }

  loadOrganizations() {
    this.registerOrg('demo_org', 'enterprise');
    this.createAgent('demo_org', {
      name: 'DataProcessor',
      type: 'Data Processing',
      description: 'Processes business data',
      permissions: ['file_read', 'file_write', 'network_access']
    });
    this.createAgent('demo_org', {
      name: 'FileSync',
      type: 'File Management',
      description: 'Syncs files to cloud',
      permissions: ['file_read', 'file_write']
    });
    this.createAgent('demo_org', {
      name: 'EmailAssistant',
      type: 'Communication',
      description: 'Manages email',
      permissions: ['network_access']
    });

    this.createWorkflow('demo_org', {
      name: 'Daily Report',
      description: 'Generate daily reports',
      nodes: [
        { id: 1, type: 'trigger', config: { type: 'schedule', cron: '0 9 * * *' } },
        { id: 2, type: 'action', config: { type: 'query_data' } },
        { id: 3, type: 'action', config: { type: 'generate_report' } },
        { id: 4, type: 'notify', config: { type: 'email' } }
      ]
    });

    this.createWorkflow('demo_org', {
      name: 'File Backup',
      description: 'Backup important files',
      nodes: [
        { id: 1, type: 'trigger', config: { type: 'schedule', cron: '0 2 * * *' } },
        { id: 2, type: 'action', config: { type: 'list_files' } },
        { id: 3, type: 'condition', config: { check: 'files_exist' } },
        { id: 4, type: 'action', config: { type: 'compress' } },
        { id: 5, type: 'action', config: { type: 'upload' } }
      ]
    });
  }

  registerOrg(orgId, tier) {
    const config = this.tiers[tier] || this.tiers.startup;
    this.organizations.set(orgId, {
      tier,
      ...config,
      agents: [],
      workflows: [],
      rateLimitUsed: 0,
      createdAt: new Date().toISOString()
    });
    return this.organizations.get(orgId);
  }

  createAgent(orgId, agentConfig) {
    const org = this.organizations.get(orgId);
    if (!org) return { error: 'Organization not found' };

    if (org.tier !== 'enterprise' && org.agents.length >= org.maxAgents) {
      return { error: `Agent limit reached for ${org.tier} tier` };
    }

    const agent = {
      id: `agent_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      orgId,
      name: agentConfig.name,
      type: agentConfig.type,
      description: agentConfig.description || '',
      status: 'idle',
      permissions: agentConfig.permissions || ['file_read', 'network_access'],
      tasksCompleted: 0,
      errors: 0,
      createdAt: new Date().toISOString(),
      lastActivity: null
    };

    org.agents.push(agent);
    this.logAudit(orgId, agent.id, 'agent_created', `Agent ${agent.name} created`, 'allowed');
    return agent;
  }

  getAgent(agentId) {
    for (const org of this.organizations.values()) {
      const agent = org.agents.find(a => a.id === agentId);
      if (agent) return { agent, org };
    }
    return null;
  }

  isPathSafe(filePath) {
    const absPath = path.resolve(filePath);
    const dangerous = [
      'C:\\Windows\\System32', 'C:\\Windows\\SysWOW64', '/System', '/bin',
      '/usr/bin', '/usr/sbin', '/private/etc', '.ssh', '.aws'
    ];
    for (const d of dangerous) {
      if (absPath.toLowerCase().includes(d.toLowerCase())) {
        return { safe: false, reason: `Protected path: ${d}` };
      }
    }
    const workspaceAbs = path.resolve(WORKSPACE_DIR);
    if (!absPath.startsWith(workspaceAbs)) {
      return { safe: false, reason: 'Outside workspace' };
    }
    return { safe: true };
  }

  isCommandSafe(command) {
    const blocked = ['rm -rf /', 'del /f /s /q', 'format', 'diskpart', 'dd if='];
    const cmdLower = command.toLowerCase();
    for (const b of blocked) {
      if (cmdLower.includes(b.toLowerCase())) {
        return { safe: false, reason: `Blocked command: ${b}` };
      }
    }
    return { safe: true };
  }

  readFile(filePath) {
    const check = this.isPathSafe(filePath);
    if (!check.safe) return { success: false, error: check.reason };

    try {
      if (!fs.existsSync(filePath)) {
        return { success: false, error: 'File not found' };
      }
      const stat = fs.statSync(filePath);
      if (stat.size > 10 * 1024 * 1024) {
        return { success: false, error: 'File too large (max 10MB)' };
      }
      const content = fs.readFileSync(filePath, 'utf-8');
      return { success: true, content, size: stat.size, path: filePath };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  writeFile(filePath, content) {
    const check = this.isPathSafe(filePath);
    if (!check.safe) return { success: false, error: check.reason };

    try {
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
      fs.writeFileSync(filePath, content, 'utf-8');
      const stat = fs.statSync(filePath);
      return { success: true, path: filePath, size: stat.size };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  listDirectory(dirPath) {
    const target = dirPath || WORKSPACE_DIR;
    const check = this.isPathSafe(target);
    if (!check.safe) return { success: false, error: check.reason };

    try {
      if (!fs.existsSync(target)) {
        return { success: false, error: 'Directory not found' };
      }
      const entries = fs.readdirSync(target, { withFileTypes: true });
      return {
        success: true,
        path: target,
        entries: entries.map(e => ({
          name: e.name,
          type: e.isDirectory() ? 'directory' : 'file',
          size: e.isFile() ? fs.statSync(path.join(target, e.name)).size : 0
        }))
      };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  deleteFile(filePath) {
    const check = this.isPathSafe(filePath);
    if (!check.safe) return { success: false, error: check.reason };

    try {
      if (!fs.existsSync(filePath)) {
        return { success: false, error: 'File not found' };
      }
      const stat = fs.statSync(filePath);
      if (stat.isDirectory()) {
        fs.rmSync(filePath, { recursive: true });
      } else {
        fs.unlinkSync(filePath);
      }
      return { success: true, path: filePath };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  executeCommand(command) {
    const check = this.isCommandSafe(command);
    if (!check.safe) return { success: false, error: check.reason };

    try {
      const result = execSync(command, {
        cwd: WORKSPACE_DIR,
        timeout: 30000,
        encoding: 'utf-8',
        shell: isWindows
      });
      return { success: true, output: result };
    } catch (e) {
      return { success: false, error: e.message, stderr: e.stderr };
    }
  }

  makeRequest(url, method = 'GET', data = null) {
    try {
      const parsed = new URL(url);
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return { success: false, error: 'Only HTTP/HTTPS allowed' };
      }
      const hostname = parsed.hostname;
      if (hostname.startsWith('10.') || hostname.startsWith('192.168.') ||
          hostname.startsWith('172.') || hostname === 'localhost') {
        return { success: false, error: 'Private network access blocked' };
      }
      return { success: true, message: 'Request would be made', url };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }

  getSystemInfo() {
    return {
      platform: process.platform,
      arch: process.arch,
      nodeVersion: process.version,
      workspace: WORKSPACE_DIR,
      cpuCount: require('os').cpus().length,
      totalMemory: require('os').totalmem(),
      freeMemory: require('os').freemem(),
      uptime: process.uptime()
    };
  }

  async executeAction(agentId, action, params = {}) {
    const agentData = this.getAgent(agentId);
    if (!agentData) return { error: 'Agent not found' };

    const { agent, org } = agentData;

    org.rateLimitUsed++;
    if (org.rateLimit > 0 && org.rateLimitUsed > org.rateLimit) {
      this.logAudit(org.id, agentId, action, 'Rate limit exceeded', 'blocked');
      return { error: 'Rate limit exceeded', blocked: true };
    }

    if (!this.checkPermission(agent, action)) {
      this.logAudit(org.id, agentId, action, `${action} not permitted`, 'blocked');
      return { error: 'Permission denied', blocked: true };
    }

    const dangerousActions = ['delete_system', 'modify_registry', 'install_software', 'delete_system_files'];
    if (dangerousActions.includes(action)) {
      this.logAudit(org.id, agentId, action, 'Dangerous action auto-blocked', 'blocked');
      return { error: 'Action auto-blocked by governance', blocked: true };
    }

    let result;
    try {
      switch (action) {
        case 'read_file':
          result = this.readFile(params.path);
          break;
        case 'write_file':
          result = this.writeFile(params.path, params.content || '');
          break;
        case 'list_directory':
          result = this.listDirectory(params.path);
          break;
        case 'delete_file':
          result = this.deleteFile(params.path);
          break;
        case 'execute':
          result = this.executeCommand(params.command);
          break;
        case 'network':
          result = this.makeRequest(params.url, params.method, params.data);
          break;
        default:
          result = { success: true, message: 'Action acknowledged' };
      }

      agent.lastActivity = new Date().toISOString();
      if (result.success) {
        agent.tasksCompleted++;
        this.logAudit(org.id, agentId, action, JSON.stringify(params), 'allowed');
      } else {
        agent.errors++;
        this.logAudit(org.id, agentId, action, JSON.stringify(params), 'warning');
      }

      return result;
    } catch (error) {
      agent.errors++;
      this.logAudit(org.id, agentId, action, error.message, 'warning');
      return { error: error.message };
    }
  }

  checkPermission(agent, action) {
    const permMap = {
      'file_read': 'file_read',
      'file_write': 'file_write',
      'file_delete': 'file_delete',
      'execute': 'execute_commands',
      'network': 'network_access',
      'registry': 'registry_access'
    };
    const requiredPerm = permMap[action];
    return requiredPerm ? agent.permissions.includes(requiredPerm) : true;
  }

  createWorkflow(orgId, workflowConfig) {
    const org = this.organizations.get(orgId);
    if (!org) return { error: 'Organization not found' };

    const workflow = {
      id: `wf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      orgId,
      name: workflowConfig.name,
      description: workflowConfig.description || '',
      nodes: workflowConfig.nodes || [],
      status: 'draft',
      trigger: workflowConfig.trigger,
      runs: 0,
      createdAt: new Date().toISOString()
    };

    org.workflows.push(workflow);
    return workflow;
  }

  async executeWorkflow(workflowId, context = {}) {
    for (const org of this.organizations.values()) {
      const workflow = org.workflows.find(w => w.id === workflowId);
      if (workflow) {
        workflow.status = 'running';
        const results = [];

        for (const node of workflow.nodes) {
          results.push({ nodeId: node.id, type: node.type, status: 'success' });
        }

        workflow.status = 'completed';
        workflow.runs++;
        workflow.lastRun = new Date().toISOString();

        return { workflowId, results, status: workflow.status };
      }
    }
    return { error: 'Workflow not found' };
  }

  logAudit(orgId, agentId, action, details, status) {
    const entry = {
      id: this.auditLog.length + 1,
      orgId,
      agentId,
      action,
      details,
      status,
      timestamp: new Date().toISOString()
    };
    this.auditLog.push(entry);
    return entry;
  }

  getAuditLogs(orgId, filters = {}) {
    let logs = this.auditLog.filter(l => l.orgId === orgId);
    if (filters.status) logs = logs.filter(l => l.status === filters.status);
    if (filters.agentId) logs = logs.filter(l => l.agentId === filters.agentId);
    return logs.slice(-100);
  }

  getOrgStats(orgId) {
    const org = this.organizations.get(orgId);
    if (!org) return null;

    return {
      tier: org.tier,
      agents: {
        total: org.agents.length,
        active: org.agents.filter(a => a.status === 'active').length,
        idle: org.agents.filter(a => a.status === 'idle').length,
        errors: org.agents.reduce((sum, a) => sum + a.errors, 0)
      },
      workflows: {
        total: org.workflows.length,
        running: org.workflows.filter(w => w.status === 'running').length,
        completed: org.workflows.filter(w => w.status === 'completed').length
      },
      rateLimit: {
        used: org.rateLimitUsed,
        limit: org.rateLimit
      },
      auditLogs: this.getAuditLogs(orgId).length
    };
  }
}

// ============ HTTP Server ============

const agentOS = new AgentOS();

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  const requestPath = url.pathname;
  const method = req.method;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Serve static files
  if (method === 'GET') {
    if (requestPath === '/' || requestPath === '/index.html') {
      const indexPath = path.join(__dirname, 'index.html');
      if (fs.existsSync(indexPath)) {
        const content = fs.readFileSync(indexPath, 'utf-8');
        res.writeHead(200, { 'Content-Type': 'text/html' });
        res.end(content);
        return;
      }
    }

    const staticExt = ['.html', '.js', '.css', '.json'];
    const ext = path.extname(requestPath);
    if (staticExt.includes(ext)) {
      const filePath = path.join(__dirname, requestPath);
      if (fs.existsSync(filePath)) {
        const contentType = ext === '.js' ? 'application/javascript' :
                           ext === '.css' ? 'text/css' :
                           ext === '.json' ? 'application/json' : 'text/html';
        const content = fs.readFileSync(filePath, 'utf-8');
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(content);
        return;
      }
    }
  }

  res.setHeader('Content-Type', 'application/json');

  try {
    // Helper function
    const readBody = () => new Promise((resolve, reject) => {
      let body = '';
      req.on('data', chunk => body += chunk);
      req.on('end', () => {
        try { resolve(body ? JSON.parse(body) : {}); } catch (e) { reject(e); }
      });
      req.on('error', reject);
    });

    // Health check
    if (requestPath === '/api/health' && method === 'GET') {
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'ok',
        version: '1.0.0',
        workspace: WORKSPACE_DIR,
        platform: process.platform
      }));
      return;
    }

    // System info
    if (requestPath === '/api/system' && method === 'GET') {
      res.writeHead(200);
      res.end(JSON.stringify(agentOS.getSystemInfo()));
      return;
    }

    // Organization
    if (requestPath === '/api/org/register' && method === 'POST') {
      const body = await readBody();
      const org = agentOS.registerOrg(body.orgId, body.tier);
      res.writeHead(201);
      res.end(JSON.stringify(org));
      return;
    }

    if (requestPath.startsWith('/api/org/') && method === 'GET') {
      const orgId = requestPath.split('/')[3];
      if (orgId === 'stats') {
        const allStats = {};
        for (const [id] of agentOS.organizations) {
          allStats[id] = agentOS.getOrgStats(id);
        }
        res.writeHead(200);
        res.end(JSON.stringify(allStats));
        return;
      }
      const stats = agentOS.getOrgStats(orgId);
      if (stats) {
        res.writeHead(200);
        res.end(JSON.stringify(stats));
      } else {
        res.writeHead(404);
        res.end(JSON.stringify({ error: 'Not found' }));
      }
      return;
    }

    // Agents
    if (requestPath === '/api/agents' && method === 'GET') {
      const orgId = url.searchParams.get('orgId');
      const org = agentOS.organizations.get(orgId);
      if (org) {
        res.writeHead(200);
        res.end(JSON.stringify(org.agents));
      } else {
        res.writeHead(200);
        res.end(JSON.stringify([]));
      }
      return;
    }

    if (requestPath === '/api/agents' && method === 'POST') {
      const body = await readBody();
      const agent = agentOS.createAgent(body.orgId, body.config);
      res.writeHead(201);
      res.end(JSON.stringify(agent));
      return;
    }

    if (requestPath.startsWith('/api/agents/') && method === 'POST') {
      const parts = requestPath.split('/');
      const agentId = parts[3];
      const body = await readBody();
      const result = await agentOS.executeAction(agentId, body.action, body.params);
      res.writeHead(result.blocked ? 403 : 200);
      res.end(JSON.stringify(result));
      return;
    }

    // Workflows
    if (requestPath === '/api/workflows' && method === 'GET') {
      const orgId = url.searchParams.get('orgId');
      const org = agentOS.organizations.get(orgId);
      if (org) {
        res.writeHead(200);
        res.end(JSON.stringify(org.workflows));
      } else {
        res.writeHead(200);
        res.end(JSON.stringify([]));
      }
      return;
    }

    if (requestPath === '/api/workflows' && method === 'POST') {
      const body = await readBody();
      const workflow = agentOS.createWorkflow(body.orgId, body.config);
      res.writeHead(201);
      res.end(JSON.stringify(workflow));
      return;
    }

    if (requestPath.startsWith('/api/workflows/') && method === 'POST') {
      const parts = requestPath.split('/');
      const workflowId = parts[3];
      const body = await readBody();
      const result = await agentOS.executeWorkflow(workflowId, body.context);
      res.writeHead(200);
      res.end(JSON.stringify(result));
      return;
    }

    // Audit
    if (requestPath === '/api/audit' && method === 'GET') {
      const orgId = url.searchParams.get('orgId');
      const filters = {
        status: url.searchParams.get('status'),
        agentId: url.searchParams.get('agentId')
      };
      const logs = agentOS.getAuditLogs(orgId, filters);
      res.writeHead(200);
      res.end(JSON.stringify(logs));
      return;
    }

    // Permissions
    if (requestPath === '/api/permissions' && method === 'GET') {
      const perms = Array.from(agentOS.permissions.values());
      res.writeHead(200);
      res.end(JSON.stringify(perms));
      return;
    }

    // File operations
    if (requestPath === '/api/files/read' && method === 'POST') {
      const body = await readBody();
      const result = agentOS.readFile(body.path);
      res.writeHead(result.success ? 200 : 403);
      res.end(JSON.stringify(result));
      return;
    }

    if (requestPath === '/api/files/write' && method === 'POST') {
      const body = await readBody();
      const result = agentOS.writeFile(body.path, body.content);
      res.writeHead(result.success ? 200 : 403);
      res.end(JSON.stringify(result));
      return;
    }

    if (requestPath === '/api/files/list' && method === 'GET') {
      const dirPath = url.searchParams.get('path');
      const result = agentOS.listDirectory(dirPath);
      res.writeHead(result.success ? 200 : 403);
      res.end(JSON.stringify(result));
      return;
    }

    if (requestPath === '/api/files/delete' && method === 'POST') {
      const body = await readBody();
      const result = agentOS.deleteFile(body.path);
      res.writeHead(result.success ? 200 : 403);
      res.end(JSON.stringify(result));
      return;
    }

    // Command execution
    if (requestPath === '/api/command' && method === 'POST') {
      const body = await readBody();
      const result = agentOS.executeCommand(body.command);
      res.writeHead(result.success ? 200 : 403);
      res.end(JSON.stringify(result));
      return;
    }

    // ============ Memory Manager API ============

    if (requestPath === '/api/memory/health' && method === 'GET') {
      res.writeHead(200);
      res.end(JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() }));
      return;
    }

    if (requestPath === '/api/memory/knowledge' && method === 'POST') {
      const body = await readBody();
      const factId = memoryStore.storeKnowledge(body.fact, body.concepts || [], body.metadata || {});
      res.writeHead(201);
      res.end(JSON.stringify({ success: true, fact_id: factId }));
      return;
    }

    if (requestPath === '/api/memory/recall' && method === 'GET') {
      const query = url.searchParams.get('query') || '';
      const topK = parseInt(url.searchParams.get('topK') || '5');
      const results = memoryStore.recallKnowledge(query, topK);
      res.writeHead(200);
      res.end(JSON.stringify({ success: true, results }));
      return;
    }

    if (requestPath === '/api/memory/stats' && method === 'GET') {
      res.writeHead(200);
      res.end(JSON.stringify(memoryStore.getStats()));
      return;
    }

    if (requestPath === '/api/memory/session' && method === 'POST') {
      const body = await readBody();
      const sessionId = memoryStore.startSession(body.agentId, body.context || {});
      res.writeHead(201);
      res.end(JSON.stringify({ success: true, session_id: sessionId }));
      return;
    }

    if (requestPath === '/api/memory/interaction' && method === 'POST') {
      const body = await readBody();
      const epId = memoryStore.addInteraction(body.sessionId || '', body.type, body.content, body.metadata || {});
      res.writeHead(201);
      res.end(JSON.stringify({ success: true, episode_id: epId }));
      return;
    }

    if (requestPath.startsWith('/api/memory/history/') && method === 'GET') {
      const agentId = requestPath.split('/api/memory/history/')[1];
      const history = memoryStore.getHistory(decodeURIComponent(agentId));
      res.writeHead(200);
      res.end(JSON.stringify({ success: true, history }));
      return;
    }

    // ============ Agent Runtime API ============

    if (requestPath === '/api/runtime/agents' && method === 'POST') {
      const body = await readBody();
      const agentId = createAgent(body.name, body.type, body.config || {}, body.permissions || []);
      res.writeHead(201);
      res.end(JSON.stringify({ success: true, agent_id: agentId }));
      return;
    }

    if (requestPath === '/api/runtime/agents' && method === 'GET') {
      const agentList = [...agents.values()];
      res.writeHead(200);
      res.end(JSON.stringify({ success: true, agents: agentList }));
      return;
    }

    if (requestPath.startsWith('/api/runtime/agents/') && method === 'GET') {
      const agentId = requestPath.split('/api/runtime/agents/')[1];
      const agent = agents.get(agentId);
      res.writeHead(agent ? 200 : 404);
      res.end(JSON.stringify(agent || { error: 'Agent not found' }));
      return;
    }

    if (requestPath === '/api/runtime/tasks' && method === 'POST') {
      const body = await readBody();
      const taskId = submitTask(body.agentId, body.taskType, body.payload || {}, body.priority || 2);
      res.writeHead(201);
      res.end(JSON.stringify({ success: true, task_id: taskId }));
      return;
    }

    if (requestPath === '/api/runtime/tasks' && method === 'GET') {
      res.writeHead(200);
      res.end(JSON.stringify({ success: true, tasks }));
      return;
    }

    if (requestPath.startsWith('/api/runtime/tasks/') && method === 'GET') {
      const taskId = requestPath.split('/api/runtime/tasks/')[1];
      const task = tasks.find(t => t.id === taskId);
      res.writeHead(task ? 200 : 404);
      res.end(JSON.stringify(task || { error: 'Task not found' }));
      return;
    }

    if (requestPath === '/api/runtime/tools' && method === 'GET') {
      res.writeHead(200);
      res.end(JSON.stringify({ success: true, tools: toolRegistry }));
      return;
    }

    if (requestPath === '/api/runtime/stats' && method === 'GET') {
      res.writeHead(200);
      res.end(JSON.stringify({
        agents: { total: agents.size, active: [...agents.values()].filter(a => a.status === 'running').length },
        tasks: { pending: tasks.filter(t => t.status === 'pending').length, total: tasks.length },
        tools: { registered: toolRegistry.length }
      }));
      return;
    }

    // 404
    res.writeHead(404);
    res.end(JSON.stringify({ error: 'Not found' }));

  } catch (error) {
    res.writeHead(500);
    res.end(JSON.stringify({ error: error.message }));
  }
});

// Start server
server.listen(PORT, () => {
  console.log(`\n========================================`);
  console.log(`   AgentOS API running on port ${PORT}`);
  console.log(`   Workspace: ${WORKSPACE_DIR}`);
  console.log(`========================================`);
  console.log(`\nAPI Endpoints:`);
  console.log(`  GET  /api/health           - Health check`);
  console.log(`  GET  /api/system           - System info`);
  console.log(`  POST /api/org/register    - Register organization`);
  console.log(`  GET  /api/org/:id/stats   - Organization stats`);
  console.log(`  GET  /api/agents          - List agents`);
  console.log(`  POST /api/agents          - Create agent`);
  console.log(`  GET  /api/workflows       - List workflows`);
  console.log(`  POST /api/workflows       - Create workflow`);
  console.log(`  GET  /api/audit           - Audit logs`);
  console.log(`  GET  /api/permissions     - Permission list`);
  console.log(`  POST /api/files/read      - Read file`);
  console.log(`  POST /api/files/write     - Write file`);
  console.log(`  GET  /api/files/list      - List directory`);
  console.log(`  POST /api/files/delete    - Delete file`);
  console.log(`  POST /api/command         - Execute command`);
  console.log(`  --- Memory ---`);
  console.log(`  GET  /api/memory/health   - Memory health`);
  console.log(`  POST /api/memory/knowledge - Store knowledge`);
  console.log(`  GET  /api/memory/recall  - Recall knowledge`);
  console.log(`  GET  /api/memory/stats   - Memory stats`);
  console.log(`  --- Runtime ---`);
  console.log(`  POST /api/runtime/agents  - Create agent`);
  console.log(`  GET  /api/runtime/agents  - List agents`);
  console.log(`  POST /api/runtime/tasks   - Submit task`);
  console.log(`  GET  /api/runtime/tools   - List tools`);
  console.log(`  GET  /api/runtime/stats   - Runtime stats`);
  console.log(`\n`);
});