import { memo, useMemo } from 'react';
import { TrendingDown, Clock, Cpu, MemoryStick, BarChart3 } from 'lucide-react';
import type { ModelResult, ComparisonModel } from '../api';

interface MetricsPanelProps {
  /** All model results to compare */
  results: ModelResult[];
  /** Currently selected model for highlighting */
  selectedModel?: ComparisonModel | null;
  /** Additional CSS class names */
  className?: string;
}

interface MetricRow {
  label: string;
  key: keyof ModelResult['metrics'];
  unit: string;
  format: (value: number) => string;
  lowerIsBetter?: boolean;
  icon: React.ReactNode;
}

/** Core metrics always displayed */
const METRIC_ROWS: MetricRow[] = [
  {
    label: 'Processing Time',
    key: 'processing_time_seconds',
    unit: 's',
    format: (v) => v.toFixed(2),
    lowerIsBetter: true,
    icon: <Clock className="h-4 w-4" />,
  },
  {
    label: 'Confidence Score',
    key: 'avg_confidence',
    unit: '%',
    format: (v) => (v * 100).toFixed(0),
    icon: <BarChart3 className="h-4 w-4" />,
  },
  {
    label: 'Memory Usage',
    key: 'memory_usage_mb',
    unit: 'MB',
    format: (v) => v.toFixed(0),
    lowerIsBetter: true,
    icon: <MemoryStick className="h-4 w-4" />,
  },
];

/** Optional metrics that display only if available */
const OPTIONAL_METRICS: MetricRow[] = [
  {
    label: 'Quality Score',
    key: 'quality_score',
    unit: '%',
    format: (v) => (v * 100).toFixed(0),
    icon: <TrendingDown className="h-4 w-4" />,
  },
  {
    label: 'Edge Preservation',
    key: 'edge_score',
    unit: '%',
    format: (v) => (v * 100).toFixed(0),
    icon: <Cpu className="h-4 w-4" />,
  },
  {
    label: 'Temporal Consistency',
    key: 'temporal_consistency',
    unit: '%',
    format: (v) => (v * 100).toFixed(0),
    icon: <Clock className="h-4 w-4" />,
  },
];

/** Helper to extract numeric values from metrics */
function getNumericValues(
  results: ModelResult[],
  key: keyof ModelResult['metrics']
): number[] {
  return results
    .map((r) => r.metrics[key])
    .filter((v): v is number => typeof v === 'number');
}

function MetricsPanelInternal({
  results,
  selectedModel,
  className = '',
}: MetricsPanelProps) {
  // Pre-compute best values for each metric to avoid repeated calculations
  const bestValues = useMemo(() => {
    const best: Record<string, number | null> = {};
    
    [...METRIC_ROWS, ...OPTIONAL_METRICS].forEach((metric) => {
      const values = getNumericValues(results, metric.key);
      if (values.length > 0) {
        best[metric.key] = metric.lowerIsBetter 
          ? Math.min(...values) 
          : Math.max(...values);
      } else {
        best[metric.key] = null;
      }
    });
    
    return best;
  }, [results]);

  // Check if any optional metrics have data
  const hasOptionalMetrics = useMemo(
    () => OPTIONAL_METRICS.some((metric) =>
      results.some((r) => typeof r.metrics[metric.key] === 'number')
    ),
    [results]
  );

  // Filter optional metrics to only show those with data
  const visibleOptionalMetrics = useMemo(
    () => OPTIONAL_METRICS.filter((metric) =>
      results.some((r) => typeof r.metrics[metric.key] === 'number')
    ),
    [results]
  );

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-900">Comparison Metrics</h3>
        <p className="text-xs text-gray-500 mt-0.5">
          Side-by-side comparison of model performance
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Metric
              </th>
              {results.map((result) => (
                <th
                  key={result.model}
                  className={`px-4 py-3 text-center text-xs font-medium uppercase tracking-wider ${
                    selectedModel === result.model
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-gray-500'
                  }`}
                >
                  {result.model_name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {METRIC_ROWS.map((metric) => {
              const bestValue = bestValues[metric.key];
              
              return (
                <tr key={metric.key} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">{metric.icon}</span>
                      <span className="text-sm text-gray-900">{metric.label}</span>
                    </div>
                  </td>
                  {results.map((result) => {
                    const value = result.metrics[metric.key];
                    const isBest = typeof value === 'number' && value === bestValue;
                    
                    return (
                      <td
                        key={result.model}
                        className={`px-4 py-3 text-center ${
                          selectedModel === result.model ? 'bg-primary-50' : ''
                        }`}
                      >
                        <div className="flex items-center justify-center gap-1">
                          <span
                            className={`text-sm font-medium ${
                              isBest ? 'text-green-600' : 'text-gray-900'
                            }`}
                          >
                            {typeof value === 'number' ? metric.format(value) : '-'}
                            {typeof value === 'number' ? metric.unit : ''}
                          </span>
                          {isBest && (
                            <span className="text-green-500" aria-label="Best value">★</span>
                          )}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
            
            {hasOptionalMetrics && (
              <>
                <tr className="bg-gray-50">
                  <td colSpan={results.length + 1} className="px-4 py-2">
                    <span className="text-xs font-medium text-gray-500 uppercase">
                      Additional Metrics
                    </span>
                  </td>
                </tr>
                {visibleOptionalMetrics.map((metric) => {
                  const bestValue = bestValues[metric.key];
                  
                  return (
                    <tr key={metric.key} className="hover:bg-gray-50">
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-400">{metric.icon}</span>
                          <span className="text-sm text-gray-900">{metric.label}</span>
                        </div>
                      </td>
                      {results.map((result) => {
                        const value = result.metrics[metric.key];
                        const isBest = typeof value === 'number' && value === bestValue;
                        
                        return (
                          <td
                            key={result.model}
                            className={`px-4 py-3 text-center ${
                              selectedModel === result.model ? 'bg-primary-50' : ''
                            }`}
                          >
                            <div className="flex items-center justify-center gap-1">
                              <span
                                className={`text-sm font-medium ${
                                  isBest ? 'text-green-600' : 'text-gray-900'
                                }`}
                              >
                                {typeof value === 'number' ? metric.format(value) : '-'}
                                {typeof value === 'number' ? metric.unit : ''}
                              </span>
                              {isBest && (
                                <span className="text-green-500" aria-label="Best value">★</span>
                              )}
                            </div>
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </>
            )}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="text-green-500">★</span>
            <span>Best in category</span>
          </span>
          <span className="flex items-center gap-1">
            <TrendingDown className="h-3 w-3" />
            <span>Lower is better</span>
          </span>
        </div>
      </div>
    </div>
  );
}

/**
 * MetricsPanel component for displaying side-by-side model metrics comparison
 * Memoized to prevent unnecessary re-renders
 */
const MetricsPanel = memo(MetricsPanelInternal);

export { MetricsPanel };
export default MetricsPanel;
