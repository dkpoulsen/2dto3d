import { memo, useState, useCallback, useMemo } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Image, ChevronLeft, ChevronRight, RefreshCw, Shuffle } from 'lucide-react';
import { DepthMapCard } from './DepthMapCard';
import { MetricsPanel } from './MetricsPanel';
import { VotingWidget } from './VotingWidget';
import { comparisonApi } from '../api';
import type { ComparisonSession, ComparisonModel, ModelResult } from '../api';

interface ModelComparisonViewProps {
  /** The comparison session to display */
  session: ComparisonSession;
  /** Handler to load a new session */
  onLoadNewSession?: () => void;
  /** Handler to load random session */
  onLoadRandomSession?: () => void;
  /** Whether data is loading */
  isLoading?: boolean;
  /** Additional CSS class names */
  className?: string;
}

type ViewMode = 'grid' | 'metrics' | 'split';

/** Helper to find the best model by a given metric */
function findBestModel(
  results: ModelResult[],
  selector: (r: ModelResult) => number,
  compare: (a: number, b: number) => boolean = (a, b) => a > b
): ModelResult | undefined {
  if (results.length === 0) return undefined;
  return results.reduce((best, current) => 
    compare(selector(current), selector(best)) ? current : best
  );
}

function ModelComparisonViewInternal({
  session,
  onLoadNewSession,
  onLoadRandomSession,
  isLoading = false,
  className = '',
}: ModelComparisonViewProps) {
  const queryClient = useQueryClient();
  const [selectedModel, setSelectedModel] = useState<ComparisonModel | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('grid');
  const [currentModelIndex, setCurrentModelIndex] = useState(0);

  // Memoized derived stats - computed once per session change
  const quickStats = useMemo(() => {
    const fastest = findBestModel(
      session.results,
      (r) => r.metrics.processing_time_seconds,
      (a, b) => a < b // Lower is better
    );
    
    const mostConfident = findBestModel(
      session.results,
      (r) => r.metrics.avg_confidence,
      (a, b) => a > b
    );
    
    const mostVotes = findBestModel(
      session.results,
      (r) => r.votes,
      (a, b) => a > b
    );
    
    const maxVotes = Math.max(0, ...session.results.map((r) => r.votes));

    return {
      fastestModel: fastest?.model_name ?? 'N/A',
      mostConfidentModel: mostConfident?.model_name ?? 'N/A',
      mostVotedModel: mostVotes?.model_name ?? 'N/A',
      maxVotes,
    };
  }, [session.results]);

  // Ensure currentModelIndex is within bounds
  const safeCurrentIndex = useMemo(() => {
    if (session.results.length === 0) return 0;
    return Math.min(currentModelIndex, session.results.length - 1);
  }, [currentModelIndex, session.results.length]);

  // Vote mutation
  const voteMutation = useMutation({
    mutationFn: ({ model, comment }: { model: ComparisonModel; comment?: string }) =>
      comparisonApi.submitVote({
        session_id: session.session_id,
        model,
        comment,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comparison', session.session_id] });
    },
  });

  // Remove vote mutation
  const removeVoteMutation = useMutation({
    mutationFn: () => comparisonApi.removeVote(session.session_id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['comparison', session.session_id] });
    },
  });

  const handleVote = useCallback((model: ComparisonModel, comment?: string) => {
    voteMutation.mutate({ model, comment });
  }, [voteMutation]);

  const handleRemoveVote = useCallback(() => {
    removeVoteMutation.mutate();
  }, [removeVoteMutation]);

  const handlePrevModel = useCallback(() => {
    setCurrentModelIndex((prev) => {
      const len = session.results.length;
      if (len === 0) return 0;
      return prev > 0 ? prev - 1 : len - 1;
    });
  }, [session.results.length]);

  const handleNextModel = useCallback(() => {
    setCurrentModelIndex((prev) => {
      const len = session.results.length;
      if (len === 0) return 0;
      return prev < len - 1 ? prev + 1 : 0;
    });
  }, [session.results.length]);

  const handleSetViewMode = useCallback((mode: ViewMode) => {
    setViewMode(mode);
  }, []);

  const handleSelectModel = useCallback((model: ComparisonModel) => {
    setSelectedModel(model);
  }, []);

  const isSubmitting = voteMutation.isPending || removeVoteMutation.isPending;

  return (
    <div className={`model-comparison-view ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Model Comparison
            </h2>
            <p className="text-sm text-gray-500 mt-0.5">
              Compare depth estimation results across different models
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-gray-100 rounded-lg p-1" role="tablist" aria-label="View modes">
              <button
                onClick={() => handleSetViewMode('grid')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  viewMode === 'grid'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                role="tab"
                aria-selected={viewMode === 'grid'}
                aria-controls="grid-panel"
              >
                Grid
              </button>
              <button
                onClick={() => handleSetViewMode('metrics')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  viewMode === 'metrics'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                role="tab"
                aria-selected={viewMode === 'metrics'}
                aria-controls="metrics-panel"
              >
                Metrics
              </button>
              <button
                onClick={() => handleSetViewMode('split')}
                className={`px-3 py-1 text-sm rounded transition-colors ${
                  viewMode === 'split'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
                role="tab"
                aria-selected={viewMode === 'split'}
                aria-controls="split-panel"
              >
                Split
              </button>
            </div>

            {/* Action Buttons */}
            {onLoadRandomSession && (
              <button
                onClick={onLoadRandomSession}
                disabled={isLoading}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors"
                title="Load random comparison"
                aria-label="Load random comparison session"
              >
                <Shuffle className="h-4 w-4" aria-hidden="true" />
                Random
              </button>
            )}
            
            {onLoadNewSession && (
              <button
                onClick={onLoadNewSession}
                disabled={isLoading}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
                aria-label="Create new comparison session"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} aria-hidden="true" />
                New Comparison
              </button>
            )}
          </div>
        </div>

        {/* Session Info */}
        <div className="mt-4 flex items-center gap-6 text-sm text-gray-500">
          <span title={session.session_id}>Session: {session.session_id.slice(0, 8)}...</span>
          <span>Frame: {session.frame_index}</span>
          <span>{session.results.length} models</span>
          {session.job_id && (
            <span title={session.job_id}>Job: {session.job_id.slice(0, 8)}...</span>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Original Frame */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Image className="h-5 w-5 text-gray-400" aria-hidden="true" />
              <h3 className="text-sm font-medium text-gray-900">Original Frame</h3>
            </div>
            <div className="bg-gray-900 rounded-lg overflow-hidden">
              <img
                src={session.original_frame_url}
                alt="Original frame for comparison"
                className="mx-auto max-h-64 object-contain"
                loading="lazy"
              />
            </div>
          </div>
        </div>

        {/* Depth Maps Section */}
        <div className="lg:col-span-2">
          {viewMode === 'grid' && (
            <div 
              id="grid-panel"
              className="grid grid-cols-1 md:grid-cols-2 gap-4"
              role="tabpanel"
              aria-label="Grid view of model results"
            >
              {session.results.map((result) => (
                <DepthMapCard
                  key={result.model}
                  result={result}
                  isSelected={selectedModel === result.model}
                  onClick={() => handleSelectModel(result.model)}
                  showMetrics={true}
                />
              ))}
            </div>
          )}

          {viewMode === 'metrics' && (
            <div id="metrics-panel" role="tabpanel" aria-label="Metrics comparison table">
              <MetricsPanel
                results={session.results}
                selectedModel={selectedModel}
              />
            </div>
          )}

          {viewMode === 'split' && (
            <div 
              id="split-panel"
              className="space-y-4"
              role="tabpanel"
              aria-label="Split view of individual models"
            >
              {/* Navigation */}
              <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-3">
                <button
                  onClick={handlePrevModel}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Previous model"
                >
                  <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                </button>
                <span className="text-sm text-gray-700" aria-live="polite">
                  {session.results[safeCurrentIndex]?.model_name} ({safeCurrentIndex + 1} of {session.results.length})
                </span>
                <button
                  onClick={handleNextModel}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Next model"
                >
                  <ChevronRight className="h-5 w-5" aria-hidden="true" />
                </button>
              </div>

              {/* Single Model View */}
              {session.results[safeCurrentIndex] && (
                <DepthMapCard
                  result={session.results[safeCurrentIndex]}
                  showMetrics={true}
                />
              )}
            </div>
          )}
        </div>

        {/* Voting Section */}
        <div className="lg:col-span-1">
          <VotingWidget
            session={session}
            results={session.results}
            onVote={handleVote}
            onRemoveVote={handleRemoveVote}
            isSubmitting={isSubmitting}
          />

          {/* Quick Stats */}
          <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Stats</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Fastest Model</span>
                <span className="font-medium text-gray-900">
                  {quickStats.fastestModel}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Highest Confidence</span>
                <span className="font-medium text-gray-900">
                  {quickStats.mostConfidentModel}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Most Votes</span>
                <span className="font-medium text-gray-900">
                  {quickStats.mostVotedModel} ({quickStats.maxVotes} votes)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * ModelComparisonView component for displaying side-by-side model comparisons
 * Memoized to prevent unnecessary re-renders
 */
const ModelComparisonView = memo(ModelComparisonViewInternal);

export { ModelComparisonView };
export default ModelComparisonView;
