import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { DownloadsPage } from '../DownloadsPage';

const BASE_URL = '/api/v1';

const mockDownloads = [
  {
    file_id: 'download-1',
    filename: 'output_3d_1.mp4',
    file_size_bytes: 5120000,
    content_type: 'video/mp4',
    created_at: '2024-01-15T12:00:00Z',
  },
  {
    file_id: 'download-2',
    filename: 'output_3d_2.mp4',
    file_size_bytes: 6144000,
    content_type: 'video/mp4',
    created_at: '2024-01-15T13:00:00Z',
  },
];

const handlers = [
  http.get(`${BASE_URL}/download/`, () => {
    return HttpResponse.json(mockDownloads);
  }),

  http.delete(`${BASE_URL}/download/:fileId`, () => {
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

describe('DownloadsPage', () => {
  it('should render page title', async () => {
    render(<DownloadsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Downloads')).toBeInTheDocument();
  });

  it('should render page description', async () => {
    render(<DownloadsPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Download your converted 3D videos')).toBeInTheDocument();
  });

  it('should display downloaded files', async () => {
    render(<DownloadsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('output_3d_1.mp4')).toBeInTheDocument();
      expect(screen.getByText('output_3d_2.mp4')).toBeInTheDocument();
    });
  });

  it('should show file size', async () => {
    render(<DownloadsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText(/5 MB/)).toBeInTheDocument();
      expect(screen.getByText(/6 MB/)).toBeInTheDocument();
    });
  });

  it('should have download buttons', async () => {
    render(<DownloadsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const downloadButtons = screen.getAllByRole('button', { name: /Download/ });
      expect(downloadButtons.length).toBe(2);
    });
  });

  it('should show delete buttons', async () => {
    render(<DownloadsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      const deleteButtons = screen.getAllByRole('button', { name: /Delete/ });
      expect(deleteButtons.length).toBe(2);
    });
  });

  it('should handle empty downloads list', async () => {
    server.use(
      http.get(`${BASE_URL}/download/`, () => {
        return HttpResponse.json([]);
      })
    );

    render(<DownloadsPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('No converted files available yet')).toBeInTheDocument();
    });
  });
});
