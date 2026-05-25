/**
 * StatePersistence - Persistence & Serialization
 * Chapter 4.3: Persistence & Serialization
 */

const zlib = require('zlib');

class StatePersistence {
  constructor(options = {}) {
    this._storage = options.storage || null;
    this._compression = options.compression !== false;
    this._encoding = options.encoding || 'utf8';
    this._prettyPrint = options.prettyPrint || false;
  }

  /**
   * Set storage backend
   * @param {Object} storage - Storage with getItem/setItem/removeItem
   */
  setStorage(storage) {
    this._storage = storage;
  }

  /**
   * Save state with optional compression
   * @param {StateManager} manager - State manager
   * @param {string} key - Storage key
   * @returns {Promise<void>}
   */
  async save(manager, key) {
    if (!this._storage) {
      throw new Error('No storage configured');
    }

    const data = manager.toJSON();
    const serialized = this._prettyPrint
      ? JSON.stringify(data, null, 2)
      : JSON.stringify(data);

    let payload;
    if (this._compression) {
      payload = zlib.deflateSync(serialized);
    } else {
      payload = serialized;
    }

    const storageData = {
      version: 1,
      timestamp: Date.now(),
      compressed: this._compression,
      data: this._compression
        ? payload.toString('base64')
        : payload
    };

    await this._storage.setItem(key, JSON.stringify(storageData));
  }

  /**
   * Load state from storage
   * @param {StateManager} manager - State manager
   * @param {string} key - Storage key
   * @returns {Promise<boolean>}
   */
  async load(manager, key) {
    if (!this._storage) {
      throw new Error('No storage configured');
    }

    const stored = await this._storage.getItem(key);
    if (!stored) {
      return false;
    }

    try {
      const storageData = JSON.parse(stored);
      let serialized;

      if (storageData.compressed) {
        const buffer = Buffer.from(storageData.data, 'base64');
        serialized = zlib.inflateSync(buffer).toString(this._encoding);
      } else {
        serialized = storageData.data;
      }

      const data = JSON.parse(serialized);
      manager.fromJSON(data);
      return true;
    } catch (err) {
      console.error('Failed to load state:', err);
      return false;
    }
  }

  /**
   * Export state to file
   * @param {StateManager} manager - State manager
   * @param {string} filepath - File path
   * @returns {Promise<void>}
   */
  async exportToFile(manager, filepath) {
    const fs = require('fs').promises;
    const data = manager.toJSON();
    const serialized = this._prettyPrint
      ? JSON.stringify(data, null, 2)
      : JSON.stringify(data);

    let payload;
    if (this._compression) {
      payload = zlib.deflateSync(serialized);
      await fs.writeFile(filepath, payload);
    } else {
      await fs.writeFile(filepath, serialized, this._encoding);
    }
  }

  /**
   * Import state from file
   * @param {StateManager} manager - State manager
   * @param {string} filepath - File path
   * @returns {Promise<boolean>}
   */
  async importFromFile(manager, filepath) {
    const fs = require('fs').promises;

    try {
      const buffer = await fs.readFile(filepath);

      // Try to decompress
      let serialized;
      try {
        serialized = zlib.inflateSync(buffer).toString(this._encoding);
      } catch {
        // Not compressed, try as plain JSON
        serialized = buffer.toString(this._encoding);
      }

      const data = JSON.parse(serialized);
      manager.fromJSON(data);
      return true;
    } catch (err) {
      console.error('Failed to import state:', err);
      return false;
    }
  }

  /**
   * Create snapshot with metadata
   * @param {StateManager} manager - State manager
   * @returns {Object}
   */
  createSnapshot(manager) {
    return {
      version: 1,
      timestamp: Date.now(),
      data: manager.toJSON(),
      keys: manager.keys()
    };
  }

  /**
   * Restore from snapshot
   * @param {StateManager} manager - State manager
   * @param {Object} snapshot - Snapshot object
   * @returns {boolean}
   */
  restoreSnapshot(manager, snapshot) {
    if (!snapshot || !snapshot.data) {
      return false;
    }
    manager.fromJSON(snapshot.data);
    return true;
  }

  /**
   * Get storage size estimate
   * @param {StateManager} manager - State manager
   * @returns {number} Size in bytes
   */
  estimateSize(manager) {
    const data = manager.toJSON();
    const serialized = JSON.stringify(data);
    return Buffer.byteLength(serialized, this._encoding);
  }

  /**
   * Clear stored state
   * @param {string} key - Storage key
   * @returns {Promise<void>}
   */
  async clear(key) {
    if (this._storage) {
      await this._storage.removeItem(key);
    }
  }
}

/**
 * Create localStorage adapter for browser
 * @returns {Object}
 */
function createLocalStorageAdapter() {
  return {
    getItem: (key) => Promise.resolve(localStorage.getItem(key)),
    setItem: (key, value) => {
      localStorage.setItem(key, value);
      return Promise.resolve();
    },
    removeItem: (key) => {
      localStorage.removeItem(key);
      return Promise.resolve();
    }
  };
}

/**
 * Create file storage adapter for Node.js
 * @param {string} filepath - Storage file path
 * @returns {Object}
 */
function createFileStorageAdapter(filepath) {
  const fs = require('fs').promises;

  return {
    getItem: async (key) => {
      try {
        const data = await fs.readFile(filepath, 'utf8');
        const store = JSON.parse(data);
        return store[key] || null;
      } catch {
        return null;
      }
    },
    setItem: async (key, value) => {
      let store = {};
      try {
        const data = await fs.readFile(filepath, 'utf8');
        store = JSON.parse(data);
      } catch {}
      store[key] = value;
      await fs.writeFile(filepath, JSON.stringify(store, null, 2));
    },
    removeItem: async (key) => {
      try {
        const data = await fs.readFile(filepath, 'utf8');
        const store = JSON.parse(data);
        delete store[key];
        await fs.writeFile(filepath, JSON.stringify(store, null, 2));
      } catch {}
    }
  };
}

module.exports = {
  StatePersistence,
  createLocalStorageAdapter,
  createFileStorageAdapter
};