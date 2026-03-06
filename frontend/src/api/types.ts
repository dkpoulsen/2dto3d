// API Types matching FastAPI backend schemas

export type JobStatus = 
  | 'pending' 
  | 'queued' 
  | 'preparing' 
  | 'running' 
  | 'paused' 
  | 'completed' 
  | 'failed' 
  | 'cancelled' 
  | 'retrying' 
  | 'skipped';

export type JobPriority = 'low' | 'normal' | 'high' | 'urgent';

export type StereoFormat = 'side_by_side' | 'anaglyph' | 'interlaced' | 'vr';

export type DepthModel = 'midas_small' | 'midas_hybrid' | 'dpt_large' | 'dpt_hybrid';

export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';

// Request types
export interface JobConfig {
  stereo_format: StereoFormat;
  depth_model: DepthModel;
  use_gpu: boolean;
  quality_preset: 'fast' | 'balanced' | 'quality';
  output_codec: string;
  output_crf: number;
  extra_options?: Record<string, unknown>;
}

export interface SubmitJobRequest {
  input_file_id: string;
  output_filename?: string;
  priority?: JobPriority;
  config?: JobConfig;
  callback_url?: string;
  scheduled_at?: string;
  depends_on?: string[];
}

export interface SubmitBatchRequest {
  input_file_ids: string[];
  priority?: JobPriority;
  config?: JobConfig;
}

// Response types
export interface UploadResponse {
  file_id: string;
  filename: string;
  file_size_bytes: number;
  content_type: string | null;
  upload_time: string;
  message: string;
}

export interface JobResult {
  success: boolean;
  output_file_id: string | null;
  output_filename: string | null;
  error_message: string | null;
  error_type: string | null;
  frames_processed: number;
  processing_time_seconds: number;
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  priority: JobPriority;
  input_filename: string;
  output_filename: string | null;
  progress: number;
  current_stage: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  elapsed_time_seconds: number | null;
  estimated_remaining_seconds: number | null;
  retry_count: number;
  result: JobResult | null;
  config: Record<string, unknown>;
  scheduled_at: string | null;
  depends_on: string[];
  dependent_jobs: string[];
}

export interface JobListResponse {
  jobs: JobResponse[];
  total_count: number;
  page: number;
  page_size: number;
}

export interface SubmitJobResponse {
  job_id: string;
  status: JobStatus;
  message: string;
  status_url: string;
}

export interface QueueStats {
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
  skipped_jobs: number;
  total_frames_processed: number;
  total_processing_time_seconds: number;
  average_processing_time_seconds: number;
  success_rate_percent: number;
}

export interface DownloadInfo {
  file_id: string;
  filename: string;
  file_size_bytes: number;
  content_type: string;
  download_url: string;
  created_at: string;
}

export interface GPUStatus {
  available: boolean;
  device_name: string | null;
  device_count: number;
  memory_used_mb: number;
  memory_free_mb: number;
  memory_total_mb: number;
  memory_utilization_percent: number;
  compute_capability: string | null;
}

export interface SystemMemory {
  total_mb: number;
  available_mb: number;
  used_mb: number;
  utilization_percent: number;
}

export interface QueueHealth {
  running: boolean;
  paused: boolean;
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  queue_depth: number;
  success_rate_percent: number;
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  uptime_seconds: number;
  queue_running: boolean;
  gpu_available: boolean;
}

export interface ComprehensiveHealthResponse {
  status: HealthStatus;
  version: string;
  uptime_seconds: number;
  timestamp: string;
  gpu: GPUStatus;
  memory: SystemMemory;
  queue: QueueHealth;
  checks: Record<string, boolean>;
}

export interface APIInfoResponse {
  name: string;
  version: string;
  description: string;
  endpoints: Record<string, string>;
  supported_formats: string[];
  supported_models: string[];
}

export interface CancelJobResponse {
  job_id: string;
  cancelled: boolean;
  message: string;
}

export interface RetryJobResponse {
  job_id: string;
  retried: boolean;
  retry_count: number;
  message: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
  detail?: Record<string, unknown>;
  request_id?: string;
}
