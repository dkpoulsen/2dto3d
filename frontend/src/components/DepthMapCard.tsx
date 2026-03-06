import { useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Image } from 'lucide-react';
import type { ModelResult, ComparisonModel } from '../api';

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

// Model descriptions
const MODEL_DESCRIPTIONS: Record<ComparisonModel, string> = {
  midas_small: 'Fast and lightweight, good for real-time',
  midas_hybrid: 'Balanced speed and quality',
  dpt_large: 'Highest quality, slower processing',
  dpt_hybrid: 'Good quality with reasonable speed',
};

export function DepthMapCard({
  result,
  isSelected = false,
  onClick,
  showMetrics = true,
  className = '',
}: DepthMapCardProps) {
  const [zoom, setZoom] = useState(1);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleZoomIn = () => {
    setZoom((z) => Math.min(4, z + 0.5));
  };

  const handleZoomOut = () => {
    setZoom((z) => Math.max(0.5, z - 0.5));
  };

  const handleResetZoom = () => {
    setZoom(1);
  };

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
      onKeyDown={(e) => {
        if (onClick && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          onClick();
        }
      }}
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
              {MODEL_DESCRIPTIONS[result.model]}
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
          style={{ height: '200px' }}
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
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />
          )}
        </div>

        {/* Zoom Controls */}
        <div className="absolute bottom-2 right-2 flex items-center gap-1 bg-black/50 rounded-lg p-1">
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleZoomOut();
            }}
            disabled={zoom <= 0.5}
            className="p-1 text-white hover:bg-white/20 rounded disabled:opacity-50"
            title="Zoom out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <span className="text-xs text-white px-1">{Math.round(zoom * 100)}%</span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleZoomIn();
            }}
            disabled={zoom >= 4}
            className="p-1 text-white hover:bg-white/20 rounded disabled:opacity-50"
            title="Zoom in"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleResetZoom();
            }}
            className="p-1 text-white hover:bg-white/20 rounded"
            title="Reset zoom"
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

export default DepthMapCard;
