import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DepthValidationEditor } from '../DepthValidationEditor';

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

const mockGetContext = vi.fn(() => mockCtx);

// Mock HTMLCanvasElement
HTMLCanvasElement.prototype.getContext = mockGetContext;

describe('DepthValidationEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetContext.mockReturnValue(mockCtx);
  });

  afterEach(() => {
    vi.clearAllTimers();
  });

  // ============================================
  // RENDERING TESTS
  // ============================================
  describe('Rendering', () => {
    it('should render the editor component with default props', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByTitle('Brush (B)')).toBeInTheDocument();
      expect(screen.getByTitle('Eraser (E)')).toBeInTheDocument();
      expect(screen.getByTitle('Undo (Ctrl+Z)')).toBeInTheDocument();
      expect(screen.getByTitle('Redo (Ctrl+Y)')).toBeInTheDocument();
      expect(screen.getByTitle('Reset')).toBeInTheDocument();
    });

    it('should render brush size control with default value', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByText('Size:')).toBeInTheDocument();
      expect(screen.getByText('20px')).toBeInTheDocument(); // DEFAULT_BRUSH_SIZE
    });

    it('should render hardness control with default value', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByText('Hardness:')).toBeInTheDocument();
      expect(screen.getByText('80%')).toBeInTheDocument(); // DEFAULT_BRUSH_HARDNESS
    });

    it('should render value control', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByText('Value:')).toBeInTheDocument();
      // Value is shown as a color swatch, check for the input
      const sliders = document.querySelectorAll('input[type="range"]');
      expect(sliders.length).toBe(3); // Size, Hardness, Value
    });

    it('should render all colormap options', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      const colormaps = ['Turbo', 'Plasma', 'Viridis', 'Magma', 'Jet', 'Inferno', 'Grayscale'];
      colormaps.forEach(cm => {
        expect(screen.getByText(cm)).toBeInTheDocument();
      });
    });

    it('should render zoom controls with default zoom', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByTitle('Zoom Out')).toBeInTheDocument();
      expect(screen.getByTitle('Zoom In')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument(); // Default zoom
    });

    it('should render export button', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByTitle('Export as PNG')).toBeInTheDocument();
    });

    it('should render save button when onSave is provided', () => {
      const onSave = vi.fn();
      render(<DepthValidationEditor width={640} height={480} onSave={onSave} />);
      
      expect(screen.getByTitle('Save Changes')).toBeInTheDocument();
    });

    it('should not render save button when onSave is not provided', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.queryByTitle('Save Changes')).not.toBeInTheDocument();
    });

    it('should render status bar with tool indicator', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByText(/Tool:/)).toBeInTheDocument();
      expect(screen.getByText(/Tool: Brush/)).toBeInTheDocument();
    });

    it('should render disabled overlay when disabled', () => {
      render(<DepthValidationEditor width={640} height={480} disabled={true} />);
      
      expect(screen.getByText('Editor Disabled')).toBeInTheDocument();
    });

    it('should apply custom className', () => {
      const { container } = render(
        <DepthValidationEditor width={640} height={480} className="custom-class" />
      );
      
      expect(container.querySelector('.depth-validation-editor')).toHaveClass('custom-class');
    });
  });

  // ============================================
  // TOOL SELECTION TESTS
  // ============================================
  describe('Tool Selection', () => {
    it('should start with brush tool selected', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByText(/Tool: Brush/)).toBeInTheDocument();
    });

    it('should switch to eraser tool when eraser button is clicked', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      await user.click(screen.getByTitle('Eraser (E)'));
      
      expect(screen.getByText(/Tool: Eraser/)).toBeInTheDocument();
    });

    it('should switch back to brush tool when brush button is clicked', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Switch to eraser
      await user.click(screen.getByTitle('Eraser (E)'));
      expect(screen.getByText(/Tool: Eraser/)).toBeInTheDocument();
      
      // Switch back to brush
      await user.click(screen.getByTitle('Brush (B)'));
      expect(screen.getByText(/Tool: Brush/)).toBeInTheDocument();
    });

    it('should apply active styling to selected tool', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      const brushButton = screen.getByTitle('Brush (B)');
      const eraserButton = screen.getByTitle('Eraser (E)');
      
      // Brush should have active class initially
      expect(brushButton).toHaveClass('bg-primary-100');
      
      // Click eraser
      await user.click(eraserButton);
      expect(eraserButton).toHaveClass('bg-red-100');
    });
  });

  // ============================================
  // BRUSH SETTINGS TESTS
  // ============================================
  describe('Brush Settings', () => {
    it('should update brush size when slider changes', async () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      const sliders = document.querySelectorAll('input[type="range"]');
      const sizeSlider = sliders[0] as HTMLInputElement;
      
      fireEvent.change(sizeSlider, { target: { value: '50' } });
      
      expect(screen.getByText('50px')).toBeInTheDocument();
    });

    it('should update brush hardness when slider changes', async () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      const sliders = document.querySelectorAll('input[type="range"]');
      const hardnessSlider = sliders[1] as HTMLInputElement;
      
      fireEvent.change(hardnessSlider, { target: { value: '50' } });
      
      // There are two 50% texts (hardness and value might show same)
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should disable sliders when editor is disabled', () => {
      render(<DepthValidationEditor width={640} height={480} disabled={true} />);
      
      const sliders = document.querySelectorAll('input[type="range"]');
      sliders.forEach(slider => {
        expect(slider).toBeDisabled();
      });
    });
  });

  // ============================================
  // UNDO/REDO TESTS
  // ============================================
  describe('Undo/Redo Functionality', () => {
    it('should disable undo button when no history to undo', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      const undoButton = screen.getByTitle('Undo (Ctrl+Z)');
      expect(undoButton).toBeDisabled();
    });

    it('should disable redo button when no history to redo', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      const redoButton = screen.getByTitle('Redo (Ctrl+Y)');
      expect(redoButton).toBeDisabled();
    });

    it('should show history count in status bar', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByText(/History:/)).toBeInTheDocument();
    });
  });

  // ============================================
  // ZOOM TESTS
  // ============================================
  describe('Zoom Functionality', () => {
    it('should start with 100% zoom', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should increase zoom when zoom in is clicked', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      await user.click(screen.getByTitle('Zoom In'));
      
      expect(screen.getByText('125%')).toBeInTheDocument();
    });

    it('should decrease zoom when zoom out is clicked', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Zoom in first
      await user.click(screen.getByTitle('Zoom In'));
      expect(screen.getByText('125%')).toBeInTheDocument();
      
      // Then zoom out
      await user.click(screen.getByTitle('Zoom Out'));
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('should not zoom below MIN_ZOOM (25%)', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Click zoom out 4 times (should get to 25%)
      for (let i = 0; i < 4; i++) {
        await user.click(screen.getByTitle('Zoom Out'));
      }
      expect(screen.getByText('25%')).toBeInTheDocument();
      
      // Try to zoom out again - should stay at 25%
      const zoomOutButton = screen.getByTitle('Zoom Out');
      expect(zoomOutButton).toBeDisabled();
    });

    it('should not zoom above MAX_ZOOM (400%)', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Click zoom in 12 times (should get to 400%)
      for (let i = 0; i < 12; i++) {
        await user.click(screen.getByTitle('Zoom In'));
      }
      expect(screen.getByText('400%')).toBeInTheDocument();
      
      // Try to zoom in again - should stay at 400%
      const zoomInButton = screen.getByTitle('Zoom In');
      expect(zoomInButton).toBeDisabled();
    });

    it('should disable zoom buttons when disabled', () => {
      render(<DepthValidationEditor width={640} height={480} disabled={true} />);
      
      expect(screen.getByTitle('Zoom In')).toBeDisabled();
      expect(screen.getByTitle('Zoom Out')).toBeDisabled();
    });
  });

  // ============================================
  // COLORMAP TESTS
  // ============================================
  describe('Colormap Functionality', () => {
    it('should start with turbo colormap selected', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      const select = screen.getByRole('combobox');
      expect(select).toHaveValue('turbo');
    });

    it('should change colormap when selection changes', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      const select = screen.getByRole('combobox');
      await user.selectOptions(select, 'plasma');
      
      expect(select).toHaveValue('plasma');
    });

    it('should toggle colormap visibility', async () => {
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} />);
      
      const toggleButton = screen.getByTitle('Toggle Colormap');
      
      // Initial state - colormap shown
      expect(toggleButton).toHaveClass('bg-purple-100');
      
      // Click to hide
      await user.click(toggleButton);
      expect(toggleButton).not.toHaveClass('bg-purple-100');
      
      // Click to show again
      await user.click(toggleButton);
      expect(toggleButton).toHaveClass('bg-purple-100');
    });

    it('should disable colormap controls when disabled', () => {
      render(<DepthValidationEditor width={640} height={480} disabled={true} />);
      
      expect(screen.getByRole('combobox')).toBeDisabled();
      expect(screen.getByTitle('Toggle Colormap')).toBeDisabled();
    });
  });

  // ============================================
  // KEYBOARD SHORTCUT TESTS
  // ============================================
  describe('Keyboard Shortcuts', () => {
    it('should switch to eraser when E key is pressed', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      fireEvent.keyDown(window, { key: 'e' });
      
      expect(screen.getByText(/Tool: Eraser/)).toBeInTheDocument();
    });

    it('should switch to brush when B key is pressed', async () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Switch to eraser first
      fireEvent.keyDown(window, { key: 'e' });
      expect(screen.getByText(/Tool: Eraser/)).toBeInTheDocument();
      
      // Then switch to brush
      fireEvent.keyDown(window, { key: 'b' });
      expect(screen.getByText(/Tool: Brush/)).toBeInTheDocument();
    });

    it('should decrease brush size when [ key is pressed', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Default is 20px
      expect(screen.getByText('20px')).toBeInTheDocument();
      
      // Press [ to decrease by 5
      fireEvent.keyDown(window, { key: '[' });
      
      expect(screen.getByText('15px')).toBeInTheDocument();
    });

    it('should increase brush size when ] key is pressed', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Default is 20px
      expect(screen.getByText('20px')).toBeInTheDocument();
      
      // Press ] to increase by 5
      fireEvent.keyDown(window, { key: ']' });
      
      expect(screen.getByText('25px')).toBeInTheDocument();
    });

    it('should not decrease brush size below MIN_BRUSH_SIZE (1)', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Set to minimum
      for (let i = 0; i < 5; i++) {
        fireEvent.keyDown(window, { key: '[' });
      }
      expect(screen.getByText('1px')).toBeInTheDocument();
      
      // Try to go below
      fireEvent.keyDown(window, { key: '[' });
      expect(screen.getByText('1px')).toBeInTheDocument();
    });

    it('should not increase brush size above MAX_BRUSH_SIZE (200)', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      // Set to maximum
      for (let i = 0; i < 40; i++) {
        fireEvent.keyDown(window, { key: ']' });
      }
      expect(screen.getByText('200px')).toBeInTheDocument();
      
      // Try to go above
      fireEvent.keyDown(window, { key: ']' });
      expect(screen.getByText('200px')).toBeInTheDocument();
    });

    it('should not handle keyboard shortcuts when disabled', () => {
      render(<DepthValidationEditor width={640} height={480} disabled={true} />);
      
      fireEvent.keyDown(window, { key: 'e' });
      
      // Should still show Brush (default)
      expect(screen.getByText(/Tool: Brush/)).toBeInTheDocument();
    });
  });

  // ============================================
  // EXPORT FUNCTIONALITY TESTS
  // ============================================
  describe('Export Functionality', () => {
    it('should have export button', () => {
      render(<DepthValidationEditor width={640} height={480} />);
      
      expect(screen.getByTitle('Export as PNG')).toBeInTheDocument();
    });

    it('should disable export when editor is disabled', () => {
      render(<DepthValidationEditor width={640} height={480} disabled={true} />);
      
      expect(screen.getByTitle('Export as PNG')).toBeDisabled();
    });
  });

  // ============================================
  // SAVE FUNCTIONALITY TESTS
  // ============================================
  describe('Save Functionality', () => {
    it('should call onSave when save button is clicked', async () => {
      const onSave = vi.fn();
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} onSave={onSave} />);
      
      await user.click(screen.getByTitle('Save Changes'));
      
      expect(onSave).toHaveBeenCalled();
    });

    it('should pass ImageData to onSave callback', async () => {
      const onSave = vi.fn();
      const user = userEvent.setup();
      render(<DepthValidationEditor width={640} height={480} onSave={onSave} />);
      
      await user.click(screen.getByTitle('Save Changes'));
      
      // The mock getImageData returns an object with data, width, height
      expect(onSave).toHaveBeenCalledWith(expect.objectContaining({
        data: expect.any(Uint8ClampedArray),
        width: 640,
        height: 480,
      }));
    });

    it('should disable save when editor is disabled', () => {
      const onSave = vi.fn();
      render(<DepthValidationEditor width={640} height={480} onSave={onSave} disabled={true} />);
      
      expect(screen.getByTitle('Save Changes')).toBeDisabled();
    });
  });

  // ============================================
  // ONCHANGE CALLBACK TESTS
  // ============================================
  describe('onChange Callback', () => {
    it('should accept onChange prop', () => {
      const onChange = vi.fn();
      render(<DepthValidationEditor width={640} height={480} onChange={onChange} />);
      
      // Component should render without errors
      expect(screen.getByTitle('Brush (B)')).toBeInTheDocument();
    });
  });

  // ============================================
  // CANVAS INITIALIZATION TESTS
  // ============================================
  describe('Canvas Initialization', () => {
    it('should initialize canvas with provided dimensions', () => {
      render(<DepthValidationEditor width={800} height={600} />);
      
      const canvases = document.querySelectorAll('canvas');
      expect(canvases.length).toBe(2); // Main canvas + overlay
    });

    it('should call putImageData with initial ImageData', () => {
      // Create a mock ImageData-like object
      const mockImageData = {
        data: new Uint8ClampedArray(4 * 640 * 480),
        width: 640,
        height: 480,
        colorSpace: 'srgb' as PredefinedColorSpace,
      } as ImageData;
      
      render(<DepthValidationEditor width={640} height={480} initialDepthMap={mockImageData} />);
      
      expect(mockCtx.putImageData).toHaveBeenCalled();
    });
  });
});
