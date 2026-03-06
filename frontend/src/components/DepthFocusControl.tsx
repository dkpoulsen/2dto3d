import { useCallback, useMemo } from 'react';
import { Focus, RotateCcw } from 'lucide-react';
import type { DepthFocusConfig } from '../api/types';

// ============================================================================
// Constants
// ============================================================================

/** Default focus configuration */
const DEFAULT_FOCUS_CONFIG: DepthFocusConfig = {
  enabled: false,
  focus_depth: 0.5,
  focus_range: 0.3,
};

/** Color constants for the visualization */
const COLORS = {
  /** Blue gradient for depth bar (from close to far) */
  DEPTH_GRADIENT: 'linear-gradient(to right, #3b82f6, #60a5fa, #93c5fd)',
  /** Green for focus zone border */
  FOCUS_ZONE: '#22c55e',
  /** Darker green for focus depth indicator */
  FOCUS_INDICATOR: '#16a34a',
};

// ============================================================================
// Component Props
// ============================================================================

interface DepthFocusControlProps {
  /** Current focus configuration */
  value: DepthFocusConfig;
  /** Callback when configuration changes */
  onChange: (config: DepthFocusConfig) => void;
  /** Whether the control is disabled */
  disabled?: boolean;
  /** Additional CSS class names */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function DepthFocusControl({
  value,
  onChange,
  disabled = false,
  className = '',
}: DepthFocusControlProps) {
  // Handle focus depth slider change
  const handleFocusDepthChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange({
        ...value,
        focus_depth: parseFloat(e.target.value),
      });
    },
    [value, onChange]
  );

  // Handle focus range slider change
  const handleFocusRangeChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange({
        ...value,
        focus_range: parseFloat(e.target.value),
      });
    },
    [value, onChange]
  );

  // Toggle enabled state
  const handleToggleEnabled = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange({ ...value, enabled: e.target.checked });
    },
    [value, onChange]
  );

  // Reset to defaults
  const handleReset = useCallback(() => {
    onChange({
      ...DEFAULT_FOCUS_CONFIG,
      enabled: value.enabled,
    });
  }, [value.enabled, onChange]);

  // Calculate focus zone visualization (memoized to avoid recalculation on every render)
  const focusZone = useMemo(() => {
    const start = Math.max(0, (value.focus_depth - value.focus_range / 2) * 100);
    const end = Math.min(100, (value.focus_depth + value.focus_range / 2) * 100);
    return {
      start,
      end,
      width: end - start,
    };
  }, [value.focus_depth, value.focus_range]);

  return (
    <div className={`depth-focus-control ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Focus className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Depth Focus</span>
        </div>
        <button
          onClick={handleReset}
          disabled={disabled}
          className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
          title="Reset to defaults"
          aria-label="Reset depth focus to defaults"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      {/* Visual Focus Zone Indicator */}
      <div className="relative bg-gray-50 rounded-lg border border-gray-200 mb-4">
        <div className="p-3">
          {/* Depth gradient visualization */}
          <div
            className="relative h-6 rounded overflow-hidden"
            style={{ background: COLORS.DEPTH_GRADIENT }}
            role="img"
            aria-label="Depth focus visualization showing pop-out, screen plane, and behind-screen zones"
          >
            {/* Focus zone overlay */}
            <div
              className="absolute top-0 h-full bg-white/40 border-l-2 border-r-2"
              style={{
                left: `${focusZone.start}%`,
                width: `${focusZone.width}%`,
                borderColor: COLORS.FOCUS_ZONE,
              }}
            />

            {/* Focus depth indicator */}
            <div
              className="absolute top-0 h-full w-1"
              style={{
                left: `${value.focus_depth * 100}%`,
                transform: 'translateX(-50%)',
                backgroundColor: COLORS.FOCUS_INDICATOR,
              }}
            />
          </div>

          {/* Labels */}
          <div className="flex justify-between mt-1 text-xs text-gray-500">
            <span>Pop Out</span>
            <span className="font-medium" style={{ color: COLORS.FOCUS_ZONE }}>
              Screen Plane
            </span>
            <span>Behind Screen</span>
          </div>
        </div>
      </div>

      {/* Focus Depth Slider */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <label htmlFor="focus-depth-slider" className="text-sm text-gray-600">
            Focus Depth
          </label>
          <span className="text-xs text-gray-500 font-mono">
            {value.focus_depth.toFixed(2)}
          </span>
        </div>
        <input
          id="focus-depth-slider"
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={value.focus_depth}
          onChange={handleFocusDepthChange}
          disabled={disabled || !value.enabled}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-500 disabled:opacity-50"
          aria-label={`Focus depth: ${value.focus_depth.toFixed(2)}. Objects at this depth appear at the screen plane.`}
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>Close</span>
          <span>Far</span>
        </div>
      </div>

      {/* Focus Range Slider */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <label htmlFor="focus-range-slider" className="text-sm text-gray-600">
            Focus Range
          </label>
          <span className="text-xs text-gray-500 font-mono">
            {value.focus_range.toFixed(2)}
          </span>
        </div>
        <input
          id="focus-range-slider"
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={value.focus_range}
          onChange={handleFocusRangeChange}
          disabled={disabled || !value.enabled}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-500 disabled:opacity-50"
          aria-label={`Focus range: ${value.focus_range.toFixed(2)}. Depth zone that stays near the screen plane.`}
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>Narrow</span>
          <span>Wide</span>
        </div>
      </div>

      {/* Description */}
      <div className="text-xs text-gray-500 mb-3 p-2 bg-gray-50 rounded">
        <p>
          <strong>Focus Depth:</strong> Objects at this depth appear at the screen plane.
          Objects closer will "pop out", objects farther will appear behind the screen.
        </p>
        <p className="mt-1">
          <strong>Focus Range:</strong> Depth zone that stays near the screen plane.
          A wider range keeps more of the scene at screen level.
        </p>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between">
        <label htmlFor="depth-focus-enabled" className="flex items-center gap-2 cursor-pointer">
          <input
            id="depth-focus-enabled"
            type="checkbox"
            checked={value.enabled}
            onChange={handleToggleEnabled}
            disabled={disabled}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-600">Enable depth focus</span>
        </label>
      </div>
    </div>
  );
}

export default DepthFocusControl;
