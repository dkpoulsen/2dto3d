import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { VotingWidget } from '../components/VotingWidget';
import { renderWithProviders, createMockSession, createMockResults } from '../test/utils';

describe('VotingWidget', () => {
  const mockSession = createMockSession();
  const mockResults = createMockResults();
  const mockOnVote = vi.fn();
  const mockOnRemoveVote = vi.fn();
  
  const defaultProps = {
    session: mockSession,
    results: mockResults,
    onVote: mockOnVote,
    onRemoveVote: mockOnRemoveVote,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render the title', () => {
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      expect(screen.getByText('Cast Your Vote')).toBeInTheDocument();
    });

    it('should show total votes count', () => {
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      expect(screen.getByText('17 votes cast')).toBeInTheDocument();
    });

    it('should show singular "vote" when only one vote', () => {
      const singleVoteSession = createMockSession({ total_votes: 1 });
      renderWithProviders(<VotingWidget {...defaultProps} session={singleVoteSession} />);
      
      expect(screen.getByText('1 vote cast')).toBeInTheDocument();
    });

    it('should show "Voting Open" badge when session is active', () => {
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      expect(screen.getByText('Voting Open')).toBeInTheDocument();
    });

    it('should show "Voting Closed" badge when session is inactive', () => {
      const inactiveSession = createMockSession({ is_active: false });
      renderWithProviders(<VotingWidget {...defaultProps} session={inactiveSession} />);
      
      expect(screen.getByText('Voting Closed')).toBeInTheDocument();
    });

    it('should display all model options', () => {
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      expect(screen.getByText('MiDaS Small')).toBeInTheDocument();
      expect(screen.getByText('MiDaS Hybrid')).toBeInTheDocument();
      expect(screen.getByText('DPT Large')).toBeInTheDocument();
      expect(screen.getByText('DPT Hybrid')).toBeInTheDocument();
    });
  });

  describe('model selection', () => {
    it('should allow selecting a model when not yet voted', async () => {
      const user = userEvent.setup();
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      // Find the first model button (radio button in radiogroup)
      const radioGroup = screen.getByRole('radiogroup');
      const radioButtons = screen.getAllByRole('radio');
      
      await user.click(radioButtons[0]);
      
      expect(radioButtons[0]).toHaveAttribute('aria-checked', 'true');
    });

    it('should only allow one model to be selected at a time', async () => {
      const user = userEvent.setup();
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      const radioButtons = screen.getAllByRole('radio');
      
      await user.click(radioButtons[0]);
      expect(radioButtons[0]).toHaveAttribute('aria-checked', 'true');
      
      await user.click(radioButtons[1]);
      expect(radioButtons[1]).toHaveAttribute('aria-checked', 'true');
      expect(radioButtons[0]).toHaveAttribute('aria-checked', 'false');
    });
  });

  describe('submitting vote', () => {
    it('should disable submit button without model selection', () => {
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      // Find the submit button by text
      const submitButton = screen.getByRole('button', { name: /submit/i });
      expect(submitButton).toBeDisabled();
    });

    it('should call onVote when submitting vote', async () => {
      const user = userEvent.setup();
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      const radioButtons = screen.getAllByRole('radio');
      await user.click(radioButtons[0]);
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);
      
      expect(mockOnVote).toHaveBeenCalledWith('midas_small', undefined);
    });

    it('should include comment when submitting with comment', async () => {
      const user = userEvent.setup();
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      const radioButtons = screen.getAllByRole('radio');
      await user.click(radioButtons[0]);
      
      // Show comment field
      await user.click(screen.getByText(/add a comment/i));
      
      // Type comment
      const commentInput = screen.getByPlaceholderText(/explain why you chose/i);
      await user.type(commentInput, 'Best quality depth map');
      
      const submitButton = screen.getByRole('button', { name: /submit/i });
      await user.click(submitButton);
      
      expect(mockOnVote).toHaveBeenCalledWith('midas_small', 'Best quality depth map');
    });
  });

  describe('after voting', () => {
    it('should show user vote when they have voted', () => {
      const votedSession = createMockSession({
        user_vote: {
          session_id: 'test-session-123',
          model: 'midas_small',
          comment: undefined,
          voted_at: '2024-01-15T10:30:00Z',
        },
      });
      
      renderWithProviders(<VotingWidget {...defaultProps} session={votedSession} />);
      
      expect(screen.getByText(/you voted for/i)).toBeInTheDocument();
    });

    it('should show vote results chart after voting', () => {
      const votedSession = createMockSession({
        user_vote: {
          session_id: 'test-session-123',
          model: 'midas_small',
          comment: undefined,
          voted_at: '2024-01-15T10:30:00Z',
        },
      });
      
      renderWithProviders(<VotingWidget {...defaultProps} session={votedSession} />);
      
      // Should show progress bars
      const progressBars = screen.getAllByRole('progressbar');
      expect(progressBars.length).toBeGreaterThan(0);
    });
  });

  describe('removing vote', () => {
    it('should show remove vote option after voting', () => {
      const votedSession = createMockSession({
        user_vote: {
          session_id: 'test-session-123',
          model: 'midas_small',
          comment: undefined,
          voted_at: '2024-01-15T10:30:00Z',
        },
      });
      
      renderWithProviders(<VotingWidget {...defaultProps} session={votedSession} />);
      
      expect(screen.getByText(/remove my vote/i)).toBeInTheDocument();
    });

    it('should show confirmation dialog when clicking remove', async () => {
      const user = userEvent.setup();
      const votedSession = createMockSession({
        user_vote: {
          session_id: 'test-session-123',
          model: 'midas_small',
          comment: undefined,
          voted_at: '2024-01-15T10:30:00Z',
        },
      });
      
      renderWithProviders(<VotingWidget {...defaultProps} session={votedSession} />);
      
      await user.click(screen.getByText(/remove my vote/i));
      
      expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('should have proper radiogroup role', () => {
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      expect(screen.getByRole('radiogroup')).toBeInTheDocument();
    });

    it('should have aria-checked on radio buttons', async () => {
      const user = userEvent.setup();
      renderWithProviders(<VotingWidget {...defaultProps} />);
      
      const radioButton = screen.getAllByRole('radio')[0];
      expect(radioButton).toHaveAttribute('aria-checked', 'false');
      
      await user.click(radioButton);
      expect(radioButton).toHaveAttribute('aria-checked', 'true');
    });
  });

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = renderWithProviders(<VotingWidget {...defaultProps} className="custom-class" />);
      
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });
});
