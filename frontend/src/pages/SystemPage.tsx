import { useQuery } from '@tanstack/react-query';
import { Activity, Cpu, HardDrive, Server, AlertTriangle } from 'lucide-react';
import { healthApi } from '../api';
import { formatMegabytes, formatDuration } from '../utils/format';
import { POLLING_INTERVALS } from '../utils/constants';

export function SystemPage() {
  const { data: health, error: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.getHealth,
    refetchInterval: POLLING_INTERVALS.NORMAL,
  });

  const { data: detailedHealth, error: detailedHealthError } = useQuery({
    queryKey: ['detailedHealth'],
    queryFn: healthApi.getDetailedHealth,
    refetchInterval: POLLING_INTERVALS.NORMAL,
  });

  const { data: apiInfo } = useQuery({
    queryKey: ['apiInfo'],
    queryFn: healthApi.getAPIInfo,
  });

  const hasError = healthError || detailedHealthError;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return { bg: 'bg-green-100', text: 'text-green-600' };
      case 'degraded':
        return { bg: 'bg-yellow-100', text: 'text-yellow-600' };
      case 'unhealthy':
        return { bg: 'bg-red-100', text: 'text-red-600' };
      default:
        return { bg: 'bg-gray-100', text: 'text-gray-600' };
    }
  };

  const getUtilizationColor = (percent: number): string => {
    if (percent > 80) return 'bg-red-500';
    if (percent > 60) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const statusColors = getStatusColor(detailedHealth?.status ?? health?.status ?? 'unknown');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">System</h2>
        <p className="mt-1 text-sm text-gray-500">
          Monitor system health and performance
        </p>
      </div>

      {hasError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3" role="alert">
          <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Connection Error</h3>
            <p className="mt-1 text-sm text-red-700">
              Unable to fetch system information. Please check if the API server is running.
            </p>
          </div>
        </div>
      )}

      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-full ${statusColors.bg}`}>
            <Activity className={`h-6 w-6 ${statusColors.text}`} aria-hidden="true" />
          </div>
          <div>
            <p className="text-lg font-medium text-gray-900 capitalize">
              {detailedHealth?.status ?? health?.status ?? 'Unknown'} Status
            </p>
            <p className="text-sm text-gray-500">
              Uptime: {formatDuration(health?.uptime_seconds ?? 0)}
            </p>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            <span className="flex items-center gap-2">
              <Cpu className="h-5 w-5 text-gray-400" aria-hidden="true" />
              GPU Status
            </span>
          </h3>
          
          {detailedHealth?.gpu?.available ? (
            <dl className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-gray-500">Device</dt>
                  <dd className="font-medium">{detailedHealth.gpu.device_name}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Compute Capability</dt>
                  <dd className="font-medium">
                    {detailedHealth.gpu.compute_capability ?? 'N/A'}
                  </dd>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-1">
                  <dt className="text-sm text-gray-600">Memory Utilization</dt>
                  <dd className="text-sm font-medium">
                    {detailedHealth.gpu.memory_utilization_percent.toFixed(1)}%
                  </dd>
                </div>
                <div 
                  className="w-full bg-gray-200 rounded-full h-3"
                  role="progressbar"
                  aria-valuenow={detailedHealth.gpu.memory_utilization_percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className={`h-3 rounded-full transition-all duration-300 ${getUtilizationColor(detailedHealth.gpu.memory_utilization_percent)}`}
                    style={{
                      width: `${Math.min(100, detailedHealth.gpu.memory_utilization_percent)}%`,
                    }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {formatMegabytes(detailedHealth.gpu.memory_used_mb)} /{' '}
                  {formatMegabytes(detailedHealth.gpu.memory_total_mb)} used
                </p>
              </div>
            </dl>
          ) : (
            <p className="text-gray-500">No GPU available</p>
          )}
        </section>

        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            <span className="flex items-center gap-2">
              <HardDrive className="h-5 w-5 text-gray-400" aria-hidden="true" />
              System Memory
            </span>
          </h3>
          
          {detailedHealth?.memory && (
            <dl className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <dt className="text-sm text-gray-600">Memory Utilization</dt>
                  <dd className="text-sm font-medium">
                    {detailedHealth.memory.utilization_percent.toFixed(1)}%
                  </dd>
                </div>
                <div 
                  className="w-full bg-gray-200 rounded-full h-3"
                  role="progressbar"
                  aria-valuenow={detailedHealth.memory.utilization_percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className={`h-3 rounded-full transition-all duration-300 ${getUtilizationColor(detailedHealth.memory.utilization_percent)}`}
                    style={{
                      width: `${Math.min(100, detailedHealth.memory.utilization_percent)}%`,
                    }}
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <dt className="text-sm text-gray-500">Total</dt>
                  <dd className="font-medium">
                    {formatMegabytes(detailedHealth.memory.total_mb)}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Used</dt>
                  <dd className="font-medium">
                    {formatMegabytes(detailedHealth.memory.used_mb)}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Available</dt>
                  <dd className="font-medium">
                    {formatMegabytes(detailedHealth.memory.available_mb)}
                  </dd>
                </div>
              </div>
            </dl>
          )}
        </section>

        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            <span className="flex items-center gap-2">
              <Server className="h-5 w-5 text-gray-400" aria-hidden="true" />
              Queue Status
            </span>
          </h3>
          
          {detailedHealth?.queue && (
            <dl className="space-y-3">
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-600">Status</dt>
                <dd
                  className={`text-sm font-medium ${
                    detailedHealth.queue.running ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {detailedHealth.queue.running ? 'Running' : 'Stopped'}
                </dd>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm text-gray-500">Queue Depth</dt>
                  <dd className="font-medium">{detailedHealth.queue.queue_depth}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Running Jobs</dt>
                  <dd className="font-medium">{detailedHealth.queue.running_jobs}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Pending Jobs</dt>
                  <dd className="font-medium">{detailedHealth.queue.pending_jobs}</dd>
                </div>
                <div>
                  <dt className="text-sm text-gray-500">Success Rate</dt>
                  <dd className="font-medium">
                    {detailedHealth.queue.success_rate_percent.toFixed(1)}%
                  </dd>
                </div>
              </div>
            </dl>
          )}
        </section>

        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            <span className="flex items-center gap-2">
              <Server className="h-5 w-5 text-gray-400" aria-hidden="true" />
              API Information
            </span>
          </h3>
          
          {apiInfo && (
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-gray-500">Name</dt>
                <dd className="font-medium">{apiInfo.name}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Version</dt>
                <dd className="font-medium">{apiInfo.version}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Supported Formats</dt>
                <div className="flex flex-wrap gap-1 mt-1">
                  {apiInfo.supported_formats.map((format) => (
                    <span
                      key={format}
                      className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded"
                    >
                      {format.toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Available Models</dt>
                <div className="flex flex-wrap gap-1 mt-1">
                  {apiInfo.supported_models.map((model) => (
                    <span
                      key={model}
                      className="px-2 py-0.5 bg-primary-50 text-primary-700 text-xs rounded"
                    >
                      {model}
                    </span>
                  ))}
                </div>
              </div>
            </dl>
          )}
        </section>
      </div>
    </div>
  );
}
