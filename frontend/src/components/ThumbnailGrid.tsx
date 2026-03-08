import { useState, useCallback, useEffect, useMemo, memo } from 'react';
import {
  Grid3X3,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Loader2,
  AlertTriangle,
  Image as ImageIcon,
  Maximize2,
  X,
} from 'lucide-react';
import type { ThumbnailFrame } from '../api/types';

// Named constants for better maintainability
const DEFAULT_THUMBNAIL_COUNT = 24;
const ZOOM_MIN = 0.5;
const ZOOM_MAX = 2;
const ZOOM_STEP = 0.25;
const ROWS_PER_PAGE = 3;

// Predefined grid column classes for responsive layouts (moved outside component for performance)
const GRID_COLS_CLASSES: Record<number, string> = {
  2: 'grid-cols-1 sm:grid-cols-2',
  3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
  4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  5: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5',
  6: 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-6',
};

/** Get responsive grid column class for a given column count */
const getGridColsClass = (cols: number): string => 
  GRID_COLS_CLASSES[cols] ?? GRID_COLS_CLASSES[4]!;

export interface ThumbnailGridProps {
  /** Job ID to fetch thumbnails for */
  jobId: string;
  /** Function to fetch thumbnail data */
  onFetchThumbnails: (jobId: string, options?: ThumbnailFetchOptions) => Promise<ThumbnailFrame[]>;
  /** Callback when a thumbnail is clicked */
  onThumbnailClick?: (frame: ThumbnailFrame) => void;
  /** Currently selected frame index */
  selectedFrameIndex?: number;
  /** Number of columns in the grid (default: 4) */
  columns?: number;
  /** Maximum thumbnail height in pixels (default: 150) */
  thumbnailHeight?: number;
  /** Whether to show depth maps alongside originals */
  showDepthMaps?: boolean;
  /** Additional CSS class names */
  className?: string;
}

export interface ThumbnailFetchOptions {
  /** Number of thumbnails to fetch (evenly distributed) */
  count?: number;
  /** Start frame index */
  startFrame?: number;
  /** End frame index */
  endFrame?: number;
}

type DisplayMode = 'original' | 'depth' | 'both';

/**
 * Thumbnail grid component for quick quality assessment of multiple frames
 * at different timestamps with their depth maps.
 */
