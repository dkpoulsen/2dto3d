import { describe, it, expect } from 'vitest';
import {
  API_CONFIG,
  POLLING_INTERVALS,
  PAGINATION,
  FILE_UPLOAD,
  QUALITY_PRESETS,
  DEFAULT_JOB_CONFIG,
} from '../constants';

describe('API_CONFIG', () => {
  it('should have correct base URL', () => {
    expect(API_CONFIG.BASE_URL).toBe('/api/v1');
  });

  it('should have default timeout', () => {
    expect(API_CONFIG.DEFAULT_TIMEOUT_MS).toBe(30000);
  });

  it('should have upload timeout', () => {
    expect(API_CONFIG.UPLOAD_TIMEOUT_MS).toBe(300000);
  });

  it('should be readonly (as const)', () => {
    // TypeScript const assertion - values should be literal types
    expect(typeof API_CONFIG.BASE_URL).toBe('string');
    expect(typeof API_CONFIG.DEFAULT_TIMEOUT_MS).toBe('number');
  });
});

describe('POLLING_INTERVALS', () => {
  it('should have FAST interval', () => {
    expect(POLLING_INTERVALS.FAST).toBe(3000);
  });

  it('should have NORMAL interval', () => {
    expect(POLLING_INTERVALS.NORMAL).toBe(5000);
  });

  it('should have SLOW interval', () => {
    expect(POLLING_INTERVALS.SLOW).toBe(10000);
  });

  it('should have increasing intervals', () => {
    expect(POLLING_INTERVALS.FAST).toBeLessThan(POLLING_INTERVALS.NORMAL);
    expect(POLLING_INTERVALS.NORMAL).toBeLessThan(POLLING_INTERVALS.SLOW);
  });
});

describe('PAGINATION', () => {
  it('should have default page size', () => {
    expect(PAGINATION.DEFAULT_PAGE_SIZE).toBe(20);
  });
});

describe('FILE_UPLOAD', () => {
  it('should have max file size', () => {
    expect(FILE_UPLOAD.MAX_SIZE_MB).toBe(500);
  });

  it('should have accepted types', () => {
    expect(FILE_UPLOAD.ACCEPTED_TYPES).toBe('video/*');
  });
});

describe('QUALITY_PRESETS', () => {
  it('should have all quality presets', () => {
    expect(QUALITY_PRESETS.FAST).toBe('fast');
    expect(QUALITY_PRESETS.BALANCED).toBe('balanced');
    expect(QUALITY_PRESETS.QUALITY).toBe('quality');
  });
});

describe('DEFAULT_JOB_CONFIG', () => {
  it('should have quality preset', () => {
    expect(DEFAULT_JOB_CONFIG.QUALITY_PRESET).toBe('balanced');
  });

  it('should have output codec', () => {
    expect(DEFAULT_JOB_CONFIG.OUTPUT_CODEC).toBe('libx264');
  });

  it('should have output CRF', () => {
    expect(DEFAULT_JOB_CONFIG.OUTPUT_CRF).toBe(23);
  });
});
