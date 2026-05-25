/**
 * Enhanced Tool Registry
 * Manages available tools for agents
 */

class ToolRegistry {
  constructor() {
    this.tools = new Map();
    this.toolCategories = new Map();
    this.toolUsage = new Map();
    this.initDefaultTools();
  }

  initDefaultTools() {
    // File operations
    this.registerTool({
      name: 'file_read',
      category: 'filesystem',
      description: 'Read contents of a file',
      parameters: [
        { name: 'path', type: 'string', required: true, description: 'File path to read' },
        { name: 'encoding', type: 'string', required: false, default: 'utf-8', description: 'File encoding' },
        { name: 'lines', type: 'number', required: false, description: 'Number of lines to read' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        try {
          const content = fs.readFileSync(params.path, params.encoding || 'utf-8');
          const lines = params.lines ? content.split('\n').slice(0, params.lines).join('\n') : content;
          return { success: true, content: lines, size: content.length };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 100
    });

    this.registerTool({
      name: 'file_write',
      category: 'filesystem',
      description: 'Write content to a file',
      parameters: [
        { name: 'path', type: 'string', required: true, description: 'File path to write' },
        { name: 'content', type: 'string', required: true, description: 'Content to write' },
        { name: 'append', type: 'boolean', required: false, default: false, description: 'Append to existing file' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        try {
          const dir = require('path').dirname(params.path);
          if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
          if (params.append) {
            fs.appendFileSync(params.path, params.content);
          } else {
            fs.writeFileSync(params.path, params.content);
          }
          return { success: true, path: params.path };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: true,
      rateLimit: 50
    });

    this.registerTool({
      name: 'file_delete',
      category: 'filesystem',
      description: 'Delete a file or directory',
      parameters: [
        { name: 'path', type: 'string', required: true, description: 'Path to delete' },
        { name: 'recursive', type: 'boolean', required: false, default: false, description: 'Delete recursively' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        try {
          if (!fs.existsSync(params.path)) return { success: false, error: 'Path not found' };
          if (params.recursive) {
            fs.rmSync(params.path, { recursive: true });
          } else {
            fs.unlinkSync(params.path);
          }
          return { success: true, path: params.path };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: true,
      rateLimit: 10
    });

    this.registerTool({
      name: 'list_directory',
      category: 'filesystem',
      description: 'List contents of a directory',
      parameters: [
        { name: 'path', type: 'string', required: false, description: 'Directory path' },
        { name: 'recursive', type: 'boolean', required: false, default: false, description: 'List recursively' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        const path = require('path');
        try {
          const target = params.path || '.';
          if (!fs.existsSync(target)) return { success: false, error: 'Directory not found' };

          const listDir = (dir, depth = 0) => {
            if (depth > 3 && params.recursive) return [];
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            return entries.map(e => {
              const fullPath = path.join(dir, e.name);
              return {
                name: e.name,
                type: e.isDirectory() ? 'directory' : 'file',
                size: e.isFile() ? fs.statSync(fullPath).size : 0,
                children: e.isDirectory() && params.recursive ? listDir(fullPath, depth + 1) : undefined
              };
            });
          };

          return { success: true, entries: listDir(target), path: target };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 100
    });

    this.registerTool({
      name: 'file_search',
      category: 'filesystem',
      description: 'Search for files by pattern',
      parameters: [
        { name: 'path', type: 'string', required: true, description: 'Directory to search' },
        { name: 'pattern', type: 'string', required: true, description: 'Search pattern (glob)' },
        { name: 'content', type: 'string', required: false, description: 'Search in file contents' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        const path = require('path');
        try {
          const results = [];
          const searchDir = (dir) => {
            if (!fs.existsSync(dir)) return;
            const entries = fs.readdirSync(dir, { withFileTypes: true });
            for (const entry of entries) {
              const fullPath = path.join(dir, entry.name);
              if (entry.isDirectory()) {
                if (!entry.name.startsWith('.')) searchDir(fullPath);
              } else {
                if (params.content) {
                  const content = fs.readFileSync(fullPath, 'utf-8');
                  if (content.includes(params.content)) {
                    results.push({ path: fullPath, matches: content.split(params.content).length - 1 });
                  }
                } else if (entry.name.includes(params.pattern) || params.pattern === '*') {
                  results.push({ path: fullPath, size: fs.statSync(fullPath).size });
                }
              }
            }
          };
          searchDir(params.path);
          return { success: true, results, count: results.length };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 30
    });

    // System operations
    this.registerTool({
      name: 'execute_command',
      category: 'system',
      description: 'Execute a shell command',
      parameters: [
        { name: 'command', type: 'string', required: true, description: 'Command to execute' },
        { name: 'timeout', type: 'number', required: false, default: 30000, description: 'Timeout in ms' },
        { name: 'cwd', type: 'string', required: false, description: 'Working directory' }
      ],
      execute: async (params) => {
        const { execSync } = require('child_process');
        try {
          const result = execSync(params.command, {
            timeout: params.timeout || 30000,
            encoding: 'utf-8',
            cwd: params.cwd
          });
          return { success: true, output: result };
        } catch (e) {
          return { success: false, error: e.message, stderr: e.stderr };
        }
      },
      requiresApproval: true,
      rateLimit: 20
    });

    this.registerTool({
      name: 'get_system_info',
      category: 'system',
      description: 'Get system information',
      parameters: [
        { name: 'detail', type: 'string', required: false, description: 'Detail level: basic, full' }
      ],
      execute: async (params) => {
        const os = require('os');
        const detail = params.detail || 'basic';
        const info = {
          platform: os.platform(),
          arch: os.arch(),
          nodeVersion: process.version,
          cpuCount: os.cpus().length,
          totalMemory: os.totalmem(),
          freeMemory: os.freemem(),
          uptime: os.uptime(),
          hostname: os.hostname()
        };
        if (detail === 'full') {
          info.cpus = os.cpus().map(c => ({
            model: c.model,
            speed: c.speed,
            times: c.times
          }));
          info.networkInterfaces = os.networkInterfaces();
        }
        return { success: true, ...info };
      },
      requiresApproval: false,
      rateLimit: 50
    });

    this.registerTool({
      name: 'process_list',
      category: 'system',
      description: 'List running processes',
      parameters: [
        { name: 'limit', type: 'number', required: false, default: 10, description: 'Max processes to return' }
      ],
      execute: async (params) => {
        const { execSync } = require('child_process');
        try {
          const isWindows = process.platform === 'win32';
          const cmd = isWindows
            ? `tasklist /FO CSV /NH | head -n ${params.limit}`
            : `ps aux | head -n ${params.limit}`;
          const output = execSync(cmd, { encoding: 'utf-8' });
          const processes = output.trim().split('\n').map(line => {
            const parts = isWindows ? line.split('","') : line.split(/\s+/);
            return {
              name: isWindows ? parts[0]?.replace(/"/g, '') : parts[10] || parts[0],
              pid: isWindows ? parseInt(parts[1]) : parseInt(part[1]),
              memory: isWindows ? parts[4]?.replace(/"/g, '') : parts[5]
            };
          });
          return { success: true, processes };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: true,
      rateLimit: 10
    });

    // Network operations
    this.registerTool({
      name: 'http_request',
      category: 'network',
      description: 'Make HTTP request',
      parameters: [
        { name: 'url', type: 'string', required: true, description: 'Request URL' },
        { name: 'method', type: 'string', required: false, default: 'GET', description: 'HTTP method' },
        { name: 'headers', type: 'object', required: false, description: 'Request headers' },
        { name: 'body', type: 'string', required: false, description: 'Request body' },
        { name: 'timeout', type: 'number', required: false, default: 10000, description: 'Timeout in ms' }
      ],
      execute: async (params) => {
        const https = require('https');
        const http = require('http');
        const { URL } = require('url');
        return new Promise((resolve) => {
          try {
            const parsed = new URL(params.url);
            const client = parsed.protocol === 'https:' ? https : http;
            const options = {
              hostname: parsed.hostname,
              port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
              path: parsed.pathname + parsed.search,
              method: params.method || 'GET',
              headers: params.headers || {},
              timeout: params.timeout || 10000
            };
            const req = client.request(options, (res) => {
              let data = '';
              res.on('data', chunk => data += chunk);
              res.on('end', () => {
                resolve({
                  success: true,
                  status: res.statusCode,
                  headers: res.headers,
                  body: data.substring(0, 10000)
                });
              });
            });
            req.on('error', e => resolve({ success: false, error: e.message }));
            req.on('timeout', () => {
              req.destroy();
              resolve({ success: false, error: 'Request timeout' });
            });
            if (params.body) req.write(params.body);
            req.end();
          } catch (e) {
            resolve({ success: false, error: e.message });
          }
        });
      },
      requiresApproval: false,
      rateLimit: 100
    });

    this.registerTool({
      name: 'dns_lookup',
      category: 'network',
      description: 'Perform DNS lookup',
      parameters: [
        { name: 'hostname', type: 'string', required: true, description: 'Hostname to lookup' },
        { name: 'type', type: 'string', required: false, default: 'A', description: 'Record type' }
      ],
      execute: async (params) => {
        const dns = require('dns');
        const { promisify } = require('util');
        const lookup = promisify(dns.resolve);
        try {
          const records = await lookup(params.hostname, params.type || 'A');
          return { success: true, hostname: params.hostname, type: params.type || 'A', records };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 50
    });

    // Data processing
    this.registerTool({
      name: 'json_parse',
      category: 'data',
      description: 'Parse JSON string',
      parameters: [
        { name: 'data', type: 'string', required: true, description: 'JSON string to parse' }
      ],
      execute: async (params) => {
        try {
          const parsed = JSON.parse(params.data);
          return { success: true, data: parsed };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 200
    });

    this.registerTool({
      name: 'json_transform',
      category: 'data',
      description: 'Transform JSON data using mapping',
      parameters: [
        { name: 'data', type: 'object', required: true, description: 'Input data' },
        { name: 'mapping', type: 'object', required: true, description: 'Field mapping' }
      ],
      execute: async (params) => {
        try {
          const result = {};
          for (const [target, source] of Object.entries(params.mapping)) {
            if (typeof source === 'string' && source.startsWith('$')) {
              const path = source.substring(1).split('.');
              let value = params.data;
              for (const key of path) {
                value = value?.[key];
              }
              result[target] = value;
            } else {
              result[target] = source;
            }
          }
          return { success: true, data: result };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 100
    });

    this.registerTool({
      name: 'csv_parse',
      category: 'data',
      description: 'Parse CSV data',
      parameters: [
        { name: 'data', type: 'string', required: true, description: 'CSV string' },
        { name: 'delimiter', type: 'string', required: false, default: ',', description: 'CSV delimiter' }
      ],
      execute: async (params) => {
        try {
          const lines = params.data.trim().split('\n');
          const delimiter = params.delimiter || ',';
          const headers = lines[0].split(delimiter).map(h => h.trim());
          const rows = lines.slice(1).map(line => {
            const values = line.split(delimiter);
            const row = {};
            headers.forEach((h, i) => {
              row[h] = values[i]?.trim();
            });
            return row;
          });
          return { success: true, headers, rows, count: rows.length };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 50
    });

    // Math operations
    this.registerTool({
      name: 'calculate',
      category: 'math',
      description: 'Perform mathematical calculations',
      parameters: [
        { name: 'expression', type: 'string', required: true, description: 'Mathematical expression' }
      ],
      execute: async (params) => {
        try {
          // Safe math evaluation (basic operations only)
          const expr = params.expression.replace(/[^0-9+\-*/().sin cos tan sqrt powlogexp ]/gi, '');
          const result = Function('"use strict"; return (' + expr + ')')();
          return { success: true, expression: params.expression, result };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 500
    });

    // Memory operations
    this.registerTool({
      name: 'memory_store',
      category: 'memory',
      description: 'Store information in memory',
      parameters: [
        { name: 'fact', type: 'string', required: true, description: 'Information to store' },
        { name: 'concepts', type: 'array', required: false, description: 'Associated concepts' },
        { name: 'importance', type: 'number', required: false, default: 0.5, description: 'Importance 0-1' }
      ],
      execute: async (params, memoryStore) => {
        if (!memoryStore) return { success: false, error: 'Memory store not available' };
        const id = memoryStore.storeKnowledge(params.fact, params.concepts || [], {
          importance: params.importance || 0.5
        });
        return { success: true, id };
      },
      requiresApproval: false,
      rateLimit: 100
    });

    this.registerTool({
      name: 'memory_recall',
      category: 'memory',
      description: 'Recall information from memory',
      parameters: [
        { name: 'query', type: 'string', required: true, description: 'Search query' },
        { name: 'topK', type: 'number', required: false, default: 5, description: 'Number of results' }
      ],
      execute: async (params, memoryStore) => {
        if (!memoryStore) return { success: false, error: 'Memory store not available' };
        const results = memoryStore.recallKnowledge(params.query, params.topK || 5);
        return { success: true, results };
      },
      requiresApproval: false,
      rateLimit: 100
    });

    // Text processing
    this.registerTool({
      name: 'text_extract',
      category: 'text',
      description: 'Extract information from text using regex',
      parameters: [
        { name: 'text', type: 'string', required: true, description: 'Input text' },
        { name: 'pattern', type: 'string', required: true, description: 'Regex pattern' },
        { name: 'flags', type: 'string', required: false, default: 'g', description: 'Regex flags' }
      ],
      execute: async (params) => {
        try {
          const regex = new RegExp(params.pattern, params.flags || 'g');
          const matches = params.text.match(regex);
          return { success: true, matches: matches || [], count: matches?.length || 0 };
        } catch (e) {
          return { success: false, error: e.message };
        }
      },
      requiresApproval: false,
      rateLimit: 100
    });

    this.registerTool({
      name: 'text_transform',
      category: 'text',
      description: 'Transform text (upper, lower, trim, etc.)',
      parameters: [
        { name: 'text', type: 'string', required: true, description: 'Input text' },
        { name: 'operation', type: 'string', required: true, description: 'Operation: upper, lower, title, trim, slug' }
      ],
      execute: async (params) => {
        let result = params.text;
        switch (params.operation) {
          case 'upper': result = result.toUpperCase(); break;
          case 'lower': result = result.toLowerCase(); break;
          case 'title': result = result.replace(/\w\S*/g, t => t.charAt(0).toUpperCase() + t.substr(1).toLowerCase()); break;
          case 'trim': result = result.trim(); break;
          case 'slug': result = result.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''); break;
          default: return { success: false, error: 'Unknown operation' };
        }
        return { success: true, result };
      },
      requiresApproval: false,
      rateLimit: 500
    });
  }

  registerTool(toolDef) {
    this.tools.set(toolDef.name, toolDef);

    if (!this.toolCategories.has(toolDef.category)) {
      this.toolCategories.set(toolDef.category, []);
    }
    this.toolCategories.get(toolDef.category).push(toolDef.name);

    this.toolUsage.set(toolDef.name, { calls: 0, errors: 0, lastUsed: null });
  }

  getTool(name) {
    return this.tools.get(name);
  }

  getToolsByCategory(category) {
    const toolNames = this.toolCategories.get(category) || [];
    return toolNames.map(name => this.tools.get(name)).filter(Boolean);
  }

  getAllTools() {
    return [...this.tools.values()];
  }

  getCategories() {
    return [...this.toolCategories.keys()];
  }

  async executeTool(name, params, memoryStore = null) {
    const tool = this.tools.get(name);
    if (!tool) {
      return { success: false, error: `Tool '${name}' not found` };
    }

    const usage = this.toolUsage.get(name);
    usage.calls++;
    usage.lastUsed = new Date().toISOString();

    try {
      const result = await tool.execute(params, memoryStore);
      return result;
    } catch (e) {
      usage.errors++;
      return { success: false, error: e.message };
    }
  }

  getToolStats() {
    const stats = {};
    for (const [name, usage] of this.toolUsage) {
      const tool = this.tools.get(name);
      stats[name] = {
        ...usage,
        category: tool?.category,
        requiresApproval: tool?.requiresApproval
      };
    }
    return stats;
  }

  checkRateLimit(toolName, windowMs = 60000) {
    const tool = this.tools.get(toolName);
    if (!tool) return { allowed: true };
    return { allowed: true, limit: tool.rateLimit }; // Simplified for now
  }
}

module.exports = { ToolRegistry };