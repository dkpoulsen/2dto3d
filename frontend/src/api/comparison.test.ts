import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';

// Mock axios
vi.mock('axios', () => {
  const mockAxios = {
    create: vi.fn(() => mockAxios),
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      response: {
        use: vi.fn(),
      },
    },
  };
  return {
    default: mockAxios,
  };
});

// Create a reference to the mock
const mockAxios = vi.mocked(axios);

// Import after mocking - need to reimport to get mocked version
import { comparisonApi } from '../api/client';
import type { 
  ComparisonSession, 
  SubmitVoteResponse, 
  LeaderboardResponse 
} from '../api/types';

describe('comparisonApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('createSession', () => {
    it('should create a new comparison session', async () => {
      const mockSession: ComparisonSession = {
        session_id: 'new-session-123',
        job_id: 'job-456',
        frame_index: 5,
        original_frame_url: 'https://example.com/frame.png',
        results: [],
        total_votes: 0,
        created_at: '2024-01-15T10:30:00Z',
        is_active: true,
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockSession });

      const result = await comparisonApi.createSession({
        job_id: 'job-456',
        frame_index: 5,
      });

      expect(mockAxios.post).toHaveBeenCalledWith('/comparison/', {
        job_id: 'job-456',
        frame_index: 5,
      });
      expect(result).toEqual(mockSession);
    });

    it('should create session with default models', async () => {
      const mockSession: ComparisonSession = {
        session_id: 'new-session-123',
        frame_index: 0,
        original_frame_url: 'https://example.com/frame.png',
        results: [],
        total_votes: 0,
        created_at: '2024-01-15T10:30:00Z',
        is_active: true,
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockSession });

      const result = await comparisonApi.createSession({});

      expect(mockAxios.post).toHaveBeenCalledWith('/comparison/', {});
      expect(result).toEqual(mockSession);
    });

    it('should create session with specific models', async () => {
      const mockSession: ComparisonSession = {
        session_id: 'new-session-123',
        frame_index: 0,
        original_frame_url: 'https://example.com/frame.png',
        results: [],
        total_votes: 0,
        created_at: '2024-01-15T10:30:00Z',
        is_active: true,
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockSession });

      await comparisonApi.createSession({
        models: ['midas_small', 'dpt_large'],
      });

      expect(mockAxios.post).toHaveBeenCalledWith('/comparison/', {
        models: ['midas_small', 'dpt_large'],
      });
    });
  });

  describe('getSession', () => {
    it('should fetch a session by ID', async () => {
      const mockSession: ComparisonSession = {
        session_id: 'session-123',
        frame_index: 10,
        original_frame_url: 'https://example.com/frame.png',
        results: [],
        total_votes: 5,
        created_at: '2024-01-15T10:30:00Z',
        is_active: true,
      };

      mockAxios.get.mockResolvedValueOnce({ data: mockSession });

      const result = await comparisonApi.getSession('session-123');

      expect(mockAxios.get).toHaveBeenCalledWith('/comparison/session-123');
      expect(result).toEqual(mockSession);
    });

    it('should throw error for non-existent session', async () => {
      mockAxios.get.mockRejectedValueOnce(new Error('Session not found'));

      await expect(comparisonApi.getSession('non-existent')).rejects.toThrow('Session not found');
    });
  });

  describe('getSessionForJob', () => {
    it('should fetch session for a job without frame index', async () => {
      const mockSession: ComparisonSession = {
        session_id: 'session-123',
        job_id: 'job-456',
        frame_index: 0,
        original_frame_url: 'https://example.com/frame.png',
        results: [],
        total_votes: 0,
        created_at: '2024-01-15T10:30:00Z',
        is_active: true,
      };

      mockAxios.get.mockResolvedValueOnce({ data: mockSession });

      const result = await comparisonApi.getSessionForJob('job-456');

      expect(mockAxios.get).toHaveBeenCalledWith('/comparison/job/job-456', { params: {} });
      expect(result).toEqual(mockSession);
    });

    it('should fetch session for a job with specific frame index', async () => {
      const mockSession: ComparisonSession = {
        session_id: 'session-123',
        job_id: 'job-456',
        frame_index: 15,
        original_frame_url: 'https://example.com/frame.png',
        results: [],
        total_votes: 0,
        created_at: '2024-01-15T10:30:00Z',
        is_active: true,
      };

      mockAxios.get.mockResolvedValueOnce({ data: mockSession });

      const result = await comparisonApi.getSessionForJob('job-456', 15);

      expect(mockAxios.get).toHaveBeenCalledWith('/comparison/job/job-456', { 
        params: { frame_index: 15 } 
      });
      expect(result).toEqual(mockSession);
    });
  });

  describe('submitVote', () => {
    it('should submit a vote', async () => {
      const mockResponse: SubmitVoteResponse = {
        session_id: 'session-123',
        model: 'midas_small',
        success: true,
        new_vote_count: 6,
        total_votes: 18,
        message: 'Vote recorded successfully',
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await comparisonApi.submitVote({
        session_id: 'session-123',
        model: 'midas_small',
      });

      expect(mockAxios.post).toHaveBeenCalledWith('/comparison/session-123/vote', {
        model: 'midas_small',
        comment: undefined,
      });
      expect(result).toEqual(mockResponse);
    });

    it('should submit a vote with comment', async () => {
      const mockResponse: SubmitVoteResponse = {
        session_id: 'session-123',
        model: 'dpt_large',
        success: true,
        new_vote_count: 8,
        total_votes: 19,
        message: 'Vote recorded successfully',
      };

      mockAxios.post.mockResolvedValueOnce({ data: mockResponse });

      const result = await comparisonApi.submitVote({
        session_id: 'session-123',
        model: 'dpt_large',
        comment: 'Best depth quality',
      });

      expect(mockAxios.post).toHaveBeenCalledWith('/comparison/session-123/vote', {
        model: 'dpt_large',
        comment: 'Best depth quality',
      });
      expect(result).toEqual(mockResponse);
    });

    it('should handle vote submission failure', async () => {
      mockAxios.post.mockRejectedValueOnce(new Error('Voting is closed'));

      await expect(comparisonApi.submitVote({
        session_id: 'session-123',
        model: 'midas_small',
      })).rejects.toThrow('Voting is closed');
    });
  });

  describe('removeVote', () => {
    it('should remove a vote', async () => {
      mockAxios.delete.mockResolvedValueOnce({ data: {} });

      await comparisonApi.removeVote('session-123');

      expect(mockAxios.delete).toHaveBeenCalledWith('/comparison/session-123/vote');
    });

    it('should handle remove vote failure', async () => {
      mockAxios.delete.mockRejectedValueOnce(new Error('No vote to remove'));

      await expect(comparisonApi.removeVote('session-123')).rejects.toThrow('No vote to remove');
    });
  });

  describe('getLeaderboard', () => {
    it('should fetch the leaderboard', async () => {
      const mockLeaderboard: LeaderboardResponse = {
        leaderboard: [
          {
            model: 'dpt_large',
            model_name: 'DPT Large',
            total_votes: 150,
            win_rate_percent: 82.3,
            avg_confidence: 0.95,
            avg_processing_time_seconds: 3.5,
            sessions_count: 50,
          },
          {
            model: 'midas_small',
            model_name: 'MiDaS Small',
            total_votes: 100,
            win_rate_percent: 75.5,
            avg_confidence: 0.82,
            avg_processing_time_seconds: 1.2,
            sessions_count: 40,
          },
        ],
        total_sessions: 200,
        total_votes: 390,
        updated_at: '2024-01-15T10:30:00Z',
      };

      mockAxios.get.mockResolvedValueOnce({ data: mockLeaderboard });

      const result = await comparisonApi.getLeaderboard();

      expect(mockAxios.get).toHaveBeenCalledWith('/comparison/leaderboard');
      expect(result).toEqual(mockLeaderboard);
    });
  });

  describe('getRandomSession', () => {
    it('should fetch a random session', async () => {
      const mockSession: ComparisonSession = {
        session_id: 'random-session-123',
        frame_index: 42,
        original_frame_url: 'https://example.com/frame.png',
        results: [],
        total_votes: 5,
        created_at: '2024-01-15T10:30:00Z',
        is_active: true,
      };

      mockAxios.get.mockResolvedValueOnce({ data: mockSession });

      const result = await comparisonApi.getRandomSession();

      expect(mockAxios.get).toHaveBeenCalledWith('/comparison/random');
      expect(result).toEqual(mockSession);
    });

    it('should return null when no sessions available', async () => {
      mockAxios.get.mockResolvedValueOnce({ data: null });

      const result = await comparisonApi.getRandomSession();

      expect(result).toBeNull();
    });

    it('should handle errors gracefully', async () => {
      mockAxios.get.mockRejectedValueOnce(new Error('No sessions available'));

      await expect(comparisonApi.getRandomSession()).rejects.toThrow('No sessions available');
    });
  });
});
