/**
 * Profiling utilities for frontend performance monitoring
 */

/**
 * Statistics for a profiled component
 */
export interface ComponentStats {
  name: string;
  totalTimeMs: number;
  callCount: number;
  avgTimeMs: number;
  minTimeMs: number;
  maxTimeMs: number;
  medianTimeMs: number;
  stdDevMs: number;
}

/**
 * Profiler result from a profiling session
 */
export interface ProfilerResult {
  sessionName: string;
  totalTimeMs: number;
  totalTimeSeconds: number;
  startTime: number;
  endTime: number;
  components: Record<string, ComponentStats>;
  bottlenecks: string[];
}

/**
 * Options for creating a profiler
 */
export interface ProfilerOptions {
  autoLog?: boolean;
  threshold?: number;
}

/**
 * Internal measurement record
 */
interface Measurement {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
}

/**
 * Component statistics accumulator
 */
class ComponentAccumulator {
  name: string;
  times: number[] = [];
  totalTimeMs = 0;
  minTimeMs = Infinity;
  maxTimeMs = 0;

  constructor(name: string) {
    this.name = name;
  }

  add(timeMs: number): void {
    this.times.push(timeMs);
    this.totalTimeMs += timeMs;
    this.minTimeMs = Math.min(this.minTimeMs, timeMs);
    this.maxTimeMs = Math.max(this.maxTimeMs, timeMs);
  }

  getStats(): ComponentStats {
    const count = this.times.length;
    const avg = count > 0 ? this.totalTimeMs / count : 0;
    
    // Calculate median
    const sorted = [...this.times].sort((a, b) => a - b);
    const median = count > 0 
      ? count % 2 === 0 
        ? (sorted[count / 2 - 1] + sorted[count / 2]) / 2 
        : sorted[Math.floor(count / 2)]
      : 0;

    // Calculate standard deviation
    const stdDev = count > 1 
      ? Math.sqrt(this.times.reduce((sum, t) => sum + Math.pow(t - avg, 2), 0) / (count - 1))
      : 0;

    return {
      name: this.name,
      totalTimeMs: Math.round(this.totalTimeMs * 1000) / 1000,
      callCount: count,
      avgTimeMs: Math.round(avg * 1000) / 1000,
      minTimeMs: Math.round(this.minTimeMs * 1000) / 1000,
      maxTimeMs: Math.round(this.maxTimeMs * 1000) / 1000,
      medianTimeMs: Math.round(median * 1000) / 1000,
      stdDevMs: Math.round(stdDev * 1000) / 1000,
    };
  }
}

/**
 * Frontend profiler for tracking component execution times
 * 
 * @example
 * ```typescript
 * const profiler = new Profiler('api_calls');
 * 
 * profiler.start();
 * profiler.measure('fetch_jobs', async () => await fetchJobs());
 * profiler.measure('fetch_stats', async () => await fetchStats());
 * profiler.stop();
 * 
 * console.log(profiler.getSummary());
 * ```
 */
export class Profiler {
  private sessionName: string;
  private autoLog: boolean;
  private threshold: number;
  
  private components: Map<string, ComponentAccumulator> = new Map();
  private startTime: number = 0;
  private endTime: number = 0;
  private measurementStack: string[] = [];
  private isRunning = false;

  constructor(sessionName: string, options: ProfilerOptions = {}) {
    this.sessionName = sessionName;
    this.autoLog = options.autoLog ?? true;
    this.threshold = options.threshold ?? 10;
  }

  /**
   * Start the profiling session
   */
  start(): this {
    this.startTime = performance.now();
    this.isRunning = true;
    if (this.autoLog) {
      console.debug(`[Profiler] Session '${this.sessionName}' started`);
    }
    return this;
  }

  /**
   * Stop the profiling session
   */
  stop(): ProfilerResult {
    this.endTime = performance.now();
    this.isRunning = false;
    const result = this.getResult();
    
    if (this.autoLog) {
      console.debug(
        `[Profiler] Session '${this.sessionName}' completed: ${result.totalTimeMs.toFixed(2)}ms`
      );
    }
    
    return result;
  }

  /**
   * Measure execution time of a sync or async function
   */
  measure<T>(componentName: string, fn: () => T | Promise<T>): T | Promise<T> {
    const startMark = `${componentName}_start_${Date.now()}`;
    const endMark = `${componentName}_end_${Date.now()}`;
    
    performance.mark(startMark);
    this.measurementStack.push(componentName);
    
    try {
      const result = fn();
      
      // Handle both sync and async functions
      if (result instanceof Promise) {
        return result.finally(() => {
          this.finishMeasurement(componentName, startMark, endMark);
        }) as T;
      }
      
      this.finishMeasurement(componentName, startMark, endMark);
      return result;
    } catch (error) {
      this.finishMeasurement(componentName, startMark, endMark);
      throw error;
    }
  }

