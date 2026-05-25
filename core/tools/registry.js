/**
 * Enhanced Tool Registry
 * Provides extensible tool system for agents
 */

class ToolRegistry {
  constructor() {
    this.tools = new Map();
    this.toolUsage = new Map();
    this.customTools = new Map();
    this.initBuiltInTools();
  }

  initBuiltInTools() {
    // File Operations
    this.register({
      name: 'file_read',
      category: 'file',
      description: 'Read contents of a file',
      params: [
        { name: 'path', type: 'string', required: true, description: 'File path to read' },
        { name: 'encoding', type: 'string', required: false, default: 'utf-8', description: 'File encoding' },
        { name: 'lines', type: 'number', required: false, description: 'Number of lines to read (for large files)' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        try {
          const content = fs.readFileSync(params.path, params.encoding || 'utf-8');
          return { success: true, content: params.lines ? content.split('\n').slice(0, params.lines).join('\n') : content };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'file_write',
      category: 'file',
      description: 'Write content to a file',
      params: [
        { name: 'path', type: 'string', required: true, description: 'File path to write' },
        { name: 'content', type: 'string', required: true, description: 'Content to write' },
        { name: 'append', type: 'boolean', required: false, default: false, description: 'Append to existing file' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        try {
          if (params.append) {
            fs.appendFileSync(params.path, params.content);
          } else {
            fs.writeFileSync(params.path, params.content);
          }
          return { success: true, path: params.path };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'file_list',
      category: 'file',
      description: 'List files in a directory',
      params: [
        { name: 'path', type: 'string', required: true, description: 'Directory path' },
        { name: 'recursive', type: 'boolean', required: false, default: false, description: 'List recursively' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        const path = require('path');
        try {
          const entries = fs.readdirSync(params.path, { withFileTypes: true });
          const files = entries.map(e => ({
            name: e.name,
            type: e.isDirectory() ? 'directory' : 'file',
            path: path.join(params.path, e.name)
          }));
          return { success: true, files };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'file_stats',
      category: 'file',
      description: 'Get file statistics',
      params: [
        { name: 'path', type: 'string', required: true, description: 'File or directory path' }
      ],
      execute: async (params) => {
        const fs = require('fs');
        try {
          const stat = fs.statSync(params.path);
          return {
            success: true,
            stats: {
              size: stat.size,
              created: stat.birthtime,
              modified: stat.mtime,
              isFile: stat.isFile(),
              isDirectory: stat.isDirectory()
            }
          };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    // Shell Operations
    this.register({
      name: 'execute_command',
      category: 'shell',
      description: 'Execute a shell command',
      params: [
        { name: 'command', type: 'string', required: true, description: 'Command to execute' },
        { name: 'timeout', type: 'number', required: false, default: 30000, description: 'Timeout in ms' }
      ],
      execute: async (params) => {
        const { execSync } = require('child_process');
        try {
          const result = execSync(params.command, { encoding: 'utf-8', timeout: params.timeout || 30000 });
          return { success: true, output: result };
        } catch (e) {
          return { success: false, error: e.message, stderr: e.stderr };
        }
      }
    });

    this.register({
      name: 'execute_python',
      category: 'shell',
      description: 'Execute Python code',
      params: [
        { name: 'code', type: 'string', required: true, description: 'Python code to execute' },
        { name: 'args', type: 'array', required: false, description: 'Command line arguments' }
      ],
      execute: async (params) => {
        const { execSync } = require('child_process');
        try {
          const result = execSync(`python -c "${params.code.replace(/"/g, '\\"')}"`, { encoding: 'utf-8' });
          return { success: true, output: result };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'execute_node',
      category: 'shell',
      description: 'Execute Node.js code',
      params: [
        { name: 'code', type: 'string', required: true, description: 'JavaScript code to execute' }
      ],
      execute: async (params) => {
        const { execSync } = require('child_process');
        try {
          const result = execSync(`node -e "${params.code.replace(/"/g, '\\"')}"`, { encoding: 'utf-8' });
          return { success: true, output: result };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    // Network Operations
    this.register({
      name: 'http_request',
      category: 'network',
      description: 'Make HTTP/HTTPS request',
      params: [
        { name: 'url', type: 'string', required: true, description: 'Request URL' },
        { name: 'method', type: 'string', required: false, default: 'GET', description: 'HTTP method' },
        { name: 'headers', type: 'object', required: false, description: 'Request headers' },
        { name: 'body', type: 'string', required: false, description: 'Request body' }
      ],
      execute: async (params) => {
        try {
          const url = new URL(params.url);
          if (!['http:', 'https:'].includes(url.protocol)) {
            return { success: false, error: 'Only HTTP/HTTPS protocols allowed' };
          }
          return { success: true, message: 'Request would be made', url: params.url, method: params.method };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'fetch_json',
      category: 'network',
      description: 'Fetch and parse JSON from URL',
      params: [
        { name: 'url', type: 'string', required: true, description: 'JSON endpoint URL' }
      ],
      execute: async (params) => {
        try {
          return { success: true, message: 'Fetch would be performed', url: params.url };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    // Data Processing
    this.register({
      name: 'parse_json',
      category: 'data',
      description: 'Parse JSON string',
      params: [
        { name: 'data', type: 'string', required: true, description: 'JSON string to parse' }
      ],
      execute: async (params) => {
        try {
          const parsed = JSON.parse(params.data);
          return { success: true, data: parsed };
        } catch (e) {
          return { success: false, error: 'Invalid JSON: ' + e.message };
        }
      }
    });

    this.register({
      name: 'to_json',
      category: 'data',
      description: 'Convert data to JSON string',
      params: [
        { name: 'data', type: 'object', required: true, description: 'Data to convert' },
        { name: 'pretty', type: 'boolean', required: false, default: false, description: 'Pretty print' }
      ],
      execute: async (params) => {
        try {
          const json = params.pretty ? JSON.stringify(params.data, null, 2) : JSON.stringify(params.data);
          return { success: true, json };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'csv_parse',
      category: 'data',
      description: 'Parse CSV data',
      params: [
        { name: 'data', type: 'string', required: true, description: 'CSV string' },
        { name: 'delimiter', type: 'string', required: false, default: ',', description: 'CSV delimiter' }
      ],
      execute: async (params) => {
        try {
          const lines = params.data.split('\n').filter(l => l.trim());
          const headers = lines[0].split(params.delimiter || ',');
          const rows = lines.slice(1).map(line => {
            const values = line.split(params.delimiter || ',');
            return headers.reduce((obj, header, i) => {
              obj[header.trim()] = values[i]?.trim();
              return obj;
            }, {});
          });
          return { success: true, headers, rows, count: rows.length };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'filter_array',
      category: 'data',
      description: 'Filter array based on condition',
      params: [
        { name: 'array', type: 'array', required: true, description: 'Array to filter' },
        { name: 'condition', type: 'string', required: true, description: 'Filter condition (e.g., "x > 5")' }
      ],
      execute: async (params) => {
        try {
          return { success: true, result: params.array, note: 'Condition evaluation not implemented in sandbox' };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'map_array',
      category: 'data',
      description: 'Transform array elements',
      params: [
        { name: 'array', type: 'array', required: true, description: 'Array to transform' },
        { name: 'operation', type: 'string', required: true, description: 'Operation to perform' }
      ],
      execute: async (params) => {
        try {
          return { success: true, result: params.array, note: 'Map operation not implemented in sandbox' };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    // String Operations
    this.register({
      name: 'regex_match',
      category: 'string',
      description: 'Match pattern using regex',
      params: [
        { name: 'text', type: 'string', required: true, description: 'Text to search' },
        { name: 'pattern', type: 'string', required: true, description: 'Regex pattern' },
        { name: 'flags', type: 'string', required: false, default: 'g', description: 'Regex flags' }
      ],
      execute: async (params) => {
        try {
          const regex = new RegExp(params.pattern, params.flags || 'g');
          const matches = params.text.match(regex);
          return { success: true, matches: matches || [], count: matches ? matches.length : 0 };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    this.register({
      name: 'string_replace',
      category: 'string',
      description: 'Replace text patterns',
      params: [
        { name: 'text', type: 'string', required: true, description: 'Input text' },
        { name: 'search', type: 'string', required: true, description: 'Text to find' },
        { name: 'replace', type: 'string', required: true, description: 'Replacement text' }
      ],
      execute: async (params) => {
        return { success: true, result: params.text.replace(params.search, params.replace) };
      }
    });

    this.register({
      name: 'split_text',
      category: 'string',
      description: 'Split text by delimiter',
      params: [
        { name: 'text', type: 'string', required: true, description: 'Text to split' },
        { name: 'delimiter', type: 'string', required: false, default: ' ', description: 'Delimiter' }
      ],
      execute: async (params) => {
        return { success: true, parts: params.text.split(params.delimiter), count: params.text.split(params.delimiter).length };
      }
    });

    this.register({
      name: 'word_count',
      category: 'string',
      description: 'Count words and characters',
      params: [
        { name: 'text', type: 'string', required: true, description: 'Text to analyze' }
      ],
      execute: async (params) => {
        const text = params.text;
        return {
          success: true,
          characters: text.length,
          charactersNoSpaces: text.replace(/\s/g, '').length,
          words: text.split(/\s+/).filter(w => w).length,
          lines: text.split('\n').length
        };
      }
    });

    // Math Operations
    this.register({
      name: 'calculate',
      category: 'math',
      description: 'Evaluate mathematical expression',
      params: [
        { name: 'expression', type: 'string', required: true, description: 'Math expression' }
      ],
      execute: async (params) => {
        try {
          // Safe evaluation - only allow numbers and operators
          const sanitized = params.expression.replace(/[^0-9+\-*/().]/g, '');
          const result = Function('"use strict"; return (' + sanitized + ')')();
          return { success: true, result };
        } catch (e) {
          return { success: false, error: e.message };
        }
      }
    });

    // Memory Operations
    this.register({
      name: 'memory_store',
      category: 'memory',
      description: 'Store information in agent memory',
      params: [
        { name: 'key', type: 'string', required: true, description: 'Memory key' },
        { name: 'value', type: 'string', required: true, description: 'Value to store' }
      ],
      execute: async (params, memoryStore) => {
        if (memoryStore) {
          memoryStore.storeKnowledge(params.value, [params.key]);
          return { success: true, key: params.key };
        }
        return { success: false, error: 'Memory store not available' };
      }
    });

    this.register({
      name: 'memory_recall',
      category: 'memory',
      description: 'Recall information from memory',
      params: [
        { name: 'query', type: 'string', required: true, description: 'Search query' }
      ],
      execute: async (params, memoryStore) => {
        if (memoryStore) {
          const results = memoryStore.recallKnowledge(params.query);
          return { success: true, results };
        }
        return { success: false, error: 'Memory store not available' };
      }
    });

    // System Operations
    this.register({
      name: 'get_system_info',
      category: 'system',
      description: 'Get system information',
      params: [],
      execute: async () => {
        const os = require('os');
        return {
          success: true,
          platform: os.platform(),
          arch: os.arch(),
          cpus: os.cpus().length,
          totalMemory: os.totalmem(),
          freeMemory: os.freemem(),
          hostname: os.hostname(),
          uptime: os.uptime()
        };
      }
    });

    this.register({
      name: 'get_time',
      category: 'system',
      description: 'Get current time and date',
      params: [
        { name: 'timezone', type: 'string', required: false, description: 'Timezone (optional)' }
      ],
      execute: async (params) => {
        const now = new Date();
        return {
          success: true,
          iso: now.toISOString(),
          unix: Math.floor(now.getTime() / 1000),
          utc: now.toUTCString(),
          local: now.toLocaleString()
        };
      }
    });

    this.register({
      name: 'sleep',
      category: 'system',
      description: 'Pause execution for specified duration',
      params: [
        { name: 'ms', type: 'number', required: true, description: 'Milliseconds to sleep' }
      ],
      execute: async (params) => {
        await new Promise(resolve => setTimeout(resolve, Math.min(params.ms, 5000)));
        return { success: true, waited: Math.min(params.ms, 5000) };
      }
    });

    // Validation
    this.register({
      name: 'validate_email',
      category: 'validation',
      description: 'Validate email address',
      params: [
        { name: 'email', type: 'string', required: true, description: 'Email to validate' }
      ],
      execute: async (params) => {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const valid = regex.test(params.email);
        return { success: true, valid, email: params.email };
      }
    });

    this.register({
      name: 'validate_url',
      category: 'validation',
      description: 'Validate URL',
      params: [
        { name: 'url', type: 'string', required: true, description: 'URL to validate' }
      ],
      execute: async (params) => {
        try {
          new URL(params.url);
          return { success: true, valid: true, url: params.url };
        } catch {
          return { success: true, valid: false, url: params.url };
        }
      }
    });
  }

  // Register a new tool
  register(tool) {
    if (this.tools.has(tool.name)) {
      throw new Error(`Tool ${tool.name} already registered`);
    }
    this.tools.set(tool.name, {
      ...tool,
      registeredAt: new Date().toISOString(),
      usageCount: 0
    });
  }

  // Register a custom tool
  registerCustom(name, handler, description = '', params = []) {
    this.customTools.set(name, {
      name,
      handler,
      description,
      params,
      registeredAt: new Date().toISOString()
    });
  }

  // Execute a tool
  async execute(toolName, params = {}, memoryStore = null) {
    const tool = this.tools.get(toolName) || this.customTools.get(toolName);
    if (!tool) {
      return { success: false, error: `Tool ${toolName} not found` };
    }

    // Validate required params
    for (const param of (tool.params || [])) {
      if (param.required && !(params[param.name] !== undefined)) {
        return { success: false, error: `Missing required parameter: ${param.name}` };
      }
    }

    // Apply default values
    const fullParams = { ...params };
    for (const param of (tool.params || [])) {
      if (fullParams[param.name] === undefined && param.default !== undefined) {
        fullParams[param.name] = param.default;
      }
    }

    try {
      // Track usage
      this.toolUsage.set(toolName, (this.toolUsage.get(toolName) || 0) + 1);
      if (this.tools.has(toolName)) {
        this.tools.get(toolName).usageCount++;
      }

      // Execute tool
      const result = await tool.execute(fullParams, memoryStore);
      return { tool: toolName, ...result };
    } catch (e) {
      return { success: false, error: e.message, tool: toolName };
    }
  }

  // Get all tools
  getAll() {
    const builtIn = [...this.tools.values()].map(t => ({
      name: t.name,
      category: t.category,
      description: t.description,
      params: t.params,
      usageCount: t.usageCount
    }));
    const custom = [...this.customTools.values()].map(t => ({
      name: t.name,
      category: 'custom',
      description: t.description,
      params: t.params
    }));
    return [...builtIn, ...custom];
  }

  // Get tools by category
  getByCategory(category) {
    return [...this.tools.values()].filter(t => t.category === category);
  }

  // Get tool details
  get(toolName) {
    return this.tools.get(toolName) || this.customTools.get(toolName);
  }

  // Get usage statistics
  getUsageStats() {
    const stats = {};
    for (const [tool, count] of this.toolUsage) {
      stats[tool] = count;
    }
    return stats;
  }

  // Delete custom tool
  deleteCustom(toolName) {
    return this.customTools.delete(toolName);
  }
}

module.exports = { ToolRegistry };