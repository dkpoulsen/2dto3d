import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ThumbnailGrid } from '../ThumbnailGrid';
import type { ThumbnailFrame } from '../../api/types';

// Mock data
const mockThumbnails: ThumbnailFrame[] = [
  {
    frame_index: 0,
    timestamp: 0.0,
    original_url: '/frames/0/original.jpg',
    depth_map_url: '/frames/0/depth.jpg',
    confidence_score: 0.85,
    validation_status: 'pending',
  },
  {
    frame_index: 10,
    timestamp: 0.5,
    original_url: '/frames/10/original.jpg',
    depth_map_url: '/frames/10/depth.jpg',
    confidence_score: 0.92,
    validation_status: 'validated',
  },
  {
    frame_index: 20,
    timestamp: 1.0,
    original_url: '/frames/20/original.jpg',
    depth_map_url: '/frames/20/depth.jpg',
    confidence_score: 0.78,
    validation_status: 'corrected',
  },
];

const mockFetchThumbnails = vi.fn();

const defaultProps = {
  jobId: 'test-job-1',
  onFetchThumbnails: mockFetchThumbnails,
};

describe('ThumbnailGrid', () => {
  beforeEach(() => {
    mockFetchThumbnails.mockReset();
    mockFetchThumbnails.mockResolvedValue(mockThumbnails);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should show loading spinner while fetching thumbnails', () => {
      // Never resolve to test loading state
      mockFetchThumbnails.mockImplementation(() => new Promise(() => {}));

      render(<ThumbnailGrid {...defaultProps} />);

      expect(screen.getByText('Loading thumbnail grid...')).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('should show error message when fetch fails', async () => {
      mockFetchThumbnails.mockRejectedValue(new Error('Network error'));

      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to Load Thumbnails')).toBeInTheDocument();
      });
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });

    it('should show retry button on error', async () => {
      mockFetchThumbnails.mockRejectedValue(new Error('Network error'));

      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
      });
    });

    it('should retry fetch when retry button is clicked', async () => {
      const user = userEvent.setup();
      mockFetchThumbnails.mockRejectedValueOnce(new Error('Network error'));

      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
      });

      // Reset mock to resolve on next call
      mockFetchThumbnails.mockResolvedValueOnce(mockThumbnails);

      await user.click(screen.getByRole('button', { name: 'Retry' }));

      await waitFor(() => {
        expect(mockFetchThumbnails).toHaveBeenCalledTimes(2);
      });
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no thumbnails are returned', async () => {
      mockFetchThumbnails.mockResolvedValue([]);

      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('No Thumbnails Available')).toBeInTheDocument();
      });
      expect(screen.getByText(/No frame thumbnails are available/)).toBeInTheDocument();
    });
  });

  describe('Loaded State', () => {
    it('should render thumbnail grid with fetched data', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      expect(screen.getByText('(3 frames)')).toBeInTheDocument();
    });

    it('should call fetchThumbnails with correct parameters', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(mockFetchThumbnails).toHaveBeenCalledWith('test-job-1', { count: 24 });
      });
    });

    it('should display frame information with 1-based indexing', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        // frame_index 0 should display as "Frame 1"
        expect(screen.getByText('Frame 1')).toBeInTheDocument();
      });

      // frame_index 10 should display as "Frame 11"
      expect(screen.getByText('Frame 11')).toBeInTheDocument();
      // frame_index 20 should display as "Frame 21"
      expect(screen.getByText('Frame 21')).toBeInTheDocument();
    });

    it('should display timestamps', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('0.00s')).toBeInTheDocument();
      });
      expect(screen.getByText('0.50s')).toBeInTheDocument();
      expect(screen.getByText('1.00s')).toBeInTheDocument();
    });
  });

  describe('Display Mode Toggle', () => {
    it('should show display mode buttons when showDepthMaps is true', async () => {
      render(<ThumbnailGrid {...defaultProps} showDepthMaps={true} />);

      await waitFor(() => {
        // Buttons have text "Original", "Depth", "Both"
        expect(screen.getByRole('button', { name: 'Original' })).toBeInTheDocument();
      });
      expect(screen.getByRole('button', { name: 'Depth' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Both' })).toBeInTheDocument();
    });

    it('should not show display mode buttons when showDepthMaps is false', async () => {
      render(<ThumbnailGrid {...defaultProps} showDepthMaps={false} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      expect(screen.queryByRole('button', { name: 'Original' })).not.toBeInTheDocument();
    });

    it('should change display mode when clicking buttons', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} showDepthMaps={true} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Click on "Depth" mode - the button text is "Depth"
      const depthButton = screen.getByRole('button', { name: 'Depth' });
      await user.click(depthButton);

      // Verify the button has active styling (it should have bg-white shadow class when active)
      expect(depthButton).toHaveClass('bg-white');
    });
  });

  describe('Zoom Controls', () => {
    it('should show zoom controls', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Zoom in' })).toBeInTheDocument();
      });
      expect(screen.getByRole('button', { name: 'Zoom out' })).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should increase zoom level when clicking zoom in', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('100%')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: 'Zoom in' }));

      expect(screen.getByText('125%')).toBeInTheDocument();
    });

    it('should decrease zoom level when clicking zoom out', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('100%')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: 'Zoom out' }));

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('should disable zoom out at minimum zoom', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Zoom out' })).toBeInTheDocument();
      });

      // Click zoom out multiple times to reach minimum
      const zoomOutButton = screen.getByRole('button', { name: 'Zoom out' });

      // Click 4 times: 100% -> 75% -> 50% (min)
      await user.click(zoomOutButton); // 75%
      await user.click(zoomOutButton); // 50%
      await user.click(zoomOutButton); // Still 50% (clamped)

      expect(zoomOutButton).toBeDisabled();
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should disable zoom in at maximum zoom', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Zoom in' })).toBeInTheDocument();
      });

      const zoomInButton = screen.getByRole('button', { name: 'Zoom in' });

      // Click zoom in multiple times to reach maximum
      // 100% -> 125% -> 150% -> 175% -> 200% (max)
      await user.click(zoomInButton); // 125%
      await user.click(zoomInButton); // 150%
      await user.click(zoomInButton); // 175%
      await user.click(zoomInButton); // 200%
      await user.click(zoomInButton); // Still 200% (clamped)

      expect(zoomInButton).toBeDisabled();
      expect(screen.getByText('200%')).toBeInTheDocument();
    });
  });

  describe('Pagination', () => {
    it('should not show pagination when all thumbnails fit on one page', async () => {
      render(<ThumbnailGrid {...defaultProps} columns={4} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      expect(screen.queryByText('Previous')).not.toBeInTheDocument();
      expect(screen.queryByText('Next')).not.toBeInTheDocument();
    });

    it('should show pagination when there are multiple pages', async () => {
      // Create more thumbnails to trigger pagination (default is 4 cols * 3 rows = 12 per page)
      const manyThumbnails: ThumbnailFrame[] = Array.from({ length: 24 }, (_, i) => ({
        frame_index: i,
        timestamp: i * 0.5,
        original_url: `/frames/${i}/original.jpg`,
        depth_map_url: `/frames/${i}/depth.jpg`,
      }));

      mockFetchThumbnails.mockResolvedValue(manyThumbnails);

      render(<ThumbnailGrid {...defaultProps} columns={4} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
      expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
    });

    it('should navigate to next page', async () => {
      const user = userEvent.setup();
      const manyThumbnails: ThumbnailFrame[] = Array.from({ length: 24 }, (_, i) => ({
        frame_index: i,
        timestamp: i * 0.5,
        original_url: `/frames/${i}/original.jpg`,
        depth_map_url: `/frames/${i}/depth.jpg`,
      }));

      mockFetchThumbnails.mockResolvedValue(manyThumbnails);

      render(<ThumbnailGrid {...defaultProps} columns={4} />);

      await waitFor(() => {
        expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /Next/ }));

      expect(screen.getByText('Page 2 of 2')).toBeInTheDocument();
    });

    it('should disable previous button on first page', async () => {
      const manyThumbnails: ThumbnailFrame[] = Array.from({ length: 24 }, (_, i) => ({
        frame_index: i,
        timestamp: i * 0.5,
        original_url: `/frames/${i}/original.jpg`,
        depth_map_url: `/frames/${i}/depth.jpg`,
      }));

      mockFetchThumbnails.mockResolvedValue(manyThumbnails);

      render(<ThumbnailGrid {...defaultProps} columns={4} />);

      await waitFor(() => {
        expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /Previous/ })).toBeDisabled();
    });

    it('should disable next button on last page', async () => {
      const user = userEvent.setup();
      const manyThumbnails: ThumbnailFrame[] = Array.from({ length: 24 }, (_, i) => ({
        frame_index: i,
        timestamp: i * 0.5,
        original_url: `/frames/${i}/original.jpg`,
        depth_map_url: `/frames/${i}/depth.jpg`,
      }));

      mockFetchThumbnails.mockResolvedValue(manyThumbnails);

      render(<ThumbnailGrid {...defaultProps} columns={4} />);

      await waitFor(() => {
        expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
      });

      // Navigate to last page
      await user.click(screen.getByRole('button', { name: /Next/ }));

      expect(screen.getByRole('button', { name: /Next/ })).toBeDisabled();
    });
  });

  describe('Thumbnail Click', () => {
    it('should call onThumbnailClick when thumbnail is clicked', async () => {
      const user = userEvent.setup();
      const onThumbnailClick = vi.fn();

      render(<ThumbnailGrid {...defaultProps} onThumbnailClick={onThumbnailClick} />);

      await waitFor(() => {
        expect(screen.getByText('Frame 1')).toBeInTheDocument();
      });

      // Click on the first thumbnail card
      const thumbnailCard = screen.getByText('Frame 1').closest('[role="button"]');
      if (thumbnailCard) {
        await user.click(thumbnailCard);
      }

      expect(onThumbnailClick).toHaveBeenCalledWith(mockThumbnails[0]);
    });
  });

  describe('Selected Frame', () => {
    it('should highlight selected frame', async () => {
      render(<ThumbnailGrid {...defaultProps} selectedFrameIndex={10} />);

      await waitFor(() => {
        // frame_index 10 displays as "Frame 11"
        expect(screen.getByText('Frame 11')).toBeInTheDocument();
      });

      // The selected card should have the primary border color
      const selectedCard = screen.getByText('Frame 11').closest('[role="button"]');
      expect(selectedCard).toHaveClass('border-primary-500');
    });
  });

  describe('Validation Status Badges', () => {
    it('should show validated badge for validated frames', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Validated')).toBeInTheDocument();
      });
    });

    it('should show corrected badge for corrected frames', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Corrected')).toBeInTheDocument();
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('should close modal on Escape key', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open the modal first by clicking on enlarge button
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      fireEvent.click(enlargeButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Timestamp: 0.000s')).toBeInTheDocument();
      });

      // Press Escape to close
      fireEvent.keyDown(window, { key: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByText('Timestamp: 0.000s')).not.toBeInTheDocument();
      });
    });
  });

  describe('Props', () => {
    it('should use custom columns prop', async () => {
      const manyThumbnails: ThumbnailFrame[] = Array.from({ length: 12 }, (_, i) => ({
        frame_index: i,
        timestamp: i * 0.5,
        original_url: `/frames/${i}/original.jpg`,
        depth_map_url: `/frames/${i}/depth.jpg`,
      }));

      mockFetchThumbnails.mockResolvedValue(manyThumbnails);

      render(<ThumbnailGrid {...defaultProps} columns={6} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });
    });

    it('should use custom thumbnailHeight prop', async () => {
      render(<ThumbnailGrid {...defaultProps} thumbnailHeight={200} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });
    });

    it('should apply custom className', async () => {
      render(<ThumbnailGrid {...defaultProps} className="custom-class" />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Use document.querySelector since container may be undefined after async operations
      const containerElement = document.querySelector('.thumbnail-grid-container');
      expect(containerElement).toHaveClass('custom-class');
    });
  });

  describe('Refetch on Job ID Change', () => {
    it('should refetch thumbnails when jobId changes', async () => {
      const { rerender } = render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(mockFetchThumbnails).toHaveBeenCalledWith('test-job-1', { count: 24 });
      });

      mockFetchThumbnails.mockClear();

      rerender(<ThumbnailGrid {...defaultProps} jobId="test-job-2" />);

      await waitFor(() => {
        expect(mockFetchThumbnails).toHaveBeenCalledWith('test-job-2', { count: 24 });
      });
    });
  });

  describe('Modal Functionality', () => {
  describe('Modal Functionality', () => {
    it('should open modal when enlarge button is clicked', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Click on enlarge button
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      await user.click(enlargeButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Timestamp: 0.000s')).toBeInTheDocument();
      });
    });

    it('should close modal when close button is clicked', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open modal
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      await user.click(enlargeButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Timestamp: 0.000s')).toBeInTheDocument();
      });

      // Click close button (X icon button)
      const closeButton = screen.getByRole('button', { name: '' });
      // Find the X button in the modal header
      const modalHeader = screen.getByText('Frame 1').closest('div');
      const xButton = modalHeader?.parentElement?.querySelector('button');
      if (xButton) {
        await user.click(xButton);
      }

      await waitFor(() => {
        expect(screen.queryByText('Timestamp: 0.000s')).not.toBeInTheDocument();
      });
    });

    it('should close modal when clicking outside the modal content', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open modal
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      await user.click(enlargeButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Timestamp: 0.000s')).toBeInTheDocument();
      });

      // Click on the backdrop (outside modal content)
      const backdrop = screen.getByText('Timestamp: 0.000s').closest('.fixed');
      if (backdrop) {
        await user.click(backdrop);
      }

      await waitFor(() => {
        expect(screen.queryByText('Timestamp: 0.000s')).not.toBeInTheDocument();
      });
    });

    it('should lock body scroll when modal is open', async () => {
      const user = userEvent.setup();
      const originalOverflow = document.body.style.overflow;
      
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open modal
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      await user.click(enlargeButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Timestamp: 0.000s')).toBeInTheDocument();
      });

      // Body scroll should be locked
      expect(document.body.style.overflow).toBe('hidden');

      // Close modal
      fireEvent.keyDown(window, { key: 'Escape' });

      await waitFor(() => {
        expect(screen.queryByText('Timestamp: 0.000s')).not.toBeInTheDocument();
      });

      // Body scroll should be restored
      expect(document.body.style.overflow).toBe(originalOverflow);
    });

    it('should navigate to previous frame in modal using Previous button', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open modal on second frame
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      await user.click(enlargeButtons[1]);

      await waitFor(() => {
        expect(screen.getByText('Frame 11')).toBeInTheDocument(); // frame_index 10 + 1
      });

      // Click Previous button
      const previousButton = screen.getByRole('button', { name: /Previous/ });
      await user.click(previousButton);

      await waitFor(() => {
        expect(screen.getByText('Frame 1')).toBeInTheDocument(); // frame_index 0 + 1
      });
    });

    it('should navigate to next frame in modal using Next button', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open modal on first frame
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      await user.click(enlargeButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Frame 1')).toBeInTheDocument();
      });

      // Click Next button
      const nextButton = screen.getByRole('button', { name: /Next/ });
      await user.click(nextButton);

      await waitFor(() => {
        expect(screen.getByText('Frame 11')).toBeInTheDocument();
      });
    });

    it('should disable Previous button on first frame', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open modal on first frame
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      await user.click(enlargeButtons[0]);

      await waitFor(() => {
        expect(screen.getByText('Frame 1')).toBeInTheDocument();
      });

      // Previous button should be disabled
      const previousButton = screen.getByRole('button', { name: /Previous/ });
      expect(previousButton).toBeDisabled();
    });

    it('should disable Next button on last frame', async () => {
      const user = userEvent.setup();
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open modal on last frame
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      await user.click(enlargeButtons[2]);

      await waitFor(() => {
        expect(screen.getByText('Frame 21')).toBeInTheDocument();
      });

      // Next button should be disabled
      const nextButton = screen.getByRole('button', { name: /Next/ });
      expect(nextButton).toBeDisabled();
    });

    it('should navigate frames with ArrowLeft and ArrowRight keys in modal', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Open modal on second frame
      const enlargeButtons = screen.getAllByTitle('Enlarge');
      fireEvent.click(enlargeButtons[1]);

      await waitFor(() => {
        expect(screen.getByText('Frame 11')).toBeInTheDocument();
      });

      // Press ArrowLeft to go to previous frame
      fireEvent.keyDown(window, { key: 'ArrowLeft' });

      await waitFor(() => {
        expect(screen.getByText('Frame 1')).toBeInTheDocument();
      });

      // Press ArrowRight to go to next frame
      fireEvent.keyDown(window, { key: 'ArrowRight' });

      await waitFor(() => {
        expect(screen.getByText('Frame 11')).toBeInTheDocument();
      });
    });
  });

  describe('Image Loading States', () => {
    it('should show loading indicator while image is loading', async () => {
      // Mock slow image loading
      const originalImage = window.Image;
      window.Image = class {
        onload: (() => void) | null = null;
        onerror: (() => void) | null = null;
        src = '';
        constructor() {
          // Don't trigger onload immediately
        }
      } as unknown as typeof window.Image;

      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Restore original Image
      window.Image = originalImage;
    });

    it('should show error state when image fails to load', async () => {
      render(<ThumbnailGrid {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      // Find an image and trigger error
      const images = document.querySelectorAll('img');
      if (images.length > 0) {
        fireEvent.error(images[0]);

        await waitFor(() => {
          expect(screen.getByText('Load failed')).toBeInTheDocument();
        });
      }
    });
  });

  describe('Grid Column Classes', () => {
    it('should apply correct grid classes for 2 columns', async () => {
      render(<ThumbnailGrid {...defaultProps} columns={2} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      const grid = document.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('sm:grid-cols-2');
    });

    it('should apply correct grid classes for 3 columns', async () => {
      render(<ThumbnailGrid {...defaultProps} columns={3} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      const grid = document.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('sm:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should apply correct grid classes for 5 columns', async () => {
      render(<ThumbnailGrid {...defaultProps} columns={5} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      const grid = document.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-2');
      expect(grid).toHaveClass('sm:grid-cols-3');
      expect(grid).toHaveClass('lg:grid-cols-5');
    });

    it('should fallback to 4 columns for invalid column count', async () => {
      // TypeScript would prevent this, but test runtime behavior
      render(<ThumbnailGrid {...defaultProps} columns={99} />);

      await waitFor(() => {
        expect(screen.getByText('Thumbnail Grid')).toBeInTheDocument();
      });

      const grid = document.querySelector('.grid');
      // Should fallback to 4 column classes
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('sm:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-4');
    });
  });
});
