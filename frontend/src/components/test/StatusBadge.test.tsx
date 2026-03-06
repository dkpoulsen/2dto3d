import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '../StatusBadge';

describe('StatusBadge', () => {
  it('should render pending status', () => {
    render(<StatusBadge status="pending" />);
    expect(screen.getByText('pending')).toBeInTheDocument();
  });

  it('should render queued status', () => {
    render(<StatusBadge status="queued" />);
    expect(screen.getByText('queued')).toBeInTheDocument();
  });

  it('should render running status', () => {
    render(<StatusBadge status="running" />);
    expect(screen.getByText('running')).toBeInTheDocument();
  });

  it('should render completed status', () => {
    render(<StatusBadge status="completed" />);
    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  it('should render failed status', () => {
    render(<StatusBadge status="failed" />);
    expect(screen.getByText('failed')).toBeInTheDocument();
  });

  it('should render cancelled status', () => {
    render(<StatusBadge status="cancelled" />);
    expect(screen.getByText('cancelled')).toBeInTheDocument();
  });

  it('should render healthy status', () => {
    render(<StatusBadge status="healthy" />);
    expect(screen.getByText('healthy')).toBeInTheDocument();
  });

  it('should render degraded status', () => {
    render(<StatusBadge status="degraded" />);
    expect(screen.getByText('degraded')).toBeInTheDocument();
  });

  it('should render unhealthy status', () => {
    render(<StatusBadge status="unhealthy" />);
    expect(screen.getByText('unhealthy')).toBeInTheDocument();
  });

  it('should handle unknown status with default styling', () => {
    render(<StatusBadge status="unknown" />);
    expect(screen.getByText('unknown')).toBeInTheDocument();
  });

  it('should capitalize status text', () => {
    render(<StatusBadge status="completed" />);
    const badge = screen.getByText('completed');
    expect(badge).toHaveClass('capitalize');
  });

  it('should be an inline-flex element', () => {
    render(<StatusBadge status="pending" />);
    const badge = screen.getByText('pending');
    expect(badge).toHaveClass('inline-flex');
  });
});
