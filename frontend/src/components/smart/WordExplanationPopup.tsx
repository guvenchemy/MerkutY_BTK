'use client';

import React, { useState, useEffect } from 'react';
import { SmartAPI } from './api';
import { WordExplanationResponse } from './types';

interface WordExplanationPopupProps {
  word: string;
  isOpen: boolean;
  onClose: () => void;
  position?: { x: number; y: number };
}

export default function WordExplanationPopup({
  word,
  isOpen,
  onClose,
  position = { x: 0, y: 0 }
}: WordExplanationPopupProps) {
  const [explanation, setExplanation] = useState<WordExplanationResponse['data'] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && word) {
      fetchWordExplanation();
    }
  }, [isOpen, word]);

  const fetchWordExplanation = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await SmartAPI.getWordExplanation(word);
      
      if (response.success) {
        setExplanation(response.data);
      } else {
        setError(response.error || 'Açıklama alınamadı');
      }
    } catch (err) {
      setError('Bağlantı hatası');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const getDifficultyColor = (level: number) => {
    if (level <= 3) return 'text-green-600 bg-green-50';
    if (level <= 6) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getDifficultyText = (level: number) => {
    if (level <= 3) return 'Kolay';
    if (level <= 6) return 'Orta';
    return 'Zor';
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />
      
      {/* Popup */}
      <div 
        className="fixed z-50 bg-white rounded-lg shadow-xl border border-gray-200 max-w-md w-full mx-4"
        style={{
          left: Math.min(position.x, window.innerWidth - 400),
          top: Math.min(position.y, window.innerHeight - 300),
          maxHeight: '80vh',
          overflow: 'auto'
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800">
            "{word}"
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-gray-600">Açıklama getiriliyor...</span>
            </div>
          )}

          {error && (
            <div className="text-center py-8">
              <div className="text-red-500 mb-2">❌ Hata</div>
              <p className="text-gray-600">{error}</p>
              <button
                onClick={fetchWordExplanation}
                className="mt-3 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              >
                Tekrar Dene
              </button>
            </div>
          )}

          {explanation && !loading && (
            <div className="space-y-4">
              {/* Difficulty Badge */}
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(explanation.difficulty_level)}`}>
                  {getDifficultyText(explanation.difficulty_level)} (Level {explanation.difficulty_level})
                </span>
                {explanation.from_cache && (
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                    📚 Cache'den
                  </span>
                )}
              </div>

              {/* Turkish Meaning */}
              <div>
                <h4 className="font-medium text-gray-700 mb-1">🇹🇷 Türkçe Anlamı:</h4>
                <p className="text-gray-800 bg-blue-50 p-3 rounded-lg">
                  {explanation.turkish_meaning}
                </p>
              </div>

              {/* English Example */}
              <div>
                <h4 className="font-medium text-gray-700 mb-1">🇬🇧 İngilizce Örnek:</h4>
                <p className="text-gray-800 bg-green-50 p-3 rounded-lg italic">
                  "{explanation.english_example}"
                </p>
              </div>

              {/* Turkish Translation */}
              <div>
                <h4 className="font-medium text-gray-700 mb-1">🔄 Örnek Çevirisi:</h4>
                <p className="text-gray-800 bg-yellow-50 p-3 rounded-lg">
                  {explanation.example_translation}
                </p>
              </div>

              {/* Learning Tip */}
              <div className="bg-gradient-to-r from-purple-50 to-pink-50 p-3 rounded-lg border-l-4 border-purple-400">
                <h4 className="font-medium text-purple-700 mb-1">💡 Öğrenme İpucu:</h4>
                <p className="text-gray-700 text-sm">
                  Bu kelimeyi cümlede kullanarak pekiştirin ve benzer anlamdaki kelimelerle karşılaştırın.
                </p>
              </div>

              {/* Timestamp */}
              <div className="text-xs text-gray-400 text-center">
                {new Date(explanation.created_at).toLocaleString('tr-TR')}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
            >
              Kapat
            </button>
            {explanation && (
              <button
                onClick={() => {
                  // TODO: Add to user's vocabulary for practice
                  console.log('Add to vocabulary:', word);
                }}
                className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              >
                📚 Kelime Listeme Ekle
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
} 