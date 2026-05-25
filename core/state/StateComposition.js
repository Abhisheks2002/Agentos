/**
 * StateComposition - Composable State Modules
 * Chapter 4.2: State Composition Patterns
 */

const { StateManager } = require('./StateManager');

/**
 * Create a composable state module
 * @param {string} name - Module name
 * @param {Object} initialState - Initial state values
 * @param {Object} methods - Methods to expose
 * @returns {Function}
 */
function createStateModule(name, initialState, methods = {}) {
  return function composeStateModule(manager) {
    // Initialize state
    for (const [key, value] of Object.entries(initialState)) {
      const fullKey = `${name}.${key}`;
      manager.state(fullKey, value);
    }

    // Create bound methods
    const boundMethods = {};
    for (const [methodName, methodFn] of Object.entries(methods)) {
      boundMethods[methodName] = methodFn.bind({ name, manager });
    }

    return {
      name,
      get: (key) => manager.get(`${name}.${key}`),
      set: (key, value) => manager.set(`${name}.${key}`, value),
      subscribe: (key, callback) => manager.subscribe(`${name}.${key}`, callback),
      ...boundMethods
    };
  };
}

/**
 * Create a derived state module
 * @param {string} name - Module name
 * @param {Function} deriveFn - Function to derive state
 * @param {string[]} dependencies - Keys to depend on
 * @returns {Function}
 */
function createDerivedModule(name, deriveFn, dependencies) {
  return function composeDerivedModule(manager) {
    const depKeys = dependencies.map(d => `${name}.${d}`);

    manager.computed(name, () => {
      const deps = {};
      for (const dep of dependencies) {
        deps[dep] = manager.get(`${name}.${dep}`);
      }
      return deriveFn(deps);
    }, depKeys);

    return {
      name,
      get: () => manager.getComputed(name),
      subscribe: (callback) => manager.subscribeComputed(name, callback)
    };
  };
}

/**
 * Merge multiple state modules
 * @param {StateManager} manager - State manager
 * @param {Array} modules - Array of module factories
 * @returns {Object} Combined module interface
 */
function mergeModules(manager, modules) {
  const instances = modules.map(module => module(manager));

  return {
    instances,
    getModule: (name) => instances.find(m => m.name === name),
    get: (moduleName, key) => {
      const module = instances.find(m => m.name === moduleName);
      return module?.get?.(key);
    },
    set: (moduleName, key, value) => {
      const module = instances.find(m => m.name === moduleName);
      return module?.set?.(key, value);
    }
  };
}

/**
 * Create a persistent state module
 * @param {string} name - Module name
 * @param {Object} initialState - Initial state
 * @param {Object} persistence - Persistence config
 * @returns {Function}
 */
function createPersistentModule(name, initialState, persistence) {
  return function composePersistentModule(manager) {
    const storageKey = persistence.key || `state.${name}`;
    const storage = persistence.storage || localStorage;

    // Create base module
    const baseModule = createStateModule(name, initialState)(manager);

    // Load persisted state
    try {
      const stored = storage.getItem(storageKey);
      if (stored) {
        const data = JSON.parse(stored);
        manager.batch(() => {
          for (const [key, value] of Object.entries(data)) {
            manager.set(`${name}.${key}`, value);
          }
        });
      }
    } catch (err) {
      console.error(`Failed to load persisted state for ${name}:`, err);
    }

    // Auto-save on changes
    const save = () => {
      try {
        const data = {};
        for (const key of Object.keys(initialState)) {
          data[key] = manager.get(`${name}.${key}`);
        }
        storage.setItem(storageKey, JSON.stringify(data));
      } catch (err) {
        console.error(`Failed to persist state for ${name}:`, err);
      }
    };

    manager.on(`change:${name}.*`, save);

    return {
      ...baseModule,
      save,
      clear: () => {
        storage.removeItem(storageKey);
        manager.batch(() => {
          for (const key of Object.keys(initialState)) {
            manager.set(`${name}.${key}`, initialState[key]);
          }
        });
      }
    };
  };
}

/**
 * Create a validated state module
 * @param {string} name - Module name
 * @param {Object} initialState - Initial state
 * @param {Object} validators - Key-validator map
 * @returns {Function}
 */
function createValidatedModule(name, initialState, validators) {
  return function composeValidatedModule(manager) {
    const baseModule = createStateModule(name, initialState)(manager);

    // Wrap setters with validation
    const wrappedSet = (key, value) => {
      const fullKey = `${name}.${key}`;
      const validator = validators[key];
      if (validator) {
        const error = validator(value);
        if (error) {
          throw new ValidationError(key, error);
        }
      }
      manager.set(fullKey, value);
    };

    return {
      ...baseModule,
      set: wrappedSet,
      validate: (key, value) => {
        const validator = validators[key];
        return validator ? validator(value) : null;
      },
      validateAll: () => {
        const errors = {};
        for (const key of Object.keys(validators)) {
          const value = manager.get(`${name}.${key}`);
          const error = validators[key](value);
          if (error) errors[key] = error;
        }
        return errors;
      }
    };
  };
}

class ValidationError extends Error {
  constructor(field, message) {
    super(`Validation error on ${field}: ${message}`);
    this.field = field;
    this.message = message;
  }
}

module.exports = {
  createStateModule,
  createDerivedModule,
  mergeModules,
  createPersistentModule,
  createValidatedModule,
  ValidationError
};