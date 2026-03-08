import { describe, it, expect, beforeAll, afterAll, afterEach, vi } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

// Mock the constants module to provide the API_BASE_URL
vi.mock('../utils/constants', () => ({
  API_CONFIG: {
    BASE_URL: '/api/v1',
    DEFAULT_TIMEOUT_MS: 30000,
    UPLOAD_TIMEOUT_MS: 300000,
  },
}));

const BASE_URL = '/api/v1';

const mockThumbnailResponse = {
  job_id: 'test-job-1',
  thumbnails: [
    {
      frame_index: 0,
      timestamp: 0.0,
      original_url: '/frames/0/original.jpg',
      depth_map_url: '/frames/0/depth.jpg',
      confidence_score: 0.85,
      validation_status: 'pending',
    },
    {
      frame_index: 10,
      timestamp: 0.5,
      original_url: '/frames/10/original.jpg',
      depth_map_url: '/frames/10/depth.jpg',
      confidence_score: 0.92,
      validation_status: 'validated',
    },
    {
      frame_index: 20,
      timestamp: 1.0,
      original_url: '/frames/20/original.jpg',
      depth_map_url: '/frames/20/depth.jpg',
      confidence_score: 0.78,
      validation_status: 'corrected',
    },
  ],
  total_frames: 100,
  duration_seconds: 5.0,
};

const mockSingleThumbnailResponse = {
  frame_index: 15,
  timestamp: 0.75,
  original_url: '/frames/15/original.jpg',
  depth_map_url: '/frames/15/depth.jpg',
  confidence_score: 0.88,
  validation_status: 'pending',
};

