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
  ComparisonSession,
  CreateComparisonRequest,
  SubmitVoteRequest,
  SubmitVoteResponse,
  LeaderboardResponse,
  Notification,
  NotificationListResponse,
  NotificationCountResponse,
  MarkReadRequest,
  MarkReadResponse,
  DismissRequest,
  DismissResponse,
  WebhookConfig,
  NotificationType,
  ThumbnailFrame,
  ThumbnailGridRequest,
  ThumbnailGridResponse,
  // Auth types
  UserRole,
  UserRegisterRequest,
  UserLoginRequest,
  TokenRefreshRequest,
  UserResponse,
  TokenResponse,
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

export const comparisonApi = {
  /** Create a new comparison session for a job/frame */
  createSession: async (request: CreateComparisonRequest): Promise<ComparisonSession> => {
    const response = await api.post<ComparisonSession>('/comparison/', request);
    return response.data;
  },

  /** Get an existing comparison session */
  getSession: async (sessionId: string): Promise<ComparisonSession> => {
    const response = await api.get<ComparisonSession>(`/comparison/${sessionId}`);
    return response.data;
  },

  /** Get comparison session for a specific job and frame */
  getSessionForJob: async (jobId: string, frameIndex?: number): Promise<ComparisonSession> => {
    const params = frameIndex !== undefined ? { frame_index: frameIndex } : {};
    const response = await api.get<ComparisonSession>(`/comparison/job/${jobId}`, { params });
    return response.data;
  },

  /** Submit a vote for a model */
  submitVote: async (request: SubmitVoteRequest): Promise<SubmitVoteResponse> => {
    const response = await api.post<SubmitVoteResponse>(`/comparison/${request.session_id}/vote`, {
      model: request.model,
      comment: request.comment,
    });
    return response.data;
  },

  /** Remove user's vote from a session */
  removeVote: async (sessionId: string): Promise<void> => {
    await api.delete(`/comparison/${sessionId}/vote`);
  },

  /** Get the model leaderboard */
  getLeaderboard: async (): Promise<LeaderboardResponse> => {
    const response = await api.get<LeaderboardResponse>('/comparison/leaderboard');
    return response.data;
  },

  /** Get random comparison session for voting */
  getRandomSession: async (): Promise<ComparisonSession | null> => {
    const response = await api.get<ComparisonSession | null>('/comparison/random');
    return response.data;
  },
};

export const notificationsApi = {
  /** List notifications with optional filtering */
  listNotifications: async (params?: {
    include_read?: boolean;
    include_dismissed?: boolean;
    notification_type?: NotificationType;
    job_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<NotificationListResponse> => {
    const response = await api.get<NotificationListResponse>('/notifications/', { params });
    return response.data;
  },

  /** Get a specific notification */
  getNotification: async (notificationId: string): Promise<Notification> => {
    const response = await api.get<Notification>(`/notifications/${notificationId}`);
    return response.data;
  },

  /** Get notification counts */
  getCounts: async (): Promise<NotificationCountResponse> => {
    const response = await api.get<NotificationCountResponse>('/notifications/count');
    return response.data;
  },

  /** Mark notifications as read */
  markAsRead: async (request: MarkReadRequest): Promise<MarkReadResponse> => {
    const response = await api.post<MarkReadResponse>('/notifications/mark-read', request);
    return response.data;
  },

  /** Mark all notifications as read */
  markAllAsRead: async (): Promise<MarkReadResponse> => {
    const response = await api.post<MarkReadResponse>('/notifications/mark-all-read');
    return response.data;
  },

  /** Dismiss notifications */
  dismiss: async (request: DismissRequest): Promise<DismissResponse> => {
    const response = await api.post<DismissResponse>('/notifications/dismiss', request);
    return response.data;
  },

  /** Delete a notification */
  deleteNotification: async (notificationId: string): Promise<void> => {
    await api.delete(`/notifications/${notificationId}`);
  },

  /** Clear all notifications */
  clearAll: async (): Promise<void> => {
    await api.delete('/notifications/');
  },

  /** Add a webhook configuration */
  addWebhook: async (config: WebhookConfig): Promise<{ message: string; url: string }> => {
    const response = await api.post<{ message: string; url: string }>('/notifications/webhooks', config);
    return response.data;
  },

  /** List webhook configurations */
  listWebhooks: async (): Promise<WebhookConfig[]> => {
    const response = await api.get<WebhookConfig[]>('/notifications/webhooks');
    return response.data;
  },

  /** Remove a webhook configuration */
  removeWebhook: async (url: string): Promise<void> => {
    await api.delete('/notifications/webhooks', { params: { url } });
  },
};

export const thumbnailApi = {
  /** Get thumbnail grid data for a job */
  getThumbnailGrid: async (jobId: string, options?: ThumbnailGridRequest): Promise<ThumbnailGridResponse> => {
    const response = await api.get<ThumbnailGridResponse>(`/jobs/${jobId}/thumbnails`, { params: options });
    return response.data;
  },

  /** Get a single frame thumbnail */
  getFrameThumbnail: async (jobId: string, frameIndex: number): Promise<ThumbnailFrame> => {
    const response = await api.get<ThumbnailFrame>(`/jobs/${jobId}/frames/${frameIndex}/thumbnail`);
    return response.data;
  },
};

export const authApi = {
  /** Register a new user */
  register: async (request: UserRegisterRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/register', request);
    return response.data;
  },

  /** Login with username/email and password */
  login: async (request: UserLoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/login', request);
    return response.data;
  },

  /** Refresh access token */
  refreshToken: async (request: TokenRefreshRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/auth/refresh', request);
    return response.data;
  },

  /** Get current user info */
  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await api.get<UserResponse>('/auth/me');
    return response.data;
  },

  /** Logout (client should discard tokens) */
  logout: async (): Promise<{ message: string }> => {
    const response = await api.post<{ message: string }>('/auth/logout');
    return response.data;
  },

  /** Set authorization header for authenticated requests */
  setAuthToken: (token: string | null): void => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete api.defaults.headers.common['Authorization'];
    }
  },
};

export default api;

