import { describe, it, expect, vi, beforeEach } from 'vitest';

// Define mocks at the top level with hoisting-aware pattern
vi.mock('axios', () => {
  const mockGet = vi.fn();
  const mockPost = vi.fn();
  
  return {
    default: {
      create: () => ({
        get: mockGet,
        post: mockPost,
        interceptors: {
          response: {
            use: vi.fn(),
          },
        },
      }),
      // Expose for testing
      __mockGet: mockGet,
      __mockPost: mockPost,
    },
  };
});

// Import after mocking
import axios from 'axios';
import { depthValidationApi } from '../client';

// Get the mock functions
const mockGet = (axios as unknown as { __mockGet: ReturnType<typeof vi.fn> }).__mockGet;
const mockPost = (axios as unknown as { __mockPost: ReturnType<typeof vi.fn> }).__mockPost;

describe('depthValidationApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ============================================
  // getValidationSession Tests
  // ============================================
  describe('getValidationSession', () => {
    it('should fetch validation session for a job', async () => {
      const mockSession = {
        job_id: 'test-job-123',
        total_frames: 10,
        frames_needing_validation: 3,
        frames: [],
        current_frame_index: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:01:00Z',
      };

      mockGet.mockResolvedValueOnce({ data: mockSession });

      const result = await depthValidationApi.getValidationSession('test-job-123');

      expect(mockGet).toHaveBeenCalledWith('/jobs/test-job-123/depth-validation');
      expect(result).toEqual(mockSession);
    });

    it('should handle errors when fetching session fails', async () => {
      const error = new Error('Network error');
      mockGet.mockRejectedValueOnce(error);

      await expect(depthValidationApi.getValidationSession('test-job-123')).rejects.toThrow('Network error');
    });
  });

  // ============================================
  // getFrameDepthMap Tests
  // ============================================
  describe('getFrameDepthMap', () => {
    it('should fetch depth map as blob', async () => {
      const mockBlob = new Blob(['mock-depth-map'], { type: 'image/png' });
      mockGet.mockResolvedValueOnce({ data: mockBlob });

      const result = await depthValidationApi.getFrameDepthMap('test-job-123', 5);

      expect(mockGet).toHaveBeenCalledWith('/jobs/test-job-123/frames/5/depth-map', {
        responseType: 'blob',
      });
      expect(result).toBe(mockBlob);
    });

    it('should handle different frame indices', async () => {
      const mockBlob = new Blob(['mock-depth-map'], { type: 'image/png' });
      mockGet.mockResolvedValue({ data: mockBlob });

      await depthValidationApi.getFrameDepthMap('job-abc', 0);
      expect(mockGet).toHaveBeenCalledWith('/jobs/job-abc/frames/0/depth-map', {
        responseType: 'blob',
      });

      await depthValidationApi.getFrameDepthMap('job-abc', 999);
      expect(mockGet).toHaveBeenCalledWith('/jobs/job-abc/frames/999/depth-map', {
        responseType: 'blob',
      });
    });
  });

  // ============================================
  // getFrameOriginal Tests
  // ============================================
  describe('getFrameOriginal', () => {
    it('should fetch original frame as blob', async () => {
      const mockBlob = new Blob(['mock-original-frame'], { type: 'image/png' });
      mockGet.mockResolvedValueOnce({ data: mockBlob });

      const result = await depthValidationApi.getFrameOriginal('test-job-123', 5);

      expect(mockGet).toHaveBeenCalledWith('/jobs/test-job-123/frames/5/original', {
        responseType: 'blob',
      });
      expect(result).toBe(mockBlob);
    });
  });

  // ============================================
  // submitCorrection Tests
  // ============================================
  describe('submitCorrection', () => {
    it('should submit correction successfully', async () => {
      const mockCorrection = {
        job_id: 'test-job-123',
        frame_index: 5,
        depth_map_data: 'base64encodeddata',
        correction_type: 'manual' as const,
      };

      const mockResponse = {
        job_id: 'test-job-123',
        frame_index: 5,
        success: true,
        message: 'Correction saved successfully',
      };

      mockPost.mockResolvedValueOnce({ data: mockResponse });

      const result = await depthValidationApi.submitCorrection(mockCorrection);

      expect(mockPost).toHaveBeenCalledWith(
        '/jobs/test-job-123/frames/5/depth-correction',
        mockCorrection
      );
      expect(result).toEqual(mockResponse);
    });

    it('should handle different correction types', async () => {
      const correctionTypes = ['manual', 'inpaint', 'interpolate'] as const;

      for (const type of correctionTypes) {
        const correction = {
          job_id: 'test-job-123',
          frame_index: 5,
          depth_map_data: 'base64encodeddata',
          correction_type: type,
        };

        mockPost.mockResolvedValueOnce({ data: { success: true } });

        await depthValidationApi.submitCorrection(correction);

        expect(mockPost).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({ correction_type: type })
        );
      }
    });
  });

  // ============================================
  // markFrameValidated Tests
  // ============================================
  describe('markFrameValidated', () => {
    it('should mark frame as validated', async () => {
      mockPost.mockResolvedValueOnce({ data: {} });

      await depthValidationApi.markFrameValidated('test-job-123', 5);

      expect(mockPost).toHaveBeenCalledWith('/jobs/test-job-123/frames/5/validate');
    });

    it('should handle different frame indices', async () => {
      mockPost.mockResolvedValue({ data: {} });

      await depthValidationApi.markFrameValidated('job-abc', 0);
      expect(mockPost).toHaveBeenCalledWith('/jobs/job-abc/frames/0/validate');

      await depthValidationApi.markFrameValidated('job-abc', 999);
      expect(mockPost).toHaveBeenCalledWith('/jobs/job-abc/frames/999/validate');
    });

    it('should propagate errors when validation fails', async () => {
      const error = new Error('Validation failed');
      mockPost.mockRejectedValueOnce(error);

      await expect(depthValidationApi.markFrameValidated('test-job-123', 5)).rejects.toThrow('Validation failed');
    });
  });
});
