/**
 * Application constants
 */

// API Configuration
export const API_CONFIG = {
  BASE_URL: '/api/v1',
  DEFAULT_TIMEOUT_MS: 30000,
  UPLOAD_TIMEOUT_MS: 300000, // 5 minutes for large files
} as const;

// Polling Intervals (in milliseconds)
export const POLLING_INTERVALS = {
  FAST: 3000,     // For running jobs
  NORMAL: 5000,   // For queue stats
  SLOW: 10000,    // For health checks
} as const;

// Pagination
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
} as const;

// File Upload
export const FILE_UPLOAD = {
  MAX_SIZE_MB: 500,
  ACCEPTED_TYPES: 'video/*',
} as const;

// Quality Presets
export const QUALITY_PRESETS = {
  FAST: 'fast',
  BALANCED: 'balanced',
  QUALITY: 'quality',
} as const;

// Default Job Configuration
export const DEFAULT_JOB_CONFIG = {
  QUALITY_PRESET: 'balanced',
  OUTPUT_CODEC: 'libx264',
  OUTPUT_CRF: 23,
} as const;


// Model Comparison Constants
export const COMPARISON = {
  /** Minimum zoom level for depth map images */
  ZOOM_MIN: 0.5,
  /** Maximum zoom level for depth map images */
  ZOOM_MAX: 4,
  /** Zoom step increment */
  ZOOM_STEP: 0.5,
  /** Default image container height in pixels */
  IMAGE_CONTAINER_HEIGHT: 200,
  /** Maximum comment length for voting */
  MAX_COMMENT_LENGTH: 500,
} as const;

// Model Display Names
export const MODEL_DISPLAY_NAMES: Record<string, string> = {
  midas_small: 'MiDaS Small',
  midas_hybrid: 'MiDaS Hybrid',
  dpt_large: 'DPT Large',
  dpt_hybrid: 'DPT Hybrid',
} as const;

// Model Descriptions for UI
export const MODEL_DESCRIPTIONS: Record<string, string> = {
  midas_small: 'Fast and lightweight, good for real-time',
  midas_hybrid: 'Balanced speed and quality',
  dpt_large: 'Highest quality, slower processing',
  dpt_hybrid: 'Good quality with reasonable speed',
} as const;