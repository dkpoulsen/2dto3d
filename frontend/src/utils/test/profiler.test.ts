/**
 * Unit tests for frontend profiler utilities
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  Profiler,
  PipelineProfiler,
  getProfiler,
  clearProfiler,
  getAllProfilers,
  profileFunction,
  timedExecution,
  timedExecutionSync,
  formatTiming,
} from '../profiler';

// Mock console.debug
vi.spyOn(console, 'debug').mockImplementation(() => {});

describe('Profiler', () => {
  beforeEach(() => {
    // Clear the profiler registry before each test
    const allProfilers = getAllProfilers();
    for (const name of allProfilers.keys()) {
      clearProfiler(name);
    }
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('constructor', () => {
    it('should create profiler with default options', () => {
      const profiler = new Profiler('test_session');
      expect(profiler.session).toBe('test_session');
      expect(profiler.getIsActive()).toBe(false);
    });

    it('should create profiler with custom options', () => {
      const profiler = new Profiler('test_session', { autoLog: false, threshold: 20 });
      expect(profiler.session).toBe('test_session');
    });
  });

  describe('start/stop', () => {
    it('should start and stop profiling session', () => {
      const profiler = new Profiler('test', { autoLog: false });

      profiler.start();
      expect(profiler.getIsActive()).toBe(true);

      const result = profiler.stop();
      expect(profiler.getIsActive()).toBe(false);
      expect(result.sessionName).toBe('test');
    });

    it('should return chainable from start', () => {
      const profiler = new Profiler('test', { autoLog: false });
      const returned = profiler.start();
      expect(returned).toBe(profiler);
    });
  });

  describe('measure', () => {
    it('should measure sync function execution time', () => {
      const profiler = new Profiler('test', { autoLog: false });
      profiler.start();

      const result = profiler.measure('sync_op', () => {
        return 42;
      });

      expect(result).toBe(42);
      const stats = profiler.getStats('sync_op');
      expect(stats).toBeDefined();
      expect(stats!.callCount).toBe(1);
      expect(stats!.totalTimeMs).toBeGreaterThanOrEqual(0);
    });

    it('should measure async function execution time', async () => {
      const profiler = new Profiler('test', { autoLog: false });
      profiler.start();

      const result = await profiler.measureAsync('async_op', async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return 'done';
      });

      expect(result).toBe('done');
      const stats = profiler.getStats('async_op');
      expect(stats).toBeDefined();
      expect(stats!.callCount).toBe(1);
    });

    it('should accumulate multiple measurements', () => {
      const profiler = new Profiler('test', { autoLog: false });

      for (let i = 0; i < 3; i++) {
        profiler.measure('repeated_op', () => i);
      }

      const stats = profiler.getStats('repeated_op');
      expect(stats!.callCount).toBe(3);
    });
  });

  describe('record', () => {
    it('should record manual timing measurement', () => {
      const profiler = new Profiler('test', { autoLog: false });
      profiler.record('manual_op', 42.5);

      const stats = profiler.getStats('manual_op');
      expect(stats).toBeDefined();
      expect(stats!.totalTimeMs).toBe(42.5);
    });

    it('should throw error for negative time', () => {
      const profiler = new Profiler('test', { autoLog: false });

      expect(() => {
        profiler.record('op', -10);
      }).toThrow('Time cannot be negative');
    });
  });

  describe('getResult', () => {
    it('should return complete profiler result', () => {
      const profiler = new Profiler('test', { autoLog: false });

      profiler.measure('op1', () => {});
      profiler.measure('op2', () => {});

      const result = profiler.getResult();

      expect(result.sessionName).toBe('test');
      expect(Object.keys(result.components)).toHaveLength(2);
      expect('op1' in result.components).toBe(true);
      expect('op2' in result.components).toBe(true);
    });

    it('should identify bottlenecks', () => {
      const profiler = new Profiler('test', { autoLog: false, threshold: 10 });

      profiler.record('small_op', 10);
      profiler.record('large_op', 90);

      const result = profiler.getResult();

      expect(result.bottlenecks).toContain('large_op');
    });
  });

  describe('getSummary', () => {
    it('should return formatted summary string', () => {
      const profiler = new Profiler('test', { autoLog: false });

      profiler.measure('operation', () => {});

      const summary = profiler.getSummary();

      expect(summary).toContain('Profiler Summary: test');
      expect(summary).toContain('operation');
    });
  });

  describe('reset', () => {
    it('should clear all profiling data', () => {
      const profiler = new Profiler('test', { autoLog: false });

      profiler.measure('op', () => {});
      profiler.reset();

      const result = profiler.getResult();
      expect(Object.keys(result.components)).toHaveLength(0);
    });
  });
});

describe('Profiler Registry', () => {
  beforeEach(() => {
    const allProfilers = getAllProfilers();
    for (const name of allProfilers.keys()) {
      clearProfiler(name);
    }
  });

  describe('getProfiler', () => {
    it('should create new profiler if not exists', () => {
      const profiler = getProfiler('new_session');
      expect(profiler.session).toBe('new_session');
    });

    it('should return existing profiler', () => {
      const profiler1 = getProfiler('session');
      const profiler2 = getProfiler('session');

      expect(profiler1).toBe(profiler2);
    });
  });

  describe('clearProfiler', () => {
    it('should remove profiler from registry', () => {
      getProfiler('to_clear');
      const result = clearProfiler('to_clear');

      expect(result).toBe(true);
    });

    it('should return false for nonexistent profiler', () => {
      const result = clearProfiler('nonexistent');
      expect(result).toBe(false);
    });
  });

  describe('getAllProfilers', () => {
    it('should return all registered profilers', () => {
      getProfiler('session1');
      getProfiler('session2');

      const all = getAllProfilers();

      expect(all.has('session1')).toBe(true);
      expect(all.has('session2')).toBe(true);
    });
  });
});

describe('profileFunction', () => {
  it('should profile a function', () => {
    const profiledFn = profileFunction('test_fn')((x: number) => x * 2);

    const result = profiledFn(5);

    expect(result).toBe(10);
  });
});

describe('timedExecution', () => {
  it('should return result and timing for async function', async () => {
    const { result, timeMs } = await timedExecution('test', async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
      return 'done';
    });

    expect(result).toBe('done');
    expect(timeMs).toBeGreaterThanOrEqual(10);
  });
});

describe('timedExecutionSync', () => {
  it('should return result and timing for sync function', () => {
    const { result, timeMs } = timedExecutionSync('test', () => 42);

    expect(result).toBe(42);
    expect(timeMs).toBeGreaterThanOrEqual(0);
  });
});

describe('formatTiming', () => {
  it('should format microseconds', () => {
    expect(formatTiming(0.5)).toBe('500μs');
  });

  it('should format milliseconds', () => {
    expect(formatTiming(12.5)).toBe('12.50ms');
  });

  it('should format seconds', () => {
    expect(formatTiming(1234.5)).toBe('1.23s');
  });

  it('should format minutes and seconds', () => {
    expect(formatTiming(90000)).toBe('1m 30s');
  });
});

describe('PipelineProfiler', () => {
  describe('constructor', () => {
    it('should create pipeline profiler', () => {
      const pipeline = new PipelineProfiler('test_pipeline');
      expect(pipeline.pipelineName).toBe('test_pipeline');
    });
  });

  describe('start/stop', () => {
    it('should start and stop pipeline', () => {
      const pipeline = new PipelineProfiler('test', false);

      pipeline.start();
      const result = pipeline.stop();

      expect(result.sessionName).toBe('test');
    });
  });

  describe('stage', () => {
    it('should track async stage timing', async () => {
      const pipeline = new PipelineProfiler('test', false);
      pipeline.start();

      await pipeline.stage('stage1', async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        return 'result';
      });

      const result = pipeline.stop();

      expect('stage1' in result.components).toBe(true);
    });

    it('should track sync stage timing', () => {
      const pipeline = new PipelineProfiler('test', false);
      pipeline.start();

      pipeline.stageSync('stage1', () => 42);

      const result = pipeline.stop();

      expect('stage1' in result.components).toBe(true);
    });
  });

  describe('getReport', () => {
    it('should return formatted report', async () => {
      const pipeline = new PipelineProfiler('test_pipeline', false);
      pipeline.start();

      await pipeline.stage('stage1', async () => {});
      pipeline.stop();

      const report = pipeline.getReport();

      expect(report).toContain('test_pipeline');
      expect(report).toContain('stage1');
    });
  });

  describe('getResult', () => {
    it('should return profiler result', async () => {
      const pipeline = new PipelineProfiler('test', false);
      pipeline.start();

      await pipeline.stage('stage1', async () => {});
      pipeline.stop();

      const result = pipeline.getResult();

      expect(result.sessionName).toBe('test');
    });
  });
});

describe('ComponentStats', () => {
  it('should calculate statistics correctly', () => {
    const profiler = new Profiler('test', { autoLog: false });

    // Add multiple measurements
    profiler.record('op', 10);
    profiler.record('op', 20);
    profiler.record('op', 30);

    const stats = profiler.getStats('op');

    expect(stats!.callCount).toBe(3);
    expect(stats!.totalTimeMs).toBe(60);
    expect(stats!.avgTimeMs).toBe(20);
    expect(stats!.minTimeMs).toBe(10);
    expect(stats!.maxTimeMs).toBe(30);
    expect(stats!.medianTimeMs).toBe(20);
  });

  it('should handle single measurement', () => {
    const profiler = new Profiler('test', { autoLog: false });

    profiler.record('op', 42);

    const stats = profiler.getStats('op');

    expect(stats!.callCount).toBe(1);
    expect(stats!.avgTimeMs).toBe(42);
    expect(stats!.stdDevMs).toBe(0);
  });
});
