/**
 * EventPipeline - Event Processing Pipeline
 * Chapter 5.2: Event Processing Pipeline
 */

const EventEmitter = require('./EventEmitter');

class PipelineStage {
  constructor(name, handler, options = {}) {
    this.name = name;
    this.handler = handler;
    this.priority = options.priority || 0;
    this.filter = options.filter || null;
    this.timeout = options.timeout || 5000;
    this._enabled = options.enabled !== false;
  }

  async process(event, context) {
    if (!this._enabled) return event;
    if (this.filter && !this.filter(event, context)) {
      return event;
    }

    try {
      const result = await this._withTimeout(this.handler(event, context));
      return result !== undefined ? result : event;
    } catch (err) {
      err.stage = this.name;
      throw err;
    }
  }

  async _withTimeout(promise) {
    return Promise.race([
      promise,
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Stage timeout')), this.timeout)
      )
    ]);
  }

  enable() {
    this._enabled = true;
  }

  disable() {
    this._enabled = false;
  }

  isEnabled() {
    return this._enabled;
  }
}

class EventPipeline extends EventEmitter {
  constructor(options = {}) {
    super(options);
    this._stages = [];
    this._errorHandlers = [];
    this._defaultTimeout = options.defaultTimeout || 5000;
    this._maxRetries = options.maxRetries || 0;
    this._stats = {
      processed: 0,
      failed: 0,
      retries: 0
    };
  }

  /**
   * Add stage to pipeline
   * @param {string} name - Stage name
   * @param {Function} handler - Handler function(event, context) => event
   * @param {Object} options - Stage options
   * @returns {PipelineStage}
   */
  use(name, handler, options = {}) {
    const stage = new PipelineStage(name, handler, {
      ...options,
      priority: options.priority || this._stages.length * 10
    });
    this._stages.push(stage);
    this._stages.sort((a, b) => a.priority - b.priority);
    return stage;
  }

  /**
   * Add async stage
   * @param {string} name - Stage name
   * @param {Function} handler - Async handler
   * @param {Object} options - Stage options
   * @returns {PipelineStage}
   */
  useAsync(name, handler, options = {}) {
    return this.use(name, async (event, context) => {
      const result = await handler(event, context);
      return result;
    }, { ...options, timeout: options.timeout || this._defaultTimeout });
  }

  /**
   * Add filter stage
   * @param {string} name - Stage name
   * @param {Function} filter - Filter function(event) => boolean
   * @returns {PipelineStage}
   */
  filter(name, filter) {
    return this.use(name, (event) => event, { filter });
  }

  /**
   * Add validation stage
   * @param {string} name - Stage name
   * @param {Function} validator - Validator function(event) => error|null
   * @returns {PipelineStage}
   */
  validate(name, validator) {
    return this.use(name, (event) => {
      const error = validator(event);
      if (error) {
        const err = new Error(`Validation failed at ${name}: ${error}`);
        err.validationError = error;
        throw err;
      }
      return event;
    });
  }

  /**
   * Add transformation stage
   * @param {string} name - Stage name
   * @param {Function} transformer - Transformer function(event) => event
   * @returns {PipelineStage}
   */
  transform(name, transformer) {
    return this.use(name, transformer);
  }

  /**
   * Remove stage by name
   * @param {string} name - Stage name
   * @returns {boolean}
   */
  removeStage(name) {
    const idx = this._stages.findIndex(s => s.name === name);
    if (idx !== -1) {
      this._stages.splice(idx, 1);
      return true;
    }
    return false;
  }

  /**
   * Get stage by name
   * @param {string} name - Stage name
   * @returns {PipelineStage|undefined}
   */
  getStage(name) {
    return this._stages.find(s => s.name === name);
  }

  /**
   * Process event through pipeline
   * @param {Object} event - Event to process
   * @param {Object} context - Context data
   * @returns {Promise<Object>}
   */
  async process(event, context = {}) {
    const pipelineContext = {
      ...context,
      pipeline: this,
      startTime: Date.now()
    };

    let currentEvent = { ...event };
    let lastError = null;

    for (let attempt = 0; attempt <= this._maxRetries; attempt++) {
      try {
        for (const stage of this._stages) {
          currentEvent = await stage.process(currentEvent, pipelineContext);
        }

        this._stats.processed++;
        this.emit('success', currentEvent, pipelineContext);
        return currentEvent;

      } catch (err) {
        lastError = err;

        if (attempt < this._maxRetries) {
          this._stats.retries++;
          this.emit('retry', { event: currentEvent, error: err, attempt });
          await this._wait(Math.pow(2, attempt) * 100);
        } else {
          this._stats.failed++;
          this._handleError(err, currentEvent, pipelineContext);
        }
      }
    }

    throw lastError;
  }

  /**
   * Process event synchronously
   * @param {Object} event - Event to process
   * @param {Object} context - Context data
   * @returns {Object}
   */
  processSync(event, context = {}) {
    const pipelineContext = {
      ...context,
      pipeline: this,
      startTime: Date.now()
    };

    let currentEvent = { ...event };

    for (const stage of this._stages) {
      if (stage.filter && !stage.filter(currentEvent, pipelineContext)) {
        continue;
      }
      currentEvent = stage.handler(currentEvent, pipelineContext);
    }

    return currentEvent;
  }

  /**
   * Add error handler
   * @param {Function} handler - Error handler function
   * @returns {this}
   */
  onError(handler) {
    this._errorHandlers.push(handler);
    return this;
  }

  /**
   * Handle pipeline error
   * @param {Error} err - Error object
   * @param {Object} event - Current event
   * @param {Object} context - Pipeline context
   */
  _handleError(err, event, context) {
    context.error = err;
    context.endTime = Date.now();
    context.duration = context.endTime - context.startTime;

    this.emit('error', err, event, context);

    for (const handler of this._errorHandlers) {
      try {
        handler(err, event, context);
      } catch (handlerErr) {
        console.error('Error handler failed:', handlerErr);
      }
    }
  }

  /**
   * Get pipeline stats
   * @returns {Object}
   */
  getStats() {
    return { ...this._stats };
  }

  /**
   * Reset stats
   */
  resetStats() {
    this._stats = { processed: 0, failed: 0, retries: 0 };
  }

  /**
   * Get stage count
   * @returns {number}
   */
  getStageCount() {
    return this._stages.length;
  }

  /**
   * Clear all stages
   */
  clear() {
    this._stages = [];
  }

  /**
   * Wait helper
   * @param {number} ms - Milliseconds
   */
  _wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

/**
 * Create middleware factory
 * @param {Object} options - Middleware options
 * @returns {Function}
 */
function createMiddleware(options = {}) {
  return function middleware(pipeline) {
    if (options.name) {
      pipeline.use(options.name, options.handler, options);
    }
  };
}

module.exports = {
  EventPipeline,
  PipelineStage,
  createMiddleware
};