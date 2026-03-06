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

// Depth Curve Types
export type CurvePreset = 
  | 'linear' 
  | 's_curve' 
  | 'contrast_boost' 
  | 'soft_curve' 
  | 'inverse_s' 
  | 'shadow_lift' 
  | 'highlight_compress';

export interface CurveControlPoint {
  x: number;  // 0-1 normalized
  y: number;  // 0-1 normalized
}

export interface DepthCurveConfig {
  enabled: boolean;
  preset?: CurvePreset | null;
  control_points: CurveControlPoint[];
}

// Extended JobConfig with depth curve support
export interface JobConfigWithCurve extends JobConfig {
  depth_curve?: DepthCurveConfig | null;
}

// Depth Focus Types - controls which depth range appears at screen plane
export interface DepthFocusConfig {
  enabled: boolean;
  /** Focus depth - normalized 0-1, where 0=closest, 1=farthest */
  focus_depth: number;
  /** Focus range - how much depth around focus point appears sharp (0-1) */
  focus_range: number;
}

// Extended JobConfig with depth focus support
export interface JobConfigWithFocus extends JobConfigWithCurve {
  depth_focus?: DepthFocusConfig | null;
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


// Depth Validation Types
export interface DepthFrame {
  frame_index: number;
  timestamp_ms: number;
  depth_map_url: string;
  original_frame_url?: string;
  needs_validation: boolean;
  validation_status: 'pending' | 'validated' | 'corrected';
  confidence_score?: number;
}

export interface DepthValidationSession {
  job_id: string;
  total_frames: number;
  frames_needing_validation: number;
  frames: DepthFrame[];
  current_frame_index: number;
  created_at: string;
  updated_at: string;
}

export interface DepthMapCorrection {
  job_id: string;
  frame_index: number;
  depth_map_data: string; // Base64 encoded PNG
  correction_type: 'manual' | 'inpaint' | 'interpolate';
  notes?: string;
}

export interface DepthMapCorrectionResponse {
  job_id: string;
  frame_index: number;
  success: boolean;
  message: string;
  updated_depth_map_url?: string;
}

// Interactive Depth Editor Types

/** A depth plane defines a named region with a specific depth value */
export interface DepthPlane {
  id: string;
  name: string;
  depth_value: number; // 0-1 normalized
  color: string; // For visual identification
  visible: boolean;
  locked: boolean;
  /** Polygon points defining the plane region (normalized 0-1) */
  points: { x: number; y: number }[];
}

/** A depth layer contains raster depth data */
export interface DepthLayer {
  id: string;
  name: string;
  visible: boolean;
  locked: boolean;
  opacity: number; // 0-1
  blend_mode: 'normal' | 'multiply' | 'screen' | 'overlay';
  /** Base64 encoded PNG depth data (grayscale) */
  data: string | null;
}

/** Configuration for the interactive depth editor */
export interface InteractiveDepthEditorConfig {
  width: number;
  height: number;
  layers: DepthLayer[];
  planes: DepthPlane[];
  active_layer_id: string | null;
  active_plane_id: string | null;
}

/** Export format for depth map */
export interface DepthMapExport {
  width: number;
  height: number;
  data: string; // Base64 encoded PNG
  planes: DepthPlane[];
}