  private finishMeasurement(name: string, startMark: string, endMark: string): void {
    performance.mark(endMark);
    
    try {
      performance.measure(name, startMark, endMark);
      const entries = performance.getEntriesByName(name);
      const lastEntry = entries[entries.length - 1];
      
      if (lastEntry) {
        const timeMs = lastEntry.duration;
        
        let accumulator = this.components.get(name);
        if (!accumulator) {
          accumulator = new ComponentAccumulator(name);
          this.components.set(name, accumulator);
        }
        accumulator.add(timeMs);
        
        if (this.autoLog) {
          console.debug(`[Profiler] '${name}': ${timeMs.toFixed(2)}ms`);
        }
      }
      
      // Cleanup
      performance.clearMarks(startMark);
      performance.clearMarks(endMark);
      performance.clearMeasures(name);
    } finally {
      this.measurementStack.pop();
    }
  }

  /**
   * Create a timed context using a callback
   */
  async measureAsync<T>(componentName: string, fn: () => Promise<T>): Promise<T> {
    return this.measure(componentName, fn) as Promise<T>;
  }

  /**
   * Record a manual timing measurement
   */
  record(componentName: string, timeMs: number): void {
    let accumulator = this.components.get(componentName);
    if (!accumulator) {
      accumulator = new ComponentAccumulator(componentName);
      this.components.set(componentName, accumulator);
    }
    accumulator.add(timeMs);
  }

  /**
   * Get statistics for a specific component
   */
  getStats(componentName: string): ComponentStats | undefined {
    const accumulator = this.components.get(componentName);
    return accumulator?.getStats();
  }

  /**
   * Get the complete profiling result
   */
  getResult(): ProfilerResult {
    const components: Record<string, ComponentStats> = {};
    let totalTimeMs = 0;
    
    for (const [name, accumulator] of this.components) {
      const stats = accumulator.getStats();
      components[name] = stats;
      totalTimeMs += stats.totalTimeMs;
    }
    
    const bottlenecks = this.getBottlenecks(totalTimeMs);
    
    return {
      sessionName: this.sessionName,
      totalTimeMs: Math.round(totalTimeMs * 1000) / 1000,
      totalTimeSeconds: Math.round((totalTimeMs / 1000) * 1000) / 1000,
      startTime: this.startTime,
      endTime: this.endTime,
      components,
      bottlenecks,
    };
  }

  private getBottlenecks(totalMs: number): string[] {
    const thresholdMs = totalMs * (this.threshold / 100);
    const bottlenecks: string[] = [];
    
    for (const [name, accumulator] of this.components) {
      if (accumulator.totalTimeMs >= thresholdMs) {
        bottlenecks.push(name);
      }
    }
    
    return bottlenecks;
  }

  /**
   * Get a human-readable summary
   */
  getSummary(topN: number = 10): string {
    const result = this.getResult();
    const sorted = Object.values(result.components)
      .sort((a, b) => b.totalTimeMs - a.totalTimeMs)
      .slice(0, topN);
    
    const lines = [
      `\n${'='.repeat(60)}`,
      `Profiler Summary: ${this.sessionName}`,
      `${'='.repeat(60)}`,
      `Total Time: ${result.totalTimeMs.toFixed(2)}ms (${result.totalTimeSeconds.toFixed(3)}s)`,
      `Components: ${Object.keys(result.components).length}`,
      '',
      `${'Component'.padEnd(30)} ${'Calls'.padStart(8)} ${'Total(ms)'.padStart(12)} ${'Avg(ms)'.padStart(10)} ${'%'.padStart(6)}`,
      '-'.repeat(70),
    ];
    
    for (const comp of sorted) {
      const percent = result.totalTimeMs > 0 
        ? (comp.totalTimeMs / result.totalTimeMs * 100).toFixed(1) 
        : '0.0';
      lines.push(
        `${comp.name.padEnd(30)} ${comp.callCount.toString().padStart(8)} ` +
        `${comp.totalTimeMs.toFixed(2).padStart(12)} ` +
        `${comp.avgTimeMs.toFixed(2).padStart(10)} ${percent.padStart(5)}%`
      );
    }
    
    lines.push('='.repeat(60));
    
    // Bottleneck analysis
    if (result.bottlenecks.length > 0) {
      lines.push('\nPotential Bottlenecks (>' + this.threshold + '% of total time):');
      for (const name of result.bottlenecks) {
        const comp = result.components[name];
        const percent = result.totalTimeMs > 0 
          ? (comp.totalTimeMs / result.totalTimeMs * 100).toFixed(1) 
          : '0.0';
        lines.push(`  - ${name}: ${percent}% (${comp.totalTimeMs.toFixed(2)}ms)`);
      }
    }
    
    return lines.join('\n');
  }

