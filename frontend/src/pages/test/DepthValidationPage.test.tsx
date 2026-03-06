import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

// Mock the modules BEFORE importing the component
vi.mock('../../api', () => ({
  depthValidationApi: {
    getValidationSession: vi.fn(),
    getFrameDepthMap: vi.fn(),
    getFrameOriginal: vi.fn(),
    submitCorrection: vi.fn(),
    markFrameValidated: vi.fn(),
  },
  jobsApi: {
    getJob: vi.fn(),
  },
}));

// Import after mocking
import { depthValidationApi, jobsApi } from '../../api';
import { DepthValidationPage } from '../DepthValidationPage';

// Mock canvas context
const mockCtx = {
  drawImage: vi.fn(),
  getImageData: vi.fn(() => ({
    data: new Uint8ClampedArray(4 * 640 * 480),
    width: 640,
    height: 480,
  })),
  putImageData: vi.fn(),
  fillRect: vi.fn(),
  createRadialGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
  arc: vi.fn(),
  fill: vi.fn(),
  beginPath: vi.fn(),
  clearRect: vi.fn(),
  stroke: vi.fn(),
  setLineDash: vi.fn(),
  fillText: vi.fn(),
  fillStyle: '',
  strokeStyle: '',
  lineWidth: 0,
  font: '',
  textAlign: '',
};

HTMLCanvasElement.prototype.getContext = vi.fn(() => mockCtx);

// Mock URL.createObjectURL and revokeObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

// Test data
const createMockSession = () => ({
  job_id: 'test-job-123',
  total_frames: 10,
  frames_needing_validation: 3,
  frames: [
    { frame_index: 0, timestamp_ms: 0, needs_validation: false, validation_status: 'validated' as const },
    { frame_index: 1, timestamp_ms: 100, needs_validation: true, validation_status: 'pending' as const, confidence_score: 0.85 },
    { frame_index: 2, timestamp_ms: 200, needs_validation: false, validation_status: 'validated' as const },
    { frame_index: 3, timestamp_ms: 300, needs_validation: true, validation_status: 'pending' as const, confidence_score: 0.72 },
    { frame_index: 4, timestamp_ms: 400, needs_validation: false, validation_status: 'corrected' as const },
    { frame_index: 5, timestamp_ms: 500, needs_validation: true, validation_status: 'pending' as const, confidence_score: 0.91 },
    { frame_index: 6, timestamp_ms: 600, needs_validation: false, validation_status: 'validated' as const },
    { frame_index: 7, timestamp_ms: 700, needs_validation: false, validation_status: 'validated' as const },
    { frame_index: 8, timestamp_ms: 800, needs_validation: false, validation_status: 'validated' as const },
    { frame_index: 9, timestamp_ms: 900, needs_validation: false, validation_status: 'validated' as const },
  ],
  current_frame_index: 0,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:01:00Z',
});

const createMockJob = () => ({
  id: 'test-job-123',
  input_filename: 'test-video.mp4',
  status: 'processing',
  progress: 50,
  created_at: '2024-01-01T00:00:00Z',
});

const mockDepthMapBlob = new Blob(['mock-depth-map-data'], { type: 'image/png' });
const mockOriginalBlob = new Blob(['mock-original-data'], { type: 'image/png' });

