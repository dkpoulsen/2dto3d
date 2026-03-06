import axios, { AxiosError } from 'axios';
import type {
  UploadResponse,
  JobResponse,
  JobListResponse,
  SubmitJobRequest,
  SubmitJobResponse,
  SubmitBatchRequest,
  QueueStats,
  DownloadInfo,
  HealthCheckResponse,
  ComprehensiveHealthResponse,
  APIInfoResponse,
  CancelJobResponse,
  RetryJobResponse,
  ErrorResponse,
  DepthValidationSession,
  DepthMapCorrection,
  DepthMapCorrectionResponse,
} from './types';
import { API_CONFIG } from '../utils/constants';

const api = axios.create({
  baseURL: API_CONFIG.BASE_URL,
  timeout: API_CONFIG.DEFAULT_TIMEOUT_MS,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ErrorResponse>) => {
    const message = error.response?.data?.message || error.message || 'An error occurred';
    return Promise.reject(new Error(message));
  }
);

export const uploadApi = {
  uploadFile: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<UploadResponse>('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: API_CONFIG.UPLOAD_TIMEOUT_MS,
  });
    return response.data;
  },

  listFiles: async (): Promise<DownloadInfo[]> => {
    const response = await api.get<DownloadInfo[]>('/upload/');
    return response.data;
  },

  getFileInfo: async (fileId: string): Promise<DownloadInfo> => {
    const response = await api.get<DownloadInfo>(`/upload/${fileId}`);
    return response.data;
  },

  deleteFile: async (fileId: string): Promise<void> => {
    await api.delete(`/upload/${fileId}`);
  },
};

export const jobsApi = {
  submitJob: async (request: SubmitJobRequest): Promise<SubmitJobResponse> => {
    const response = await api.post<SubmitJobResponse>('/jobs/', request);
    return response.data;
  },

  submitBatch: async (request: SubmitBatchRequest): Promise<SubmitJobResponse[]> => {
    const response = await api.post<SubmitJobResponse[]>('/jobs/batch', request);
    return response.data;
  },

  getJob: async (jobId: string): Promise<JobResponse> => {
    const response = await api.get<JobResponse>(`/jobs/${jobId}`);
    return response.data;
  },

  listJobs: async (params?: {
    status?: string;
    page?: number;
    page_size?: number;
  }): Promise<JobListResponse> => {
    const response = await api.get<JobListResponse>('/jobs/', { params });
    return response.data;
  },

  cancelJob: async (jobId: string): Promise<CancelJobResponse> => {
    const response = await api.post<CancelJobResponse>(`/jobs/${jobId}/cancel`);
    return response.data;
  },

  retryJob: async (jobId: string): Promise<RetryJobResponse> => {
    const response = await api.post<RetryJobResponse>(`/jobs/${jobId}/retry`);
    return response.data;
  },

  removeJob: async (jobId: string): Promise<void> => {
    await api.delete(`/jobs/${jobId}`);
  },

  getQueueStats: async (): Promise<QueueStats> => {
    const response = await api.get<QueueStats>('/jobs/stats/queue');
    return response.data;
  },
};

export const downloadsApi = {
  listDownloads: async (): Promise<DownloadInfo[]> => {
    const response = await api.get<DownloadInfo[]>('/download/');
    return response.data;
  },

  getDownloadInfo: async (fileId: string): Promise<DownloadInfo> => {
    const response = await api.get<DownloadInfo>(`/download/${fileId}/info`);
    return response.data;
  },

  getDownloadUrl: (fileId: string): string => {
    return `${API_CONFIG.BASE_URL}/download/${fileId}`;
  },

  deleteDownload: async (fileId: string): Promise<void> => {
    await api.delete(`/download/${fileId}`);
  },
};

export const healthApi = {
  getHealth: async (): Promise<HealthCheckResponse> => {
    const response = await api.get<HealthCheckResponse>('/health');
    return response.data;
  },

  getDetailedHealth: async (): Promise<ComprehensiveHealthResponse> => {
    const response = await api.get<ComprehensiveHealthResponse>('/health/detailed');
    return response.data;
  },

  getAPIInfo: async (): Promise<APIInfoResponse> => {
    const response = await api.get<APIInfoResponse>('/');
    return response.data;
  },

  getQueueStats: async (): Promise<QueueStats> => {
    const response = await api.get<QueueStats>('/queue');
    return response.data;
  },
};

export const depthValidationApi = {
  getValidationSession: async (jobId: string): Promise<DepthValidationSession> => {
    const response = await api.get<DepthValidationSession>(`/jobs/${jobId}/depth-validation`);
    return response.data;
  },

  getFrameDepthMap: async (jobId: string, frameIndex: number): Promise<Blob> => {
    const response = await api.get(`/jobs/${jobId}/frames/${frameIndex}/depth-map`, {
      responseType: 'blob',
    });
    return response.data;
  },

  getFrameOriginal: async (jobId: string, frameIndex: number): Promise<Blob> => {
    const response = await api.get(`/jobs/${jobId}/frames/${frameIndex}/original`, {
      responseType: 'blob',
    });
    return response.data;
  },

  submitCorrection: async (correction: DepthMapCorrection): Promise<DepthMapCorrectionResponse> => {
    const response = await api.post<DepthMapCorrectionResponse>(
      `/jobs/${correction.job_id}/frames/${correction.frame_index}/depth-correction`,
      correction
    );
    return response.data;
  },

  markFrameValidated: async (jobId: string, frameIndex: number): Promise<void> => {
    await api.post(`/jobs/${jobId}/frames/${frameIndex}/validate`);
  },
};

export default api;
