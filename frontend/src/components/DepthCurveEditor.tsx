import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { RotateCcw, Sliders } from 'lucide-react';
import type { CurveControlPoint, CurvePreset, DepthCurveConfig } from '../api/types';

// ============================================================================
// Constants
// ============================================================================

/** Default SVG canvas size in pixels */
const DEFAULT_SIZE = 280;

/** Padding around the graph area */
const GRAPH_PADDING = 40;

/** Cardinal spline tension for smooth curves (0-1, lower = tighter) */
const CURVE_TENSION = 0.3;

/** Maximum number of control points allowed */
const MAX_CONTROL_POINTS = 10;

/** Radius for control point circles */
const CONTROL_POINT_RADIUS = {
  endpoint: 6,
  regular: 5,
  hover: 12,
  default: 8,
} as const;

// ============================================================================
// Preset Curve Definitions
// ============================================================================

const PRESET_CURVES: Record<CurvePreset, CurveControlPoint[]> = {
  linear: [
    { x: 0, y: 0 },
    { x: 1, y: 1 },
  ],
  s_curve: [
    { x: 0, y: 0 },
    { x: 0.25, y: 0.15 },
    { x: 0.5, y: 0.5 },
    { x: 0.75, y: 0.85 },
    { x: 1, y: 1 },
  ],
  contrast_boost: [
    { x: 0, y: 0 },
    { x: 0.2, y: 0.05 },
    { x: 0.5, y: 0.5 },
    { x: 0.8, y: 0.95 },
    { x: 1, y: 1 },
  ],
  soft_curve: [
    { x: 0, y: 0 },
    { x: 0.3, y: 0.25 },
    { x: 0.7, y: 0.75 },
    { x: 1, y: 1 },
  ],
  inverse_s: [
    { x: 0, y: 0 },
    { x: 0.25, y: 0.35 },
    { x: 0.5, y: 0.5 },
    { x: 0.75, y: 0.65 },
    { x: 1, y: 1 },
  ],
  shadow_lift: [
    { x: 0, y: 0.15 },
    { x: 0.25, y: 0.3 },
    { x: 0.5, y: 0.55 },
    { x: 0.75, y: 0.8 },
    { x: 1, y: 1 },
  ],
  highlight_compress: [
    { x: 0, y: 0 },
    { x: 0.25, y: 0.2 },
    { x: 0.5, y: 0.5 },
    { x: 0.75, y: 0.75 },
    { x: 1, y: 0.9 },
  ],
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Generate a unique ID for a control point based on its position
 * This provides stable keys even when points are reordered
 */
function generatePointId(point: CurveControlPoint, index: number): string {
  return `point-${point.x.toFixed(3)}-${point.y.toFixed(3)}-${index}`;
}

/**
 * Generate smooth curve path using cardinal spline interpolation
 */
function generateCurvePath(
  points: CurveControlPoint[],
  toSvgCoords: (p: CurveControlPoint) => { x: number; y: number }
): string {
  if (points.length < 2) return '';

  const sortedPoints = [...points].sort((a, b) => a.x - b.x);
  const svgPoints = sortedPoints.map(toSvgCoords);

  // Simple linear interpolation for 2 points
  if (svgPoints.length === 2) {
    return `M ${svgPoints[0].x} ${svgPoints[0].y} L ${svgPoints[1].x} ${svgPoints[1].y}`;
  }

  // Generate smooth curve using cardinal spline
  let path = `M ${svgPoints[0].x} ${svgPoints[0].y}`;

  for (let i = 0; i < svgPoints.length - 1; i++) {
    const p0 = svgPoints[Math.max(0, i - 1)];
    const p1 = svgPoints[i];
    const p2 = svgPoints[i + 1];
    const p3 = svgPoints[Math.min(svgPoints.length - 1, i + 2)];

    // Calculate control points for smooth curve
    const cp1x = p1.x + (p2.x - p0.x) * CURVE_TENSION;
    const cp1y = p1.y + (p2.y - p0.y) * CURVE_TENSION;
    const cp2x = p2.x - (p3.x - p1.x) * CURVE_TENSION;
    const cp2y = p2.y - (p3.y - p1.y) * CURVE_TENSION;

    path += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
  }

  return path;
}

// ============================================================================
// Component Props
// ============================================================================

interface DepthCurveEditorProps {
  /** Current curve configuration */
  value: DepthCurveConfig;
  /** Callback when configuration changes */
  onChange: (config: DepthCurveConfig) => void;
  /** Whether the editor is disabled */
  disabled?: boolean;
  /** SVG canvas size in pixels */
  size?: number;
  /** Additional CSS class names */
  className?: string;
}

// ============================================================================
// Component
// ============================================================================

export function DepthCurveEditor({
  value,
  onChange,
  disabled = false,
  size = DEFAULT_SIZE,
  className = '',
}: DepthCurveEditorProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [draggingIndex, setDraggingIndex] = useState<number | null>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const graphSize = size - GRAPH_PADDING * 2;

  // Convert normalized coordinates to SVG coordinates
  const toSvgCoords = useCallback(
    (point: CurveControlPoint): { x: number; y: number } => ({
      x: GRAPH_PADDING + point.x * graphSize,
      y: GRAPH_PADDING + (1 - point.y) * graphSize,
    }),
    [graphSize]
  );

  // Convert SVG coordinates to normalized coordinates
  const toNormalized = useCallback(
    (svgX: number, svgY: number): CurveControlPoint => ({
      x: Math.max(0, Math.min(1, (svgX - GRAPH_PADDING) / graphSize)),
      y: Math.max(0, Math.min(1, 1 - (svgY - GRAPH_PADDING) / graphSize)),
    }),
    [graphSize]
  );

  // Generate curve path - memoized for performance
  const curvePath = useMemo(
    () => generateCurvePath(value.control_points, toSvgCoords),
    [value.control_points, toSvgCoords]
  );

  // Handle mouse down on a control point
  const handleMouseDown = useCallback(
    (index: number) => (e: React.MouseEvent) => {
      if (disabled) return;
      e.preventDefault();
      setDraggingIndex(index);
    },
    [disabled]
  );

  // Handle mouse up - ends dragging
  const handleMouseUp = useCallback(() => {
    setDraggingIndex(null);
  }, []);

  // Update points during drag operation
  const updatePointPosition = useCallback(
    (clientX: number, clientY: number, pointIndex: number) => {
      if (!svgRef.current) return;

      const rect = svgRef.current.getBoundingClientRect();
      const x = clientX - rect.left;
      const y = clientY - rect.top;

      const newPoint = toNormalized(x, y);
      const newPoints = [...value.control_points];

      // Find the point being dragged (may have moved index due to sorting)
      const draggedPoint = value.control_points[pointIndex];
      const currentIndex = newPoints.findIndex(
        (p) => Math.abs(p.x - draggedPoint.x) < 0.001 && Math.abs(p.y - draggedPoint.y) < 0.001
      );

      const targetIndex = currentIndex >= 0 ? currentIndex : pointIndex;

      // Ensure endpoints stay at their x boundaries
      if (pointIndex === 0) {
        newPoints[0] = { x: 0, y: Math.max(0, Math.min(1, newPoint.y)) };
      } else if (pointIndex === value.control_points.length - 1) {
        newPoints[newPoints.length - 1] = { x: 1, y: Math.max(0, Math.min(1, newPoint.y)) };
      } else {
        newPoints[targetIndex] = {
          x: Math.max(0, Math.min(1, newPoint.x)),
          y: Math.max(0, Math.min(1, newPoint.y)),
        };
      }

      // Sort points by x to maintain order
      newPoints.sort((a, b) => a.x - b.x);

      onChange({
        ...value,
        preset: null, // Clear preset when manually adjusting
        control_points: newPoints,
      });
    },
    [value, onChange, toNormalized]
  );

  // Add global mouse event listeners when dragging
  useEffect(() => {
    if (draggingIndex === null) return;

    const handleGlobalMouseMove = (e: MouseEvent) => {
      updatePointPosition(e.clientX, e.clientY, draggingIndex);
    };

    window.addEventListener('mousemove', handleGlobalMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleGlobalMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [draggingIndex, updatePointPosition, handleMouseUp]);

  // Handle preset selection
  const handlePresetChange = useCallback(
    (preset: CurvePreset) => {
      onChange({
        enabled: value.enabled,
        preset,
        control_points: PRESET_CURVES[preset],
      });
    },
    [value.enabled, onChange]
  );

  // Reset to linear curve
  const handleReset = useCallback(() => {
    onChange({
      enabled: value.enabled,
      preset: 'linear',
      control_points: PRESET_CURVES.linear,
    });
  }, [value.enabled, onChange]);

  // Add new control point
  const handleAddPoint = useCallback(
    (e: React.MouseEvent) => {
      if (disabled || !svgRef.current) return;

      const rect = svgRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Only add if clicked on the graph area
      if (
        x < GRAPH_PADDING ||
        x > size - GRAPH_PADDING ||
        y < GRAPH_PADDING ||
        y > size - GRAPH_PADDING
      ) {
        return;
      }

      const newPoint = toNormalized(x, y);
      const newPoints = [...value.control_points, newPoint].sort((a, b) => a.x - b.x);

      // Limit to max control points
      if (newPoints.length > MAX_CONTROL_POINTS) return;

      onChange({
        ...value,
        preset: null,
        control_points: newPoints,
      });
    },
    [disabled, size, toNormalized, value, onChange]
  );

  // Remove control point (double click)
  const handleRemovePoint = useCallback(
    (index: number) => (e: React.MouseEvent) => {
      e.stopPropagation();
      if (disabled) return;
      if (value.control_points.length <= 2) return; // Keep at least 2 points
      if (index === 0 || index === value.control_points.length - 1) return; // Don't remove endpoints

      const newPoints = value.control_points.filter((_, i) => i !== index);
      onChange({
        ...value,
        preset: null,
        control_points: newPoints,
      });
    },
    [disabled, value, onChange]
  );

  // Toggle enabled state
  const handleToggleEnabled = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onChange({ ...value, enabled: e.target.checked });
    },
    [value, onChange]
  );

  return (
    <div className={`depth-curve-editor ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sliders className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">Depth Curve</span>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={value.preset || ''}
            onChange={(e) => handlePresetChange(e.target.value as CurvePreset)}
            disabled={disabled}
            className="text-xs px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
          >
            <option value="">Custom</option>
            <option value="linear">Linear</option>
            <option value="s_curve">S-Curve</option>
            <option value="contrast_boost">Contrast Boost</option>
            <option value="soft_curve">Soft Curve</option>
            <option value="inverse_s">Inverse S</option>
            <option value="shadow_lift">Shadow Lift</option>
            <option value="highlight_compress">Highlight Compress</option>
          </select>
          <button
            onClick={handleReset}
            disabled={disabled}
            className="p-1 text-gray-400 hover:text-gray-600 disabled:opacity-50"
            title="Reset to linear"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* SVG Curve Editor */}
      <div className="relative bg-gray-50 rounded-lg border border-gray-200">
        <svg
          ref={svgRef}
          width={size}
          height={size}
          className={`cursor-crosshair ${disabled ? 'opacity-50' : ''}`}
          onClick={handleAddPoint}
        >
          {/* Grid Pattern Definition */}
          <defs>
            <pattern
              id="grid"
              width={graphSize / 4}
              height={graphSize / 4}
              patternUnits="userSpaceOnUse"
              x={GRAPH_PADDING}
              y={GRAPH_PADDING}
            >
              <path
                d={`M ${graphSize / 4} 0 L 0 0 0 ${graphSize / 4}`}
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="1"
              />
            </pattern>
            <linearGradient id="depthGradient" x1="0%" y1="100%" x2="0%" y2="0%">
              <stop offset="0%" stopColor="#1e3a8a" />
              <stop offset="50%" stopColor="#3b82f6" />
              <stop offset="100%" stopColor="#93c5fd" />
            </linearGradient>
          </defs>

          {/* Grid */}
          <rect
            x={GRAPH_PADDING}
            y={GRAPH_PADDING}
            width={graphSize}
            height={graphSize}
            fill="url(#grid)"
          />

          {/* Axis Labels */}
          <text
            x={GRAPH_PADDING + graphSize / 2}
            y={size - 8}
            textAnchor="middle"
            className="text-xs fill-gray-500"
          >
            Input Depth
          </text>
          <text
            x={12}
            y={GRAPH_PADDING + graphSize / 2}
            textAnchor="middle"
            transform={`rotate(-90, 12, ${GRAPH_PADDING + graphSize / 2})`}
            className="text-xs fill-gray-500"
          >
            Output Depth
          </text>

          {/* Diagonal Reference Line (Linear) */}
          <line
            x1={GRAPH_PADDING}
            y1={GRAPH_PADDING + graphSize}
            x2={GRAPH_PADDING + graphSize}
            y2={GRAPH_PADDING}
            stroke="#d1d5db"
            strokeWidth="1"
            strokeDasharray="4 4"
          />

          {/* Curve Path */}
          <path
            d={curvePath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Control Point Lines */}
          {value.control_points.map((point, index) => {
            if (index === 0) return null;
            const svgPoint = toSvgCoords(point);
            const prevPoint = toSvgCoords(value.control_points[index - 1]);

            return (
              <line
                key={`line-${generatePointId(point, index)}`}
                x1={prevPoint.x}
                y1={prevPoint.y}
                x2={svgPoint.x}
                y2={svgPoint.y}
                stroke="#93c5fd"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
            );
          })}

          {/* Control Points */}
          {value.control_points.map((point, index) => {
            const svgPoint = toSvgCoords(point);
            const isEndpoint = index === 0 || index === value.control_points.length - 1;
            const isHovered = hoverIndex === index;
            const isDragging = draggingIndex === index;
            const pointId = generatePointId(point, index);

            return (
              <g key={pointId}>
                {/* Outer ring for better click target */}
                <circle
                  cx={svgPoint.x}
                  cy={svgPoint.y}
                  r={isHovered || isDragging ? CONTROL_POINT_RADIUS.hover : CONTROL_POINT_RADIUS.default}
                  fill="transparent"
                  className="cursor-pointer"
                  onMouseDown={handleMouseDown(index)}
                  onMouseEnter={() => setHoverIndex(index)}
                  onMouseLeave={() => setHoverIndex(null)}
                  onDoubleClick={handleRemovePoint(index)}
                />
                {/* Visible circle */}
                <circle
                  cx={svgPoint.x}
                  cy={svgPoint.y}
                  r={isEndpoint ? CONTROL_POINT_RADIUS.endpoint : CONTROL_POINT_RADIUS.regular}
                  fill={isEndpoint ? '#3b82f6' : '#60a5fa'}
                  stroke="white"
                  strokeWidth="2"
                  className={`cursor-pointer transition-all ${
                    isHovered || isDragging ? 'filter drop-shadow-md' : ''
                  }`}
                  style={{
                    transform: isHovered || isDragging ? 'scale(1.2)' : 'scale(1)',
                    transformOrigin: `${svgPoint.x}px ${svgPoint.y}px`,
                  }}
                />
              </g>
            );
          })}
        </svg>

        {/* Instructions */}
        <div className="absolute bottom-1 left-1 right-1 text-center">
          <span className="text-[10px] text-gray-400">
            Click to add • Double-click to remove
          </span>
        </div>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="flex items-center justify-between mt-3">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={value.enabled}
            onChange={handleToggleEnabled}
            disabled={disabled}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-600">Enable curve adjustment</span>
        </label>
        <span className="text-xs text-gray-400">
          {value.control_points.length} point{value.control_points.length !== 1 ? 's' : ''}
        </span>
      </div>
    </div>
  );
}

export default DepthCurveEditor;
