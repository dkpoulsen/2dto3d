import { useState, useCallback } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Image, ChevronLeft, ChevronRight, RefreshCw, Shuffle } from 'lucide-react';
import { DepthMapCard } from './DepthMapCard';
import { MetricsPanel } from './MetricsPanel';
import { VotingWidget } from './VotingWidget';
import { comparisonApi } from '../api';
import type { ComparisonSession, ComparisonModel } from '../api';

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

export function ModelComparisonView({
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

  // Vote mutation
  const voteMutation = useMutation({
    mutationFn: ({ model, comment }: { model: ComparisonModel; comment?: string }) =>
      comparisonApi.submitVote({
        session_id: session.session_id,
        model,
        comment,
      }),
    onSuccess: () => {
      // Invalidate and refetch session data
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

  const handlePrevModel = () => {
    setCurrentModelIndex((prev) => 
      prev > 0 ? prev - 1 : session.results.length - 1
    );
  };

  const handleNextModel = () => {
    setCurrentModelIndex((prev) => 
      prev < session.results.length - 1 ? prev + 1 : 0
    );
  };

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
            <div className="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-1 text-sm rounded ${
                  viewMode === 'grid'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Grid
              </button>
              <button
                onClick={() => setViewMode('metrics')}
                className={`px-3 py-1 text-sm rounded ${
                  viewMode === 'metrics'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Metrics
              </button>
              <button
                onClick={() => setViewMode('split')}
                className={`px-3 py-1 text-sm rounded ${
                  viewMode === 'split'
                    ? 'bg-white text-gray-900 shadow'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Split
              </button>
            </div>

            {/* Action Buttons */}
            {onLoadRandomSession && (
              <button
                onClick={onLoadRandomSession}
                disabled={isLoading}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                title="Load random comparison"
              >
                <Shuffle className="h-4 w-4" />
                Random
              </button>
            )}
            
            {onLoadNewSession && (
              <button
                onClick={onLoadNewSession}
                disabled={isLoading}
                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                New Comparison
              </button>
            )}
          </div>
        </div>

        {/* Session Info */}
        <div className="mt-4 flex items-center gap-6 text-sm text-gray-500">
          <span>Session: {session.session_id.slice(0, 8)}...</span>
          <span>Frame: {session.frame_index}</span>
          <span>{session.results.length} models</span>
          {session.job_id && (
            <span>Job: {session.job_id.slice(0, 8)}...</span>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Original Frame */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <Image className="h-5 w-5 text-gray-400" />
              <h3 className="text-sm font-medium text-gray-900">Original Frame</h3>
            </div>
            <div className="bg-gray-900 rounded-lg overflow-hidden">
              <img
                src={session.original_frame_url}
                alt="Original frame"
                className="mx-auto max-h-64 object-contain"
              />
            </div>
          </div>
        </div>

        {/* Depth Maps Section */}
        <div className="lg:col-span-2">
          {viewMode === 'grid' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {session.results.map((result) => (
                <DepthMapCard
                  key={result.model}
                  result={result}
                  isSelected={selectedModel === result.model}
                  onClick={() => setSelectedModel(result.model)}
                  showMetrics={true}
                />
              ))}
            </div>
          )}

          {viewMode === 'metrics' && (
            <MetricsPanel
              results={session.results}
              selectedModel={selectedModel}
            />
          )}

          {viewMode === 'split' && (
            <div className="space-y-4">
              {/* Navigation */}
              <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 p-3">
                <button
                  onClick={handlePrevModel}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <span className="text-sm text-gray-700">
                  {session.results[currentModelIndex]?.model_name} ({currentModelIndex + 1} of {session.results.length})
                </span>
                <button
                  onClick={handleNextModel}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>

              {/* Single Model View */}
              {session.results[currentModelIndex] && (
                <DepthMapCard
                  result={session.results[currentModelIndex]}
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
            isSubmitting={voteMutation.isPending || removeVoteMutation.isPending}
          />

          {/* Quick Stats */}
          <div className="mt-4 bg-white rounded-lg border border-gray-200 p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Quick Stats</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Fastest Model</span>
                <span className="font-medium text-gray-900">
                  {session.results.reduce((fastest, r) => 
                    r.metrics.processing_time_seconds < fastest.metrics.processing_time_seconds ? r : fastest
                  ).model_name}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Highest Confidence</span>
                <span className="font-medium text-gray-900">
                  {session.results.reduce((best, r) => 
                    r.metrics.avg_confidence > best.metrics.avg_confidence ? r : best
                  ).model_name}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Most Votes</span>
                <span className="font-medium text-gray-900">
                  {session.results.reduce((top, r) => 
                    r.votes > top.votes ? r : top
                  ).model_name} ({Math.max(...session.results.map(r => r.votes))} votes)
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ModelComparisonView;
