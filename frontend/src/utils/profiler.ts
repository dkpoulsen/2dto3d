/**
 * Profiling utilities for frontend performance monitoring
 *
 * @module utils/profiler
 *
 * This module provides per-component timing analysis and profiling utilities:
 * - Profiler class for tracking component timings
 * - Pipeline profiler for multi-stage processing
 * - Statistics aggregation and reporting
 *
 * @example
 * ```typescript
 * import { Profiler, profileFunction, timedExecution } from '@/utils/profiler';
 *
 * // Using the profiler directly
 * const profiler = new Profiler('api_calls');
 *
 * profiler.start();
 * await profiler.measureAsync('fetch_jobs', async () => await fetchJobs());
 * await profiler.measureAsync('fetch_stats', async () => await fetchStats());
 * profiler.stop();
 *
 * console.log(profiler.getSummary());
 *
 * // Using the decorator
 * const profiledFetch = profileFunction('fetch_data', fetchData);
 * const result = await profiledFetch();
 *
 * // Quick timing
 * const { result, timeMs } = await timedExecution('process_data', async () => process(data));
 * ```
 */

// Constants
const DEFAULT_BOTTLENECK_THRESHOLD = 10; // Percentage of total time
const DEFAULT_TOP_N_COMPONENTS = 10;
const MAX_STORED_TIMES = 10000; // Maximum times to store per component for stats

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
 * Internal component statistics accumulator
 */
class ComponentAccumulator {
  readonly name: string;
  private times: number[] = [];
  private totalTimeMs = 0;
  private minTimeMs = Infinity;
  private maxTimeMs = 0;

  constructor(name: string) {
    this.name = name;
  }

  add(timeMs: number): void {
    if (timeMs < 0) {
      throw new Error(`Time cannot be negative: ${timeMs}`);
    }

    this.times.push(timeMs);
    this.totalTimeMs += timeMs;
    this.minTimeMs = Math.min(this.minTimeMs, timeMs);
    this.maxTimeMs = Math.max(this.maxTimeMs, timeMs);

    // Keep bounded for memory
    if (this.times.length > MAX_STORED_TIMES) {
      // Remove a random sample to maintain representative data
      const idx = Math.floor(Math.random() * this.times.length);
      this.times.splice(idx, 1);
    }
  }

  getStats(): ComponentStats {
    const count = this.times.length;
    const avg = count > 0 ? this.totalTimeMs / count : 0;

    // Calculate median
    const sorted = [...this.times].sort((a, b) => a - b);
    const median =
      count > 0
        ? count % 2 === 0
          ? (sorted[count / 2 - 1] + sorted[count / 2]) / 2
          : sorted[Math.floor(count / 2)]
        : 0;

    // Calculate standard deviation
    const stdDev =
      count > 1
        ? Math.sqrt(
            this.times.reduce((sum, t) => sum + Math.pow(t - avg, 2), 0) / (count - 1)
          )
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
  private isRunning = false;

  constructor(sessionName: string, options: ProfilerOptions = {}) {
    this.sessionName = sessionName;
    this.autoLog = options.autoLog ?? true;
    this.threshold = options.threshold ?? DEFAULT_BOTTLENECK_THRESHOLD;
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

      // Cleanup performance marks
      performance.clearMarks(startMark);
      performance.clearMarks(endMark);
      performance.clearMeasures(name);
    } catch {
      // Ignore errors in measurement finalization
    }
  }

  /**
   * Create a timed context using a callback (async)
   */
  async measureAsync<T>(componentName: string, fn: () => Promise<T>): Promise<T> {
    return this.measure(componentName, fn) as Promise<T>;
  }

  /**
   * Record a manual timing measurement
   */
  record(componentName: string, timeMs: number): void {
    if (timeMs < 0) {
      throw new Error(`Time cannot be negative: ${timeMs}`);
    }

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
      if (accumulator['totalTimeMs'] >= thresholdMs) {
        bottlenecks.push(name);
      }
    }

    return bottlenecks;
  }

  /**
   * Get a human-readable summary
   */
  getSummary(topN: number = DEFAULT_TOP_N_COMPONENTS): string {
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
      const percent =
        result.totalTimeMs > 0 ? ((comp.totalTimeMs / result.totalTimeMs) * 100).toFixed(1) : '0.0';
      lines.push(
        `${comp.name.padEnd(30)} ${comp.callCount.toString().padStart(8)} ` +
          `${comp.totalTimeMs.toFixed(2).padStart(12)} ` +
          `${comp.avgTimeMs.toFixed(2).padStart(10)} ${percent.padStart(5)}%`
      );
    }

    lines.push('='.repeat(60));

    // Bottleneck analysis
    if (result.bottlenecks.length > 0) {
      lines.push(`\nPotential Bottlenecks (>${this.threshold}% of total time):`);
      for (const name of result.bottlenecks) {
        const comp = result.components[name];
        const percent =
          result.totalTimeMs > 0
            ? ((comp.totalTimeMs / result.totalTimeMs) * 100).toFixed(1)
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
    this.isRunning = false;
  }

  /**
   * Check if the profiler is currently running
   */
  getIsActive(): boolean {
    return this.isRunning;
  }

  /**
   * Get the session name
   */
  get session(): string {
    return this.sessionName;
  }
}

