import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Trash2, Upload as UploadIcon, FileVideo, AlertCircle, AlertTriangle } from 'lucide-react';
import { FileDropZone } from '../components';
import { uploadApi } from '../api';
import { formatBytes, formatDate } from '../utils/format';
import { POLLING_INTERVALS } from '../utils/constants';
import type { DownloadInfo } from '../api';

export function UploadPage() {
  const queryClient = useQueryClient();

  const { data: files, isLoading, error } = useQuery({
    queryKey: ['uploadedFiles'],
    queryFn: uploadApi.listFiles,
    refetchInterval: POLLING_INTERVALS.NORMAL,
  });

  const uploadMutation = useMutation({
    mutationFn: uploadApi.uploadFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploadedFiles'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: uploadApi.deleteFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploadedFiles'] });
    },
  });

  const handleFilesSelected = async (selectedFiles: File[]) => {
    for (const file of selectedFiles) {
      try {
        await uploadMutation.mutateAsync(file);
      } catch (error) {
        // Error is handled by the mutation state
        console.error('Upload failed:', error);
      }
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Upload Videos</h2>
        <p className="mt-1 text-sm text-gray-500">
          Upload 2D video files for conversion to 3D
        </p>
      </div>

      {/* Error Alert */}
      {(uploadMutation.isError || deleteMutation.isError || error) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <h3 className="text-sm font-medium text-red-800">Operation Failed</h3>
            <p className="mt-1 text-sm text-red-700">
              {uploadMutation.error?.message || 
               deleteMutation.error?.message || 
               (error as Error)?.message ||
               'An unexpected error occurred'}
            </p>
          </div>
        </div>
      )}

      {/* Upload Zone */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <FileDropZone
          onFilesSelected={handleFilesSelected}
          disabled={uploadMutation.isPending}
        />
        
        {uploadMutation.isPending && (
          <div className="mt-4 space-y-2" role="status" aria-live="polite">
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <UploadIcon className="h-4 w-4 animate-pulse" aria-hidden="true" />
              Uploading file...
            </div>
          </div>
        )}
      </div>

      {/* Uploaded Files */}
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Uploaded Files</h3>
        </div>
        
        {isLoading ? (
          <div className="p-6 text-center text-gray-500" role="status" aria-live="polite">
            Loading...
          </div>
        ) : files && files.length > 0 ? (
          <ul className="divide-y divide-gray-200" role="list">
            {files.map((file: DownloadInfo) => (
              <li
                key={file.file_id}
                className="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
              >
                <div className="flex items-center gap-3">
                  <FileVideo className="h-5 w-5 text-gray-400" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {file.filename}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatBytes(file.file_size_bytes)} • Uploaded{' '}
                      {formatDate(file.created_at)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(file.file_id)}
                  disabled={deleteMutation.isPending}
                  className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                  title="Delete file"
                  aria-label={`Delete ${file.filename}`}
                >
                  <Trash2 className="h-4 w-4" aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div className="p-6 text-center">
            <AlertCircle className="h-8 w-8 text-gray-400 mx-auto" aria-hidden="true" />
            <p className="mt-2 text-sm text-gray-500">No files uploaded yet</p>
          </div>
        )}
      </div>
    </div>
  );
}
