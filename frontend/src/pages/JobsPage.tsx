import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  X,
  RotateCcw,
  Trash2,
  Plus,
  RefreshCw,
  Filter,
  AlertTriangle,
} from 'lucide-react';
import { StatusBadge, ProgressBar } from '../components';
import { jobsApi, uploadApi } from '../api';
import { formatDuration, capitalize } from '../utils/format';
import { POLLING_INTERVALS, PAGINATION, DEFAULT_JOB_CONFIG } from '../utils/constants';
import type { JobStatus, JobPriority, StereoFormat, DepthModel, DownloadInfo } from '../api';

const statusFilters: (JobStatus | 'all')[] = [
  'all',
  'pending',
  'queued',
  'running',
  'completed',
  'failed',
  'cancelled',
];

export function JobsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<JobStatus | 'all'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  const { data: jobs, isLoading, refetch, error: queryError } = useQuery({
    queryKey: ['jobs', statusFilter, page],
    queryFn: () =>
      jobsApi.listJobs({
        status: statusFilter === 'all' ? undefined : statusFilter,
        page,
        page_size: PAGINATION.DEFAULT_PAGE_SIZE,
      }),
    refetchInterval: POLLING_INTERVALS.NORMAL,
  });

  const { data: uploadedFiles } = useQuery({
    queryKey: ['uploadedFiles'],
    queryFn: uploadApi.listFiles,
  });

  const cancelMutation = useMutation({
    mutationFn: jobsApi.cancelJob,
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const retryMutation = useMutation({
    mutationFn: jobsApi.retryJob,
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const removeMutation = useMutation({
    mutationFn: jobsApi.removeJob,
    onSuccess: () => {
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Jobs</h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage video conversion jobs
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
            aria-label="Refresh jobs list"
          >
            <RefreshCw className="h-5 w-5" aria-hidden="true" />
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            New Job
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {(error || queryError) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Operation Failed</h3>
            <p className="mt-1 text-sm text-red-700">
              {error || (queryError as Error)?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => setError(null)}
              className="mt-2 text-sm font-medium text-red-800 hover:text-red-900"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2" role="group" aria-label="Filter by status">
        <Filter className="h-4 w-4 text-gray-400" aria-hidden="true" />
        {statusFilters.map((status) => (
          <button
            key={status}
            onClick={() => setStatusFilter(status)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              statusFilter === status
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
            aria-pressed={statusFilter === status}
          >
            {capitalize(status)}
          </button>
        ))}
      </div>

      {/* Jobs Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-center text-gray-500" role="status" aria-live="polite">
            Loading...
          </div>
        ) : jobs && jobs.jobs.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Job ID
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Input File
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Status
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Progress
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Duration
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {jobs.jobs.map((job) => (
                    <tr key={job.job_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900 font-mono">
                        {job.job_id.slice(0, 8)}...
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {job.input_filename}
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={job.status} />
                      </td>
                      <td className="px-6 py-4 w-48">
                        {job.status === 'running' || job.status === 'preparing' ? (
                          <ProgressBar progress={job.progress} stage={job.current_stage} />
                        ) : job.status === 'completed' ? (
                          <span className="text-sm text-green-600">Completed</span>
                        ) : job.status === 'failed' ? (
                          <span className="text-sm text-red-600" title={job.result?.error_message || undefined}>
                            {job.result?.error_message?.slice(0, 30) || 'Failed'}
                            {job.result?.error_message && job.result.error_message.length > 30 && '...'}
                          </span>
                        ) : (
                          <span className="text-sm text-gray-400">-</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {formatDuration(job.elapsed_time_seconds)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1" role="group" aria-label="Job actions">
                          {(job.status === 'pending' || job.status === 'queued' || job.status === 'running') && (
                            <button
                              onClick={() => cancelMutation.mutate(job.job_id)}
                              disabled={cancelMutation.isPending}
                              className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded disabled:opacity-50"
                              title="Cancel job"
                              aria-label={`Cancel job ${job.job_id.slice(0, 8)}`}
                            >
                              <X className="h-4 w-4" aria-hidden="true" />
                            </button>
                          )}
                          {job.status === 'failed' && (
                            <button
                              onClick={() => retryMutation.mutate(job.job_id)}
                              disabled={retryMutation.isPending}
                              className="p-1.5 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded disabled:opacity-50"
                              title="Retry job"
                              aria-label={`Retry job ${job.job_id.slice(0, 8)}`}
                            >
                              <RotateCcw className="h-4 w-4" aria-hidden="true" />
                            </button>
                          )}
                          {(job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') && (
                            <button
                              onClick={() => removeMutation.mutate(job.job_id)}
                              disabled={removeMutation.isPending}
                              className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded disabled:opacity-50"
                              title="Remove job"
                              aria-label={`Remove job ${job.job_id.slice(0, 8)}`}
                            >
                              <Trash2 className="h-4 w-4" aria-hidden="true" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {jobs.total_count > jobs.page_size && (
              <nav className="px-6 py-4 border-t border-gray-200 flex items-center justify-between" aria-label="Pagination">
                <p className="text-sm text-gray-500">
                  Showing {jobs.jobs.length} of {jobs.total_count} jobs
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                    aria-label="Previous page"
                  >
                    Previous
                  </button>
                  <span className="px-3 py-1 text-sm text-gray-600" aria-current="page">
                    Page {page}
                  </span>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={jobs.jobs.length < jobs.page_size}
                    className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                    aria-label="Next page"
                  >
                    Next
                  </button>
                </div>
              </nav>
            )}
          </>
        ) : (
          <div className="p-6 text-center text-gray-500">
            No jobs found. Create a new job to get started.
          </div>
        )}
      </div>

      {/* Create Job Modal */}
      {showCreateModal && (
        <CreateJobModal
          files={uploadedFiles || []}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            queryClient.invalidateQueries({ queryKey: ['jobs'] });
          }}
          onError={(err) => setError(err)}
        />
      )}
    </div>
  );
}

interface CreateJobModalProps {
  files: DownloadInfo[];
  onClose: () => void;
  onSuccess: () => void;
  onError: (error: string) => void;
}

function CreateJobModal({ files, onClose, onSuccess, onError }: CreateJobModalProps) {
  const [selectedFileId, setSelectedFileId] = useState('');
  const [priority, setPriority] = useState<JobPriority>('normal');
  const [stereoFormat, setStereoFormat] = useState<StereoFormat>('side_by_side');
  const [depthModel, setDepthModel] = useState<DepthModel>('midas_small');
  const [useGpu, setUseGpu] = useState(true);

  const createMutation = useMutation({
    mutationFn: () =>
      jobsApi.submitJob({
        input_file_id: selectedFileId,
        priority,
        config: {
          stereo_format: stereoFormat,
          depth_model: depthModel,
          use_gpu: useGpu,
          quality_preset: DEFAULT_JOB_CONFIG.QUALITY_PRESET,
          output_codec: DEFAULT_JOB_CONFIG.OUTPUT_CODEC,
          output_crf: DEFAULT_JOB_CONFIG.OUTPUT_CRF,
        },
      }),
    onSuccess,
    onError: (err: Error) => onError(err.message),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate();
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <form className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4" onSubmit={handleSubmit}>
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 id="modal-title" className="text-lg font-medium text-gray-900">Create New Job</h3>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label htmlFor="input-file" className="block text-sm font-medium text-gray-700 mb-1">
              Input File
            </label>
            <select
              id="input-file"
              value={selectedFileId}
              onChange={(e) => setSelectedFileId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-primary-500 focus:border-primary-500"
              required
            >
              <option value="">Select a file...</option>
              {files.map((file) => (
                <option key={file.file_id} value={file.file_id}>
                  {file.filename}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <select
              id="priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as JobPriority)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="low">Low</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </div>

          <div>
            <label htmlFor="stereo-format" className="block text-sm font-medium text-gray-700 mb-1">
              3D Format
            </label>
            <select
              id="stereo-format"
              value={stereoFormat}
              onChange={(e) => setStereoFormat(e.target.value as StereoFormat)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="side_by_side">Side by Side</option>
              <option value="anaglyph">Anaglyph</option>
              <option value="interlaced">Interlaced</option>
              <option value="vr">VR</option>
            </select>
          </div>

          <div>
            <label htmlFor="depth-model" className="block text-sm font-medium text-gray-700 mb-1">
              Depth Model
            </label>
            <select
              id="depth-model"
              value={depthModel}
              onChange={(e) => setDepthModel(e.target.value as DepthModel)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="midas_small">MiDaS Small (Fast)</option>
              <option value="midas_hybrid">MiDaS Hybrid (Balanced)</option>
              <option value="dpt_hybrid">DPT Hybrid (Quality)</option>
              <option value="dpt_large">DPT Large (Best Quality)</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="useGpu"
              checked={useGpu}
              onChange={(e) => setUseGpu(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <label htmlFor="useGpu" className="text-sm text-gray-700">
              Use GPU acceleration
            </label>
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!selectedFileId || createMutation.isPending}
            className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating...' : 'Create Job'}
          </button>
        </div>
      </form>
    </div>
  );
}
