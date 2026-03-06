import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Download, Trash2, FileVideo, AlertCircle, AlertTriangle } from 'lucide-react';
import { downloadsApi } from '../api';
import { formatBytes, formatDate } from '../utils/format';
import { POLLING_INTERVALS } from '../utils/constants';
import type { DownloadInfo } from '../api';

export function DownloadsPage() {
  const queryClient = useQueryClient();

  const { data: downloads, isLoading, error } = useQuery({
    queryKey: ['downloads'],
    queryFn: downloadsApi.listDownloads,
    refetchInterval: POLLING_INTERVALS.NORMAL,
  });

  const deleteMutation = useMutation({
    mutationFn: downloadsApi.deleteDownload,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['downloads'] }),
  });

  const handleDownload = (file: DownloadInfo) => {
    const link = document.createElement('a');
    link.href = downloadsApi.getDownloadUrl(file.file_id);
    link.download = file.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const errorMessage = deleteMutation.error?.message || (error as Error)?.message;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Downloads</h2>
        <p className="mt-1 text-sm text-gray-500">
          Download your converted 3D videos
        </p>
      </div>

      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3" role="alert">
          <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Operation Failed</h3>
            <p className="mt-1 text-sm text-red-700">{errorMessage}</p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-center text-gray-500" role="status" aria-live="polite">
            Loading...
          </div>
        ) : downloads && downloads.length > 0 ? (
          <ul className="divide-y divide-gray-200" role="list">
            {downloads.map((file) => (
              <li
                key={file.file_id}
                className="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <FileVideo className="h-8 w-8 text-primary-600" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.filename}</p>
                    <p className="text-xs text-gray-500">
                      {formatBytes(file.file_size_bytes)} • Created {formatDate(file.created_at)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDownload(file)}
                    className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700"
                    aria-label={`Download ${file.filename}`}
                  >
                    <Download className="h-4 w-4" aria-hidden="true" />
                    Download
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(file.file_id)}
                    disabled={deleteMutation.isPending}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded disabled:opacity-50"
                    aria-label={`Delete ${file.filename}`}
                  >
                    <Trash2 className="h-4 w-4" aria-hidden="true" />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="p-6 text-center">
            <AlertCircle className="h-8 w-8 text-gray-400 mx-auto" aria-hidden="true" />
            <p className="mt-2 text-sm text-gray-500">No converted files available yet</p>
            <p className="mt-1 text-xs text-gray-400">Complete some jobs to see results here</p>
          </div>
        )}
      </div>
    </div>
  );
}
