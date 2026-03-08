import { memo, useState, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Image } from 'lucide-react';
import type { ModelResult } from '../api';
import { COMPARISON, MODEL_DESCRIPTIONS } from '../utils/constants';

interface DepthMapCardProps {
  /** Model result to display */
  result: ModelResult;
  /** Whether this card is selected/highlighted */
  isSelected?: boolean;
  /** Click handler for card selection */
  onClick?: () => void;
  /** Whether to show metrics */
  showMetrics?: boolean;
  /** Additional CSS class names */
  className?: string;
}

function DepthMapCardInternal({
  result,
  isSelected = false,
  onClick,
  showMetrics = true,
  className = '',
}: DepthMapCardProps) {
  const [zoom, setZoom] = useState(1);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleZoomIn = useCallback(() => {
    setZoom((z) => Math.min(COMPARISON.ZOOM_MAX, z + COMPARISON.ZOOM_STEP));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((z) => Math.max(COMPARISON.ZOOM_MIN, z - COMPARISON.ZOOM_STEP));
  }, []);

  const handleResetZoom = useCallback(() => {
    setZoom(1);
  }, []);

  const handleImageLoad = useCallback(() => {
    setImageLoaded(true);
  }, []);

  const handleImageError = useCallback(() => {
    setImageError(true);
  }, []);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (onClick && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        onClick();
      }
    },
    [onClick]
  );

  const handleZoomOutClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      handleZoomOut();
    },
    [handleZoomOut]
  );

  const handleZoomInClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      handleZoomIn();
    },
    [handleZoomIn]
  );

  const handleResetZoomClick = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      handleResetZoom();
    },
    [handleResetZoom]
  );

  // Get model description from constants or use model_name as fallback
  const modelDescription = MODEL_DESCRIPTIONS[result.model] ?? result.model_name;

  return (
    <div
      className={`bg-white rounded-lg border-2 transition-all ${
        isSelected
          ? 'border-primary-500 ring-2 ring-primary-200'
          : 'border-gray-200 hover:border-gray-300'
      } ${onClick ? 'cursor-pointer' : ''} ${className}`}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={handleKeyDown}
      aria-pressed={isSelected}
      aria-label={`Select ${result.model_name} depth map`}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              {result.model_name}
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {modelDescription}
            </p>
          </div>
          {isSelected && (
            <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 text-primary-700 rounded-full">
              Selected
            </span>
          )}
        </div>
      </div>

      {/* Image Container */}
      <div className="relative bg-gray-900 overflow-hidden">
        <div
          className="relative overflow-auto"
          style={{ height: `${COMPARISON.IMAGE_CONTAINER_HEIGHT}px` }}
        >
          {!imageLoaded && !imageError && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            </div>
          )}

          {imageError ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
              <Image className="h-12 w-12 mb-2" />
              <span className="text-sm">Failed to load image</span>
            </div>
          ) : (
            <img
              src={result.depth_map_url}
              alt={`Depth map from ${result.model_name}`}
              className={`mx-auto transition-opacity ${
                imageLoaded ? 'opacity-100' : 'opacity-0'
              }`}
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: 'center',
              }}
              onLoad={handleImageLoad}
              onError={handleImageError}
            />
          )}
        </div>

        {/* Zoom Controls */}
        <div className="absolute bottom-2 right-2 flex items-center gap-1 bg-black/50 rounded-lg p-1">
          <button
            onClick={handleZoomOutClick}
            disabled={zoom <= COMPARISON.ZOOM_MIN}
            className="p-1 text-white hover:bg-white/20 rounded disabled:opacity-50"
            title="Zoom out"
            aria-label="Zoom out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <span className="text-xs text-white px-1" aria-label={`Zoom level ${Math.round(zoom * 100)}%`}>
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomInClick}
            disabled={zoom >= COMPARISON.ZOOM_MAX}
            className="p-1 text-white hover:bg-white/20 rounded disabled:opacity-50"
            title="Zoom in"
            aria-label="Zoom in"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={handleResetZoomClick}
            className="p-1 text-white hover:bg-white/20 rounded"
            title="Reset zoom"
            aria-label="Reset zoom"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Metrics */}
      {showMetrics && (
        <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Processing Time:</span>
              <span className="ml-1 font-medium text-gray-900">
                {result.metrics.processing_time_seconds.toFixed(2)}s
              </span>
            </div>
            <div>
              <span className="text-gray-500">Confidence:</span>
              <span className="ml-1 font-medium text-gray-900">
                {(result.metrics.avg_confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div>
              <span className="text-gray-500">Memory:</span>
              <span className="ml-1 font-medium text-gray-900">
                {result.metrics.memory_usage_mb.toFixed(0)} MB
              </span>
            </div>
            {result.metrics.quality_score !== undefined && (
              <div>
                <span className="text-gray-500">Quality:</span>
                <span className="ml-1 font-medium text-gray-900">
                  {(result.metrics.quality_score * 100).toFixed(0)}%
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Vote Count */}
      <div className="px-4 py-2 border-t border-gray-100 flex items-center justify-between">
        <span className="text-xs text-gray-500">
          {result.votes} {result.votes === 1 ? 'vote' : 'votes'}
        </span>
        {result.user_voted && (
          <span className="text-xs font-medium text-primary-600">
            Your vote
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * DepthMapCard component for displaying model comparison results
 * Memoized to prevent unnecessary re-renders when parent updates
 */
const DepthMapCard = memo(DepthMapCardInternal);

export { DepthMapCard };
export default DepthMapCard;
