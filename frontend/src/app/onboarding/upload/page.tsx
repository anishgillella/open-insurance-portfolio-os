'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/primitives';
import { Select } from '@/components/primitives/Select';
import { FileUpload } from '@/components/primitives/FileUpload';
import { Button } from '@/components/primitives/Button';
import { useOnboarding } from '@/lib/onboarding-context';

const documentTypeOptions = [
  { value: 'policy', label: 'Policy' },
  { value: 'certificate', label: 'Certificate of Insurance' },
  { value: 'endorsement', label: 'Endorsement' },
  { value: 'declaration', label: 'Declaration Page' },
  { value: 'other', label: 'Other' },
];

export default function UploadPolicyPage() {
  const router = useRouter();
  const { state, updateData, completeStep } = useOnboarding();
  const [isLoading, setIsLoading] = useState(false);

  const [documentType, setDocumentType] = useState(
    state.data.documentType || 'policy'
  );
  const [files, setFiles] = useState<File[]>(state.data.uploadedFiles || []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Save to context
    updateData({
      documentType,
      uploadedFiles: files,
    });
    completeStep('upload');

    // Navigate to plan selection
    router.push('/onboarding/plan');

    setIsLoading(false);
  };

  const handleSkip = () => {
    completeStep('upload');
    router.push('/onboarding/plan');
  };

  return (
    <Card variant="elevated" padding="lg" className="w-full">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">
          Upload your first policy
        </h1>
        <p className="text-[var(--color-text-muted)] mt-2">
          Upload your insurance policy documents to get started.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <Select
          label="Select Document Type"
          options={documentTypeOptions}
          value={documentType}
          onChange={setDocumentType}
        />

        <FileUpload
          onFilesChange={setFiles}
          accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
          multiple
          maxSize={10}
        />

        <div className="space-y-3">
          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            loading={isLoading}
          >
            Next
          </Button>

          <button
            type="button"
            onClick={handleSkip}
            className="w-full text-center text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors py-2"
          >
            Skip
          </button>
        </div>
      </form>
    </Card>
  );
}
