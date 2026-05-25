/**
 * Webhook System
 * Event-driven automation with HTTP callbacks
 */

class WebhookSystem {
  constructor() {
    this.webhooks = new Map();
    this.events = new Map();
    this.deliveryLogs = new Map();
    this.nextWebhookId = 1;
    this.nextEventId = 1;
    this.initDefaultWebhooks();
  }

  initDefaultWebhooks() {
    // Register default event types
    this.registerEventType('agent.created', 'When a new agent is created');
    this.registerEventType('agent.started', 'When an agent starts running');
    this.registerEventType('agent.stopped', 'When an agent stops');
    this.registerEventType('agent.error', 'When an agent encounters an error');
    this.registerEventType('workflow.started', 'When a workflow starts');
    this.registerEventType('workflow.completed', 'When a workflow completes');
    this.registerEventType('workflow.failed', 'When a workflow fails');
    this.registerEventType('file.created', 'When a file is created');
    this.registerEventType('file.modified', 'When a file is modified');
    this.registerEventType('file.deleted', 'When a file is deleted');
    this.registerEventType('action.blocked', 'When an action is blocked by governance');
    this.registerEventType('rate_limit.exceeded', 'When rate limit is exceeded');
  }

  registerEventType(eventType, description) {
    this.events.set(eventType, {
      type: eventType,
      description,
      webhooks: [],
      count: 0
    });
  }

  // Register a webhook
  register(config) {
    const webhookId = `wh_${this.nextWebhookId++}`;

    const webhook = {
      id: webhookId,
      name: config.name || `Webhook ${webhookId}`,
      url: config.url,
      events: config.events || [],
      secret: config.secret || this.generateSecret(),
      method: config.method || 'POST',
      headers: config.headers || {},
      enabled: config.enabled !== false,
      timeout: config.timeout || 30000,
      retryOnFailure: config.retryOnFailure !== false,
      maxRetries: config.maxRetries || 3,
      retryDelay: config.retryDelay || 5000,
      lastTriggered: null,
      lastStatus: null,
      lastError: null,
      triggerCount: 0,
      createdAt: new Date().toISOString()
    };

    // Validate URL
    try {
      const parsed = new URL(webhook.url);
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        return { error: 'Invalid URL protocol' };
      }
    } catch (e) {
      return { error: 'Invalid URL' };
    }

    // Add to event subscriptions
    for (const eventType of webhook.events) {
      if (this.events.has(eventType)) {
        this.events.get(eventType).webhooks.push(webhookId);
      }
    }

