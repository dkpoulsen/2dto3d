import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { uploadApi, jobsApi, downloadsApi, healthApi } from '../client';

const BASE_URL = '/api/v1';

const handlers = [
  http.post(`${BASE_URL}/upload/`, () => {
    return HttpResponse.json({
      file_id: 'new-file-1',
      filename: 'uploaded.mp4',
      file_size_bytes: 2048000,
      content_type: 'video/mp4',
      upload_time: '2024-01-15T11:00:00Z',
      message: 'File uploaded successfully',
    });
  }),

  http.get(`${BASE_URL}/upload/`, () => {
    return HttpResponse.json([
      {
        file_id: 'file-1',
        filename: 'test.mp4',
        file_size_bytes: 1024000,
        content_type: 'video/mp4',
        created_at: '2024-01-15T10:00:00Z',
      },
    ]);
  }),

  http.delete(`${BASE_URL}/upload/:fileId`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${BASE_URL}/jobs/`, () => {
    return HttpResponse.json({
      jobs: [
        {
          job_id: 'job-1',
          status: 'completed',
          priority: 'normal',
          input_filename: 'input.mp4',
          output_filename: 'output.mp4',
          progress: 1,
          current_stage: 'completed',
          created_at: '2024-01-15T10:00:00Z',
          started_at: '2024-01-15T10:01:00Z',
          completed_at: '2024-01-15T10:30:00Z',
          elapsed_time_seconds: 1740,
          estimated_remaining_seconds: null,
          retry_count: 0,
          result: {
            success: true,
            output_file_id: 'out-1',
            output_filename: 'output.mp4',
            error_message: null,
            error_type: null,
            frames_processed: 1000,
            processing_time_seconds: 1740,
          },
          config: {},
          scheduled_at: null,
          depends_on: [],
          dependent_jobs: [],
        },
      ],
      total_count: 1,
      page: 1,
      page_size: 20,
    });
  }),

  http.get(`${BASE_URL}/jobs/:jobId`, () => {
    return HttpResponse.json({
      job_id: 'job-1',
      status: 'running',
      priority: 'normal',
      input_filename: 'input.mp4',
      output_filename: null,
      progress: 0.5,
      current_stage: 'processing',
      created_at: '2024-01-15T10:00:00Z',
      started_at: '2024-01-15T10:01:00Z',
      completed_at: null,
      elapsed_time_seconds: 600,
      estimated_remaining_seconds: 600,
      retry_count: 0,
      result: null,
      config: {},
      scheduled_at: null,
      depends_on: [],
      dependent_jobs: [],
    });
  }),

  http.post(`${BASE_URL}/jobs/`, () => {
    return HttpResponse.json({
      job_id: 'new-job-1',
      status: 'pending',
      message: 'Job created successfully',
      status_url: '/api/v1/jobs/new-job-1',
    });
  }),

  http.post(`${BASE_URL}/jobs/:jobId/cancel`, () => {
    return HttpResponse.json({
      job_id: 'job-1',
      cancelled: true,
      message: 'Job cancelled',
    });
  }),

  http.post(`${BASE_URL}/jobs/:jobId/retry`, () => {
    return HttpResponse.json({
      job_id: 'job-1',
      retried: true,
      retry_count: 1,
      message: 'Job retry initiated',
    });
  }),

  http.delete(`${BASE_URL}/jobs/:jobId`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${BASE_URL}/jobs/stats/queue`, () => {
    return HttpResponse.json({
      total_jobs: 10,
      pending_jobs: 2,
      running_jobs: 1,
      completed_jobs: 6,
      failed_jobs: 1,
      success_rate_percent: 85.7,
    });
  }),

  http.get(`${BASE_URL}/download/`, () => {
    return HttpResponse.json([
      {
        file_id: 'download-1',
        filename: 'output_3d.mp4',
        file_size_bytes: 5120000,
        content_type: 'video/mp4',
        created_at: '2024-01-15T12:00:00Z',
      },
    ]);
  }),

  http.get(`${BASE_URL}/download/:fileId/info`, () => {
    return HttpResponse.json({
      file_id: 'download-1',
      filename: 'output_3d.mp4',
      file_size_bytes: 5120000,
      content_type: 'video/mp4',
      created_at: '2024-01-15T12:00:00Z',
    });
  }),

  http.delete(`${BASE_URL}/download/:fileId`, () => {
    return new HttpResponse(null, { status: 204 });
  }),

  http.get(`${BASE_URL}/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '0.1.0',
      uptime_seconds: 86400,
      queue_running: true,
      gpu_available: true,
    });
  }),

  http.get(`${BASE_URL}/health/detailed`, () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '0.1.0',
      uptime_seconds: 86400,
      timestamp: '2024-01-15T12:00:00Z',
      gpu: {
        available: true,
        device_name: 'NVIDIA RTX 3080',
        device_count: 1,
        memory_used_mb: 2048,
        memory_free_mb: 8192,
        memory_total_mb: 10240,
        memory_utilization_percent: 20,
        compute_capability: '8.6',
      },
      memory: {
        total_mb: 32768,
        available_mb: 16384,
        used_mb: 16384,
        utilization_percent: 50,
      },
      queue: {
        running: true,
        paused: false,
        total_jobs: 10,
        pending_jobs: 2,
        running_jobs: 1,
        completed_jobs: 6,
        failed_jobs: 1,
        queue_depth: 3,
        success_rate_percent: 85.7,
      },
      checks: {
        api: true,
        database: true,
        gpu: true,
      },
    });
  }),

  http.get(`${BASE_URL}/`, () => {
    return HttpResponse.json({
      name: '2Dto3D Converter API',
      version: '0.1.0',
      description: 'Convert 2D videos to 3D',
      endpoints: {},
      supported_formats: ['mp4', 'avi', 'mov'],
      supported_models: ['midas_small', 'midas_hybrid'],
    });
  }),

  http.get(`${BASE_URL}/queue`, () => {
    return HttpResponse.json({
      total_jobs: 10,
      pending_jobs: 2,
      running_jobs: 1,
      completed_jobs: 6,
      failed_jobs: 1,
      success_rate_percent: 85.7,
    });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('uploadApi', () => {
  it('should list files', async () => {
    const files = await uploadApi.listFiles();
    expect(files).toHaveLength(1);
    expect(files[0].filename).toBe('test.mp4');
  });

  it('should upload file', async () => {
    const file = new File(['content'], 'uploaded.mp4', { type: 'video/mp4' });
    const result = await uploadApi.uploadFile(file);
    expect(result.file_id).toBe('new-file-1');
    expect(result.filename).toBe('uploaded.mp4');
  });

  it('should delete file', async () => {
    await expect(uploadApi.deleteFile('file-1')).resolves.not.toThrow();
  });
});

describe('jobsApi', () => {
  it('should list jobs', async () => {
    const result = await jobsApi.listJobs();
    expect(result.jobs).toHaveLength(1);
    expect(result.total_count).toBe(1);
  });

  it('should list jobs with filters', async () => {
    const result = await jobsApi.listJobs({ status: 'completed', page: 1 });
    expect(result.jobs).toBeDefined();
  });

  it('should get single job', async () => {
    const job = await jobsApi.getJob('job-1');
    expect(job.job_id).toBe('job-1');
    expect(job.status).toBe('running');
  });

  it('should submit job', async () => {
    const result = await jobsApi.submitJob({
      input_file_id: 'file-1',
    });
    expect(result.job_id).toBe('new-job-1');
    expect(result.status).toBe('pending');
  });

  it('should cancel job', async () => {
    const result = await jobsApi.cancelJob('job-1');
    expect(result.cancelled).toBe(true);
  });

  it('should retry job', async () => {
    const result = await jobsApi.retryJob('job-1');
    expect(result.retried).toBe(true);
    expect(result.retry_count).toBe(1);
  });

  it('should remove job', async () => {
    await expect(jobsApi.removeJob('job-1')).resolves.not.toThrow();
  });

  it('should get queue stats', async () => {
    const stats = await jobsApi.getQueueStats();
    expect(stats.total_jobs).toBe(10);
    expect(stats.success_rate_percent).toBe(85.7);
  });
});

describe('downloadsApi', () => {
  it('should list downloads', async () => {
    const downloads = await downloadsApi.listDownloads();
    expect(downloads).toHaveLength(1);
    expect(downloads[0].filename).toBe('output_3d.mp4');
  });

  it('should get download info', async () => {
    const info = await downloadsApi.getDownloadInfo('download-1');
    expect(info.file_id).toBe('download-1');
  });

  it('should generate download URL', () => {
    const url = downloadsApi.getDownloadUrl('download-1');
    expect(url).toBe('/api/v1/download/download-1');
  });

  it('should delete download', async () => {
    await expect(downloadsApi.deleteDownload('download-1')).resolves.not.toThrow();
  });
});

describe('healthApi', () => {
  it('should get health', async () => {
    const health = await healthApi.getHealth();
    expect(health.status).toBe('healthy');
    expect(health.queue_running).toBe(true);
  });

  it('should get detailed health', async () => {
    const health = await healthApi.getDetailedHealth();
    expect(health.gpu.available).toBe(true);
    expect(health.queue.running).toBe(true);
  });

  it('should get API info', async () => {
    const info = await healthApi.getAPIInfo();
    expect(info.name).toBe('2Dto3D Converter API');
    expect(info.supported_formats).toContain('mp4');
  });

  it('should get queue stats', async () => {
    const stats = await healthApi.getQueueStats();
    expect(stats.total_jobs).toBe(10);
  });
});