export function ThumbnailGrid({
  jobId,
  onFetchThumbnails,
  onThumbnailClick,
  selectedFrameIndex,
  columns = 4,
  thumbnailHeight = 150,
  showDepthMaps = true,
  className = '',
}: ThumbnailGridProps) {
  const [thumbnails, setThumbnails] = useState<ThumbnailFrame[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [displayMode, setDisplayMode] = useState<DisplayMode>(showDepthMaps ? 'both' : 'original');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [page, setPage] = useState(0);
  const [enlargedFrame, setEnlargedFrame] = useState<ThumbnailFrame | null>(null);
  
  const itemsPerPage = columns * ROWS_PER_PAGE;
  const totalPages = Math.ceil(thumbnails.length / itemsPerPage);
  const startIndex = page * itemsPerPage;
  const visibleThumbnails = thumbnails.slice(startIndex, startIndex + itemsPerPage);

  // Fetch thumbnails when component mounts or jobId changes
  useEffect(() => {
    const fetchThumbnails = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await onFetchThumbnails(jobId, { count: DEFAULT_THUMBNAIL_COUNT });
        setThumbnails(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load thumbnails');
      } finally {
        setIsLoading(false);
      }
    };

    if (jobId) {
      fetchThumbnails();
    }
  }, [jobId, onFetchThumbnails]);

  const handleZoomIn = useCallback(() => {
    setZoomLevel((prev) => Math.min(ZOOM_MAX, prev + ZOOM_STEP));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoomLevel((prev) => Math.max(ZOOM_MIN, prev - ZOOM_STEP));
  }, []);

  const handlePrevPage = useCallback(() => {
    setPage((prev) => Math.max(0, prev - 1));
  }, []);

  const handleNextPage = useCallback(() => {
    setPage((prev) => Math.min(totalPages - 1, prev + 1));
  }, [totalPages]);

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      handlePrevPage();
    } else if (e.key === 'ArrowRight') {
      handleNextPage();
    } else if (e.key === 'Escape' && enlargedFrame) {
      setEnlargedFrame(null);
    }
  }, [handlePrevPage, handleNextPage, enlargedFrame]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);


  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 bg-white rounded-lg border border-gray-200">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        <span className="mt-3 text-gray-600">Loading thumbnail grid...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <AlertTriangle className="h-8 w-8 text-red-600 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-red-800">Failed to Load Thumbnails</h3>
        <p className="mt-2 text-sm text-red-700">{error}</p>
        <button
          onClick={() => {
            setIsLoading(true);
            setError(null);
            onFetchThumbnails(jobId, { count: DEFAULT_THUMBNAIL_COUNT })
              .then(setThumbnails)
              .catch((err) => setError(err.message))
              .finally(() => setIsLoading(false));
          }}
          className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    );
  }

  if (thumbnails.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
        <ImageIcon className="h-8 w-8 text-gray-400 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-gray-700">No Thumbnails Available</h3>
        <p className="mt-2 text-sm text-gray-500">
          No frame thumbnails are available for this video yet.
        </p>
      </div>
    );
  }

  // Cache the current index for the enlarged frame to avoid repeated findIndex calls
  const enlargedFrameIndex = enlargedFrame 
    ? thumbnails.findIndex((t) => t.frame_index === enlargedFrame.frame_index) 
    : -1;

  return (
    <div className={`thumbnail-grid-container ${className}`}>
      {/* Header with controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <Grid3X3 className="h-5 w-5 text-gray-500" />
            <h3 className="text-lg font-semibold text-gray-900">Thumbnail Grid</h3>
            <span className="text-sm text-gray-500">
              ({thumbnails.length} frames)
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Display mode toggle */}
            {showDepthMaps && (
              <div className="flex items-center bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setDisplayMode('original')}
                  className={`px-3 py-1 text-sm rounded ${
                    displayMode === 'original'
                      ? 'bg-white text-gray-900 shadow'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title="Show original frames only"
                >
                  Original
                </button>
                <button
                  onClick={() => setDisplayMode('depth')}
                  className={`px-3 py-1 text-sm rounded ${
                    displayMode === 'depth'
                      ? 'bg-white text-gray-900 shadow'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title="Show depth maps only"
                >
                  Depth
                </button>
                <button
                  onClick={() => setDisplayMode('both')}
                  className={`px-3 py-1 text-sm rounded ${
                    displayMode === 'both'
                      ? 'bg-white text-gray-900 shadow'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                  title="Show both original and depth maps"
                >
                  Both
                </button>
              </div>
            )}

            {/* Zoom controls */}
            <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
              <button
                onClick={handleZoomOut}
                disabled={zoomLevel <= ZOOM_MIN}
                className="p-1 text-gray-600 hover:text-gray-900 rounded disabled:opacity-50"
                title="Zoom out"
              >
                <ZoomOut className="h-4 w-4" />
              </button>
              <span className="text-xs text-gray-600 px-2 min-w-[3rem] text-center">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                disabled={zoomLevel >= ZOOM_MAX}
                className="p-1 text-gray-600 hover:text-gray-900 rounded disabled:opacity-50"
                title="Zoom in"
              >
                <ZoomIn className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Thumbnail Grid */}
      <div
        className={`grid ${getGridColsClass(columns)} gap-3`}
        style={{
          transform: `scale(${zoomLevel})`,
          transformOrigin: 'top left',
        }}
      >
        {visibleThumbnails.map((frame) => (
          <ThumbnailCard
            key={frame.frame_index}
            frame={frame}
            displayMode={displayMode}
            thumbnailHeight={thumbnailHeight}
            isSelected={frame.frame_index === selectedFrameIndex}
            onClick={() => onThumbnailClick?.(frame)}
            onEnlarge={() => setEnlargedFrame(frame)}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 mt-4 bg-white rounded-lg border border-gray-200 p-3">
          <button
            onClick={handlePrevPage}
            disabled={page === 0}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>
          <span className="text-sm text-gray-600">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={handleNextPage}
            disabled={page >= totalPages - 1}
            className="flex items-center gap-1 px-3 py-1.5 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Enlarged Frame Modal */}
      {enlargedFrame && (
        <EnlargedFrameModal
          frame={enlargedFrame}
          displayMode={displayMode}
          onClose={() => setEnlargedFrame(null)}
          onPrevious={() => {
            if (enlargedFrameIndex > 0) {
              setEnlargedFrame(thumbnails[enlargedFrameIndex - 1]);
            }
          }}
          onNext={() => {
            if (enlargedFrameIndex < thumbnails.length - 1) {
              setEnlargedFrame(thumbnails[enlargedFrameIndex + 1]);
            }
          }}
          hasPrevious={enlargedFrameIndex > 0}
          hasNext={enlargedFrameIndex < thumbnails.length - 1}
        />
      )}
    </div>
  );
}

/**
 * Individual thumbnail card component props
 */
interface ThumbnailCardProps {
  frame: ThumbnailFrame;
  displayMode: DisplayMode;
  thumbnailHeight: number;
  isSelected: boolean;
  onClick?: () => void;
  onEnlarge?: () => void;
}

/**
 * Memoized thumbnail card component for performance
 */
const ThumbnailCard = memo(function ThumbnailCard({
  frame,
  displayMode,
  thumbnailHeight,
  isSelected,
  onClick,
  onEnlarge,
}: ThumbnailCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const showOriginal = displayMode === 'original' || displayMode === 'both';
  const showDepth = displayMode === 'depth' || displayMode === 'both';

  return (
    <div
      className={`bg-white rounded-lg border-2 overflow-hidden transition-all cursor-pointer group ${
        isSelected
          ? 'border-primary-500 ring-2 ring-primary-200'
          : 'border-gray-200 hover:border-gray-300'
      }`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick?.();
        }
      }}
      aria-label={`Frame ${frame.frame_index + 1} at ${(frame.timestamp ?? 0).toFixed(2)}s`}
    >
      {/* Image container */}
      <div
        className={`relative bg-gray-900 overflow-hidden ${
          displayMode === 'both' ? 'flex' : ''
        }`}
        style={{ height: thumbnailHeight }}
      >
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-white opacity-50" />
          </div>
        )}

        {imageError ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-400">
            <ImageIcon className="h-8 w-8" />
            <span className="text-xs mt-1">Load failed</span>
          </div>
        ) : (
          <>
            {showOriginal && (
              <img
                src={frame.original_url}
                alt={`Frame ${frame.frame_index + 1}`}
                className={`w-full h-full object-cover transition-opacity ${
                  imageLoaded ? 'opacity-100' : 'opacity-0'
                } ${displayMode === 'both' ? 'w-1/2' : ''}`}
                onLoad={() => setImageLoaded(true)}
                onError={() => setImageError(true)}
              />
            )}
            {showDepth && (
              <img
                src={frame.depth_map_url}
                alt={`Depth map for frame ${frame.frame_index + 1}`}
                className={`w-full h-full object-cover transition-opacity ${
                  imageLoaded ? 'opacity-100' : 'opacity-0'
                } ${displayMode === 'both' ? 'w-1/2' : ''}`}
                onLoad={() => setImageLoaded(true)}
                onError={() => setImageError(true)}
              />
            )}
          </>
        )}

        {/* Enlarge button overlay */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onEnlarge?.();
          }}
          className="absolute top-2 right-2 p-1.5 bg-black/50 text-white rounded opacity-0 group-hover:opacity-100 transition-opacity"
          title="Enlarge"
        >
          <Maximize2 className="h-4 w-4" />
        </button>

        {/* Validation status badge */}
        {frame.validation_status && frame.validation_status !== 'pending' && (
          <div
            className={`absolute top-2 left-2 px-2 py-0.5 text-xs font-medium rounded ${
              frame.validation_status === 'validated'
                ? 'bg-green-500 text-white'
                : 'bg-blue-500 text-white'
            }`}
          >
            {frame.validation_status === 'validated' ? 'Validated' : 'Corrected'}
          </div>
        )}
      </div>

      {/* Frame info */}
      <div className="px-3 py-2 border-t border-gray-100">
        <div className="flex items-center justify-between text-xs">
          <span className="font-medium text-gray-900">Frame {frame.frame_index + 1}</span>
          <span className="text-gray-500">{(frame.timestamp ?? 0).toFixed(2)}s</span>
        </div>
        {frame.confidence_score !== undefined && (
          <div className="mt-1">
            <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary-500 transition-all"
                style={{ width: `${(frame.confidence_score ?? 0) * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">
              Confidence: {((frame.confidence_score ?? 0) * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
});

/**
 * Modal component for enlarged frame view props
 */
interface EnlargedFrameModalProps {
  frame: ThumbnailFrame;
  displayMode: DisplayMode;
  onClose: () => void;
  onPrevious: () => void;
  onNext: () => void;
  hasPrevious: boolean;
  hasNext: boolean;
}

/**
 * Memoized modal component for enlarged frame view
 */
const EnlargedFrameModal = memo(function EnlargedFrameModal({
  frame,
  displayMode,
  onClose,
  onPrevious,
  onNext,
  hasPrevious,
  hasNext,
}: EnlargedFrameModalProps) {
  const showOriginal = displayMode === 'original' || displayMode === 'both';
  const showDepth = displayMode === 'depth' || displayMode === 'both';

  // Lock body scroll when modal is open
  useEffect(() => {
    const originalStyle = window.getComputedStyle(document.body).overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = originalStyle;
    };
  }, []);

  // Focus trap and keyboard navigation
  useEffect(() => {
    const handleModalKeyDown = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'ArrowLeft' && hasPrevious) {
        onPrevious();
      } else if (e.key === 'ArrowRight' && hasNext) {
        onNext();
      }
    };
    window.addEventListener('keydown', handleModalKeyDown);
    return () => window.removeEventListener('keydown', handleModalKeyDown);
  }, [hasPrevious, hasNext, onPrevious, onNext]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
      onClick={onClose}
    >
      <div
        className="relative bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Frame {frame.frame_index + 1}
            </h3>
            <p className="text-sm text-gray-500">
              Timestamp: {(frame.timestamp ?? 0).toFixed(3)}s
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Image content */}
        <div className="p-4 overflow-auto" style={{ maxHeight: 'calc(90vh - 130px)' }}>
          <div className={`flex ${displayMode === 'both' ? 'gap-4' : ''}`}>
            {showOriginal && (
              <div className={`flex-1 ${displayMode === 'both' ? 'w-1/2' : 'w-full'}`}>
                {displayMode === 'both' && (
                  <p className="text-sm font-medium text-gray-700 mb-2">Original Frame</p>
                )}
                <img
                  src={frame.original_url}
                  alt={`Frame ${frame.frame_index + 1}`}
                  className="w-full rounded-lg shadow"
                />
              </div>
            )}
            {showDepth && (
              <div className={`flex-1 ${displayMode === 'both' ? 'w-1/2' : 'w-full'}`}>
                {displayMode === 'both' && (
                  <p className="text-sm font-medium text-gray-700 mb-2">Depth Map</p>
                )}
                <img
                  src={frame.depth_map_url}
                  alt={`Depth map for frame ${frame.frame_index + 1}`}
                  className="w-full rounded-lg shadow"
                />
              </div>
            )}
          </div>
        </div>

        {/* Footer with navigation */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
          <button
            onClick={onPrevious}
            disabled={!hasPrevious}
            className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>
          <div className="text-sm text-gray-600">
            {frame.confidence_score !== undefined && (
              <span>Confidence: {((frame.confidence_score ?? 0) * 100).toFixed(1)}%</span>
            )}
          </div>
          <button
            onClick={onNext}
            disabled={!hasNext}
            className="flex items-center gap-2 px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
});

export default ThumbnailGrid;
