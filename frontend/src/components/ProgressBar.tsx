import { useEffect, useRef } from 'react';

interface ProgressBarProps {
  progress: number;
  stage?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function ProgressBar({ progress, stage, size = 'md' }: ProgressBarProps) {
  const prevProgress = useRef(progress);
  
  useEffect(() => {
    prevProgress.current = progress;
  }, [progress]);

  const clampedProgress = Math.min(100, Math.max(0, progress * 100));
  
  const heightClass = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  }[size];

  return (
    <div className="w-full">
      <div className={`w-full bg-gray-200 rounded-full overflow-hidden ${heightClass}`}>
        <div
          className="bg-primary-600 transition-all duration-300 ease-out rounded-full h-full"
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-500">{stage || 'Processing'}</span>
        <span className="text-xs font-medium text-gray-700">
          {clampedProgress.toFixed(1)}%
        </span>
      </div>
    </div>
  );
}
