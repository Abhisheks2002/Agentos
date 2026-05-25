/**
 * EventQueue - Async Event Processing Queue
 */

class EventQueue {
  constructor(options = {}) {
    this._queue = [];
    this._processing = false;
    this._maxSize = options.maxSize || 1000;
    this._ concurrency = options.concurrency || 1;
  }

  /**
   * Add handler to queue
   * @param {Function} handler - Handler to enqueue
   */
  enqueue(handler) {
    if (this._queue.length >= this._maxSize) {
      console.warn('Event queue full, dropping handler');
      return false;
    }
    this._queue.push(handler);
    if (!this._processing) {
      this._process();
    }
    return true;
  }

  /**
   * Process queue
   */
  async _process() {
    if (this._processing) return;
    this._processing = true;

    while (this._queue.length > 0) {
      const handler = this._queue.shift();
      try {
        await handler();
      } catch (err) {
        console.error('Event queue handler error:', err);
      }
    }

    this._processing = false;
  }

  /**
   * Clear queue
   */
  clear() {
    this._queue = [];
  }

  /**
   * Get queue size
   * @returns {number}
   */
  size() {
    return this._queue.length;
  }

  /**
   * Check if queue is empty
   * @returns {boolean}
   */
  isEmpty() {
    return this._queue.length === 0;
  }
}

module.exports = EventQueue;