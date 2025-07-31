'use client';

import { useState } from 'react';

interface VocabularyUploadProps {
  username: string;
  onUploadSuccess: () => void;
}

export default function VocabularyUpload({ username, onUploadSuccess }: VocabularyUploadProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      setError('Please upload an Excel file (.xlsx or .xls)');
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('username', username);

      const response = await fetch('http://localhost:8000/api/vocabulary/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setUploadResult(
        `Successfully processed ${data.words_processed} words, added ${data.words_added} new words to your vocabulary. New level: ${data.user_level.level}`
      );
      onUploadSuccess();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsUploading(false);
      // Reset file input
      event.target.value = '';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 mb-6">
      <h3 className="text-lg font-bold text-teal-400 mb-3">📚 Upload Your Vocabulary</h3>
      
      <div className="space-y-4">
        <div>
          <label htmlFor="vocabulary-file" className="block text-sm text-gray-300 mb-2">
            Upload Excel file with your known words (single column: "words")
          </label>
          <input
            id="vocabulary-file"
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileUpload}
            disabled={isUploading}
            className="block w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-teal-600 file:text-white hover:file:bg-teal-700 disabled:opacity-50"
          />
        </div>

        {isUploading && (
          <div className="flex items-center gap-2 text-blue-400">
            <div className="animate-spin text-xl">⏳</div>
            <span>Processing vocabulary...</span>
          </div>
        )}

        {uploadResult && (
          <div className="bg-green-800 border border-green-600 text-green-200 px-4 py-3 rounded">
            ✅ {uploadResult}
          </div>
        )}

        {error && (
          <div className="bg-red-800 border border-red-600 text-red-200 px-4 py-3 rounded">
            ❌ {error}
          </div>
        )}

        <div className="text-xs text-gray-400">
          💡 <strong>Excel Format:</strong> Create a single column with header "words" and list your known words below.
        </div>
      </div>
    </div>
  );
} 