/**
 * State Management Module
 * Chapter 4: Advanced State Management
 */

const { StateManager, Observable, Computed } = require('./StateManager');
const {
  createStateModule,
  createDerivedModule,
  mergeModules,
  createPersistentModule,
  createValidatedModule,
  ValidationError
} = require('./StateComposition');
const { StatePersistence, createLocalStorageAdapter, createFileStorageAdapter } = require('./StatePersistence');

module.exports = {
  // Core
  StateManager,
  Observable,
  Computed,

  // Composition
  createStateModule,
  createDerivedModule,
  mergeModules,
  createPersistentModule,
  createValidatedModule,
  ValidationError,

  // Persistence
  StatePersistence,
  createLocalStorageAdapter,
  createFileStorageAdapter
};