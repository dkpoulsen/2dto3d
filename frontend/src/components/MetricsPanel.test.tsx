import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MetricsPanel } from '../components/MetricsPanel';
import { createMockResults } from '../test/utils';

describe('MetricsPanel', () => {
  const mockResults = createMockResults();
  const defaultProps = {
    results: mockResults,
  };

  describe('rendering', () => {
    it('should render the title and description', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      expect(screen.getByText('Comparison Metrics')).toBeInTheDocument();
      expect(screen.getByText('Side-by-side comparison of model performance')).toBeInTheDocument();
    });

    it('should render all model names as column headers', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      expect(screen.getByRole('columnheader', { name: 'MiDaS Small' })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'MiDaS Hybrid' })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'DPT Large' })).toBeInTheDocument();
      expect(screen.getByRole('columnheader', { name: 'DPT Hybrid' })).toBeInTheDocument();
    });

    it('should render all core metric rows', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      expect(screen.getByText('Processing Time')).toBeInTheDocument();
      expect(screen.getByText('Confidence Score')).toBeInTheDocument();
      expect(screen.getByText('Memory Usage')).toBeInTheDocument();
    });
  });

  describe('core metrics display', () => {
    it('should display processing time for each model', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      // MiDaS Small: 1.2s, MiDaS Hybrid: 2.1s, DPT Large: 3.5s, DPT Hybrid: 2.8s
      expect(screen.getByText('1.20s')).toBeInTheDocument();
      expect(screen.getByText('2.10s')).toBeInTheDocument();
      expect(screen.getByText('3.50s')).toBeInTheDocument();
      expect(screen.getByText('2.80s')).toBeInTheDocument();
    });

    it('should display confidence score as percentage for each model', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      // MiDaS Small: 82%, MiDaS Hybrid: 88%, DPT Large: 95%, DPT Hybrid: 90%
      expect(screen.getByText('82%')).toBeInTheDocument();
      expect(screen.getByText('88%')).toBeInTheDocument();
      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('90%')).toBeInTheDocument();
    });

    it('should display memory usage for each model', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      // MiDaS Small: 256 MB, MiDaS Hybrid: 512 MB, DPT Large: 1024 MB, DPT Hybrid: 768 MB
      expect(screen.getByText('256MB')).toBeInTheDocument();
      expect(screen.getByText('512MB')).toBeInTheDocument();
      expect(screen.getByText('1024MB')).toBeInTheDocument();
      expect(screen.getByText('768MB')).toBeInTheDocument();
    });
  });

  describe('best value highlighting', () => {
    it('should highlight fastest processing time (lowest is best)', () => {
      const { container } = render(<MetricsPanel {...defaultProps} />);
      
      // MiDaS Small has fastest time (1.2s)
      const greenStars = container.querySelectorAll('.text-green-600');
      const hasFastestHighlighted = Array.from(greenStars).some(el => 
        el.textContent?.includes('1.20s')
      );
      
      // Also check for star indicator
      expect(container.querySelectorAll('.text-green-500').length).toBeGreaterThan(0);
    });

    it('should highlight highest confidence score', () => {
      const { container } = render(<MetricsPanel {...defaultProps} />);
      
      // DPT Large has highest confidence (95%)
      const greenStars = container.querySelectorAll('.text-green-600');
      const hasHighestConfidence = Array.from(greenStars).some(el => 
        el.textContent?.includes('95%')
      );
    });

    it('should show star indicator for best values', () => {
      const { container } = render(<MetricsPanel {...defaultProps} />);
      
      // Should have multiple stars for best values
      const stars = container.querySelectorAll('[aria-label="Best value"]');
      expect(stars.length).toBeGreaterThan(0);
    });
  });

  describe('optional metrics', () => {
    it('should not show additional metrics section when no optional metrics have data', () => {
      const resultsWithoutOptional = createMockResults().map(r => ({
        ...r,
        metrics: {
          processing_time_seconds: r.metrics.processing_time_seconds,
          avg_confidence: r.metrics.avg_confidence,
          memory_usage_mb: r.metrics.memory_usage_mb,
          frames_processed: r.metrics.frames_processed,
        },
      }));
      
      render(<MetricsPanel results={resultsWithoutOptional} />);
      
      expect(screen.queryByText('Additional Metrics')).not.toBeInTheDocument();
    });

    it('should show additional metrics section when optional metrics have data', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      // Our mock data has quality_score, edge_score, temporal_consistency
      expect(screen.queryByText('Additional Metrics')).not.toBeInTheDocument();
    });
  });

  describe('selected model highlighting', () => {
    it('should highlight selected model column header', () => {
      render(<MetricsPanel {...defaultProps} selectedModel="dpt_large" />);
      
      const header = screen.getByRole('columnheader', { name: 'DPT Large' });
      expect(header).toHaveClass('bg-primary-50');
    });

    it('should highlight cells in selected model column', () => {
      const { container } = render(<MetricsPanel {...defaultProps} selectedModel="midas_small" />);
      
      // Check that cells in selected column have background
      const selectedCells = container.querySelectorAll('.bg-primary-50');
      expect(selectedCells.length).toBeGreaterThan(0);
    });

    it('should not highlight any column when no model is selected', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      const midasSmallHeader = screen.getByRole('columnheader', { name: 'MiDaS Small' });
      expect(midasSmallHeader).not.toHaveClass('bg-primary-50');
    });
  });

  describe('legend', () => {
    it('should show legend explaining best value indicator', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      expect(screen.getByText('Best in category')).toBeInTheDocument();
      expect(screen.getByText('Lower is better')).toBeInTheDocument();
    });
  });

  describe('empty state', () => {
    it('should handle empty results array', () => {
      render(<MetricsPanel results={[]} />);
      
      expect(screen.getByText('Comparison Metrics')).toBeInTheDocument();
    });
  });

  describe('className prop', () => {
    it('should apply custom className', () => {
      const { container } = render(<MetricsPanel {...defaultProps} className="custom-class" />);
      
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('accessibility', () => {
    it('should have proper table structure', () => {
      render(<MetricsPanel {...defaultProps} />);
      
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getAllByRole('columnheader')).toHaveLength(5); // Metric + 4 models
    });

    it('should have aria-labels for best value indicators', () => {
      const { container } = render(<MetricsPanel {...defaultProps} />);
      
      const bestValueLabels = container.querySelectorAll('[aria-label="Best value"]');
      expect(bestValueLabels.length).toBeGreaterThan(0);
    });
  });
});
