import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { DashboardPage } from '../DashboardPage';

const BASE_URL = '/api/v1';

const handlers = [
  http.get(`${BASE_URL}/jobs/stats/queue`, () => {
    return HttpResponse.json({
      total_jobs: 100,
      pending_jobs: 10,
      running_jobs: 5,
      completed_jobs: 80,
      failed_jobs: 5,
      cancelled_jobs: 0,
      skipped_jobs: 0,
      total_frames_processed: 100000,
      total_processing_time_seconds: 360000,
      average_processing_time_seconds: 4500,
      success_rate_percent: 94.1,
    });
  }),

  http.get('/health', () => {
    return HttpResponse.json({
      status: 'healthy',
      version: '0.1.0',
      uptime_seconds: 86400,
      queue_running: true,
      gpu_available: true,
    });
  }),

  http.get('/health/detailed', () => {
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
        total_jobs: 100,
        pending_jobs: 10,
        running_jobs: 5,
        completed_jobs: 80,
        failed_jobs: 5,
        queue_depth: 15,
        success_rate_percent: 94.1,
      },
      checks: {},
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

describe('DashboardPage', () => {
  it('should render page title', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('should render page description', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });
    expect(screen.getByText(/Overview of your 2D to 3D/)).toBeInTheDocument();
  });

  it('should display queue statistics', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('100')).toBeInTheDocument(); // Total Jobs
    });

    expect(screen.getByText('80')).toBeInTheDocument(); // Completed
    expect(screen.getByText('5')).toBeInTheDocument(); // Failed
    expect(screen.getByText('94.1%')).toBeInTheDocument(); // Success Rate
  });

  it('should display stat card titles', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });

    expect(screen.getByText('Total Jobs')).toBeInTheDocument();
    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText('Success Rate')).toBeInTheDocument();
  });

  it('should display service status section', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Service Status')).toBeInTheDocument();
    });
  });

  it('should display GPU status section', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('GPU Status')).toBeInTheDocument();
    });
  });

  it('should display system memory section', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('System Memory')).toBeInTheDocument();
    });
  });

  it('should show queue running status', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Running')).toBeInTheDocument();
    });
  });

  it('should show GPU availability', async () => {
    render(<DashboardPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('Yes')).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    server.use(
      http.get(`${BASE_URL}/jobs/stats/queue`, () => {
        return HttpResponse.json(
          { error: 'Server error' },
          { status: 500 }
        );
      })
    );

    render(<DashboardPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      // Should still render the page structure
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });
});
