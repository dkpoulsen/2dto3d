import { Upload } from 'lucide-react';
import { useCallback } from 'react';

interface FileDropZoneProps {
  onFilesSelected: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  disabled?: boolean;
}

export function FileDropZone({
  onFilesSelected,
  accept = 'video/*',
  multiple = true,
  disabled = false,
}: FileDropZoneProps) {
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (disabled) return;
      
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        onFilesSelected(multiple ? files : [files[0]]);
      }
    },
    [disabled, multiple, onFilesSelected]
  );

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length > 0) {
        onFilesSelected(multiple ? files : [files[0]]);
      }
    },
    [multiple, onFilesSelected]
  );

  return (
    <div
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
        transition-colors duration-200
        ${disabled
          ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
          : 'border-gray-300 hover:border-primary-400 hover:bg-primary-50'
        }
      `}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
    >
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={handleFileInput}
        disabled={disabled}
        className="hidden"
        id="file-upload"
      />
      <label htmlFor="file-upload" className="cursor-pointer">
        <Upload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="mt-2 text-sm text-gray-600">
          <span className="font-medium text-primary-600 hover:text-primary-500">
            Click to upload
          </span>{' '}
          or drag and drop
        </p>
        <p className="mt-1 text-xs text-gray-500">
          MP4, AVI, MOV, MKV, WebM up to 500MB
        </p>
      </label>
    </div>
  );
}
