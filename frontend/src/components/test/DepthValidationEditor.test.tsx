import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DepthValidationEditor } from '../DepthValidationEditor';

// Mock canvas context
const mockGetContext = vi.fn(() => ({
  drawImage: vi.fn(),
  getImageData: vi.fn(() => ({
    data: new Uint8ClampedArray(4),
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
}));

// Mock HTMLCanvasElement
HTMLCanvasElement.prototype.getContext = mockGetContext;

describe('DepthValidationEditor', () => {
  it('should render the editor component', () => {
    render(<DepthValidationEditor width={640} height={480} />);
    
    // Check that toolbar elements are present
    expect(screen.getByTitle('Brush (B)')).toBeInTheDocument();
    expect(screen.getByTitle('Eraser (E)')).toBeInTheDocument();
    expect(screen.getByTitle('Undo (Ctrl+Z)')).toBeInTheDocument();
    expect(screen.getByTitle('Redo (Ctrl+Y)')).toBeInTheDocument();
  });

  it('should render brush size control', () => {
    render(<DepthValidationEditor width={640} height={480} />);
    
    // Check for size label and range input
    expect(screen.getByText('Size:')).toBeInTheDocument();
    const sliders = document.querySelectorAll('input[type="range"]');
    expect(sliders.length).toBeGreaterThan(0);
  });

  it('should render hardness control', () => {
    render(<DepthValidationEditor width={640} height={480} />);
    
    // Check for hardness label
    expect(screen.getByText('Hardness:')).toBeInTheDocument();
  });

  it('should render value control', () => {
    render(<DepthValidationEditor width={640} height={480} />);
    
    // Check for value label
    expect(screen.getByText('Value:')).toBeInTheDocument();
  });

  it('should render colormap selector', () => {
    render(<DepthValidationEditor width={640} height={480} />);
    
    // Check for colormap options
    expect(screen.getByText('Turbo')).toBeInTheDocument();
    expect(screen.getByText('Plasma')).toBeInTheDocument();
    expect(screen.getByText('Viridis')).toBeInTheDocument();
    expect(screen.getByText('Magma')).toBeInTheDocument();
    expect(screen.getByText('Jet')).toBeInTheDocument();
    expect(screen.getByText('Inferno')).toBeInTheDocument();
    expect(screen.getByText('Grayscale')).toBeInTheDocument();
  });

  it('should render zoom controls', () => {
    render(<DepthValidationEditor width={640} height={480} />);
    
    expect(screen.getByTitle('Zoom Out')).toBeInTheDocument();
    expect(screen.getByTitle('Zoom In')).toBeInTheDocument();
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
  });
});
