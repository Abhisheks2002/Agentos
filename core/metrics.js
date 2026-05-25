/**
 * Metrics and Monitoring System
 * Provides observability for AgentOS
 */

class MetricsSystem {
  constructor() {
    this.metrics = new Map();
    this.counters = new Map();
    this.gauges = new Map();
    this.histograms = new Map();
    this.timers = new Map();
    this.alerts = new Map();
    this.nextAlertId = 1;
    this.initDefaultMetrics();
  }

  initDefaultMetrics() {
    // Initialize default counters
    this.counter('api_requests_total', 'Total API requests');
    this.counter('api_requests_errors', 'Total API request errors');
    this.counter('agents_created_total', 'Total agents created');
    this.counter('agents_completed_tasks', 'Total tasks completed by agents');
    this.counter('workflows_executed_total', 'Total workflows executed');
    this.counter('files_read_total', 'Total file read operations');
    this.counter('files_written_total', 'Total file write operations');
    this.counter('actions_blocked_total', 'Total actions blocked');
    this.counter('webhooks_delivered_total', 'Total webhooks delivered');
    this.counter('webhooks_failed_total', 'Total webhooks failed');

    // Initialize default gauges
    this.gauge('agents_active', 'Number of active agents');
    this.gauge('workflows_running', 'Number of running workflows');
    this.gauge('memory_usage_bytes', 'Current memory usage');
    this.gauge('cpu_usage_percent', 'Current CPU usage');
    this.gauge('connected_clients', 'Number of connected clients');

    // Initialize default histograms
    this.histogram('api_request_duration', 'API request duration in seconds');
    this.histogram('agent_task_duration', 'Agent task duration in seconds');
    this.histogram('workflow_execution_duration', 'Workflow execution duration in seconds');
  }

  // Counter operations
  counter(name, description = '') {
    if (!this.counters.has(name)) {
      this.counters.set(name, { value: 0, description });
    }
    return this.counters.get(name);
  }

  incrementCounter(name, value = 1) {
    const counter = this.counter(name);
    counter.value += value;
    counter.lastUpdated = new Date().toISOString();
    return counter.value;
  }

  resetCounter(name) {
    const counter = this.counter(name);
    counter.value = 0;
    counter.lastUpdated = new Date().toISOString();
    return 0;
  }

  getCounter(name) {
    return this.counters.get(name);
  }

  // Gauge operations
  gauge(name, description = '') {
    if (!this.gauges.has(name)) {
      this.gauges.set(name, { value: 0, description, lastUpdated: null });
    }
    return this.gauges.get(name);
  }

  setGauge(name, value) {
    const gauge = this.gauge(name);
    gauge.value = value;
    gauge.lastUpdated = new Date().toISOString();
    return value;
  }

  getGauge(name) {
    return this.gauges.get(name);
  }

  // Histogram operations
  histogram(name, description = '') {
    if (!this.histograms.has(name)) {
      this.histograms.set(name, {
        values: [],
        description,
        count: 0,
        sum: 0,
        min: Infinity,
        max: -Infinity,
        lastUpdated: null
      });
    }
    return this.histograms.get(name);
  }

  recordValue(name, value) {
    const hist = this.histogram(name);
    hist.values.push(value);
    hist.count++;
    hist.sum += value;
    hist.min = Math.min(hist.min, value);
    hist.max = Math.max(hist.max, value);
    hist.lastUpdated = new Date().toISOString();

    // Keep only last 1000 values
    if (hist.values.length > 1000) {
      const removed = hist.values.shift();
      hist.sum -= removed;
      hist.count--;
    }

    return hist;
  }

  getHistogramStats(name) {
    const hist = this.histograms.get(name);
    if (!hist || hist.values.length === 0) return null;

    const sorted = [...hist.values].sort((a, b) => a - b);
    const sum = hist.sum;
    const count = hist.count;

    return {
      count,
      sum,
      min: hist.min,
      max: hist.max,
      mean: sum / count,
      median: sorted[Math.floor(count / 2)],
      p50: sorted[Math.floor(count * 0.50)],
      p75: sorted[Math.floor(count * 0.75)],
      p90: sorted[Math.floor(count * 0.90)],
      p95: sorted[Math.floor(count * 0.95)],
      p99: sorted[Math.floor(count * 0.99)]
    };
  }

  // Timer operations
  startTimer(name) {
    this.timers.set(name, Date.now());
  }

  stopTimer(name) {
    const startTime = this.timers.get(name);
    if (!startTime) return null;

    const duration = (Date.now() - startTime) / 1000; // Convert to seconds
    this.timers.delete(name);
    this.recordValue(name, duration);
    return duration;
  }

