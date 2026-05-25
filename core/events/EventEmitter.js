/**
 * EventEmitter - Event System Fundamentals
 * Chapter 5: Event-Driven Architecture
 */

const EventQueue = require('./EventQueue');

class EventEmitter {
  constructor(options = {}) {
    this._events = new Map();
    this._onceEvents = new Map();
    this._maxListeners = options.maxListeners || 100;
    this._eventQueue = options.async ? new EventQueue() : null;
    this._priority = options.priority || 0;
    this._filters = [];
    this._globalFilters = [];
    this._closed = false;
  }

  /**
   * Register event listener
   * @param {string} event - Event name
   * @param {Function} listener - Listener function
   * @returns {this}
   */
  on(event, listener) {
    if (this._closed) return this;
    if (!this._events.has(event)) {
      this._events.set(event, new Set());
    }
    const listeners = this._events.get(event);
    if (listeners.size >= this._maxListeners) {
      console.warn(`Warning: Max listeners (${this._maxListeners}) exceeded for ${event}`);
    }
    listeners.add(listener);
    return this;
  }

  /**
   * Register one-time event listener
   * @param {string} event - Event name
   * @param {Function} listener - Listener function
   * @returns {this}
   */
  once(event, listener) {
    if (this._closed) return this;
    if (!this._onceEvents.has(event)) {
      this._onceEvents.set(event, new Set());
    }
    const wrappedListener = (...args) => {
      this._onceEvents.get(event).delete(wrappedListener);
      listener.apply(this, args);
    };
    this._onceEvents.get(event).add(wrappedListener);
    this.on(event, wrappedListener);
    return this;
  }

  /**
   * Register listener for multiple events
   * @param {string[]} events - Event names
   * @param {Function} listener - Listener function
   * @returns {this}
   */
  onMany(events, listener) {
    for (const event of events) {
      this.on(event, listener);
    }
    return this;
  }

  /**
   * Unregister event listener
   * @param {string} event - Event name
   * @param {Function} listener - Listener function
   * @returns {this}
   */
  off(event, listener) {
    const listeners = this._events.get(event);
    if (listeners) {
      listeners.delete(listener);
    }
    const onceListeners = this._onceEvents.get(event);
    if (onceListeners) {
      onceListeners.delete(listener);
    }
    return this;
  }

  /**
   * Unregister all listeners for event
   * @param {string} event - Event name
   * @returns {this}
   */
  removeAllListeners(event) {
    if (event) {
      this._events.delete(event);
      this._onceEvents.delete(event);
    } else {
      this._events.clear();
      this._onceEvents.clear();
    }
    return this;
  }

  /**
   * Emit event synchronously
   * @param {string} event - Event name
   * @param {...*} args - Arguments to pass to listeners
   * @returns {boolean}
   */
  emit(event, ...args) {
    if (this._closed) return false;

    // Apply event filters
    for (const filter of this._globalFilters) {
      if (!filter(event, ...args)) {
        return false;
      }
    }
    for (const filter of this._filters) {
      if (!filter(event, ...args)) {
        return false;
      }
    }

    let handled = false;
    const listeners = this._events.get(event);
    const onceListeners = this._onceEvents.get(event);

    // Process regular listeners
    if (listeners) {
      for (const listener of listeners) {
        try {
          listener.apply(this, args);
          handled = true;
        } catch (err) {
          console.error(`Error in event listener for ${event}:`, err);
        }
      }
    }

    // Process one-time listeners
    if (onceListeners) {
      for (const listener of onceListeners) {
        try {
          listener.apply(this, args);
          handled = true;
        } catch (err) {
          console.error(`Error in once event listener for ${event}:`, err);
        }
      }
      this._onceEvents.delete(event);
    }

    return handled;
  }

  /**
   * Emit event asynchronously
   * @param {string} event - Event name
   * @param {...*} args - Arguments to pass to listeners
   */
  asyncEmit(event, ...args) {
    if (this._eventQueue) {
      this._eventQueue.enqueue(() => this.emit(event, ...args));
    } else {
      return Promise.resolve().then(() => this.emit(event, ...args));
    }
  }

  /**
   * Add event filter
   * @param {Function} filter - Filter function(event, ...args) => boolean
   * @returns {this}
   */
  addFilter(filter) {
    this._filters.push(filter);
    return this;
  }

  /**
   * Remove event filter
   * @param {Function} filter - Filter function to remove
   * @returns {this}
   */
  removeFilter(filter) {
    const idx = this._filters.indexOf(filter);
    if (idx !== -1) this._filters.splice(idx, 1);
    return this;
  }

  /**
   * Add global filter (affects all emitters)
   * @param {Function} filter - Filter function
   * @static
   */
  static addGlobalFilter(filter) {
    EventEmitter._globalFilters.push(filter);
  }

  /**
   * Get listener count for event
   * @param {string} event - Event name
   * @returns {number}
   */
  listenerCount(event) {
    const regular = this._events.get(event)?.size || 0;
    const once = this._onceEvents.get(event)?.size || 0;
    return regular + once;
  }

  /**
   * Get all event names
   * @returns {string[]}
   */
  eventNames() {
    return Array.from(new Set([
      ...this._events.keys(),
      ...this._onceEvents.keys()
    ]));
  }

  /**
   * Get listeners for event
   * @param {string} event - Event name
   * @returns {Function[]}
   */
  listeners(event) {
    const result = [];
    const regular = this._events.get(event);
    const once = this._onceEvents.get(event);
    if (regular) result.push(...regular);
    if (once) result.push(...once);
    return result;
  }

  /**
   * Set max listeners
   * @param {number} n - Max listener count
   * @returns {this}
   */
  setMaxListeners(n) {
    this._maxListeners = n;
    return this;
  }

  /**
   * Get max listeners
   * @returns {number}
   */
  getMaxListeners() {
    return this._maxListeners;
  }

  /**
   * Close the emitter
   */
  close() {
    this._closed = true;
    this.removeAllListeners();
  }

  /**
   * Dispose and cleanup
   */
  dispose() {
    this.close();
    this._filters = [];
    if (this._eventQueue) {
      this._eventQueue.clear();
    }
  }
}

// Static global filters
EventEmitter._globalFilters = [];

module.exports = EventEmitter;