const handlers = [
  http.get(`${BASE_URL}/jobs/:jobId/thumbnails`, ({ request }) => {
    const url = new URL(request.url);
    const count = url.searchParams.get('count');
    const startFrame = url.searchParams.get('start_frame');
    const endFrame = url.searchParams.get('end_frame');

    // Return different responses based on query params
    if (count === '12') {
      return HttpResponse.json({
        ...mockThumbnailResponse,
        thumbnails: mockThumbnailResponse.thumbnails.slice(0, 2),
      });
    }

    if (startFrame && endFrame) {
      return HttpResponse.json({
        ...mockThumbnailResponse,
        thumbnails: [
          {
            frame_index: parseInt(startFrame),
            timestamp: parseInt(startFrame) * 0.05,
            original_url: `/frames/${startFrame}/original.jpg`,
            depth_map_url: `/frames/${startFrame}/depth.jpg`,
          },
        ],
      });
    }

    return HttpResponse.json(mockThumbnailResponse);
  }),

  http.get(`${BASE_URL}/jobs/:jobId/frames/:frameIndex/thumbnail`, ({ params }) => {
    const { frameIndex } = params;
    
    return HttpResponse.json({
      ...mockSingleThumbnailResponse,
      frame_index: parseInt(frameIndex as string),
      timestamp: parseInt(frameIndex as string) * 0.05,
      original_url: `/frames/${frameIndex}/original.jpg`,
      depth_map_url: `/frames/${frameIndex}/depth.jpg`,
    });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('thumbnailApi', () => {
  describe('getThumbnailGrid', () => {
    it('should fetch thumbnail grid data for a job', async () => {
      // Import dynamically after mocks are set up
      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('test-job-1');

      expect(result.job_id).toBe('test-job-1');
      expect(result.thumbnails).toHaveLength(3);
      expect(result.total_frames).toBe(100);
      expect(result.duration_seconds).toBe(5.0);
    });

    it('should fetch thumbnails with count parameter', async () => {
      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('test-job-1', { count: 12 });

      expect(result.thumbnails).toHaveLength(2);
    });

    it('should fetch thumbnails with frame range parameters', async () => {
      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('test-job-1', {
        start_frame: 10,
        end_frame: 50,
      });

      expect(result.thumbnails).toBeDefined();
      expect(result.thumbnails[0].frame_index).toBe(10);
    });

    it('should return thumbnail frames with correct structure', async () => {
      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('test-job-1');

      const firstThumbnail = result.thumbnails[0];
      expect(firstThumbnail).toHaveProperty('frame_index');
      expect(firstThumbnail).toHaveProperty('timestamp');
      expect(firstThumbnail).toHaveProperty('original_url');
      expect(firstThumbnail).toHaveProperty('depth_map_url');
    });

    it('should include optional confidence_score when present', async () => {
      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('test-job-1');

      expect(result.thumbnails[0].confidence_score).toBe(0.85);
      expect(result.thumbnails[1].confidence_score).toBe(0.92);
    });

    it('should include validation_status when present', async () => {
      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('test-job-1');

      expect(result.thumbnails[0].validation_status).toBe('pending');
      expect(result.thumbnails[1].validation_status).toBe('validated');
      expect(result.thumbnails[2].validation_status).toBe('corrected');
    });

    it('should handle API errors gracefully', async () => {
      server.use(
        http.get(`${BASE_URL}/jobs/:jobId/thumbnails`, () => {
          return new HttpResponse(
            JSON.stringify({ error: 'job_not_found', message: 'Job not found' }),
            { status: 404 }
          );
        })
      );

      const { thumbnailApi } = await import('../client');

      await expect(thumbnailApi.getThumbnailGrid('nonexistent-job')).rejects.toThrow('Job not found');
    });

    it('should handle server errors', async () => {
      server.use(
        http.get(`${BASE_URL}/jobs/:jobId/thumbnails`, () => {
          return new HttpResponse(
            JSON.stringify({ error: 'internal_error', message: 'Internal server error' }),
            { status: 500 }
          );
        })
      );

      const { thumbnailApi } = await import('../client');

      await expect(thumbnailApi.getThumbnailGrid('test-job-1')).rejects.toThrow();
    });
  });

  describe('getFrameThumbnail', () => {
    it('should fetch a single frame thumbnail', async () => {
      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getFrameThumbnail('test-job-1', 15);

      expect(result.frame_index).toBe(15);
      expect(result.timestamp).toBe(0.75);
      expect(result.original_url).toBe('/frames/15/original.jpg');
      expect(result.depth_map_url).toBe('/frames/15/depth.jpg');
    });

    it('should return thumbnail with correct frame index', async () => {
      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getFrameThumbnail('test-job-1', 42);

      expect(result.frame_index).toBe(42);
    });

    it('should handle frame not found error', async () => {
      server.use(
        http.get(`${BASE_URL}/jobs/:jobId/frames/:frameIndex/thumbnail`, () => {
          return new HttpResponse(
            JSON.stringify({ error: 'frame_not_found', message: 'Frame not found' }),
            { status: 404 }
          );
        })
      );

      const { thumbnailApi } = await import('../client');

      await expect(thumbnailApi.getFrameThumbnail('test-job-1', 999)).rejects.toThrow('Frame not found');
    });

    it('should handle job not found error for single frame', async () => {
      server.use(
        http.get(`${BASE_URL}/jobs/:jobId/frames/:frameIndex/thumbnail`, () => {
          return new HttpResponse(
            JSON.stringify({ error: 'job_not_found', message: 'Job not found' }),
            { status: 404 }
          );
        })
      );

      const { thumbnailApi } = await import('../client');

      await expect(thumbnailApi.getFrameThumbnail('nonexistent-job', 0)).rejects.toThrow('Job not found');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty thumbnails array', async () => {
      server.use(
        http.get(`${BASE_URL}/jobs/:jobId/thumbnails`, () => {
          return HttpResponse.json({
            job_id: 'empty-job',
            thumbnails: [],
            total_frames: 0,
            duration_seconds: 0,
          });
        })
      );

      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('empty-job');

      expect(result.thumbnails).toHaveLength(0);
      expect(result.total_frames).toBe(0);
    });

    it('should handle thumbnails without optional fields', async () => {
      server.use(
        http.get(`${BASE_URL}/jobs/:jobId/thumbnails`, () => {
          return HttpResponse.json({
            job_id: 'minimal-job',
            thumbnails: [
              {
                frame_index: 0,
                timestamp: 0,
                original_url: '/frames/0/original.jpg',
                depth_map_url: '/frames/0/depth.jpg',
              },
            ],
            total_frames: 1,
            duration_seconds: 0.1,
          });
        })
      );

      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('minimal-job');

      expect(result.thumbnails[0].confidence_score).toBeUndefined();
      expect(result.thumbnails[0].validation_status).toBeUndefined();
    });

    it('should handle large frame counts', async () => {
      server.use(
        http.get(`${BASE_URL}/jobs/:jobId/thumbnails`, () => {
          const largeThumbnailArray = Array.from({ length: 100 }, (_, i) => ({
            frame_index: i * 10,
            timestamp: i * 0.5,
            original_url: `/frames/${i * 10}/original.jpg`,
            depth_map_url: `/frames/${i * 10}/depth.jpg`,
          }));

          return HttpResponse.json({
            job_id: 'large-job',
            thumbnails: largeThumbnailArray,
            total_frames: 1000,
            duration_seconds: 50,
          });
        })
      );

      const { thumbnailApi } = await import('../client');
      const result = await thumbnailApi.getThumbnailGrid('large-job', { count: 100 });

      expect(result.thumbnails).toHaveLength(100);
      expect(result.total_frames).toBe(1000);
    });
  });
});
