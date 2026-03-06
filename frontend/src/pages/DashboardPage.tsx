import { useQuery } from '@tanstack/react-query';
import {
  ListVideo,
  CheckCircle,
  XCircle,
  Clock,
  Cpu,
  HardDrive,
  AlertTriangle,
} from 'lucide-react';
import { StatCard } from '../components';
import { jobsApi, healthApi } from '../api';
import { formatUptime, formatMegabytes } from '../utils/format';
import { POLLING_INTERVALS } from '../utils/constants';

export function DashboardPage() {
  const { data: queueStats, error: queueError } = useQuery({
    queryKey: ['queueStats'],
    queryFn: jobsApi.getQueueStats,
    refetchInterval: POLLING_INTERVALS.NORMAL,
  });

  const { data: health, error: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.getHealth,
    refetchInterval: POLLING_INTERVALS.SLOW,
  });

  const { data: detailedHealth, error: detailedHealthError } = useQuery({
    queryKey: ['detailedHealth'],
    queryFn: healthApi.getDetailedHealth,
    refetchInterval: POLLING_INTERVALS.SLOW,
  });

  const hasError = queueError || healthError || detailedHealthError;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your 2D to 3D video conversion system
        </p>
      </div>

      {/* Error Alert */}
      {hasError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Connection Error</h3>
            <p className="mt-1 text-sm text-red-700">
              Unable to fetch system status. Please check if the API server is running.
            </p>
          </div>
        </div>
      )}

      {/* Queue Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Jobs"
          value={queueStats?.total_jobs ?? 0}
          icon={<ListVideo className="h-6 w-6 text-primary-600" aria-hidden="true" />}
        />
        <StatCard
          title="Completed"
          value={queueStats?.completed_jobs ?? 0}
          icon={<CheckCircle className="h-6 w-6 text-green-600" aria-hidden="true" />}
        />
        <StatCard
          title="Failed"
          value={queueStats?.failed_jobs ?? 0}
          icon={<XCircle className="h-6 w-6 text-red-600" aria-hidden="true" />}
        />
        <StatCard
          title="Success Rate"
          value={`${(queueStats?.success_rate_percent ?? 0).toFixed(1)}%`}
          icon={<Clock className="h-6 w-6 text-blue-600" aria-hidden="true" />}
        />
      </div>

      {/* System Health */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        {/* Service Status */}
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Service Status</h3>
          <dl className="space-y-4">
            <div className="flex items-center justify-between">
              <dt className="text-sm text-gray-600">API Version</dt>
              <dd className="text-sm font-medium">{health?.version ?? '-'}</dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-sm text-gray-600">Uptime</dt>
              <dd className="text-sm font-medium">
                {formatUptime(health?.uptime_seconds ?? 0)}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-sm text-gray-600">Queue Status</dt>
              <dd
                className={`text-sm font-medium ${
                  health?.queue_running ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {health?.queue_running ? 'Running' : 'Stopped'}
              </dd>
            </div>
            <div className="flex items-center justify-between">
              <dt className="text-sm text-gray-600">GPU Available</dt>
              <dd
                className={`text-sm font-medium ${
                  health?.gpu_available ? 'text-green-600' : 'text-yellow-600'
                }`}
              >
                {health?.gpu_available ? 'Yes' : 'No'}
              </dd>
            </div>
          </dl>
        </section>

        {/* GPU Status */}
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            <span className="flex items-center gap-2">
              <Cpu className="h-5 w-5" aria-hidden="true" />
              GPU Status
            </span>
          </h3>
          {detailedHealth?.gpu?.available ? (
            <dl className="space-y-4">
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-600">Device</dt>
                <dd className="text-sm font-medium">
                  {detailedHealth.gpu.device_name ?? 'Unknown'}
                </dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-sm text-gray-600">Memory Used</dt>
                <dd className="text-sm font-medium">
                  {detailedHealth.gpu.memory_used_mb.toFixed(0)} MB /{' '}
                  {detailedHealth.gpu.memory_total_mb.toFixed(0)} MB
                </dd>
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <dt className="text-sm text-gray-600">Memory Utilization</dt>
                  <dd className="text-sm font-medium">
                    {detailedHealth.gpu.memory_utilization_percent.toFixed(1)}%
                  </dd>
                </div>
                <div 
                  className="w-full bg-gray-200 rounded-full h-2"
                  role="progressbar"
                  aria-valuenow={detailedHealth.gpu.memory_utilization_percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.min(100, detailedHealth.gpu.memory_utilization_percent)}%`,
                    }}
                  />
                </div>
              </div>
            </dl>
          ) : (
            <p className="text-sm text-gray-500">No GPU available</p>
          )}
        </section>
      </div>

      {/* Memory Status */}
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          <span className="flex items-center gap-2">
            <HardDrive className="h-5 w-5" aria-hidden="true" />
            System Memory
          </span>
        </h3>
        {detailedHealth?.memory && (
          <dl className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <dt className="text-sm text-gray-600">Total</dt>
              <dd className="text-lg font-medium">
                {formatMegabytes(detailedHealth.memory.total_mb)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600">Used</dt>
              <dd className="text-lg font-medium">
                {formatMegabytes(detailedHealth.memory.used_mb)}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-gray-600">Available</dt>
              <dd className="text-lg font-medium">
                {formatMegabytes(detailedHealth.memory.available_mb)}
              </dd>
            </div>
          </dl>
        )}
      </section>
    </div>
  );
}