// Helper to render with providers
const renderWithProviders = (initialRoute = '/jobs/test-job-123/validate') => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/jobs/:jobId/validate" element={<DepthValidationPage />} />
          <Route path="/jobs" element={<div>Jobs Page</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('DepthValidationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Set up default mock implementations
    vi.mocked(depthValidationApi.getValidationSession).mockResolvedValue(createMockSession());
    vi.mocked(depthValidationApi.getFrameDepthMap).mockResolvedValue(mockDepthMapBlob);
    vi.mocked(depthValidationApi.getFrameOriginal).mockResolvedValue(mockOriginalBlob);
    vi.mocked(depthValidationApi.submitCorrection).mockResolvedValue({ success: true });
    vi.mocked(depthValidationApi.markFrameValidated).mockResolvedValue(undefined);
    vi.mocked(jobsApi.getJob).mockResolvedValue(createMockJob());
  });

  // ============================================
  // LOADING STATE TESTS
  // ============================================
  describe('Loading State', () => {
    it('should show loading spinner while fetching session', () => {
      // Make the API call never resolve
      vi.mocked(depthValidationApi.getValidationSession).mockImplementation(
        () => new Promise(() => {})
      );

      renderWithProviders();

      expect(screen.getByText('Loading validation session...')).toBeInTheDocument();
    });
  });

  // ============================================
  // ERROR STATE TESTS
  // ============================================
  describe('Error State', () => {
    it('should show error message when session fails to load', async () => {
      vi.mocked(depthValidationApi.getValidationSession).mockRejectedValue(
        new Error('Network error')
      );

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Session')).toBeInTheDocument();
      });
    });

    it('should show back to jobs button on error', async () => {
      vi.mocked(depthValidationApi.getValidationSession).mockRejectedValue(
        new Error('Network error')
      );

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Back to Jobs')).toBeInTheDocument();
      });
    });

    it('should navigate to jobs when back button clicked on error', async () => {
      const user = userEvent.setup();
      vi.mocked(depthValidationApi.getValidationSession).mockRejectedValue(
        new Error('Network error')
      );

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Back to Jobs')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Back to Jobs'));

      await waitFor(() => {
        expect(screen.getByText('Jobs Page')).toBeInTheDocument();
      });
    });
  });

  // ============================================
  // HEADER TESTS
  // ============================================
  describe('Header', () => {
    it('should render page title', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Depth Validation')).toBeInTheDocument();
      });
    });

    it('should show job filename', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText(/Job: test-video.mp4/)).toBeInTheDocument();
      });
    });

    it('should show frames needing validation count', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('3 frames need validation')).toBeInTheDocument();
      });
    });

    it('should show current frame counter', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText(/Frame 1/)).toBeInTheDocument();
        expect(screen.getByText(/10/)).toBeInTheDocument();
      });
    });
  });

  // ============================================
  // FRAME NAVIGATION TESTS
  // ============================================
  describe('Frame Navigation', () => {
    it('should render frame navigation panel', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Frame Navigation')).toBeInTheDocument();
      });
    });

    it('should render all frames in the list', async () => {
      renderWithProviders();

      await waitFor(() => {
        for (let i = 0; i < 10; i++) {
          expect(screen.getByText(`Frame ${i + 1}`)).toBeInTheDocument();
        }
      });
    });

    it('should disable prev button on first frame', async () => {
      renderWithProviders();

      await waitFor(() => {
        const prevButton = screen.getByRole('button', { name: /Prev/ });
        expect(prevButton).toBeDisabled();
      });
    });

    it('should enable next button on first frame', async () => {
      renderWithProviders();

      await waitFor(() => {
        const nextButton = screen.getByRole('button', { name: /Next/ });
        expect(nextButton).not.toBeDisabled();
      });
    });

    it('should navigate to next frame when next button clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/ })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Next/ }));

      // Wait for frame to change
      await waitFor(() => {
        expect(screen.getByText(/Frame 2/)).toBeInTheDocument();
      });
    });

    it('should navigate to prev frame when prev button clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/ })).toBeInTheDocument();
      });

      // Go to frame 2 first
      await user.click(screen.getByRole('button', { name: /Next/ }));

      await waitFor(() => {
        const prevButton = screen.getByRole('button', { name: /Prev/ });
        expect(prevButton).not.toBeDisabled();
      });

      // Then go back
      await user.click(screen.getByRole('button', { name: /Prev/ }));

      // Wait for frame to change back
      await waitFor(() => {
        expect(screen.getByText(/Frame 1/)).toBeInTheDocument();
      });
    });
  });

  // ============================================
  // SKIP TO VALIDATION TESTS
  // ============================================
  describe('Skip to Next Validation', () => {
    it('should render skip to next validation button', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Skip to Next Validation')).toBeInTheDocument();
      });
    });

    it('should navigate to next frame needing validation when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Skip to Next Validation')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Skip to Next Validation'));

      // Should go to frame 2 (first frame needing validation after frame 1)
      await waitFor(() => {
        expect(screen.getByText(/Frame 2/)).toBeInTheDocument();
      });
    });
  });

  // ============================================
  // DEPTH EDITOR PANEL TESTS
  // ============================================
  describe('Depth Editor Panel', () => {
    it('should render depth map editor header', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Depth Map Editor')).toBeInTheDocument();
      });
    });

    it('should render toggle original view button', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Show Original')).toBeInTheDocument();
      });
    });

    it('should show depth editor by default', async () => {
      renderWithProviders();

      await waitFor(() => {
        // Check that the editor toolbar is present
        expect(screen.getByTitle('Brush (B)')).toBeInTheDocument();
      });
    });

    it('should toggle to original view when button clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Show Original')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Show Original'));

      await waitFor(() => {
        expect(screen.getByText('Show Depth')).toBeInTheDocument();
      });
    });
  });

  // ============================================
  // ACTIONS PANEL TESTS
  // ============================================
  describe('Actions Panel', () => {
    it('should render actions header', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Actions')).toBeInTheDocument();
      });
    });

    it('should render mark as validated button', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Mark as Validated')).toBeInTheDocument();
      });
    });

    it('should call markFrameValidated when button clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Mark as Validated')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Mark as Validated'));

      await waitFor(() => {
        expect(depthValidationApi.markFrameValidated).toHaveBeenCalledWith('test-job-123', 0);
      });
    });

    it('should render keyboard shortcuts section', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Keyboard Shortcuts')).toBeInTheDocument();
      });
    });

    it('should show all keyboard shortcuts', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Previous frame')).toBeInTheDocument();
        expect(screen.getByText('Next frame')).toBeInTheDocument();
        expect(screen.getByText('Skip to validation')).toBeInTheDocument();
        expect(screen.getByText('Mark validated')).toBeInTheDocument();
        expect(screen.getByText('Save correction')).toBeInTheDocument();
        expect(screen.getByText('Toggle original')).toBeInTheDocument();
      });
    });
  });

  // ============================================
  // PROGRESS INDICATOR TESTS
  // ============================================
  describe('Progress Indicator', () => {
    it('should render progress section', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Progress')).toBeInTheDocument();
      });
    });

    it('should show validated frames count', async () => {
      renderWithProviders();

      await waitFor(() => {
        // 10 total - 3 needing validation = 7 validated
        expect(screen.getByText('7 of 10 frames validated')).toBeInTheDocument();
      });
    });

    it('should render progress bar', async () => {
      renderWithProviders();

      await waitFor(() => {
        const progressBar = document.querySelector('.bg-green-500');
        expect(progressBar).toBeInTheDocument();
      });
    });
  });

  // ============================================
  // FRAME INFO TESTS
  // ============================================
  describe('Frame Info', () => {
    it('should show frame timestamp', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Frame Navigation')).toBeInTheDocument();
      });

      // Navigate to frame 2 which has timestamp 100ms
      await user.click(screen.getByRole('button', { name: /Frame 2/ }));

      await waitFor(() => {
        expect(screen.getByText(/Timestamp: 0.10s/)).toBeInTheDocument();
      });
    });

    it('should show confidence score when available', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Frame Navigation')).toBeInTheDocument();
      });

      // Navigate to frame 2 which has confidence score 0.85
      await user.click(screen.getByRole('button', { name: /Frame 2/ }));

      await waitFor(() => {
        expect(screen.getByText(/Confidence: 85.0%/)).toBeInTheDocument();
      });
    });

    it('should show validation status', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText(/Status:/)).toBeInTheDocument();
      });
    });
  });

  // ============================================
  // KEYBOARD NAVIGATION TESTS
  // ============================================
  describe('Keyboard Navigation', () => {
    it('should navigate to next frame with right arrow', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Frame Navigation')).toBeInTheDocument();
      });

      fireEvent.keyDown(window, { key: 'ArrowRight' });

      // Wait for frame to change
      await waitFor(() => {
        expect(screen.getByText(/Frame 2/)).toBeInTheDocument();
      });
    });

    it('should navigate to prev frame with left arrow', async () => {
      const user = userEvent.setup();
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Next/ })).toBeInTheDocument();
      });

      // Go to frame 2 first
      await user.click(screen.getByRole('button', { name: /Next/ }));

      await waitFor(() => {
        expect(screen.getByText(/Frame 2/)).toBeInTheDocument();
      });

      // Then press left arrow
      fireEvent.keyDown(window, { key: 'ArrowLeft' });

      // Wait for frame to change back
      await waitFor(() => {
        expect(screen.getByText(/Frame 1/)).toBeInTheDocument();
      });
    });

    it('should skip to next validation with Tab', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Frame Navigation')).toBeInTheDocument();
      });

      fireEvent.keyDown(window, { key: 'Tab' });

      // Should go to frame 2 (first frame needing validation after frame 1)
      await waitFor(() => {
        expect(screen.getByText(/Frame 2/)).toBeInTheDocument();
      });
    });

    it('should toggle original view with O key', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Show Original')).toBeInTheDocument();
      });

      fireEvent.keyDown(window, { key: 'o' });

      await waitFor(() => {
        expect(screen.getByText('Show Depth')).toBeInTheDocument();
      });
    });

    it('should not handle keyboard shortcuts when focused on input', async () => {
      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Frame Navigation')).toBeInTheDocument();
      });

      // Simulate focus on an input
      const input = document.createElement('input');
      document.body.appendChild(input);
      input.focus();

      fireEvent.keyDown(window, { key: 'ArrowRight', target: input });

      // Should stay on frame 1 since we're focused on input
      await waitFor(() => {
        expect(screen.getByText(/Frame 1/)).toBeInTheDocument();
      });

      document.body.removeChild(input);
    });
  });

  // ============================================
  // ERROR ALERT TESTS
  // ============================================
  describe('Error Alert', () => {
    it('should show error alert when error occurs', async () => {
      vi.mocked(depthValidationApi.getFrameDepthMap).mockRejectedValue(
        new Error('Failed to load depth map')
      );

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Failed to load frame')).toBeInTheDocument();
      });
    });

    it('should dismiss error when close button clicked', async () => {
      const user = userEvent.setup();
      vi.mocked(depthValidationApi.getFrameDepthMap).mockRejectedValue(
        new Error('Failed to load depth map')
      );

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Failed to load frame')).toBeInTheDocument();
      });

      // Find and click the close button (×)
      const closeButton = screen.getByRole('button', { name: '' });
      await user.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('Failed to load frame')).not.toBeInTheDocument();
      });
    });
  });

  // ============================================
  // MUTATION LOADING STATES
  // ============================================
  describe('Mutation Loading States', () => {
    it('should show loading spinner during validation', async () => {
      const user = userEvent.setup();
      vi.mocked(depthValidationApi.markFrameValidated).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      );

      renderWithProviders();

      await waitFor(() => {
        expect(screen.getByText('Mark as Validated')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Mark as Validated'));

      // Should show loading spinner (Loader2 with animate-spin)
      await waitFor(() => {
        const spinner = document.querySelector('.animate-spin');
        expect(spinner).toBeInTheDocument();
      });
    });
  });
});
