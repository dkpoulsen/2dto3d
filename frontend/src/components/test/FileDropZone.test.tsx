import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { FileDropZone } from '../FileDropZone';

describe('FileDropZone', () => {
  it('should render upload instructions', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} />);
    expect(screen.getByText('Click to upload')).toBeInTheDocument();
    expect(screen.getByText(/or drag and drop/)).toBeInTheDocument();
  });

  it('should render supported file types', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} />);
    expect(screen.getByText(/MP4, AVI, MOV, MKV, WebM/)).toBeInTheDocument();
  });

  it('should have a file input element', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} />);
    const input = document.querySelector('input[type="file"]');
    expect(input).toBeInTheDocument();
  });

  it('should accept multiple files by default', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.multiple).toBe(true);
  });

  it('should accept single file when multiple is false', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} multiple={false} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.multiple).toBe(false);
  });

  it('should accept video files by default', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.accept).toBe('video/*');
  });

  it('should accept custom file types', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} accept="image/*" />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.accept).toBe('image/*');
  });

  it('should call onFilesSelected when files are selected via input', async () => {
    const user = userEvent.setup();
    const onFilesSelected = vi.fn();
    render(<FileDropZone onFilesSelected={onFilesSelected} />);

    const file = new File(['test content'], 'test.mp4', { type: 'video/mp4' });
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    await user.upload(input, file);

    expect(onFilesSelected).toHaveBeenCalledWith([file]);
  });

  it('should handle drag over event', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} />);
    const dropZone = screen.getByText('Click to upload').closest('div')!;
    
    fireEvent.dragOver(dropZone);
    // Should not throw error
  });

  it('should be disabled when disabled prop is true', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} disabled />);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });

  it('should not call onFilesSelected when disabled and dropping', () => {
    const onFilesSelected = vi.fn();
    render(<FileDropZone onFilesSelected={onFilesSelected} disabled />);
    
    const dropZone = screen.getByText('Click to upload').closest('div')!;
    const file = new File(['test'], 'test.mp4', { type: 'video/mp4' });
    
    fireEvent.drop(dropZone, {
      dataTransfer: {
        files: [file],
      },
    });

    expect(onFilesSelected).not.toHaveBeenCalled();
  });

  it('should have cursor-not-allowed when disabled', () => {
    render(<FileDropZone onFilesSelected={vi.fn()} disabled />);
    const dropZone = screen.getByText('Click to upload').closest('div')!;
    expect(dropZone.className).toContain('cursor-not-allowed');
  });
});
