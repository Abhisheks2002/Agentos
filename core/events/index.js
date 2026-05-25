/**
 * Event System Module
 * Chapter 5: Event-Driven Architecture
 */

const EventEmitter = require('./EventEmitter');
const EventQueue = require('./EventQueue');
const { EventPipeline, PipelineStage, createMiddleware } = require('./EventPipeline');

module.exports = {
  // Core
  EventEmitter,

  // Queue
  EventQueue,

  // Pipeline
  EventPipeline,
  PipelineStage,
  createMiddleware
};