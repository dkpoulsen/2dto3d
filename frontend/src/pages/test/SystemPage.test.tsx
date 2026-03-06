import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { SystemPage } from '../SystemPage';

const BASE_URL = '/api/v1';

const handlers = [
  http.get('/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '0.0.0',
      uptime_seconds: 86400,
      queue_running: true,
      gpu_available: true,
    });
  }),

  http.get('/health/detailed', () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '1.0.0',
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
        total_jobs: 100,
        pending_jobs: 10,
        running_jobs: 5,
        completed_jobs: 80,
        failed_jobs: 5,
        queue_depth: 15,
        success_rate_percent: 94.1,
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
      version: '1.0.0',
      description: 'Convert 2D videos to 3D',
      endpoints: {},
      supported_formats: ['mp4', 'avi', 'mov', 'mkv', 'webm'],
      supported_models: ['midas_small', 'midas_hybrid', 'dpt_hybrid', 'dpt_large'],
    });
  }),
];

const server = setupServer(...handlers);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('SystemPage', () => {
  it('should render page title', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });
    expect(screen.getByText('System')).toBeInTheDocument();
  });

  it('should render page description', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Monitor system health and performance')).toBeInTheDocument();
  });

  it('should display health status', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('healthy Status')).toBeInTheDocument();
    });
  });

  it('should display GPU status section', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('GPU Status')).toBeInTheDocument();
    });
  });

  it('should display system memory section', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('System Memory')).toBeInTheDocument();
    });
  });

  it('should display queue status section', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Queue Status')).toBeInTheDocument();
    });
  });

  it('should display API information section', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('API Information')).toBeInTheDocument();
    });
  });

  it('should show GPU device name', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('NVIDIA RTX 3080')).toBeInTheDocument();
    });
  });

  it('should show queue statistics', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument();
      expect(screen.getByText('94.1%')).toBeInTheDocument();
    });
  });

  it('should show supported formats', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('MP4')).toBeInTheDocument();
      expect(screen.getByText('AVI')).toBeInTheDocument();
      expect(screen.getByText('MOV')).toBeInTheDocument();
    });
  });

  it('should show supported models', async () => {
    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('midas_small')).toBeInTheDocument();
      expect(screen.getByText('midas_hybrid')).toBeInTheDocument();
    });
  });

  it('should handle no GPU gracefully', async () => {
    server.use(
      http.get('/health/detailed', () => {
        return HttpResponse.json({
          status: 'degraded',
          version: '1.0.0',
          uptime_seconds: 86400,
          timestamp: '2024-01-15T12:00:00Z',
          gpu: {
            available: false,
            device_name: null,
            device_count: 0,
            memory_used_mb: 0,
            memory_free_mb: 0,
            memory_total_mb: 1,
            memory_utilization_percent: 1,
            compute_capability: null,
          },
          memory: {
            total_mb: 32768,
            available_mb: 16384,
            used_mb: 16384,
            utilization_percent: 50,
          },
          queue: {
            running: false,
            paused: true,
            total_jobs: 0,
            pending_jobs: 0,
            running_jobs: 0,
            completed_jobs: 0,
            failed_jobs: 0,
            queue_depth: 0,
            success_rate_percent: 0,
          },
          checks: {
            api: true,
            database: true,
            gpu: false,
          },
        });
      })
    );

    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('No GPU available')).toBeInTheDocument();
    });
  });

  it('should handle connection error', async () => {
    server.use(
      http.get('/health', () => {
        return HttpResponse.json(
          { error: 'Server error' },
          { status: 500 }
        );
      })
    );

    render(<SystemPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
    });
  });
});
