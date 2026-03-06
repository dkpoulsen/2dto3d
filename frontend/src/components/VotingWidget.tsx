import { useState } from 'react';
import { ThumbsUp, Check, X, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import type { ModelResult, ComparisonModel, ComparisonSession } from '../api';

interface VotingWidgetProps {
  /** Current comparison session */
  session: ComparisonSession;
  /** All model results */
  results: ModelResult[];
  /** Handler when user votes for a model */
  onVote: (model: ComparisonModel, comment?: string) => void;
  /** Handler when user removes their vote */
  onRemoveVote: () => void;
  /** Whether a vote is currently being submitted */
  isSubmitting?: boolean;
  /** Additional CSS class names */
  className?: string;
}

export function VotingWidget({
  session,
  results,
  onVote,
  onRemoveVote,
  isSubmitting = false,
  className = '',
}: VotingWidgetProps) {
  const [selectedModel, setSelectedModel] = useState<ComparisonModel | null>(
    session.user_vote?.model || null
  );
  const [comment, setComment] = useState(session.user_vote?.comment || '');
  const [showComment, setShowComment] = useState(false);
  const [showConfirmRemove, setShowConfirmRemove] = useState(false);

  const hasVoted = !!session.user_vote;
  const canVote = session.is_active && !isSubmitting;

  const handleSelectModel = (model: ComparisonModel) => {
    if (!canVote || hasVoted) return;
    setSelectedModel(model);
  };

  const handleSubmitVote = () => {
    if (!selectedModel || !canVote) return;
    onVote(selectedModel, comment || undefined);
  };

  const handleRemoveVote = () => {
    if (showConfirmRemove) {
      onRemoveVote();
      setShowConfirmRemove(false);
    } else {
      setShowConfirmRemove(true);
    }
  };

  const handleCancelRemove = () => {
    setShowConfirmRemove(false);
  };

  // Sort results by vote count
  const sortedResults = [...results].sort((a, b) => b.votes - a.votes);

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Cast Your Vote</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              {session.total_votes} {session.total_votes === 1 ? 'vote' : 'votes'} cast
            </p>
          </div>
          {session.is_active ? (
            <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded-full">
              Voting Open
            </span>
          ) : (
            <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
              Voting Closed
            </span>
          )}
        </div>
      </div>

      {/* Model Selection */}
      <div className="p-4 space-y-2">
        {hasVoted ? (
          <>
            <p className="text-sm text-gray-600 mb-3">
              You voted for <span className="font-semibold">{session.user_vote!.model}</span>
            </p>
            
            {/* Results Chart */}
            <div className="space-y-2">
              {sortedResults.map((result, index) => {
                const votePercentage = session.total_votes > 0
                  ? (result.votes / session.total_votes) * 100
                  : 0;
                const isUserVote = result.model === session.user_vote!.model;
                
                return (
                  <div key={result.model} className="relative">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-sm ${isUserVote ? 'font-semibold text-primary-700' : 'text-gray-700'}`}>
                        {index === 0 && result.votes > 0 && '🏆 '}
                        {result.model_name}
                      </span>
                      <span className="text-sm text-gray-500">
                        {result.votes} ({votePercentage.toFixed(0)}%)
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          isUserVote ? 'bg-primary-500' : 'bg-gray-400'
                        }`}
                        style={{ width: `${votePercentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Remove Vote */}
            {showConfirmRemove ? (
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800 mb-2">
                  Are you sure you want to remove your vote?
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleRemoveVote}
                    disabled={isSubmitting}
                    className="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50"
                  >
                    Yes, remove
                  </button>
                  <button
                    onClick={handleCancelRemove}
                    className="px-3 py-1 text-sm bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={handleRemoveVote}
                disabled={isSubmitting || !session.is_active}
                className="mt-4 flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 disabled:opacity-50"
              >
                <X className="h-4 w-4" />
                Remove my vote
              </button>
            )}
          </>
        ) : (
          <>
            <p className="text-sm text-gray-600 mb-3">
              Select the model that produced the best depth estimation:
            </p>

            {/* Model Buttons */}
            <div className="grid grid-cols-2 gap-2">
              {results.map((result) => (
                <button
                  key={result.model}
                  onClick={() => handleSelectModel(result.model)}
                  disabled={!canVote}
                  className={`p-3 rounded-lg border-2 text-left transition-all ${
                    selectedModel === result.model
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  } ${!canVote ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-medium ${
                      selectedModel === result.model ? 'text-primary-900' : 'text-gray-900'
                    }`}>
                      {result.model_name}
                    </span>
                    {selectedModel === result.model && (
                      <Check className="h-4 w-4 text-primary-600" />
                    )}
                  </div>
                  <span className="text-xs text-gray-500">
                    {result.votes} current votes
                  </span>
                </button>
              ))}
            </div>

            {/* Optional Comment */}
            <div className="mt-3">
              <button
                onClick={() => setShowComment(!showComment)}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
              >
                {showComment ? (
                  <>
                    <ChevronUp className="h-4 w-4" />
                    Hide comment
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4" />
                    <MessageSquare className="h-4 w-4" />
                    Add a comment (optional)
                  </>
                )}
              </button>
              
              {showComment && (
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Explain why you chose this model..."
                  className="mt-2 w-full px-3 py-2 border border-gray-300 rounded-lg text-sm resize-none focus:ring-primary-500 focus:border-primary-500"
                  rows={3}
                  maxLength={500}
                />
              )}
            </div>

            {/* Submit Button */}
            <button
              onClick={handleSubmitVote}
              disabled={!selectedModel || isSubmitting}
              className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Submitting...
                </>
              ) : (
                <>
                  <ThumbsUp className="h-4 w-4" />
                  Submit Vote
                </>
              )}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default VotingWidget;
