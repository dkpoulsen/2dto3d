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

  // ============================================================
  // Edge Case Tests
  // ============================================================

  it('handles boundary values for focus_depth (0.0 and 1.0)', () => {
    const boundaryValue: DepthFocusConfig = {
      enabled: true,
      focus_depth: 0.0,
      focus_range: 0.3,
    };
    const onChange = vi.fn();
    render(<DepthFocusControl value={boundaryValue} onChange={onChange} />);

    // Slider should show 0.00 value
    expect(screen.getByText('0.00')).toBeInTheDocument();

    // Change to max value
    const depthSlider = screen.getByLabelText(/Focus depth:/i);
    fireEvent.change(depthSlider, { target: { value: '1.0' } });

    expect(onChange).toHaveBeenCalledWith({
      ...boundaryValue,
      focus_depth: 1.0,
    });
  });

  it('handles boundary values for focus_range (0.0 and 1.0)', () => {
    const boundaryValue: DepthFocusConfig = {
      enabled: true,
      focus_depth: 0.5,
      focus_range: 0.0,
    };
    const onChange = vi.fn();
    render(<DepthFocusControl value={boundaryValue} onChange={onChange} />);

    // Slider should show 0.00 value
    expect(screen.getByText('0.00')).toBeInTheDocument();

    // Change to max value
    const rangeSlider = screen.getByLabelText(/Focus range:/i);
    fireEvent.change(rangeSlider, { target: { value: '1.0' } });

    expect(onChange).toHaveBeenCalledWith({
      ...boundaryValue,
      focus_range: 1.0,
    });
  });

  it('handles focus_range larger than focus_depth correctly', () => {
    // Edge case: range is larger than depth position
    const edgeValue: DepthFocusConfig = {
      enabled: true,
      focus_depth: 0.1, // Very close to the front
      focus_range: 0.5, // Wide range
    };
    const onChange = vi.fn();
    const { container } = render(
      <DepthFocusControl value={edgeValue} onChange={onChange} />
    );

    // Should render without errors - focus zone visualization should handle this
    expect(container.querySelector('.depth-focus-control')).toBeInTheDocument();
  });

  it('handles focus_depth at maximum with large focus_range', () => {
    // Edge case: depth at max and range extends beyond
    const edgeValue: DepthFocusConfig = {
      enabled: true,
      focus_depth: 1.0, // Farthest possible
      focus_range: 0.5, // Range extends beyond max
    };
    const onChange = vi.fn();
    const { container } = render(
      <DepthFocusControl value={edgeValue} onChange={onChange} />
    );

    // Should render without errors
    expect(container.querySelector('.depth-focus-control')).toBeInTheDocument();
  });

  it('displays correct value labels with different precision', () => {
    const customValue: DepthFocusConfig = {
      enabled: true,
      focus_depth: 0.123456,
      focus_range: 0.987654,
    };
    const onChange = vi.fn();
    render(<DepthFocusControl value={customValue} onChange={onChange} />);

    // Should display values formatted to 2 decimal places
    expect(screen.getByText('0.12')).toBeInTheDocument();
    expect(screen.getByText('0.99')).toBeInTheDocument();
  });

  it('preserves enabled state through multiple interactions', () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <DepthFocusControl value={defaultValue} onChange={onChange} />
    );

    // Enable
    const checkbox = screen.getByRole('checkbox', { name: /enable depth focus/i });
    fireEvent.click(checkbox);

    // Get the updated value
    const enabledValue = onChange.mock.calls[0][0] as DepthFocusConfig;

    // Re-render with enabled value
    rerender(<DepthFocusControl value={enabledValue} onChange={onChange} />);

    // Change depth
    const depthSlider = screen.getByLabelText(/Focus depth:/i);
    fireEvent.change(depthSlider, { target: { value: '0.8' } });

    // Should still be enabled
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0] as DepthFocusConfig;
    expect(lastCall.enabled).toBe(true);
    expect(lastCall.focus_depth).toBe(0.8);
  });

  it('applies custom className when provided', () => {
    const onChange = vi.fn();
    const { container } = render(
      <DepthFocusControl
        value={defaultValue}
        onChange={onChange}
        className="custom-class"
      />
    );

    expect(container.querySelector('.depth-focus-control.custom-class')).toBeInTheDocument();
  });

  it('displays help text explaining the feature', () => {
    const onChange = vi.fn();
    render(<DepthFocusControl value={defaultValue} onChange={onChange} />);

    // Check for descriptive text - use getAllByText since 'screen plane' appears multiple times
    expect(screen.getAllByText(/screen plane/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Objects at this depth appear/i)).toBeInTheDocument();
  });

  it('handles rapid successive slider changes', () => {
    const enabledValue: DepthFocusConfig = { ...defaultValue, enabled: true };
    const onChange = vi.fn();
    render(<DepthFocusControl value={enabledValue} onChange={onChange} />);

    const depthSlider = screen.getByLabelText(/Focus depth:/i);

    // Simulate rapid changes
    fireEvent.change(depthSlider, { target: { value: '0.1' } });
    fireEvent.change(depthSlider, { target: { value: '0.5' } });
    fireEvent.change(depthSlider, { target: { value: '0.9' } });

    // Should have been called at least once (React may batch updates)
    expect(onChange).toHaveBeenCalled();
    // Verify last call has the final value
    const lastCall = onChange.mock.calls[onChange.mock.calls.length - 1][0] as DepthFocusConfig;
    expect(lastCall.focus_depth).toBe(0.9);
  });

  it('reset button preserves the enabled state', () => {
    // Start with enabled and modified values
    const modifiedEnabled: DepthFocusConfig = {
      enabled: true,
      focus_depth: 0.9,
      focus_range: 0.8,
    };
    const onChange = vi.fn();
    render(<DepthFocusControl value={modifiedEnabled} onChange={onChange} />);

    const resetButton = screen.getByRole('button', { name: /reset.*defaults/i });
    fireEvent.click(resetButton);

    // Should reset values but stay enabled
    expect(onChange).toHaveBeenCalledWith({
      enabled: true,
      focus_depth: 0.5,
      focus_range: 0.3,
    });

    // Test disabled state in separate test - not rerender
    // This test only verifies enabled state is preserved
  });
});
