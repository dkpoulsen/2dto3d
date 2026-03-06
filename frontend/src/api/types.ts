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
  depth_focus?: DepthFocusConfig;
  upscaling?: UpscalingConfig;
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
  depth_curve?: DepthCurveConfig;
}

// Depth Focus Types - controls which depth range appears at screen plane
export interface DepthFocusConfig {
  enabled: boolean;
  /** Focus depth - normalized 0-1, where 0=closest, 1=farthest */
  focus_depth: number;
  /** Focus range - how much depth around focus point appears sharp (0-1) */
  focus_range: number;
}

// Upscaling Types - AI-based video super-resolution
export type UpscalingModelType =
  | 'esrgan'
  | 'realesrgan-x4plus'
  | 'realesrgan-x4plus-anime'
  | 'realesrgan-x2plus'
  | 'realesrgan-general-x4v3';

export interface UpscalingConfig {
  /** Whether AI upscaling is enabled */
  enabled: boolean;
  /** Upscaling model to use */
  model_type: UpscalingModelType;
  /** Upscaling factor (2x or 4x) */
  scale: number;
  /** Tile size for processing large images. 0 = auto */
  tile_size: number;
  /** Denoising strength (0.0 = none, 1.0 = max) */
  denoise_strength: number;
}

// Extended JobConfig with depth focus support
export interface JobConfigWithFocus extends JobConfigWithCurve {
  depth_focus?: DepthFocusConfig;
  upscaling?: UpscalingConfig;
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

// Model Performance Comparison Types

/** Available depth estimation models for comparison */
export type ComparisonModel = 'midas_small' | 'midas_hybrid' | 'dpt_large' | 'dpt_hybrid';

/** Metrics for a single model's depth estimation */
export interface ModelMetrics {
  /** Processing time in seconds */
  processing_time_seconds: number;
  /** Average confidence score (0-1) */
  avg_confidence: number;
  /** Memory usage in MB */
  memory_usage_mb: number;
  /** Number of frames processed */
  frames_processed: number;
  /** Quality score if ground truth available (0-1) */
  quality_score?: number;
  /** Edge preservation score (0-1) */
  edge_score?: number;
  /** Depth consistency across frames (0-1) */
  temporal_consistency?: number;
}

/** Individual model result in a comparison session */
export interface ModelResult {
  /** Model identifier */
  model: ComparisonModel;
  /** Display name of the model */
  model_name: string;
  /** Depth map image URL (with colormap applied) */
  depth_map_url: string;
  /** Original depth map URL (grayscale) */
  raw_depth_map_url?: string;
  /** Metrics for this model */
  metrics: ModelMetrics;
  /** Number of votes received */
  votes: number;
  /** Whether the current user has voted for this model */
  user_voted: boolean;
}

/** User vote for a comparison */
export interface ComparisonVote {
  /** Session ID */
  session_id: string;
  /** Model that received the vote */
  model: ComparisonModel;
  /** Optional user comment */
 comment?: string;
  /** Timestamp of the vote */
  voted_at: string;
}

/** Comparison session containing multiple model results */
export interface ComparisonSession {
  /** Unique session identifier */
  session_id: string;
  /** Source job ID if applicable */
  job_id?: string;
  /** Frame index being compared */
  frame_index: number;
  /** Original frame image URL */
  original_frame_url: string;
  /** All model results for comparison */
  results: ModelResult[];
  /** Total votes cast in this session */
  total_votes: number;
  /** Session creation time */
  created_at: string;
  /** Whether the session is active for voting */
  is_active: boolean;
  /** Current user's vote if any */
  user_vote?: ComparisonVote;
}

/** Request to create a new comparison session */
export interface CreateComparisonRequest {
  /** Source job ID */
  job_id?: string;
  /** Specific frame index to compare (optional, defaults to middle frame) */
  frame_index?: number;
  /** Models to include in comparison */
  models?: ComparisonModel[];
}

/** Request to submit a vote */
export interface SubmitVoteRequest {
  /** Session ID */
  session_id: string;
  /** Model receiving the vote */
  model: ComparisonModel;
  /** Optional comment */
  comment?: string;
}

/** Response after submitting a vote */
export interface SubmitVoteResponse {
  /** Session ID */
  session_id: string;
  /** Model that received the vote */
  model: ComparisonModel;
  /** Whether the vote was successfully recorded */
  success: boolean;
  /** Updated vote count for the model */
  new_vote_count: number;
  /** Total votes in the session */
  total_votes: number;
  /** Message about the vote */
  message: string;
}

/** Leaderboard entry for model rankings */
export interface LeaderboardEntry {
  /** Model identifier */
  model: ComparisonModel;
  /** Display name */
  model_name: string;
  /** Total votes received */
  total_votes: number;
  /** Win rate percentage */
  win_rate_percent: number;
  /** Average confidence across all comparisons */
  avg_confidence: number;
  /** Average processing time */
  avg_processing_time_seconds: number;
  /** Number of comparison sessions participated in */
  sessions_count: number;
}

/** Leaderboard response */
export interface LeaderboardResponse {
  /** Leaderboard entries ranked by votes */
  leaderboard: LeaderboardEntry[];
  /** Total comparison sessions */
  total_sessions: number;
  /** Total votes cast */
  total_votes: number;
  /** Last updated timestamp */
  updated_at: string;
}

// ============================================================================
// Notification Types
// ============================================================================

/** Types of notifications supported by the system */
export type NotificationType =
  | 'job_completed'
  | 'job_failed'
  | 'job_cancelled'
  | 'job_started'
  | 'job_progress'
  | 'job_retrying'
  | 'system_alert'
  | 'webhook_failed';

/** Priority levels for notifications */
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';

/** A single notification */
export interface Notification {
  notification_id: string;
  notification_type: NotificationType;
  title: string;
  message: string;
  priority: NotificationPriority;
  job_id: string | null;
  data: Record<string, unknown>;
  read: boolean;
  dismissed: boolean;
  created_at: string;
  expires_at: string | null;
}

/** List of notifications with metadata */
export interface NotificationListResponse {
  notifications: Notification[];
  total_count: number;
  unread_count: number;
  page: number;
  page_size: number;
}

/** Notification count response */
export interface NotificationCountResponse {
  total: number;
  unread: number;
  dismissed: number;
}

/** Request to mark notifications as read */
export interface MarkReadRequest {
  notification_ids: string[];
}

/** Response after marking notifications as read */
export interface MarkReadResponse {
  updated_count: number;
  message: string;
}

/** Request to dismiss notifications */
export interface DismissRequest {
  notification_ids: string[];
}

/** Response after dismissing notifications */
export interface DismissResponse {
  updated_count: number;
  message: string;
}

/** Webhook configuration */
export interface WebhookConfig {
  url: string;
  secret: string | null;
  events: NotificationType[];
  enabled: boolean;
}

// ============================================================================
// Thumbnail Grid Types
// ============================================================================

/** A single frame thumbnail for the grid view */
export interface ThumbnailFrame {
  /** Frame index in the video */
  frame_index: number;
  /** Timestamp in seconds */
  timestamp: number;
  /** URL to the original frame image */
  original_url: string;
  /** URL to the depth map image */
  depth_map_url: string;
  /** Optional confidence score (0-1) */
  confidence_score?: number;
  /** Validation status */
  validation_status?: 'pending' | 'validated' | 'corrected';
}

/** Request parameters for fetching thumbnail grid data */
export interface ThumbnailGridRequest {
  /** Number of thumbnails to fetch (evenly distributed across video) */
  count?: number;
  /** Start frame index (optional) */
  start_frame?: number;
  /** End frame index (optional) */
  end_frame?: number;
}

/** Response containing thumbnail grid data */
export interface ThumbnailGridResponse {
  /** Job ID */
  job_id: string;
  /** List of thumbnail frames */
  thumbnails: ThumbnailFrame[];
  /** Total frames in the video */
  total_frames: number;
  /** Video duration in seconds */
  duration_seconds: number;
}
