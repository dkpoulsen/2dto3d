import { memo, useState, useCallback, useMemo } from 'react';
import { ThumbsUp, Check, X, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import type { ModelResult, ComparisonModel, ComparisonSession } from '../api';
import { COMPARISON } from '../utils/constants';

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

function VotingWidgetInternal({
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

  // Derived state
  const hasVoted = Boolean(session.user_vote);
  const canVote = session.is_active && !isSubmitting;

  // Sort results by vote count (memoized)
  const sortedResults = useMemo(
    () => [...results].sort((a, b) => b.votes - a.votes),
    [results]
  );

  // Calculate vote percentages (memoized)
  const votePercentages = useMemo(() => {
    const percentages = new Map<ComparisonModel, number>();
    if (session.total_votes === 0) {
      results.forEach((r) => percentages.set(r.model, 0));
    } else {
      results.forEach((r) => {
        percentages.set(r.model, (r.votes / session.total_votes) * 100);
      });
    }
    return percentages;
  }, [results, session.total_votes]);

  // Handlers with useCallback
  const handleSelectModel = useCallback(
    (model: ComparisonModel) => {
      if (!canVote || hasVoted) return;
      setSelectedModel(model);
    },
    [canVote, hasVoted]
  );

  const handleSubmitVote = useCallback(() => {
    if (!selectedModel || !canVote) return;
    // Trim and validate comment
    const trimmedComment = comment.trim();
    onVote(selectedModel, trimmedComment || undefined);
  }, [selectedModel, canVote, comment, onVote]);

  const handleRemoveVote = useCallback(() => {
    if (showConfirmRemove) {
      onRemoveVote();
      setShowConfirmRemove(false);
    } else {
      setShowConfirmRemove(true);
    }
  }, [showConfirmRemove, onRemoveVote]);

  const handleCancelRemove = useCallback(() => {
    setShowConfirmRemove(false);
  }, []);

  const handleToggleComment = useCallback(() => {
    setShowComment((prev) => !prev);
  }, []);

  const handleCommentChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setComment(e.target.value);
  }, []);

  // Validate comment length
  const commentLength = comment.length;
  const isCommentValid = commentLength <= COMPARISON.MAX_COMMENT_LENGTH;

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
            <div className="space-y-2" role="list" aria-label="Vote results">
              {sortedResults.map((result, index) => {
                const votePercentage = votePercentages.get(result.model) ?? 0;
                const isUserVote = result.model === session.user_vote!.model;
                const isWinner = index === 0 && result.votes > 0;
                
                return (
                  <div key={result.model} className="relative" role="listitem">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-sm ${isUserVote ? 'font-semibold text-primary-700' : 'text-gray-700'}`}>
                        {isWinner && '🏆 '}
                        {result.model_name}
                      </span>
                      <span className="text-sm text-gray-500">
                        {result.votes} ({votePercentage.toFixed(0)}%)
                      </span>
                    </div>
                    <div 
                      className="w-full bg-gray-200 rounded-full h-2 overflow-hidden"
                      role="progressbar"
                      aria-valuenow={votePercentage}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={`${result.model_name} vote percentage`}
                    >
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
              <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg" role="alert">
                <p className="text-sm text-yellow-800 mb-2">
                  Are you sure you want to remove your vote?
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleRemoveVote}
                    disabled={isSubmitting}
                    className="px-3 py-1 text-sm bg-yellow-600 text-white rounded hover:bg-yellow-700 disabled:opacity-50 transition-colors"
                    aria-label="Confirm remove vote"
                  >
                    Yes, remove
                  </button>
                  <button
                    onClick={handleCancelRemove}
                    className="px-3 py-1 text-sm bg-white border border-gray-300 text-gray-700 rounded hover:bg-gray-50 transition-colors"
                    aria-label="Cancel remove vote"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={handleRemoveVote}
                disabled={isSubmitting || !session.is_active}
                className="mt-4 flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 disabled:opacity-50 transition-colors"
                aria-label="Remove your vote"
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
            <div className="grid grid-cols-2 gap-2" role="radiogroup" aria-label="Select a model to vote for">
              {results.map((result) => {
                const isSelected = selectedModel === result.model;
                
                return (
                  <button
                    key={result.model}
                    onClick={() => handleSelectModel(result.model)}
                    disabled={!canVote}
                    className={`p-3 rounded-lg border-2 text-left transition-all ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 hover:border-gray-300'
                    } ${!canVote ? 'opacity-50 cursor-not-allowed' : ''}`}
                    role="radio"
                    aria-checked={isSelected}
                    aria-label={`Vote for ${result.model_name}, currently ${result.votes} votes`}
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-sm font-medium ${
                        isSelected ? 'text-primary-900' : 'text-gray-900'
                      }`}>
                        {result.model_name}
                      </span>
                      {isSelected && (
                        <Check className="h-4 w-4 text-primary-600" aria-hidden="true" />
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {result.votes} current votes
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Optional Comment */}
            <div className="mt-3">
              <button
                onClick={handleToggleComment}
                className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition-colors"
                aria-expanded={showComment}
                aria-controls="comment-section"
              >
                {showComment ? (
                  <>
                    <ChevronUp className="h-4 w-4" aria-hidden="true" />
                    Hide comment
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4" aria-hidden="true" />
                    <MessageSquare className="h-4 w-4" aria-hidden="true" />
                    Add a comment (optional)
                  </>
                )}
              </button>
              
              {showComment && (
                <div id="comment-section" className="mt-2">
                  <textarea
                    value={comment}
                    onChange={handleCommentChange}
                    placeholder="Explain why you chose this model..."
                    className={`w-full px-3 py-2 border rounded-lg text-sm resize-none focus:ring-primary-500 focus:border-primary-500 ${
                      !isCommentValid ? 'border-red-300' : 'border-gray-300'
                    }`}
                    rows={3}
                    maxLength={COMPARISON.MAX_COMMENT_LENGTH}
                    aria-label="Optional comment for your vote"
                    aria-describedby="comment-counter"
                  />
                  <div id="comment-counter" className="text-xs text-gray-400 mt-1 text-right">
                    {commentLength}/{COMPARISON.MAX_COMMENT_LENGTH}
                  </div>
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              onClick={handleSubmitVote}
              disabled={!selectedModel || isSubmitting || !isCommentValid}
              className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              aria-label="Submit your vote"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" aria-hidden="true" />
                  Submitting...
                </>
              ) : (
                <>
                  <ThumbsUp className="h-4 w-4" aria-hidden="true" />
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

/**
 * VotingWidget component for casting and managing votes in model comparisons
 * Memoized to prevent unnecessary re-renders
 */
const VotingWidget = memo(VotingWidgetInternal);

export { VotingWidget };
export default VotingWidget;
