import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Trophy, RefreshCw, Search } from 'lucide-react';
import { ModelComparisonView } from '../components/ModelComparisonView';
import { comparisonApi } from '../api';
import { POLLING_INTERVALS } from '../utils/constants';
type TabView = 'comparison' | 'leaderboard';

export function ModelComparisonPage() {
  const [activeTab, setActiveTab] = useState<TabView>('comparison');
  const [jobIdInput, setJobIdInput] = useState('');
  const [frameInput, setFrameInput] = useState('');

  // Fetch random session for comparison
  const {
    data: randomSession,
    isLoading: isLoadingRandom,
    refetch: fetchRandomSession,
  } = useQuery({
    queryKey: ['comparison', 'random'],
    queryFn: () => comparisonApi.getRandomSession(),
    refetchInterval: false,
  });

  // Fetch leaderboard
  const { data: leaderboard, isLoading: isLoadingLeaderboard } = useQuery({
    queryKey: ['comparison', 'leaderboard'],
    queryFn: () => comparisonApi.getLeaderboard(),
    refetchInterval: POLLING_INTERVALS.NORMAL,
  });

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: () =>
      comparisonApi.createSession({
        job_id: jobIdInput || undefined,
        frame_index: frameInput ? parseInt(frameInput, 10) : undefined,
      }),
    onSuccess: () => {
      setJobIdInput('');
      setFrameInput('');
    },
  });

  // Current session to display
  const currentSession = createSessionMutation.data || randomSession;

  // Handle loading random session
  const handleLoadRandom = () => {
    createSessionMutation.reset();
    fetchRandomSession();
  };

  // Handle creating new session
  const handleCreateSession = () => {
    createSessionMutation.mutate();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Model Comparison</h2>
          <p className="mt-1 text-sm text-gray-500">
            Compare depth estimation models side-by-side and vote for the best results
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8" aria-label="Tabs">
          <button
            onClick={() => setActiveTab('comparison')}
            className={`${
              activeTab === 'comparison'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            <Search className="h-4 w-4 inline-block mr-2" />
            Comparison Tool
          </button>
          <button
            onClick={() => setActiveTab('leaderboard')}
            className={`${
              activeTab === 'leaderboard'
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
          >
            <Trophy className="h-4 w-4 inline-block mr-2" />
            Leaderboard
          </button>
        </nav>
      </div>

      {/* Comparison Tab */}
      {activeTab === 'comparison' && (
        <div className="space-y-6">
          {/* Session Creation Controls */}
          <div className="bg-white rounded-lg border border-gray-200 p-4">
            <h3 className="text-sm font-medium text-gray-900 mb-3">
              Start New Comparison
            </h3>
            <div className="flex flex-wrap items-end gap-4">
              <div className="flex-1 min-w-48">
                <label htmlFor="job-id" className="block text-xs font-medium text-gray-700 mb-1">
                  Job ID (optional)
                </label>
                <input
                  id="job-id"
                  type="text"
                  value={jobIdInput}
                  onChange={(e) => setJobIdInput(e.target.value)}
                  placeholder="Enter job ID..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <div className="w-32">
                <label htmlFor="frame-index" className="block text-xs font-medium text-gray-700 mb-1">
                  Frame Index (optional)
                </label>
                <input
                  id="frame-index"
                  type="number"
                  value={frameInput}
                  onChange={(e) => setFrameInput(e.target.value)}
                  placeholder="Auto"
                  min="0"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
              <button
                onClick={handleCreateSession}
                disabled={createSessionMutation.isPending}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700 disabled:opacity-50"
              >
                {createSessionMutation.isPending ? 'Creating...' : 'Create Comparison'}
              </button>
              <button
                onClick={handleLoadRandom}
                disabled={isLoadingRandom}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 inline mr-2 ${isLoadingRandom ? 'animate-spin' : ''}`} />
                Load Random
              </button>
            </div>
            {createSessionMutation.isError && (
              <p className="mt-2 text-sm text-red-600">
                Failed to create comparison session. Please try again.
              </p>
            )}
          </div>

          {/* Comparison View */}
          {isLoadingRandom && !currentSession ? (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-500">Loading comparison...</p>
            </div>
          ) : currentSession ? (
            <ModelComparisonView
              session={currentSession}
              onLoadRandomSession={handleLoadRandom}
              isLoading={isLoadingRandom || createSessionMutation.isPending}
            />
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
              <Search className="h-12 w-12 text-gray-300 mx-auto" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">No Comparison Loaded</h3>
              <p className="mt-2 text-sm text-gray-500">
                Click "Load Random" to view a random comparison, or enter a Job ID to create a new comparison session.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Leaderboard Tab */}
      {activeTab === 'leaderboard' && (
        <div className="space-y-6">
          {/* Stats Overview */}
          {leaderboard && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Total Sessions</p>
                <p className="text-2xl font-bold text-gray-900">
                  {leaderboard.total_sessions}
                </p>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Total Votes Cast</p>
                <p className="text-2xl font-bold text-gray-900">
                  {leaderboard.total_votes}
                </p>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-500">Last Updated</p>
                <p className="text-lg font-medium text-gray-900">
                  {new Date(leaderboard.updated_at).toLocaleString()}
                </p>
              </div>
            </div>
          )}

          {/* Leaderboard Table */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            {isLoadingLeaderboard ? (
              <div className="p-12 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                <p className="mt-4 text-gray-500">Loading leaderboard...</p>
              </div>
            ) : leaderboard && leaderboard.leaderboard.length > 0 ? (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Model
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Votes
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Win Rate
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg Confidence
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Avg Time
                    </th>
                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sessions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {leaderboard.leaderboard.map((entry, index) => (
                    <tr key={entry.model} className={index === 0 ? 'bg-yellow-50' : ''}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                          index === 0 ? 'bg-yellow-200 text-yellow-800' :
                          index === 1 ? 'bg-gray-200 text-gray-800' :
                          index === 2 ? 'bg-orange-200 text-orange-800' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {index === 0 ? '🏆' : index + 1}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm font-medium text-gray-900">
                          {entry.model_name}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="text-sm font-semibold text-gray-900">
                          {entry.total_votes}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-primary-500 h-2 rounded-full"
                              style={{ width: `${entry.win_rate_percent}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-600">
                            {entry.win_rate_percent.toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="text-sm text-gray-600">
                          {(entry.avg_confidence * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="text-sm text-gray-600">
                          {entry.avg_processing_time_seconds.toFixed(2)}s
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <span className="text-sm text-gray-600">
                          {entry.sessions_count}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-12 text-center">
                <Trophy className="h-12 w-12 text-gray-300 mx-auto" />
                <h3 className="mt-4 text-lg font-medium text-gray-900">No Data Yet</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Start comparing models and casting votes to build the leaderboard.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default ModelComparisonPage;
