import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DepthFocusControl } from '../DepthFocusControl';
import type { DepthFocusConfig } from '../../api/types';

describe('DepthFocusControl', () => {
  const defaultValue: DepthFocusConfig = {
    enabled: false,
    focus_depth: 0.5,
    focus_range: 0.3,
  };

  it('renders with correct default values', () => {
    const onChange = vi.fn();
    render(<DepthFocusControl value={defaultValue} onChange={onChange} />);

    // Check header
    expect(screen.getByText('Depth Focus')).toBeInTheDocument();

    // Check labels
    expect(screen.getByLabelText(/Focus depth:/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Focus range:/i)).toBeInTheDocument();

    // Check sliders are disabled by default (feature not enabled)
    expect(screen.getByLabelText(/Focus depth:/i)).toBeDisabled();
    expect(screen.getByLabelText(/Focus range:/i)).toBeDisabled();
  });

  it('enables sliders when checkbox is checked', () => {
    const onChange = vi.fn();
    render(<DepthFocusControl value={defaultValue} onChange={onChange} />);

    // Enable the feature
    const checkbox = screen.getByRole('checkbox', { name: /enable depth focus/i });
    fireEvent.click(checkbox);

    // Should call onChange with enabled=true
    expect(onChange).toHaveBeenCalledWith({
      ...defaultValue,
      enabled: true,
    });
  });

  it('has accessible elements', () => {
    const onChange = vi.fn();
    render(<DepthFocusControl value={defaultValue} onChange={onChange} />);

    // Check for accessibility labels
    const depthSlider = screen.getByLabelText(/Focus depth:/i);
    const rangeSlider = screen.getByLabelText(/Focus range:/i);

    expect(depthSlider).toHaveAttribute('aria-label');
    expect(rangeSlider).toHaveAttribute('aria-label');

    // Check reset button has aria-label
    const resetButton = screen.getByRole('button', { name: /reset.*defaults/i });
    expect(resetButton).toBeInTheDocument();
  });

  it('displays visual focus zone indicator', () => {
    const onChange = vi.fn();
    render(<DepthFocusControl value={defaultValue} onChange={onChange} />);

    // Check for visualization labels
    expect(screen.getByText('Pop Out')).toBeInTheDocument();
    expect(screen.getByText('Screen Plane')).toBeInTheDocument();
    expect(screen.getByText('Behind Screen')).toBeInTheDocument();
  });

  it('calls onChange when focus depth slider changes', () => {
    const enabledValue: DepthFocusConfig = { ...defaultValue, enabled: true };
    const onChange = vi.fn();
    render(<DepthFocusControl value={enabledValue} onChange={onChange} />);

    const depthSlider = screen.getByLabelText(/Focus depth:/i);
    fireEvent.change(depthSlider, { target: { value: '0.75' } });

    expect(onChange).toHaveBeenCalledWith({
      ...enabledValue,
      focus_depth: 0.75,
    });
  });

  it('calls onChange when focus range slider changes', () => {
    const enabledValue: DepthFocusConfig = { ...defaultValue, enabled: true };
    const onChange = vi.fn();
    render(<DepthFocusControl value={enabledValue} onChange={onChange} />);

    const rangeSlider = screen.getByLabelText(/Focus range:/i);
    fireEvent.change(rangeSlider, { target: { value: '0.5' } });

    expect(onChange).toHaveBeenCalledWith({
      ...enabledValue,
      focus_range: 0.5,
    });
  });

  it('calls onChange with defaults when reset button is clicked', () => {
    const modifiedValue: DepthFocusConfig = {
      enabled: true,
      focus_depth: 0.8,
      focus_range: 0.6,
    };
    const onChange = vi.fn();
    render(<DepthFocusControl value={modifiedValue} onChange={onChange} />);

    const resetButton = screen.getByRole('button', { name: /reset.*defaults/i });
    fireEvent.click(resetButton);

    // Should reset depth and range but preserve enabled state
    expect(onChange).toHaveBeenCalledWith({
      enabled: true,
      focus_depth: 0.5,
      focus_range: 0.3,
    });
  });

  it('is disabled when disabled prop is true', () => {
    const onChange = vi.fn();
    render(<DepthFocusControl value={defaultValue} onChange={onChange} disabled />);

    // Checkbox should be disabled
    const checkbox = screen.getByRole('checkbox', { name: /enable depth focus/i });
    expect(checkbox).toBeDisabled();

    // Reset button should be disabled
    const resetButton = screen.getByRole('button', { name: /reset.*defaults/i });
    expect(resetButton).toBeDisabled();
  });
});
