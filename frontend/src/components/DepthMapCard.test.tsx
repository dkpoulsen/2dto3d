import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DepthMapCard } from '../components/DepthMapCard';
import { createMockModelResult } from '../test/utils';

describe('DepthMapCard', () => {
  const mockResult = createMockModelResult();
  const defaultProps = {
    result: mockResult,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('should render model name and description', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.getByText('MiDaS Small')).toBeInTheDocument();
      expect(screen.getByText(/Fast and lightweight/)).toBeInTheDocument();
    });

    it('should render depth map image with correct src', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      const image = screen.getByRole('img', { name: /depth map from midas small/i });
      expect(image).toHaveAttribute('src', mockResult.depth_map_url);
    });

    it('should display processing time in metrics', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.getByText(/1.50s/)).toBeInTheDocument();
    });

    it('should display confidence percentage', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.getByText('85%')).toBeInTheDocument();
    });

    it('should display memory usage', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.getByText(/512 MB/)).toBeInTheDocument();
    });

    it('should display quality score when available', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.getByText('90%')).toBeInTheDocument();
    });

    it('should display vote count', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.getByText('5 votes')).toBeInTheDocument();
    });

    it('should display singular vote when only one vote', () => {
      render(<DepthMapCard {...defaultProps} result={{ ...mockResult, votes: 1 }} />);
      
      expect(screen.getByText('1 vote')).toBeInTheDocument();
    });

    it('should show "Your vote" indicator when user has voted', () => {
      render(<DepthMapCard {...defaultProps} result={{ ...mockResult, user_voted: true }} />);
      
      expect(screen.getByText('Your vote')).toBeInTheDocument();
    });

    it('should not show "Your vote" indicator when user has not voted', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.queryByText('Your vote')).not.toBeInTheDocument();
    });
  });

  describe('selection state', () => {
    it('should not show selected state by default', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.queryByText('Selected')).not.toBeInTheDocument();
    });

    it('should show selected state when isSelected is true', () => {
      render(<DepthMapCard {...defaultProps} isSelected={true} />);
      
      expect(screen.getByText('Selected')).toBeInTheDocument();
    });

    it('should apply selected styling when selected', () => {
      const { container } = render(<DepthMapCard {...defaultProps} isSelected={true} />);
      
      const card = container.firstChild;
      expect(card).toHaveClass('border-primary-500');
    });

    it('should not apply selected styling when not selected', () => {
      const { container } = render(<DepthMapCard {...defaultProps} isSelected={false} />);
      
      const card = container.firstChild;
      expect(card).not.toHaveClass('border-primary-500');
    });
  });

  describe('click handling', () => {
    it('should call onClick when card is clicked', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      
      render(<DepthMapCard {...defaultProps} onClick={onClick} />);
      
      // Click on the header to trigger card selection
      await user.click(screen.getByText('MiDaS Small'));
      
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('should not call onClick when zoom buttons are clicked', async () => {
      const onClick = vi.fn();
      const user = userEvent.setup();
      
      render(<DepthMapCard {...defaultProps} onClick={onClick} />);
      
      // Find and click zoom in button
      const zoomInButton = screen.getByLabelText('Zoom in');
      await user.click(zoomInButton);
      
      expect(onClick).not.toHaveBeenCalled();
    });
  });

  describe('keyboard accessibility', () => {
    it('should be focusable when onClick is provided', () => {
      const onClick = vi.fn();
      const { container } = render(<DepthMapCard {...defaultProps} onClick={onClick} />);
      
      // The card div itself has role="button"
      const card = container.firstChild;
      expect(card).toHaveAttribute('tabIndex', '0');
      expect(card).toHaveAttribute('role', 'button');
    });

    it('should not be focusable when onClick is not provided', () => {
      const { container } = render(<DepthMapCard {...defaultProps} />);
      
      // The card div does not have role="button" when no onClick
      const card = container.firstChild;
      expect(card).not.toHaveAttribute('role', 'button');
    });

    it('should respond to Enter key press', async () => {
      const onClick = vi.fn();
      const { container } = render(<DepthMapCard {...defaultProps} onClick={onClick} />);
      
      const card = container.firstChild as HTMLElement;
      fireEvent.keyDown(card, { key: 'Enter' });
      
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    it('should respond to Space key press', async () => {
      const onClick = vi.fn();
      const { container } = render(<DepthMapCard {...defaultProps} onClick={onClick} />);
      
      const card = container.firstChild as HTMLElement;
      fireEvent.keyDown(card, { key: ' ' });
      
      expect(onClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('zoom controls', () => {
    it('should display current zoom level as 100% by default', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.getByLabelText('Zoom level 100%')).toBeInTheDocument();
    });

    it('should increase zoom when zoom in button is clicked', async () => {
      const user = userEvent.setup();
      render(<DepthMapCard {...defaultProps} />);
      
      const zoomInButton = screen.getByLabelText('Zoom in');
      await user.click(zoomInButton);
      
      expect(screen.getByLabelText('Zoom level 150%')).toBeInTheDocument();
    });

    it('should decrease zoom when zoom out button is clicked', async () => {
      const user = userEvent.setup();
      render(<DepthMapCard {...defaultProps} />);
      
      // First zoom in to have room to zoom out
      await user.click(screen.getByLabelText('Zoom in'));
      expect(screen.getByLabelText('Zoom level 150%')).toBeInTheDocument();
      
      // Then zoom out
      await user.click(screen.getByLabelText('Zoom out'));
      expect(screen.getByLabelText('Zoom level 100%')).toBeInTheDocument();
    });

    it('should reset zoom when reset button is clicked', async () => {
      const user = userEvent.setup();
      render(<DepthMapCard {...defaultProps} />);
      
      // Zoom in multiple times
      await user.click(screen.getByLabelText('Zoom in'));
      await user.click(screen.getByLabelText('Zoom in'));
      expect(screen.getByLabelText('Zoom level 200%')).toBeInTheDocument();
      
      // Reset
      await user.click(screen.getByLabelText('Reset zoom'));
      expect(screen.getByLabelText('Zoom level 100%')).toBeInTheDocument();
    });

    it('should disable zoom out button at minimum zoom', async () => {
      const user = userEvent.setup();
      render(<DepthMapCard {...defaultProps} />);
      
      // Zoom out to minimum (50%)
      await user.click(screen.getByLabelText('Zoom out'));
      expect(screen.getByLabelText('Zoom level 50%')).toBeInTheDocument();
      
      // Now zoom out should be disabled
      const zoomOutButton = screen.getByLabelText('Zoom out');
      expect(zoomOutButton).toBeDisabled();
    });

    it('should disable zoom in button at maximum zoom', async () => {
      const user = userEvent.setup();
      render(<DepthMapCard {...defaultProps} />);
      
      // Zoom in to maximum (4x = 400%)
      for (let i = 0; i < 6; i++) {
        await user.click(screen.getByLabelText('Zoom in'));
      }
      
      const zoomInButton = screen.getByLabelText('Zoom in');
      expect(zoomInButton).toBeDisabled();
    });

    it('should cap zoom at maximum value', async () => {
      const user = userEvent.setup();
      render(<DepthMapCard {...defaultProps} />);
      
      // Try to zoom in many times
      for (let i = 0; i < 10; i++) {
        await user.click(screen.getByLabelText('Zoom in'));
      }
      
      expect(screen.getByLabelText('Zoom level 400%')).toBeInTheDocument();
    });

    it('should cap zoom at minimum value', async () => {
      const user = userEvent.setup();
      render(<DepthMapCard {...defaultProps} />);
      
      // Try to zoom out many times
      for (let i = 0; i < 10; i++) {
        await user.click(screen.getByLabelText('Zoom out'));
      }
      
      expect(screen.getByLabelText('Zoom level 50%')).toBeInTheDocument();
    });
  });

  describe('image loading states', () => {
    it('should show loading spinner while image is loading', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      // The loading spinner should be present (animate-spin class)
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should hide spinner after image loads', async () => {
      render(<DepthMapCard {...defaultProps} />);
      
      const image = screen.getByRole('img');
      fireEvent.load(image);
      
      await waitFor(() => {
        expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
      });
    });

    it('should show error state when image fails to load', async () => {
      render(<DepthMapCard {...defaultProps} />);
      
      const image = screen.getByRole('img');
      fireEvent.error(image);
      
      expect(screen.getByText('Failed to load image')).toBeInTheDocument();
    });
  });

  describe('showMetrics prop', () => {
    it('should show metrics by default', () => {
      render(<DepthMapCard {...defaultProps} />);
      
      expect(screen.getByText('Processing Time:')).toBeInTheDocument();
    });

    it('should hide metrics when showMetrics is false', () => {
      render(<DepthMapCard {...defaultProps} showMetrics={false} />);
      
      expect(screen.queryByText('Processing Time:')).not.toBeInTheDocument();
    });
  });

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(<DepthMapCard {...defaultProps} className="custom-class" />);
      
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('accessibility', () => {
    it('should have correct aria-label for selection', () => {
      const { container } = render(<DepthMapCard {...defaultProps} onClick={() => {}} />);
      
      expect(container.firstChild).toHaveAttribute('aria-label', 'Select MiDaS Small depth map');
    });

    it('should have aria-pressed when selected', () => {
      const { container } = render(<DepthMapCard {...defaultProps} onClick={() => {}} isSelected={true} />);
      
      expect(container.firstChild).toHaveAttribute('aria-pressed', 'true');
    });

    it('should have aria-pressed false when not selected', () => {
      const { container } = render(<DepthMapCard {...defaultProps} onClick={() => {}} isSelected={false} />);
      
      expect(container.firstChild).toHaveAttribute('aria-pressed', 'false');
    });
  });
});
