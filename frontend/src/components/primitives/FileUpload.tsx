'use client';

import { forwardRef, useState } from 'react';
import { cn } from '@/lib/utils';
import { Upload, X, FileText, ImageIcon, File } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface FileUploadProps {
  onFilesChange: (files: File[]) => void;
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // in MB
  label?: string;
  error?: string;
  disabled?: boolean;
  className?: string;
}

const FileUpload = forwardRef<HTMLDivElement, FileUploadProps>(
  (
    {
      onFilesChange,
      accept = '.pdf,.doc,.docx,.png,.jpg,.jpeg',
      multiple = false,
      maxSize = 10,
      label,
      error,
      disabled,
      className,
    },
    ref
  ) => {
    const [isDragging, setIsDragging] = useState(false);
    const [files, setFiles] = useState<File[]>([]);
    const [uploadError, setUploadError] = useState<string | null>(null);

    const validateFile = (file: File): boolean => {
      if (file.size > maxSize * 1024 * 1024) {
        setUploadError(`File size must be less than ${maxSize}MB`);
        return false;
      }
      setUploadError(null);
      return true;
    };

    const handleFiles = (newFiles: FileList | null) => {
      if (!newFiles) return;

      const validFiles: File[] = [];
      Array.from(newFiles).forEach((file) => {
        if (validateFile(file)) {
          validFiles.push(file);
        }
      });

      if (validFiles.length > 0) {
        const updatedFiles = multiple ? [...files, ...validFiles] : validFiles;
        setFiles(updatedFiles);
        onFilesChange(updatedFiles);
      }
    };

    const handleDragOver = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (!disabled) {
        handleFiles(e.dataTransfer.files);
      }
    };

    const removeFile = (index: number) => {
      const updatedFiles = files.filter((_, i) => i !== index);
      setFiles(updatedFiles);
      onFilesChange(updatedFiles);
    };

    const getFileIcon = (file: File) => {
      if (file.type.startsWith('image/')) return <ImageIcon size={20} aria-hidden="true" />;
      if (file.type === 'application/pdf') return <FileText size={20} aria-hidden="true" />;
      return <File size={20} aria-hidden="true" />;
    };

    const formatFileSize = (bytes: number) => {
      if (bytes < 1024) return `${bytes} B`;
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    return (
      <div ref={ref} className={cn('w-full', className)}>
        {label && (
          <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1.5">
            {label}
          </label>
        )}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            'relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200',
            isDragging
              ? 'border-[var(--color-primary-500)] bg-[var(--color-primary-50)]'
              : 'border-[var(--color-border-default)] hover:border-[var(--color-primary-300)] bg-[var(--color-surface)]',
            disabled && 'opacity-50 cursor-not-allowed',
            error && 'border-[var(--color-critical-500)]'
          )}
        >
          <input
            type="file"
            accept={accept}
            multiple={multiple}
            disabled={disabled}
            onChange={(e) => handleFiles(e.target.files)}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
          />
          <div className="flex flex-col items-center gap-3">
            <div
              className={cn(
                'w-12 h-12 rounded-full flex items-center justify-center',
                isDragging
                  ? 'bg-[var(--color-primary-500)] text-white'
                  : 'bg-[var(--color-surface-sunken)] text-[var(--color-text-muted)]'
              )}
            >
              <Upload size={24} />
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                Drag & drop or{' '}
                <span className="text-[var(--color-primary-500)]">choose files</span> to
                upload
              </p>
              <p className="text-xs text-[var(--color-text-muted)] mt-1">
                PDF, DOC, PNG, JPG up to {maxSize}MB
              </p>
            </div>
          </div>
        </div>

        {(error || uploadError) && (
          <p className="mt-1.5 text-sm text-[var(--color-critical-500)]">
            {error || uploadError}
          </p>
        )}

        <AnimatePresence>
          {files.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-4 space-y-2"
            >
              {files.map((file, index) => (
                <motion.div
                  key={`${file.name}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="flex items-center gap-3 p-3 bg-[var(--color-surface-sunken)] rounded-lg"
                >
                  <div className="text-[var(--color-text-muted)]">
                    {getFileIcon(file)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-[var(--color-text-muted)]">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeFile(index)}
                    className="p-1 rounded-full hover:bg-[var(--color-surface)] text-[var(--color-text-muted)] hover:text-[var(--color-critical-500)] transition-colors"
                  >
                    <X size={16} />
                  </button>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

FileUpload.displayName = 'FileUpload';

export { FileUpload };
