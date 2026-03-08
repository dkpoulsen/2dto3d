import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type {
  ComparisonSession,
  ComparisonModel,
  ModelResult,
  LeaderboardEntry,
  LeaderboardResponse,
  SubmitVoteResponse,
} from '../api';

/**
 * Creates a new QueryClient for testing
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
        refetchOnWindowFocus: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

/**
 * Custom render function that includes providers
 */
export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { queryClient?: QueryClient }
) {
  const { queryClient = createTestQueryClient(), ...renderOptions } = options || {};

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

// ============================================================================
// Mock Data Factory Functions
// ============================================================================

/**
 * Creates a mock ModelResult for testing
 */
export function createMockModelResult(overrides?: Partial<ModelResult>): ModelResult {
  return {
    model: 'midas_small' as ComparisonModel,
    model_name: 'MiDaS Small',
    depth_map_url: 'https://example.com/depth-map.png',
    raw_depth_map_url: 'https://example.com/raw-depth-map.png',
    metrics: {
      processing_time_seconds: 1.5,
      avg_confidence: 0.85,
      memory_usage_mb: 512,
      frames_processed: 1,
      quality_score: 0.9,
      edge_score: 0.8,
      temporal_consistency: 0.95,
    },
    votes: 5,
    user_voted: false,
    ...overrides,
  };
}

/**
 * Creates a mock ComparisonSession for testing
 */
export function createMockSession(overrides?: Partial<ComparisonSession>): ComparisonSession {
  return {
    session_id: 'test-session-123',
    job_id: 'test-job-456',
    frame_index: 10,
    original_frame_url: 'https://example.com/original-frame.png',
    results: [
      createMockModelResult({ model: 'midas_small', model_name: 'MiDaS Small', votes: 5 }),
      createMockModelResult({ model: 'midas_hybrid', model_name: 'MiDaS Hybrid', votes: 3 }),
      createMockModelResult({ model: 'dpt_large', model_name: 'DPT Large', votes: 7 }),
      createMockModelResult({ model: 'dpt_hybrid', model_name: 'DPT Hybrid', votes: 2 }),
    ],
    total_votes: 17,
    created_at: '2024-01-15T10:30:00Z',
    is_active: true,
    ...overrides,
  };
}

/**
 * Creates a mock LeaderboardEntry for testing
 */
export function createMockLeaderboardEntry(
  overrides?: Partial<LeaderboardEntry>
): LeaderboardEntry {
  return {
    model: 'midas_small' as ComparisonModel,
    model_name: 'MiDaS Small',
    total_votes: 100,
    win_rate_percent: 75.5,
    avg_confidence: 0.85,
    avg_processing_time_seconds: 1.5,
    sessions_count: 50,
    ...overrides,
  };
}

/**
 * Creates a mock LeaderboardResponse for testing
 */
export function createMockLeaderboard(overrides?: Partial<LeaderboardResponse>): LeaderboardResponse {
  return {
    leaderboard: [
      createMockLeaderboardEntry({ model: 'dpt_large', model_name: 'DPT Large', total_votes: 150, win_rate_percent: 82.3 }),
      createMockLeaderboardEntry({ model: 'midas_small', model_name: 'MiDaS Small', total_votes: 100, win_rate_percent: 75.5 }),
      createMockLeaderboardEntry({ model: 'midas_hybrid', model_name: 'MiDaS Hybrid', total_votes: 80, win_rate_percent: 68.2 }),
      createMockLeaderboardEntry({ model: 'dpt_hybrid', model_name: 'DPT Hybrid', total_votes: 60, win_rate_percent: 55.0 }),
    ],
    total_sessions: 200,
    total_votes: 390,
    updated_at: '2024-01-15T10:30:00Z',
    ...overrides,
  };
}

/**
 * Creates a mock SubmitVoteResponse for testing
 */
export function createMockVoteResponse(overrides?: Partial<SubmitVoteResponse>): SubmitVoteResponse {
  return {
    session_id: 'test-session-123',
    model: 'midas_small' as ComparisonModel,
    success: true,
    new_vote_count: 6,
    total_votes: 18,
    message: 'Vote recorded successfully',
    ...overrides,
  };
}

/**
 * Creates multiple mock results for comparison
 */
export function createMockResults(): ModelResult[] {
  return [
    createMockModelResult({
      model: 'midas_small',
      model_name: 'MiDaS Small',
      metrics: { processing_time_seconds: 1.2, avg_confidence: 0.82, memory_usage_mb: 256, frames_processed: 1 },
      votes: 5,
    }),
    createMockModelResult({
      model: 'midas_hybrid',
      model_name: 'MiDaS Hybrid',
      metrics: { processing_time_seconds: 2.1, avg_confidence: 0.88, memory_usage_mb: 512, frames_processed: 1 },
      votes: 3,
    }),
    createMockModelResult({
      model: 'dpt_large',
      model_name: 'DPT Large',
      metrics: { processing_time_seconds: 3.5, avg_confidence: 0.95, memory_usage_mb: 1024, frames_processed: 1 },
      votes: 10,
    }),
    createMockModelResult({
      model: 'dpt_hybrid',
      model_name: 'DPT Hybrid',
      metrics: { processing_time_seconds: 2.8, avg_confidence: 0.90, memory_usage_mb: 768, frames_processed: 1 },
      votes: 2,
    }),
  ];
}
