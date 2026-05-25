/**
 * Task Scheduler
 * Manages scheduled tasks and cron jobs
 */

class TaskScheduler {
  constructor() {
    this.jobs = new Map();
    this.runningJobs = new Map();
    this.executionHistory = new Map();
    this.listeners = new Map();
    this.nextJobId = 1;
    this.startScheduler();
  }

  // Parse cron expression
  parseCron(cronExpr) {
    const parts = cronExpr.split(' ');
    if (parts.length !== 5) return null;

    const cron = {
      minute: parts[0],
      hour: parts[1],
      dayOfMonth: parts[2],
      month: parts[3],
      dayOfWeek: parts[4]
    };

    // Expand cron fields
    const expand = (field, min, max) => {
      if (field === '*') return { start: min, end: max, step: 1 };
      if (field.includes('/')) {
        const [range, step] = field.split('/');
        return { start: range === '*' ? min : parseInt(range), end: max, step: parseInt(step) };
      }
      if (field.includes('-')) {
        const [start, end] = field.split('-');
        return { start: parseInt(start), end: parseInt(end), step: 1 };
      }
      if (field.includes(',')) {
        return { values: field.split(',').map(Number), step: 1 };
      }
      return { values: [parseInt(field)], step: 1 };
    };

    return {
      minute: expand(cron.minute, 0, 59),
      hour: expand(cron.hour, 0, 23),
      dayOfMonth: expand(cron.dayOfMonth, 1, 31),
      month: expand(cron.month, 1, 12),
      dayOfWeek: expand(cron.dayOfWeek, 0, 6)
    };
  }

  // Check if cron matches current time
  matchesCron(cron, date) {
    const d = {
      minute: date.getMinutes(),
      hour: date.getHours(),
      dayOfMonth: date.getDate(),
      month: date.getMonth() + 1,
      dayOfWeek: date.getDay()
    };

    const match = (field) => {
      if (field.values) return field.values.includes(d[field.key]);
      if (field.values === undefined) {
        const v = d[field.key];
        if (field.start !== undefined) {
          for (let i = field.start; i <= field.end; i += field.step) {
            if (v === i) return true;
          }
        }
      }
      return false;
    };

    return (
      match({ ...cron.minute, key: 'minute' }) &&
      match({ ...cron.hour, key: 'hour' }) &&
      match({ ...cron.dayOfMonth, key: 'dayOfMonth' }) &&
      match({ ...cron.month, key: 'month' }) &&
      match({ ...cron.dayOfWeek, key: 'dayOfWeek' })
    );
  }

  // Schedule a new job
  schedule(cronExpr, callback, options = {}) {
    const cron = this.parseCron(cronExpr);
    if (!cron) return null;

    const jobId = `job_${this.nextJobId++}`;
    const job = {
      id: jobId,
      name: options.name || `Job ${jobId}`,
      cron: cronExpr,
      cronParsed: cron,
      callback,
      description: options.description || '',
      enabled: options.enabled !== false,
      timeout: options.timeout || 300000,
      retries: options.retries || 0,
      retryDelay: options.retryDelay || 5000,
      maxHistory: options.maxHistory || 50,
      lastRun: null,
      nextRun: this.getNextRunTime(cron),
      runCount: 0,
      createdAt: new Date().toISOString()
    };

    this.jobs.set(jobId, job);
    return job;
  }

  // Calculate next run time
  getNextRunTime(cron) {
    const now = new Date();
    for (let i = 0; i < 1000; i++) {
      const check = new Date(now.getTime() + i * 60000);
      if (this.matchesCron(cron, check)) {
        return check;
      }
    }
    return null;
  }

  // Start the scheduler
  startScheduler() {
    if (this.schedulerInterval) return;

    this.schedulerInterval = setInterval(() => {
      const now = new Date();
      for (const [jobId, job] of this.jobs) {
        if (!job.enabled) continue;

        if (this.matchesCron(job.cronParsed, now)) {
          this.executeJob(jobId);
        }
      }
    }, 60000); // Check every minute
  }

