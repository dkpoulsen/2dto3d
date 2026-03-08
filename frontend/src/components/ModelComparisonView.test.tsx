import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ModelComparisonView } from '../components/ModelComparisonView';
import { renderWithProviders, createMockSession, createMockResults } from '../test/utils';

// Mock the comparison API
vi.mock('../api', () => ({
  comparisonApi: {
    submitVote: vi.fn(),
    removeVote: vi.fn(),
  },
}));

describe('ModelComparisonView', () => {
  const mockSession = createMockSession();
  const defaultProps = {
    session: mockSession,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render the title and description', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByText('Model Comparison')).toBeInTheDocument();
      expect(screen.getByText(/compare depth estimation results/i)).toBeInTheDocument();
    });

    it('should display session info', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByText(/session:/i)).toBeInTheDocument();
      expect(screen.getByText(/frame: 10/i)).toBeInTheDocument();
      expect(screen.getByText('4 models')).toBeInTheDocument();
    });

    it('should display original frame image', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      const image = screen.getByAltText('Original frame for comparison');
      expect(image).toBeInTheDocument();
      expect(image).toHaveAttribute('src', mockSession.original_frame_url);
    });

    it('should display model names in grid view', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      // Each model name appears in its card
      expect(screen.getByText('MiDaS Small')).toBeInTheDocument();
      expect(screen.getByText('MiDaS Hybrid')).toBeInTheDocument();
      expect(screen.getByText('DPT Large')).toBeInTheDocument();
      expect(screen.getByText('DPT Hybrid')).toBeInTheDocument();
    });
  });

  describe('view mode tabs', () => {
    it('should have Grid tab visible', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByRole('tab', { name: 'Grid' })).toBeInTheDocument();
    });

    it('should have Metrics tab visible', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByRole('tab', { name: 'Metrics' })).toBeInTheDocument();
    });

    it('should have Split tab visible', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByRole('tab', { name: 'Split' })).toBeInTheDocument();
    });

    it('should switch to Metrics view when tab is clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      await user.click(screen.getByRole('tab', { name: 'Metrics' }));
      
      // Should show metrics panel
      expect(screen.getByText('Comparison Metrics')).toBeInTheDocument();
    });

    it('should switch to Split view when tab is clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      await user.click(screen.getByRole('tab', { name: 'Split' }));
      
      // Should show navigation controls
      expect(screen.getByLabelText('Previous model')).toBeInTheDocument();
      expect(screen.getByLabelText('Next model')).toBeInTheDocument();
    });
  });

  describe('split view navigation', () => {
    it('should show navigation controls in split view', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      await user.click(screen.getByRole('tab', { name: 'Split' }));
      
      expect(screen.getByLabelText('Previous model')).toBeInTheDocument();
      expect(screen.getByLabelText('Next model')).toBeInTheDocument();
    });

    it('should navigate to next model when next button is clicked', async () => {
      const user = userEvent.setup();
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      await user.click(screen.getByRole('tab', { name: 'Split' }));
      await user.click(screen.getByLabelText('Next model'));
      
      // Should show second model - aria-live region should announce
      expect(screen.getByText(/MiDaS Hybrid/)).toBeInTheDocument();
    });
  });

  describe('quick stats', () => {
    it('should display fastest model label', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByText('Fastest Model')).toBeInTheDocument();
    });

    it('should display highest confidence label', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByText('Highest Confidence')).toBeInTheDocument();
    });

    it('should display most votes label', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByText('Most Votes')).toBeInTheDocument();
    });
  });

  describe('action buttons', () => {
    it('should show random button when onLoadRandomSession is provided', () => {
      const onLoadRandom = vi.fn();
      renderWithProviders(<ModelComparisonView {...defaultProps} onLoadRandomSession={onLoadRandom} />);
      
      expect(screen.getByText('Random')).toBeInTheDocument();
    });

    it('should not show random button when onLoadRandomSession is not provided', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.queryByText('Random')).not.toBeInTheDocument();
    });

    it('should call onLoadRandomSession when random button is clicked', async () => {
      const onLoadRandom = vi.fn();
      const user = userEvent.setup();
      renderWithProviders(<ModelComparisonView {...defaultProps} onLoadRandomSession={onLoadRandom} />);
      
      await user.click(screen.getByText('Random'));
      
      expect(onLoadRandom).toHaveBeenCalledTimes(1);
    });
  });

  describe('VotingWidget integration', () => {
    it('should render voting widget', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByText('Cast Your Vote')).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('should have proper tablist structure', () => {
      renderWithProviders(<ModelComparisonView {...defaultProps} />);
      
      expect(screen.getByRole('tablist')).toBeInTheDocument();
    });
  });

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = renderWithProviders(<ModelComparisonView {...defaultProps} className="custom-class" />);
      
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });
});
