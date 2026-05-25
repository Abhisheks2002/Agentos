/**
 * State Management Tests
 * Chapter 4.5: Testing State Management
 */

const { StateManager, Observable, Computed } = require('../core/state/StateManager');
const {
  createStateModule,
  createDerivedModule,
  mergeModules,
  createValidatedModule,
  ValidationError
} = require('../core/state/StateComposition');
const { StatePersistence } = require('../core/state/StatePersistence');

// Simple test framework
const tests = {
  passed: 0,
  failed: 0,
  results: []
};

function test(name, fn) {
  try {
    fn();
    tests.passed++;
    tests.results.push({ name, status: 'passed' });
    console.log(`  ✓ ${name}`);
  } catch (err) {
    tests.failed++;
    tests.results.push({ name, status: 'failed', error: err.message });
    console.log(`  ✗ ${name}: ${err.message}`);
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(message || `Expected ${expected}, got ${actual}`);
  }
}

console.log('\n=== State Management Tests ===\n');

// Test Observable
console.log('Testing Observable:');
test('Observable gets initial value', () => {
  const obs = new Observable(42);
  assertEqual(obs.get(), 42);
});

test('Observable sets new value and notifies subscribers', () => {
  const obs = new Observable(10);
  let notified = false;
  obs.subscribe((newVal, oldVal) => {
    notified = true;
    assertEqual(newVal, 20);
    assertEqual(oldVal, 10);
  });
  obs.set(20);
  assert(notified, 'Subscriber should be notified');
});

test('Observable prevents duplicate values', () => {
  const obs = new Observable(5);
  let callCount = 0;
  obs.subscribe(() => callCount++);
  obs.set(5);
  obs.set(5);
  assertEqual(callCount, 0);
});

// Test Computed
console.log('\nTesting Computed:');
test('Computes value from dependencies', () => {
  const a = new Observable(2);
  const b = new Observable(3);
  const computed = new Computed((x, y) => x + y, [a, b]);
  assertEqual(computed.get(), 5);
});

test('Updates when dependency changes', () => {
  const a = new Observable(2);
  const b = new Observable(3);
  const computed = new Computed((x, y) => x * y, [a, b]);
  assertEqual(computed.get(), 6);
  a.set(5);
  assertEqual(computed.get(), 15);
});

test('Notifies on value change', () => {
  const a = new Observable(1);
  const b = new Observable(2);
  const computed = new Computed((x, y) => x + y, [a, b]);
  let notified = false;
  computed.subscribe(() => notified = true);
  a.set(10);
  assert(notified, 'Should notify subscribers');
});

// Test StateManager
console.log('\nTesting StateManager:');
test('Creates state with initial value', () => {
  const manager = new StateManager({ name: 'test' });
  manager.state('count', 0);
  assertEqual(manager.get('count'), 0);
});

test('Sets and gets values', () => {
  const manager = new StateManager({ name: 'test' });
  manager.set('name', 'AgentOS');
  assertEqual(manager.get('name'), 'AgentOS');
});

test('Creates computed values', () => {
  const manager = new StateManager({ name: 'test' });
  manager.state('a', 5);
  manager.state('b', 10);
  manager.computed('sum', (a, b) => a + b, ['a', 'b']);
  assertEqual(manager.getComputed('sum'), 15);
});

test('Subscribes to state changes', () => {
  const manager = new StateManager({ name: 'test' });
  manager.state('value', 0);
  let newVal, oldVal;
  manager.subscribe('value', (n, o) => {
    newVal = n;
    oldVal = o;
  });
  manager.set('value', 42);
  assertEqual(newVal, 42);
  assertEqual(oldVal, 0);
});

test('Batches multiple updates', () => {
  const manager = new StateManager({ name: 'test' });
  manager.state('a', 0);
  manager.state('b', 0);
  let changeCount = 0;
  manager.subscribe('change', () => changeCount++);

  manager.batch(() => {
    manager.set('a', 1);
    manager.set('b', 2);
  });

  assertEqual(manager.get('a'), 1);
  assertEqual(manager.get('b'), 2);
});

test('Uses middleware', () => {
  const manager = new StateManager({ name: 'test' });
  let middlewareCalled = false;
  manager.useMiddleware({
    onChange: (event) => {
      middlewareCalled = true;
      assertEqual(event.key, 'test');
    }
  });
  manager.state('test', 'value');
  manager.set('test', 'newValue');
  assert(middlewareCalled);
});

test('Exports toJSON', () => {
  const manager = new StateManager({ name: 'test' });
  manager.set('a', 1);
  manager.set('b', 2);
  const json = manager.toJSON();
  assertEqual(json.a, 1);
  assertEqual(json.b, 2);
});

test('Loads fromJSON', () => {
  const manager = new StateManager({ name: 'test' });
  manager.state('a', 0);
  manager.state('b', 0);
  manager.fromJSON({ a: 10, b: 20 });
  assertEqual(manager.get('a'), 10);
  assertEqual(manager.get('b'), 20);
});

// Test State Composition
console.log('\nTesting StateComposition:');
test('Creates state module', () => {
  const manager = new StateManager({ name: 'test' });
  const module = createStateModule('user', { name: '', age: 0 });
  const instance = module(manager);
  instance.set('name', 'John');
  assertEqual(manager.get('user.name'), 'John');
});

test('Creates derived module', () => {
  const manager = new StateManager({ name: 'test' });
  manager.state('a', 2);
  manager.state('b', 3);
  const derived = createDerivedModule('calc', (deps) => deps.a + deps.b, ['a', 'b']);
  derived(manager);
  assertEqual(manager.getComputed('calc'), 5);
});

test('Validates state module', () => {
  const manager = new StateManager({ name: 'test' });
  const validators = {
    age: (v) => v < 0 ? 'Age must be positive' : null
  };
  const module = createValidatedModule('person', { name: '', age: 0 }, validators);
  const instance = module(manager);

  try {
    instance.set('age', -5);
    throw new Error('Should have thrown');
  } catch (err) {
    if (err instanceof ValidationError) {
      assertEqual(err.field, 'age');
    } else {
      throw err;
    }
  }
});

// Test StatePersistence
console.log('\nTesting StatePersistence:');
test('Serializes and deserializes state', () => {
  const manager = new StateManager({ name: 'test' });
  manager.set('name', 'AgentOS');
  manager.set('version', 1);

  const json = JSON.stringify(manager.toJSON());
  const data = JSON.parse(json);

  const manager2 = new StateManager({ name: 'test2' });
  manager2.fromJSON(data);

  assertEqual(manager2.get('name'), 'AgentOS');
  assertEqual(manager2.get('version'), 1);
});

test('Creates snapshot', () => {
  const persistence = new StatePersistence({ compression: false });
  const manager = new StateManager({ name: 'test' });
  manager.set('key', 'value');

  const snapshot = persistence.createSnapshot(manager);
  assertEqual(snapshot.data.key, 'value');
});

test('Restores from snapshot', () => {
  const persistence = new StatePersistence({ compression: false });
  const manager = new StateManager({ name: 'test' });
  manager.set('key', 'value');

  const snapshot = persistence.createSnapshot(manager);

  const manager2 = new StateManager({ name: 'test2' });
  const result = persistence.restoreSnapshot(manager2, snapshot);
  assert(result);
  assertEqual(manager2.get('key'), 'value');
});

// Print summary
console.log('\n=== Test Summary ===');
console.log(`Passed: ${tests.passed}`);
console.log(`Failed: ${tests.failed}`);
console.log(`Total: ${tests.passed + tests.failed}`);

process.exit(tests.failed > 0 ? 1 : 0);