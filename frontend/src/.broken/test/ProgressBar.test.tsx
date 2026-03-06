import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressBar } from '../ProgressBar';

describe('ProgressBar', () => {
  it('should render progress bar with correct percentage', () => {
    render(<ProgressBar progress={0.5} />);
    expect(screen.getByText('50.0%')).toBeInTheDocument();
  });

  it('should clamp progress below 0', () => {
    render(<ProgressBar progress={-0.5} />);
    expect(screen.getByText('0.0%')).toBeInTheDocument();
  });

  it('should clamp progress above 1', () => {
    render(<ProgressBar progress={1.5} />);
    expect(screen.getByText('100.0%')).toBeInTheDocument();
  });

  it('should display stage text', () => {
    render(<ProgressBar progress={0.3} stage="Processing frames" />);
    expect(screen.getByText('Processing frames')).toBeInTheDocument();
  });

  it('should display default stage when not provided', () => {
    render(<ProgressBar progress={0.5} />);
    expect(screen.getByText('Processing')).toBeInTheDocument();
  });

  it('should apply small size class', () => {
    render(<ProgressBar progress={0.5} size="sm" />);
    const container = screen.getByText('Processing').parentElement?.parentElement;
    expect(container?.querySelector('.h-1')).toBeTruthy();
  });

  it('should apply medium size class by default', () => {
    render(<ProgressBar progress={0.5} />);
    const container = screen.getByText('Processing').parentElement?.parentElement;
    expect(container?.querySelector('.h-2')).toBeTruthy();
  });

  it('should apply large size class', () => {
    render(<ProgressBar progress={0.5} size="lg" />);
    const container = screen.getByText('Processing').parentElement?.parentElement;
    expect(container?.querySelector('.h-3')).toBeTruthy();
  });

  it('should show exact percentage for zero progress', () => {
    render(<ProgressBar progress={0} />);
    expect(screen.getByText('0.0%')).toBeInTheDocument();
  });

  it('should show exact percentage for full progress', () => {
    render(<ProgressBar progress={1} />);
    expect(screen.getByText('100.0%')).toBeInTheDocument();
  });

  it('should format decimal percentages correctly', () => {
    render(<ProgressBar progress={0.333} />);
    expect(screen.getByText('33.3%')).toBeInTheDocument();
  });
});