/** Global profiler registry */
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
 *
 * @example
 * ```typescript
 * const profiledFetch = profileFunction('fetch_data', async (url: string) => {
 *   return fetch(url);
 * });
 * const result = await profiledFetch('/api/data');
 * ```
 */
export function profileFunction<T extends (...args: unknown[]) => unknown>(
  componentName: string,
  profilerName?: string
): (fn: T) => T {
  return (fn: T): T => {
    const profiler = profilerName
      ? getProfiler(profilerName)
      : new Profiler(componentName, { autoLog: false });

    return ((...args: Parameters<T>): ReturnType<T> => {
      return profiler.measure(componentName, () => fn(...args)) as ReturnType<T>;
    }) as T;
  };
}

/**
 * Time an async function execution and return result with timing
 *
 * @example
 * ```typescript
 * const { result, timeMs } = await timedExecution('fetch_data', async () => {
 *   const response = await fetch('/api/data');
 *   return response.json();
 * });
 * console.log(`Fetched in ${timeMs.toFixed(2)}ms`);
 * ```
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
 *
 * @example
 * ```typescript
 * const { result, timeMs } = timedExecutionSync('process_data', () => {
 *   return heavyComputation(data);
 * });
 * ```
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
 *
 * @example
 * ```typescript
 * console.log(`Duration: ${formatTiming(1234.5)}`); // "1.23s"
 * console.log(`Duration: ${formatTiming(12.5)}`);   // "12.50ms"
 * console.log(`Duration: ${formatTiming(0.5)}`);    // "500μs"
 * ```
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
 *
 * @example
 * ```typescript
 * const pipeline = new PipelineProfiler('video_conversion');
 *
 * pipeline.start();
 * await pipeline.stage('frame_extraction', async () => extractFrames(video));
 * await pipeline.stage('depth_estimation', async () => estimateDepth(frames));
 * await pipeline.stage('stereo_generation', async () => generateStereo(frames, depth));
 * pipeline.stop();
 *
 * console.log(pipeline.getReport());
 * ```
 */
export class PipelineProfiler {
  private name: string;
  private profiler: Profiler;

  constructor(name: string, autoLog: boolean = true) {
    this.name = name;
    this.profiler = new Profiler(name, { autoLog });
  }

  /**
   * Start the pipeline profiling
   */
  start(): this {
    this.profiler.start();
    return this;
  }

  /**
   * Stop the pipeline and get results
   */
  stop(): ProfilerResult {
    return this.profiler.stop();
  }

  /**
   * Execute a stage and measure its timing
   */
  async stage<T>(stageName: string, fn: () => Promise<T>): Promise<T> {
    console.debug(`[PipelineProfiler] '${this.name}' entering stage: ${stageName}`);
    const result = await this.profiler.measureAsync(stageName, fn);
    console.debug(`[PipelineProfiler] '${this.name}' completed stage: ${stageName}`);
    return result;
  }

  /**
   * Execute a sync stage and measure its timing
   */
  stageSync<T>(stageName: string, fn: () => T): T {
    console.debug(`[PipelineProfiler] '${this.name}' entering stage: ${stageName}`);
    const result = this.profiler.measure(stageName, fn);
    console.debug(`[PipelineProfiler] '${this.name}' completed stage: ${stageName}`);
    return result;
  }

  /**
   * Get a detailed pipeline performance report
   */
  getReport(): string {
    const result = this.profiler.getResult();
    const summary = this.profiler.getSummary();

    // Add pipeline-specific analysis
    const lines = [summary];
    lines.push('\nPipeline Flow Analysis:');

    const sortedStages = Object.values(result.components).sort(
      (a, b) => b.totalTimeMs - a.totalTimeMs
    );

    for (let i = 0; i < sortedStages.length; i++) {
      const stage = sortedStages[i];
      const percent =
        result.totalTimeMs > 0
          ? ((stage.totalTimeMs / result.totalTimeMs) * 100).toFixed(1)
          : '0.0';
      lines.push(`  ${i + 1}. ${stage.name}: ${stage.totalTimeMs.toFixed(2)}ms (${percent}%)`);
    }

    return lines.join('\n');
  }

  /**
   * Get the profiling result
   */
  getResult(): ProfilerResult {
    return this.profiler.getResult();
  }

  /**
   * Get the pipeline name
   */
  get pipelineName(): string {
    return this.name;
  }
}