  // Execute a job
  async executeJob(jobId, manual = false) {
    const job = this.jobs.get(jobId);
    if (!job) return { error: 'Job not found' };

    if (!manual && this.runningJobs.has(jobId)) {
      return { error: 'Job already running' };
    }

    const executionId = `exec_${Date.now()}`;
    const execution = {
      id: executionId,
      jobId,
      jobName: job.name,
      startTime: new Date().toISOString(),
      endTime: null,
      status: 'running',
      manual,
      result: null,
      error: null
    };

    this.runningJobs.set(jobId, execution);
    job.lastRun = new Date().toISOString();
    job.runCount++;

    // Add to history
    if (!this.executionHistory.has(jobId)) {
      this.executionHistory.set(jobId, []);
    }
    const history = this.executionHistory.get(jobId);
    history.unshift(execution);
    if (history.length > job.maxHistory) history.pop();

    // Execute with timeout
    let result;
    try {
      result = await Promise.race([
        job.callback(),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error('Job timeout')), job.timeout)
        )
      ]);

      execution.status = 'completed';
      execution.result = result;
      this.emit('jobComplete', { job, execution, result });
    } catch (error) {
      execution.status = 'failed';
      execution.error = error.message;

      if (job.retries > 0) {
        for (let i = 0; i < job.retries; i++) {
          await new Promise(r => setTimeout(r, job.retryDelay));
          try {
            result = await job.callback();
            execution.status = 'completed';
            execution.result = result;
            execution.retried = true;
            break;
          } catch (e) {
            execution.lastError = e.message;
          }
        }
      }

      this.emit('jobFailed', { job, execution, error: execution.error });
    }

    execution.endTime = new Date().toISOString();
    this.runningJobs.delete(jobId);

    // Update next run
    job.nextRun = this.getNextRunTime(job.cronParsed);

    this.emit('jobExecuted', { job, execution });

    return { executionId, status: execution.status, result };
  }

  // Get job info
  getJob(jobId) {
    const job = this.jobs.get(jobId);
    if (!job) return null;

    return {
      ...job,
      isRunning: this.runningJobs.has(jobId),
      nextRun: job.nextRun,
      lastRun: job.lastRun
    };
  }

  // Get all jobs
  getAllJobs() {
    const jobs = [];
    for (const [id, job] of this.jobs) {
      jobs.push(this.getJob(id));
    }
    return jobs;
  }

  // Enable/disable job
  setJobEnabled(jobId, enabled) {
    const job = this.jobs.get(jobId);
    if (!job) return { error: 'Job not found' };

    job.enabled = enabled;
    return { success: true, enabled };
  }

  // Delete job
  deleteJob(jobId) {
    if (!this.jobs.has(jobId)) return { error: 'Job not found' };

    this.jobs.delete(jobId);
    this.executionHistory.delete(jobId);
    return { success: true };
  }

  // Get job history
  getJobHistory(jobId, limit = 10) {
    const history = this.executionHistory.get(jobId) || [];
    return history.slice(0, limit);
  }

  // Get all execution history
  getAllHistory(limit = 50) {
    const all = [];
    for (const history of this.executionHistory.values()) {
      all.push(...history);
    }
    return all.sort((a, b) => new Date(b.startTime) - new Date(a.startTime)).slice(0, limit);
  }

  // Event emitter
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  emit(event, data) {
    const callbacks = this.listeners.get(event) || [];
    for (const cb of callbacks) {
      try {
        cb(data);
      } catch (e) {
        console.error('Scheduler event error:', e);
      }
    }
  }

  // Get scheduler stats
  getStats() {
    let totalRuns = 0;
    let failedRuns = 0;

    for (const history of this.executionHistory.values()) {
      for (const exec of history) {
        totalRuns++;
        if (exec.status === 'failed') failedRuns++;
      }
    }

    return {
      totalJobs: this.jobs.size,
      enabledJobs: [...this.jobs.values()].filter(j => j.enabled).length,
      runningJobs: this.runningJobs.size,
      totalExecutions: totalRuns,
      failedExecutions: failedRuns,
      successRate: totalRuns > 0 ? ((totalRuns - failedRuns) / totalRuns * 100).toFixed(1) + '%' : '0%'
    };
  }

  // Stop scheduler
  stop() {
    if (this.schedulerInterval) {
      clearInterval(this.schedulerInterval);
      this.schedulerInterval = null;
    }
  }
}

module.exports = { TaskScheduler };