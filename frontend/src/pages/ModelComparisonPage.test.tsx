import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ModelComparisonPage } from '../pages/ModelComparisonPage';
import { renderWithProviders, createMockSession, createMockLeaderboard } from '../test/utils';

// Mock the API client
vi.mock('../api', () => ({
  comparisonApi: {
    getRandomSession: vi.fn(),
    getSession: vi.fn(),
    getLeaderboard: vi.fn(),
    createSession: vi.fn(),
  },
}));

// Import after mocking
import { comparisonApi } from '../api';

const mockComparisonApi = vi.mocked(comparisonApi);

describe('ModelComparisonPage', () => {
  const mockSession = createMockSession();
  const mockLeaderboard = createMockLeaderboard();

  beforeEach(() => {
    vi.clearAllMocks();
    mockComparisonApi.getRandomSession.mockResolvedValue(mockSession);
    mockComparisonApi.getLeaderboard.mockResolvedValue(mockLeaderboard);
  });

  describe('initial render', () => {
    it('should render the page title', () => {
      renderWithProviders(<ModelComparisonPage />);
      
      expect(screen.getByText('Model Comparison')).toBeInTheDocument();
    });

    it('should render page description', () => {
      renderWithProviders(<ModelComparisonPage />);
      
      expect(screen.getByText(/compare depth estimation models/i)).toBeInTheDocument();
    });

    it('should show tabs for Comparison and Leaderboard', () => {
      renderWithProviders(<ModelComparisonPage />);
      
      expect(screen.getByText('Comparison Tool')).toBeInTheDocument();
      expect(screen.getByText('Leaderboard')).toBeInTheDocument();
    });
  });

  describe('comparison tab', () => {
    it('should load random session on mount', async () => {
      renderWithProviders(<ModelComparisonPage />);
      
      await waitFor(() => {
        expect(mockComparisonApi.getRandomSession).toHaveBeenCalled();
      });
    });

    it('should display comparison view after session loads', async () => {
      renderWithProviders(<ModelComparisonPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Model Comparison')).toBeInTheDocument();
      });
    });

    it('should show "Load Random" button', async () => {
      renderWithProviders(<ModelComparisonPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Load Random')).toBeInTheDocument();
      });
    });

    it('should load new random session when clicking Random button', async () => {
      const user = userEvent.setup();
      const secondSession = createMockSession({ session_id: 'second-session' });
      
      mockComparisonApi.getRandomSession
        .mockResolvedValueOnce(mockSession)
        .mockResolvedValueOnce(secondSession);
      
      renderWithProviders(<ModelComparisonPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Load Random')).toBeInTheDocument();
      });
      
      await user.click(screen.getByText('Load Random'));
      
      await waitFor(() => {
        expect(mockComparisonApi.getRandomSession).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('leaderboard tab', () => {
    it('should switch to Leaderboard tab when clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ModelComparisonPage />);
      
      await user.click(screen.getByText('Leaderboard'));
      
      // Should be selected
      const leaderboardTab = screen.getByText('Leaderboard').closest('button');
      expect(leaderboardTab).toHaveClass('border-primary-500');
    });

    it('should display leaderboard data after switching to tab', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ModelComparisonPage />);
      
      await user.click(screen.getByText('Leaderboard'));
      
      await waitFor(() => {
        expect(mockComparisonApi.getLeaderboard).toHaveBeenCalled();
      });
    });

    it('should display leaderboard entries', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ModelComparisonPage />);
      
      await user.click(screen.getByText('Leaderboard'));
      
      await waitFor(() => {
        expect(screen.getByText('DPT Large')).toBeInTheDocument();
        expect(screen.getByText('MiDaS Small')).toBeInTheDocument();
      });
    });
  });

  describe('create comparison form', () => {
    it('should have job ID input', () => {
      renderWithProviders(<ModelComparisonPage />);
      
      expect(screen.getByLabelText(/job id/i)).toBeInTheDocument();
    });

    it('should have frame index input', () => {
      renderWithProviders(<ModelComparisonPage />);
      
      expect(screen.getByLabelText(/frame index/i)).toBeInTheDocument();
    });

    it('should have create comparison button', () => {
      renderWithProviders(<ModelComparisonPage />);
      
      expect(screen.getByText('Create Comparison')).toBeInTheDocument();
    });

    it('should call createSession when form is submitted', async () => {
      const user = userEvent.setup();
      mockComparisonApi.createSession.mockResolvedValueOnce(mockSession);
      
      renderWithProviders(<ModelComparisonPage />);
      
      const jobIdInput = screen.getByLabelText(/job id/i);
      await user.type(jobIdInput, 'test-job-123');
      
      await user.click(screen.getByText('Create Comparison'));
      
      await waitFor(() => {
        expect(mockComparisonApi.createSession).toHaveBeenCalledWith({
          job_id: 'test-job-123',
          frame_index: undefined,
        });
      });
    });
  });

  describe('loading state', () => {
    it('should show loading indicator while fetching session', () => {
      // Make API never resolve
      mockComparisonApi.getRandomSession.mockImplementation(() => new Promise(() => {}));
      
      renderWithProviders(<ModelComparisonPage />);
      
      expect(screen.getByText(/loading comparison/i)).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('should have proper heading hierarchy', () => {
      renderWithProviders(<ModelComparisonPage />);
      
      const heading = screen.getByRole('heading', { level: 2 });
      expect(heading).toHaveTextContent('Model Comparison');
    });
  });
});
