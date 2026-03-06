import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { JobsPage } from '../JobsPage';

const BASE_URL = '/api/v1';

const mockJobs = [
  {
    job_id: 'job-1',
    status: 'completed',
    priority: 'normal',
    input_filename: 'input1.mp4',
    output_filename: 'output1.mp4',
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
      output_filename: 'output1.mp4',
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
  {
    job_id: 'job-2',
    status: 'running',
    priority: 'high',
    input_filename: 'input2.mp4',
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
  },
];

const handlers = [
  http.get(`${BASE_URL}/jobs/`, ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const page = url.searchParams.get('page');
    const page_size = url.searchParams.get('page_size');
    
    let filteredJobs = mockJobs;
    if (status && status !== 'all') {
      filteredJobs = mockJobs.filter(job => job.status === status);
    }
    
    return HttpResponse.json({
      jobs: filteredJobs,
      total_count: filteredJobs.length,
      page: parseInt(page || '1'),
      page_size: parseInt(page_size || '20'),
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

  http.post(`${BASE_URL}/jobs/`, async () => {
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

describe('JobsPage', () => {
  it('should render page title', async () => {
    render(<JobsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Jobs')).toBeInTheDocument();
  });

  it('should render page description', async () => {
    render(<JobsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Manage video conversion jobs')).toBeInTheDocument();
  });

  it('should render new job button', async () => {
    render(<JobsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('New Job')).toBeInTheDocument();
  });

  it('should display filter buttons', async () => {
    render(<JobsPage />, { wrapper: createWrapper() });
    const filterLabels = ['All', 'Pending', 'Queued', 'Running', 'Completed', 'Failed', 'Cancelled'];
    
    filterLabels.forEach(label => {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument();
    });
  });

  it('should display jobs table', async () => {
    render(<JobsPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('Job ID')).toBeInTheDocument();
      expect(screen.getByText('Input File')).toBeInTheDocument();
      expect(screen.getByText('Status')).toBeInTheDocument();
    });
  });

  it('should display job data', async () => {
    render(<JobsPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('input1.mp4')).toBeInTheDocument();
      expect(screen.getByText('input2.mp4')).toBeInTheDocument();
    });
  });

  it('should filter jobs by status', async () => {
    const user = userEvent.setup();
    render(<JobsPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('input1.mp4')).toBeInTheDocument();
    });

    const completedButton = screen.getByRole('button', { name: 'Completed' });
    await user.click(completedButton);

    await waitFor(() => {
      expect(screen.getByText('input1.mp4')).toBeInTheDocument();
    });
  });

  it('should show cancel button for running jobs', async () => {
    render(<JobsPage />, { wrapper: createWrapper() });
    
    await waitFor(() => {
      const cancelButtons = screen.getAllByRole('button', { name: /Cancel job/ });
      expect(cancelButtons.length).toBeGreaterThan(0);
    });
  });

  it('should open create job modal', async () => {
    const user = userEvent.setup();
    render(<JobsPage />, { wrapper: createWrapper() });
    
    const newJobButton = screen.getByText('New Job');
    await user.click(newJobButton);

    expect(screen.getByText('Create New Job')).toBeInTheDocument();
  });

  it('should close modal on cancel', async () => {
    const user = userEvent.setup();
    render(<JobsPage />, { wrapper: createWrapper() });
    
    const newJobButton = screen.getByText('New Job');
    await user.click(newJobButton);

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(screen.queryByText('Create New Job')).not.toBeInTheDocument();
  });
});
