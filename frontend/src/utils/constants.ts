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