  // Generic metric operations
  getMetric(name) {
    if (this.counters.has(name)) return { type: 'counter', ...this.counters.get(name) };
    if (this.gauges.has(name)) return { type: 'gauge', ...this.gauges.get(name) };
    if (this.histograms.has(name)) return { type: 'histogram', stats: this.getHistogramStats(name) };
    return null;
  }

  // Get all metrics
  getAllMetrics() {
    const metrics = {
      counters: {},
      gauges: {},
      histograms: {}
    };

    for (const [name, data] of this.counters) {
      metrics.counters[name] = { value: data.value, description: data.description };
    }

    for (const [name, data] of this.gauges) {
      metrics.gauges[name] = { value: data.value, description: data.description };
    }

    for (const [name] of this.histograms) {
      metrics.histograms[name] = this.getHistogramStats(name);
    }

    return metrics;
  }

  // Alert system
  createAlert(config) {
    const alertId = `alert_${this.nextAlertId++}`;

    const alert = {
      id: alertId,
      name: config.name,
      metric: config.metric,
      condition: config.condition, // 'gt', 'lt', 'eq', 'gte', 'lte'
      threshold: config.threshold,
      severity: config.severity || 'warning', // 'info', 'warning', 'critical'
      enabled: config.enabled !== false,
      triggered: false,
      lastTriggered: null,
      message: config.message || '',
      createdAt: new Date().toISOString()
    };

    this.alerts.set(alertId, alert);
    return alert;
  }

  getAlert(alertId) {
    return this.alerts.get(alertId);
  }

  getAllAlerts() {
    return [...this.alerts.values()];
  }

  getAlertsBySeverity(severity) {
    return [...this.alerts.values()].filter(a => a.severity === severity);
  }

  // Check all alerts
  checkAlerts() {
    const triggered = [];

    for (const alert of this.alerts.values()) {
      if (!alert.enabled) continue;

      let currentValue;
      if (this.counters.has(alert.metric)) {
        currentValue = this.counters.get(alert.metric).value;
      } else if (this.gauges.has(alert.metric)) {
        currentValue = this.gauges.get(alert.metric).value;
      } else {
        continue;
      }

      let isTriggered = false;
      switch (alert.condition) {
        case 'gt': isTriggered = currentValue > alert.threshold; break;
        case 'lt': isTriggered = currentValue < alert.threshold; break;
        case 'eq': isTriggered = currentValue === alert.threshold; break;
        case 'gte': isTriggered = currentValue >= alert.threshold; break;
        case 'lte': isTriggered = currentValue <= alert.threshold; break;
      }

      if (isTriggered && !alert.triggered) {
        alert.triggered = true;
        alert.lastTriggered = new Date().toISOString();
        triggered.push(alert);
      } else if (!isTriggered && alert.triggered) {
        alert.triggered = false;
      }
    }

    return triggered;
  }

  deleteAlert(alertId) {
    return this.alerts.delete(alertId);
  }

  // Prometheus-compatible metrics export
  exportPrometheus() {
    let output = '';

    // Counters
    for (const [name, data] of this.counters) {
      output += `# TYPE ${name} counter\n`;
      output += `# HELP ${name} ${data.description}\n`;
      output += `${name} ${data.value}\n\n`;
    }

    // Gauges
    for (const [name, data] of this.gauges) {
      output += `# TYPE ${name} gauge\n`;
      output += `# HELP ${name} ${data.description}\n`;
      output += `${name} ${data.value}\n\n`;
    }

    // Histograms (simplified)
    for (const [name, data] of this.histograms) {
      output += `# TYPE ${name} summary\n`;
      output += `# HELP ${name} ${data.description}\n`;
      const stats = this.getHistogramStats(name);
      if (stats) {
        output += `${name}_count ${stats.count}\n`;
        output += `${name}_sum ${stats.sum.toFixed(2)}\n`;
      }
      output += '\n';
    }

    return output;
  }

  // Get system summary
  getSummary() {
    return {
      counters: this.counters.size,
      gauges: this.gauges.size,
      histograms: this.histograms.size,
      alerts: {
        total: this.alerts.size,
        triggered: [...this.alerts.values()].filter(a => a.triggered).length
      },
      triggeredAlerts: this.checkAlerts()
    };
  }

  // Update system metrics
  updateSystemMetrics() {
    const memUsage = process.memoryUsage();
    this.setGauge('memory_usage_bytes', memUsage.heapUsed);
    this.setGauge('memory_usage_rss', memUsage.rss);

    const cpuUsage = process.cpuUsage();
    this.setGauge('cpu_usage_user', cpuUsage.user);
    this.setGauge('cpu_usage_system', cpuUsage.system);
  }
}

module.exports = { MetricsSystem };