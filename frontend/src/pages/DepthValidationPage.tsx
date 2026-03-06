import { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ChevronLeft,
  ChevronRight,
  Check,
  SkipForward,
  AlertTriangle,
  Loader2,
  ArrowLeft,
  Image as ImageIcon,
} from 'lucide-react';
import { DepthValidationEditor } from '../components/DepthValidationEditor';
import { depthValidationApi, jobsApi } from '../api';
import { POLLING_INTERVALS } from '../utils/constants';
// Types are inferred from API responses

export function DepthValidationPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [depthMapData, setDepthMapData] = useState<ImageData | null>(null);
  const [originalFrameUrl, setOriginalFrameUrl] = useState<string | null>(null);
  const [showOriginal, setShowOriginal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Fetch validation session
  const { 
    data: session, 
    isLoading: isLoadingSession,
    error: sessionError 
  } = useQuery({
    queryKey: ['depthValidation', jobId],
    queryFn: () => depthValidationApi.getValidationSession(jobId!),
    enabled: !!jobId,
    refetchInterval: POLLING_INTERVALS.NORMAL,
  });
  
  // Fetch job details
  const { data: job } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJob(jobId!),
    enabled: !!jobId,
  });
  
  // Load current frame data
  useEffect(() => {
    if (!jobId || currentFrameIndex === undefined) return;
    
    const loadFrameData = async () => {
      try {
        // Load depth map
        const depthBlob = await depthValidationApi.getFrameDepthMap(jobId, currentFrameIndex);
        const depthUrl = URL.createObjectURL(depthBlob);
        
        // Load into ImageData
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          if (ctx) {
            ctx.drawImage(img, 0, 0);
            setDepthMapData(ctx.getImageData(0, 0, img.width, img.height));
          }
          URL.revokeObjectURL(depthUrl);
        };
        img.src = depthUrl;
        
        // Load original frame
        try {
          const originalBlob = await depthValidationApi.getFrameOriginal(jobId, currentFrameIndex);
          setOriginalFrameUrl(URL.createObjectURL(originalBlob));
        } catch {
          setOriginalFrameUrl(null);
        }
        
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load frame');
      }
    };
    
    loadFrameData();
    
    // Cleanup - revoke previous original frame URL
    return () => {
      setOriginalFrameUrl(prev => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
    };
  }, [jobId, currentFrameIndex]);
  
  // Mark frame as validated mutation
  const validateMutation = useMutation({
    mutationFn: () => depthValidationApi.markFrameValidated(jobId!, currentFrameIndex),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['depthValidation', jobId] });
      moveToNextFrame();
    },
    onError: (err: Error) => setError(err.message),
  });
  
  // Submit correction mutation
  const correctionMutation = useMutation({
    mutationFn: (imageData: ImageData) => {
      // Convert ImageData to base64
      const canvas = document.createElement('canvas');
      canvas.width = imageData.width;
      canvas.height = imageData.height;
      const ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('Failed to create canvas context');
      ctx.putImageData(imageData, 0, 0);
      
      const base64 = canvas.toDataURL('image/png').split(',')[1];
      
      return depthValidationApi.submitCorrection({
        job_id: jobId!,
        frame_index: currentFrameIndex,
        depth_map_data: base64,
        correction_type: 'manual',
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['depthValidation', jobId] });
      moveToNextFrame();
    },
    onError: (err: Error) => setError(err.message),
  });
  
  // Navigation helpers
  const currentFrame = session?.frames[currentFrameIndex];
  const needsValidationFrames = session?.frames.filter(f => f.needs_validation) || [];
  
  
  const moveToNextFrame = useCallback(() => {
    if (!session) return;
    
    // Find next frame needing validation
    const nextValidationFrame = needsValidationFrames.find(
      f => f.frame_index > currentFrameIndex && f.needs_validation
    );
    
    if (nextValidationFrame) {
      setCurrentFrameIndex(nextValidationFrame.frame_index);
    } else if (currentFrameIndex < session.total_frames - 1) {
      // Move to next frame even if it doesn't need validation
      setCurrentFrameIndex(currentFrameIndex + 1);
    }
  }, [session, needsValidationFrames, currentFrameIndex]);
  
  const moveToPrevFrame = useCallback(() => {
    if (currentFrameIndex > 0) {
      setCurrentFrameIndex(currentFrameIndex - 1);
    }
  }, [currentFrameIndex]);
  
  const skipToNextValidation = useCallback(() => {
    const nextFrame = needsValidationFrames.find(
      f => f.frame_index > currentFrameIndex && f.needs_validation
    );
    if (nextFrame) {
      setCurrentFrameIndex(nextFrame.frame_index);
    }
  }, [needsValidationFrames, currentFrameIndex]);
  
  // Handle editor changes - could track dirty state here
  const handleEditorChange = useCallback((_imageData: ImageData) => {
    // Intentionally empty - could track dirty state for unsaved changes indicator
  }, []);
  
  const handleEditorSave = useCallback((imageData: ImageData) => {
    correctionMutation.mutate(imageData);
  }, [correctionMutation]);
  
  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle if typing in an input
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      
      switch (e.key) {
        case 'ArrowLeft':
          moveToPrevFrame();
          break;
        case 'ArrowRight':
          moveToNextFrame();
          break;
        case 'Enter':
          if (e.ctrlKey || e.metaKey) {
            // Ctrl+Enter = save correction
            if (depthMapData) {
              handleEditorSave(depthMapData);
            }
          } else {
            // Enter = mark as validated
            validateMutation.mutate();
          }
          break;
        case 'Tab':
          e.preventDefault();
          skipToNextValidation();
          break;
        case 'o':
          setShowOriginal(prev => !prev);
          break;
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [moveToPrevFrame, moveToNextFrame, skipToNextValidation, validateMutation, handleEditorSave, depthMapData]);
  
  if (isLoadingSession) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        <span className="ml-3 text-gray-600">Loading validation session...</span>
      </div>
    );
  }
  
  if (sessionError || !session) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <AlertTriangle className="h-8 w-8 text-red-600 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-red-800">Failed to Load Session</h3>
        <p className="mt-2 text-sm text-red-700">
          {sessionError instanceof Error ? sessionError.message : 'Unable to load depth validation session'}
        </p>
        <button
          onClick={() => navigate('/jobs')}
          className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
        >
          Back to Jobs
        </button>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/jobs')}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Depth Validation</h2>
            <p className="text-sm text-gray-500">
              Job: {job?.input_filename || jobId}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Progress indicator */}
          <div className="text-sm text-gray-600">
            <span className="font-medium">{session.frames_needing_validation}</span> frames need validation
          </div>
          
          {/* Frame counter */}
          <div className="bg-gray-100 px-4 py-2 rounded-lg">
            <span className="text-sm text-gray-600">Frame </span>
            <span className="font-bold text-gray-900">{currentFrameIndex + 1}</span>
            <span className="text-sm text-gray-600"> / {session.total_frames}</span>
          </div>
        </div>
      </div>
      
      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm text-red-700">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800"
          >
            &times;
          </button>
        </div>
      )}
      
      {/* Main Content */}
      <div className="flex gap-4">
        {/* Left Panel: Frame Navigation */}
        <div className="w-64 bg-white rounded-lg border border-gray-200 p-4 space-y-4">
          <h3 className="font-medium text-gray-900">Frame Navigation</h3>
          
          {/* Frame List */}
          <div className="h-64 overflow-y-auto border border-gray-200 rounded-lg">
            {session.frames.map((frame) => (
              <button
                key={frame.frame_index}
                onClick={() => setCurrentFrameIndex(frame.frame_index)}
                className={`w-full px-3 py-2 text-left text-sm flex items-center justify-between ${
                  frame.frame_index === currentFrameIndex
                    ? 'bg-primary-50 text-primary-700'
                    : 'hover:bg-gray-50'
                }`}
              >
                <span>Frame {frame.frame_index + 1}</span>
                {frame.validation_status === 'validated' && (
                  <Check className="h-4 w-4 text-green-500" />
                )}
                {frame.validation_status === 'corrected' && (
                  <Check className="h-4 w-4 text-blue-500" />
                )}
                {frame.needs_validation && (
                  <span className="w-2 h-2 bg-orange-400 rounded-full" />
                )}
              </button>
            ))}
          </div>
          
          {/* Navigation Buttons */}
          <div className="flex gap-2">
            <button
              onClick={moveToPrevFrame}
              disabled={currentFrameIndex === 0}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
              Prev
            </button>
            <button
              onClick={moveToNextFrame}
              disabled={currentFrameIndex >= session.total_frames - 1}
              className="flex-1 flex items-center justify-center gap-1 px-3 py-2 border rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
          
          <button
            onClick={skipToNextValidation}
            disabled={!needsValidationFrames.find(f => f.frame_index > currentFrameIndex)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 border border-orange-300 text-orange-700 rounded-lg hover:bg-orange-50 disabled:opacity-50"
          >
            <SkipForward className="h-4 w-4" />
            Skip to Next Validation
          </button>
          
          {/* Frame Info */}
          {currentFrame && (
            <div className="text-xs text-gray-500 space-y-1 pt-4 border-t">
              <div>Timestamp: {(currentFrame.timestamp_ms / 1000).toFixed(2)}s</div>
              {currentFrame.confidence_score !== undefined && (
                <div>Confidence: {(currentFrame.confidence_score * 100).toFixed(1)}%</div>
              )}
              <div>Status: {currentFrame.validation_status}</div>
            </div>
          )}
        </div>
        
        {/* Center: Depth Editor */}
        <div className="flex-1 bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-medium text-gray-900">Depth Map Editor</h3>
            
            {/* Toggle Original View */}
            <button
              onClick={() => setShowOriginal(!showOriginal)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm ${
                showOriginal
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <ImageIcon className="h-4 w-4" />
              {showOriginal ? 'Show Depth' : 'Show Original'}
            </button>
          </div>
          
          {showOriginal && originalFrameUrl ? (
            <div className="flex justify-center">
              <img
                src={originalFrameUrl}
                alt="Original frame"
                className="max-w-full rounded-lg shadow"
              />
            </div>
          ) : depthMapData ? (
            <DepthValidationEditor
              initialDepthMap={depthMapData}
              width={depthMapData.width}
              height={depthMapData.height}
              onChange={handleEditorChange}
              onSave={handleEditorSave}
            />
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              Loading depth map...
            </div>
          )}
        </div>
        
        {/* Right Panel: Actions */}
        <div className="w-64 bg-white rounded-lg border border-gray-200 p-4 space-y-4">
          <h3 className="font-medium text-gray-900">Actions</h3>
          
          <button
            onClick={() => validateMutation.mutate()}
            disabled={validateMutation.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {validateMutation.isPending ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Check className="h-5 w-5" />
            )}
            Mark as Validated
          </button>
          
          <p className="text-xs text-gray-500">
            Press Enter to mark the current frame as validated, or Ctrl+Enter to save manual corrections.
          </p>
          
          <div className="pt-4 border-t space-y-2">
            <h4 className="text-sm font-medium text-gray-700">Keyboard Shortcuts</h4>
            <dl className="text-xs text-gray-500 space-y-1">
              <div className="flex justify-between">
                <dt>Previous frame</dt>
                <dd className="font-mono">←</dd>
              </div>
              <div className="flex justify-between">
                <dt>Next frame</dt>
                <dd className="font-mono">→</dd>
              </div>
              <div className="flex justify-between">
                <dt>Skip to validation</dt>
                <dd className="font-mono">Tab</dd>
              </div>
              <div className="flex justify-between">
                <dt>Mark validated</dt>
                <dd className="font-mono">Enter</dd>
              </div>
              <div className="flex justify-between">
                <dt>Save correction</dt>
                <dd className="font-mono">Ctrl+Enter</dd>
              </div>
              <div className="flex justify-between">
                <dt>Toggle original</dt>
                <dd className="font-mono">O</dd>
              </div>
            </dl>
          </div>
          
          {/* Validation Progress */}
          <div className="pt-4 border-t">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Progress</h4>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{
                  width: `${((session.total_frames - session.frames_needing_validation) / session.total_frames) * 100}%`
                }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              {session.total_frames - session.frames_needing_validation} of {session.total_frames} frames validated
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DepthValidationPage;