  /**
   * Reset all profiling data
   */
  reset(): void {
    this.components.clear();
    this.startTime = 0;
    this.endTime = 0;
    this.measurementStack = [];
    this.isRunning = false;
  }

  /**
   * Check if the profiler is currently running
   */
  getIsActive(): boolean {
    return this.isRunning;
  }
}

/**
 * Global profiler registry
 */
const profilers = new Map<string, Profiler>();

/**
 * Get or create a profiler by name
 */
export function getProfiler(name: string, options?: ProfilerOptions): Profiler {
  let profiler = profilers.get(name);
  if (!profiler) {
    profiler = new Profiler(name, options);
    profilers.set(name, profiler);
  }
  return profiler;
}

/**
 * Clear a profiler from the registry
 */
export function clearProfiler(name: string): boolean {
  return profilers.delete(name);
}

/**
 * Get all registered profilers
 */
export function getAllProfilers(): Map<string, Profiler> {
  return new Map(profilers);
}

/**
 * Profile decorator/factory for functions
 */
export function profileFunction<T extends (...args: unknown[]) => unknown>(
  componentName: string,
  profilerName?: string
): (fn: T) => T {
  return (fn: T): T => {
    const profiler = profilerName ? getProfiler(profilerName) : new Profiler(componentName, { autoLog: false });
    
    return ((...args: Parameters<T>): ReturnType<T> => {
      return profiler.measure(componentName, () => fn(...args)) as ReturnType<T>;
    }) as T;
  };
}

/**
 * Time an async function execution and return result with timing
 */
export async function timedExecution<T>(
  name: string,
  fn: () => Promise<T>
): Promise<{ result: T; timeMs: number }> {
  const start = performance.now();
  const result = await fn();
  const timeMs = performance.now() - start;
  
  console.debug(`[Profiler] '${name}': ${timeMs.toFixed(2)}ms`);
  
  return { result, timeMs };
}

/**
 * Time a sync function execution and return result with timing
 */
export function timedExecutionSync<T>(name: string, fn: () => T): { result: T; timeMs: number } {
  const start = performance.now();
  const result = fn();
  const timeMs = performance.now() - start;
  
  console.debug(`[Profiler] '${name}': ${timeMs.toFixed(2)}ms`);
  
  return { result, timeMs };
}

/**
 * Format timing for display
 */
export function formatTiming(ms: number): string {
  if (ms < 1) {
    return `${(ms * 1000).toFixed(0)}μs`;
  } else if (ms < 1000) {
    return `${ms.toFixed(2)}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(2)}s`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.round((ms % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  }
}

/**
 * Pipeline profiler for multi-stage processing
 */
export class PipelineProfiler {
  private name: string;
  private profiler: Profiler;
  private stageTimes: number[] = [];

  constructor(name: string, autoLog: boolean = true) {
    this.name = name;
    this.profiler = new Profiler(name, { autoLog });
  }

  start(): this {
    this.profiler.start();
    return this;
  }

  stop(): ProfilerResult {
    return this.profiler.stop();
  }

  /**
   * Execute a stage and measure its timing
   */
  async stage<T>(stageName: string, fn: () => Promise<T>): Promise<T> {
    const stageStart = performance.now();
    
    try {
      const result = await this.profiler.measureAsync(stageName, fn);
      return result;
    } finally {
      const stageTime = performance.now() - stageStart;
      this.stageTimes.push(stageTime);
    }
  }

  /**
   * Execute a sync stage and measure its timing
   */
  stageSync<T>(stageName: string, fn: () => T): T {
    const stageStart = performance.now();
    
    try {
      return this.profiler.measure(stageName, fn);
    } finally {
      const stageTime = performance.now() - stageStart;
      this.stageTimes.push(stageTime);
    }
  }

  getReport(): string {
    return this.profiler.getSummary();
  }

  getResult(): ProfilerResult {
    return this.profiler.getResult();
  }
}