    this.webhooks.set(webhookId, webhook);
    return webhook;
  }

  generateSecret() {
    return 'whsec_' + Math.random().toString(36).substring(2, 15) +
           Math.random().toString(36).substring(2, 15);
  }

  // Trigger webhooks for an event
  async trigger(eventType, payload) {
    const event = this.events.get(eventType);
    if (!event) return { error: 'Unknown event type' };

    event.count++;
    const results = [];

    for (const webhookId of event.webhooks) {
      const webhook = this.webhooks.get(webhookId);
      if (!webhook || !webhook.enabled) continue;

      const result = await this.deliver(webhook, eventType, payload);
      results.push({ webhookId, ...result });

      webhook.lastTriggered = new Date().toISOString();
      webhook.triggerCount++;
    }

    return { eventType, triggered: results.length, results };
  }

  // Deliver webhook
  async deliver(webhook, eventType, payload) {
    const deliveryId = `delivery_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const delivery = {
      id: deliveryId,
      webhookId: webhook.id,
      webhookName: webhook.name,
      eventType,
      payload,
      url: webhook.url,
      method: webhook.method,
      status: 'pending',
      attempts: 0,
      maxAttempts: webhook.maxRetries + 1,
      createdAt: new Date().toISOString(),
      response: null,
      error: null
    };

    if (!this.deliveryLogs.has(webhook.id)) {
      this.deliveryLogs.set(webhook.id, []);
    }
    this.deliveryLogs.get(webhook.id).unshift(delivery);

    // Attempt delivery
    let lastError;
    for (let attempt = 0; attempt <= webhook.maxRetries; attempt++) {
      delivery.attempts++;
      delivery.status = 'attempting';

      try {
        const result = await this.attemptDelivery(webhook, eventType, payload, attempt > 0);
        delivery.status = 'delivered';
        delivery.response = result;
        webhook.lastStatus = 200;

        return { success: true, deliveryId, attempts: delivery.attempts };
      } catch (e) {
        lastError = e.message;
        delivery.error = e.message;
        webhook.lastError = e.message;

        if (attempt < webhook.maxRetries && webhook.retryOnFailure) {
          await new Promise(r => setTimeout(r, webhook.retryDelay));
        }
      }
    }

    delivery.status = 'failed';
    webhook.lastStatus = 500;
    return { success: false, deliveryId, error: lastError, attempts: delivery.attempts };
  }

  // Attempt to deliver webhook
  async attemptDelivery(webhook, eventType, payload, isRetry) {
    const https = require('https');
    const http = require('http');
    const crypto = require('crypto');

    const body = JSON.stringify({
      event: eventType,
      timestamp: new Date().toISOString(),
      data: payload,
      retry: isRetry
    });

    // Generate signature
    const signature = crypto
      .createHmac('sha256', webhook.secret)
      .update(body)
      .digest('hex');

    const headers = {
      'Content-Type': 'application/json',
      'X-Webhook-Signature': signature,
      'X-Webhook-Event': eventType,
      'User-Agent': 'AgentOS-Webhook/1.0',
      ...webhook.headers
    };

    const parsed = new URL(webhook.url);
    const client = parsed.protocol === 'https:' ? https : http;

    return new Promise((resolve, reject) => {
      const options = {
        hostname: parsed.hostname,
        port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
        path: parsed.pathname + parsed.search,
        method: webhook.method,
        headers,
        timeout: webhook.timeout
      };

      const req = client.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve({ status: res.statusCode, body: data });
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      });

      req.on('error', reject);
      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });

      req.write(body);
      req.end();
    });
  }

  // Get webhook
  getWebhook(webhookId) {
    return this.webhooks.get(webhookId);
  }

  // Get all webhooks
  getAllWebhooks() {
    return [...this.webhooks.values()];
  }

  // Update webhook
  updateWebhook(webhookId, updates) {
    const webhook = this.webhooks.get(webhookId);
    if (!webhook) return { error: 'Webhook not found' };

    // Update allowed fields
    const allowed = ['name', 'url', 'events', 'enabled', 'timeout', 'retryOnFailure', 'maxRetries', 'headers'];
    for (const key of allowed) {
      if (updates[key] !== undefined) {
        webhook[key] = updates[key];
      }
    }

    // Update event subscriptions
    if (updates.events) {
      // Remove from old events
      for (const event of this.events.values()) {
        event.webhooks = event.webhooks.filter(id => id !== webhookId);
      }
      // Add to new events
      for (const eventType of webhook.events) {
        if (this.events.has(eventType)) {
          this.events.get(eventType).webhooks.push(webhookId);
        }
      }
    }

    return webhook;
  }

  // Delete webhook
  deleteWebhook(webhookId) {
    const webhook = this.webhooks.get(webhookId);
    if (!webhook) return { error: 'Webhook not found' };

    // Remove from event subscriptions
    for (const event of this.events.values()) {
      event.webhooks = event.webhooks.filter(id => id !== webhookId);
    }

    this.webhooks.delete(webhookId);
    this.deliveryLogs.delete(webhookId);

    return { success: true };
  }

  // Get delivery logs
  getDeliveryLogs(webhookId, limit = 10) {
    const logs = this.deliveryLogs.get(webhookId) || [];
    return logs.slice(0, limit);
  }

  // Get all delivery logs
  getAllDeliveryLogs(limit = 50) {
    const all = [];
    for (const logs of this.deliveryLogs.values()) {
      all.push(...logs);
    }
    return all.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt)).slice(0, limit);
  }

  // Get event types
  getEventTypes() {
    return [...this.events.values()];
  }

  // Test webhook
  async testWebhook(webhookId) {
    const webhook = this.webhooks.get(webhookId);
    if (!webhook) return { error: 'Webhook not found' };

    const testPayload = {
      test: true,
      message: 'This is a test webhook from AgentOS',
      webhookId: webhook.id
    };

    return await this.deliver(webhook, 'webhook.test', testPayload);
  }

  // Get stats
  getStats() {
    let totalDeliveries = 0;
    let successfulDeliveries = 0;
    let failedDeliveries = 0;

    for (const logs of this.deliveryLogs.values()) {
      for (const log of logs) {
        totalDeliveries++;
        if (log.status === 'delivered') successfulDeliveries++;
        if (log.status === 'failed') failedDeliveries++;
      }
    }

    return {
      totalWebhooks: this.webhooks.size,
      enabledWebhooks: [...this.webhooks.values()].filter(w => w.enabled).length,
      eventTypes: this.events.size,
      totalDeliveries,
      successfulDeliveries,
      failedDeliveries,
      successRate: totalDeliveries > 0
        ? ((successfulDeliveries / totalDeliveries) * 100).toFixed(1) + '%'
        : '0%'
    };
  }
}

module.exports = { WebhookSystem };