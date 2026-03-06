import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { UploadPage } from '../UploadPage';

const BASE_URL = '/api/v1';

const mockFiles = [
  {
    file_id: 'file-1',
    filename: 'test-video.mp4',
    file_size_bytes: 1024000,
    content_type: 'video/mp4',
    created_at: '2024-01-15T10:00:00Z',
  },
];

const handlers = [
  http.get(`${BASE_URL}/upload/`, () => {
    return HttpResponse.json(mockFiles);
  }),

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

  http.delete(`${BASE_URL}/upload/:fileId`, () => {
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
      queries: { retry: false },
    },
  });

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('UploadPage', () => {
  it('should render page title', () => {
    render(<UploadPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Upload Videos')).toBeInTheDocument();
  });

  it('should render page description', () => {
    render(<UploadPage />, { wrapper: createWrapper() });
    expect(screen.getByText(/Upload 2D video files/)).toBeInTheDocument();
  });

  it('should render upload zone', async () => {
    render(<UploadPage />, { wrapper: createWrapper() });
    await waitFor(() => {
      expect(screen.getByText('Click to upload')).toBeInTheDocument();
    });
  });

  it('should render uploaded files section', async () => {
    render(<UploadPage />, { wrapper: createWrapper() });
    await waitFor(() => {
    expect(screen.getByText('Uploaded Files')).toBeInTheDocument();
  });
  });

  it('should display uploaded file details', async () => {
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
    expect(screen.getByText('test-video.mp4')).toBeInTheDocument();
  });
  });

  it('should show loading state initially', () => {
    render(<UploadPage />, { wrapper: createWrapper() });
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should handle delete button click', async () => {
    const user = userEvent.setup();
    render(<UploadPage />, { wrapper: createWrapper() });

    await waitFor(() => {
      expect(screen.getByText('test-video.mp4')).toBeInTheDocument();
  });

    const deleteButtons = screen.getAllByRole('button');
    expect(deleteButtons.length).toBeGreaterThan(0);
  });
});
