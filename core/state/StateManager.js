/**
 * StateManager - Reactive State Management System
 * Chapter 4: Advanced State Management
 */

const { EventEmitter } = require('../events/EventEmitter');

class Observable {
  constructor(value) {
    this._value = value;
    this._subscribers = new Set();
  }

  get() {
    return this._value;
  }

  set(newValue) {
    const oldValue = this._value;
    if (oldValue === newValue) return;

    this._value = newValue;
    this._notify(oldValue, newValue);
  }

  subscribe(callback) {
    this._subscribers.add(callback);
    return () => this._subscribers.delete(callback);
  }

  _notify(oldValue, newValue) {
    for (const callback of this._subscribers) {
      try {
        callback(newValue, oldValue);
      } catch (err) {
        console.error('Observable subscriber error:', err);
      }
    }
  }
}

class Computed {
  constructor(computeFn, dependencies = []) {
    this._computeFn = computeFn;
    this._dependencies = dependencies;
    this._value = undefined;
    this._subscribers = new Set();
    this._dirty = true;

    this._dependencyUnsubscribe = [];
    this._setupDependencies();
    this._compute();
  }

  _setupDependencies() {
    for (const dep of this._dependencies) {
      const unsubscribe = dep.subscribe(() => {
        this._dirty = true;
        this._compute();
      });
      this._dependencyUnsubscribe.push(unsubscribe);
    }
  }

  _compute() {
    const oldValue = this._value;
    try {
      const values = this._dependencies.map(d => d.get());
      this._value = this._computeFn(...values);
      this._dirty = false;
      this._notify(oldValue, this._value);
    } catch (err) {
      console.error('Computed value error:', err);
    }
  }

  get() {
    if (this._dirty) {
      this._compute();
    }
    return this._value;
  }

  subscribe(callback) {
    this._subscribers.add(callback);
    return () => this._subscribers.delete(callback);
  }

  _notify(oldValue, newValue) {
    if (oldValue !== newValue) {
      for (const callback of this._subscribers) {
        try {
          callback(newValue, oldValue);
        } catch (err) {
          console.error('Computed subscriber error:', err);
        }
      }
    }
  }

  dispose() {
    for (const unsub of this._dependencyUnsubscribe) {
      unsub();
    }
    this._subscribers.clear();
  }
}

class StateManager extends EventEmitter {
  constructor(options = {}) {
    super();
    this._state = new Map();
    this._computeds = new Map();
    this._middleware = options.middleware || [];
    this._batchDepth = 0;
    this._batchCallbacks = [];
    this._name = options.name || 'StateManager';

    // Emit state changes as events
    this.on('change', () => {});
  }

  /**
   * Create or get an observable state value
   * @param {string} key - State key
   * @param {*} initialValue - Initial value
   * @returns {Observable}
   */
  state(key, initialValue) {
    if (!this._state.has(key)) {
      this._state.set(key, new Observable(initialValue));
    }
    return this._state.get(key);
  }

  /**
   * Get current value of a state key
   * @param {string} key - State key
   * @returns {*}
   */
  get(key) {
    const observable = this._state.get(key);
    return observable ? observable.get() : undefined;
  }

  /**
   * Set value for a state key
   * @param {string} key - State key
   * @param {*} value - New value
   */
  set(key, value) {
    const observable = this._state.get(key);
    if (observable) {
      const oldValue = observable.get();
      observable.set(value);
      this._emitChange(key, value, oldValue);
    } else {
      this._state.set(key, new Observable(value));
      this._emitChange(key, value, undefined);
    }
  }

  /**
   * Create a computed value that auto-updates when dependencies change
   * @param {string} key - Computed value key
   * @param {Function} computeFn - Function to compute value
   * @param {string[]} dependencyKeys - Keys to depend on
   * @returns {Computed}
   */
  computed(key, computeFn, dependencyKeys) {
    const dependencies = dependencyKeys
      .map(k => this._state.get(k))
      .filter(Boolean);

    const computed = new Computed(computeFn, dependencies);
    this._computeds.set(key, computed);
    return computed;
  }

  /**
   * Get computed value
   * @param {string} key - Computed key
   * @returns {*}
   */
  getComputed(key) {
    const computed = this._computeds.get(key);
    return computed ? computed.get() : undefined;
  }

  /**
   * Subscribe to a state key
   * @param {string} key - State key
   * @param {Function} callback - Callback(newValue, oldValue)
   * @returns {Function} Unsubscribe function
   */
  subscribe(key, callback) {
    const observable = this._state.get(key);
    if (observable) {
      return observable.subscribe(callback);
    }
    return () => {};
  }

  /**
   * Subscribe to computed value
   * @param {string} key - Computed key
   * @param {Function} callback - Callback(newValue, oldValue)
   * @returns {Function} Unsubscribe function
   */
  subscribeComputed(key, callback) {
    const computed = this._computeds.get(key);
    if (computed) {
      return computed.subscribe(callback);
    }
    return () => {};
  }

  /**
   * Batch multiple state updates
   * @param {Function} callback - Function that performs multiple sets
   */
  batch(callback) {
    this._batchDepth++;
    try {
      callback();
    } finally {
      this._batchDepth--;
      if (this._batchDepth === 0) {
        this._flushBatch();
      }
    }
  }

  _emitChange(key, newValue, oldValue) {
    const changeEvent = { key, newValue, oldValue, timestamp: Date.now() };

    // Apply middleware
    for (const mw of this._middleware) {
      if (mw.onChange) {
        mw.onChange(changeEvent);
      }
    }

    if (this._batchDepth > 0) {
      this._batchCallbacks.push(changeEvent);
    } else {
      this.emit('change', changeEvent);
      this.emit(`change:${key}`, newValue, oldValue);
    }
  }

  _flushBatch() {
    const callbacks = [...this._batchCallbacks];
    this._batchCallbacks = [];

    for (const event of callbacks) {
      this.emit('change', event);
      this.emit(`change:${event.key}`, event.newValue, event.oldValue);
    }
  }

  /**
   * Add middleware to state changes
   * @param {Object} middleware - Middleware with onChange method
   */
  useMiddleware(middleware) {
    this._middleware.push(middleware);
  }

  /**
   * Get all state as object
   * @returns {Object}
   */
  toJSON() {
    const obj = {};
    for (const [key, observable] of this._state) {
      obj[key] = observable.get();
    }
    return obj;
  }

  /**
   * Load state from object
   * @param {Object} data - State object
   */
  fromJSON(data) {
    this.batch(() => {
      for (const [key, value] of Object.entries(data)) {
        this.set(key, value);
      }
    });
  }

  /**
   * Get state keys
   * @returns {string[]}
   */
  keys() {
    return Array.from(this._state.keys());
  }

  /**
   * Check if state key exists
   * @param {string} key - State key
   * @returns {boolean}
   */
  has(key) {
    return this._state.has(key);
  }

  /**
   * Remove state key
   * @param {string} key - State key
   */
  delete(key) {
    const observable = this._state.get(key);
    if (observable) {
      const oldValue = observable.get();
      this._state.delete(key);
      this._emitChange(key, undefined, oldValue);
    }
  }

  /**
   * Clear all state
   */
  clear() {
    const keys = this.keys();
    this.batch(() => {
      for (const key of keys) {
        this.delete(key);
      }
    });
  }

  /**
   * Dispose manager and cleanup
   */
  dispose() {
    for (const computed of this._computeds.values()) {
      computed.dispose();
    }
    this._state.clear();
    this._computeds.clear();
    this._middleware = [];
    super.dispose();
  }
}

module.exports = { StateManager, Observable, Computed };