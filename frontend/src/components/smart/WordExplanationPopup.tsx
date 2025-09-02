'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { SmartAPI } from './api';
import { WordExplanationResponse } from './types';

interface WordExplanationPopupProps {
  word: string;
  isOpen: boolean;
  onClose: () => void;
  position?: { x: number; y: number };
  currentUser?: string;
  onVocabularyAdded?: () => void; // Dashboard refresh callback
}

export default function WordExplanationPopup({
  word,
  isOpen,
  onClose,
  position: _position = { x: 0, y: 0 }, // Renamed to avoid unused variable warning
  currentUser,
  onVocabularyAdded
}: WordExplanationPopupProps) {
  
  const [explanation, setExplanation] = useState<WordExplanationResponse['data'] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addingToVocabulary, setAddingToVocabulary] = useState(false);
  const [wordStatus, setWordStatus] = useState<string | null>(null); // Kelimenin mevcut durumu
  const [userId, setUserId] = useState<number | null>(null); // Dynamic user ID

  const fetchUserId = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/auth/user-id/${currentUser}`);
      
      if (response.ok) {
        const data = await response.json();
        setUserId(data.user_id);
      } else {
        console.error('User ID alınamadı');
      }
    } catch (error) {
      console.error('User ID fetch error:', error);
    }
  }, [currentUser]);

  const fetchWordExplanation = useCallback(async () => {
    if (!word || !userId) return;
    
    setLoading(true);
    try {
      const result = await SmartAPI.getWordExplanation(word);
      if (result.success) {
        setExplanation(result.data);
      } else {
        console.error('Failed to fetch explanation:', result.error);
      }
    } catch (error) {
      console.error('Error fetching explanation:', error);
    } finally {
      setLoading(false);
    }
  }, [word, userId]);

  const fetchWordStatus = useCallback(async () => {
    if (!word || !userId) return;
    
    try {
      const result = await SmartAPI.getVocabularyStatus(userId, word);
      if (result.success) {
        setWordStatus(result.data?.status || null);
      }
    } catch (error) {
      console.error('Error fetching word status:', error);
    }
  }, [word, userId]);

  useEffect(() => {
    if (isOpen && word && currentUser) {
      setWordStatus(null); // Reset status
      fetchUserId(); // Get user ID first
    }
  }, [isOpen, word, currentUser, fetchUserId]);

  useEffect(() => {
    if (isOpen && word && userId) {
      fetchWordExplanation();
      fetchWordStatus(); // Kelimenin mevcut durumunu da kontrol et
    }
  }, [isOpen, word, userId, fetchWordExplanation, fetchWordStatus]);

  const fetchWordStatusDirect = async () => {
    if (!userId || !word) return;
    
    try {
      // Kullanıcının bu kelimeye sahip olup olmadığını kontrol et
      const response = await fetch(`http://localhost:8000/api/text-analysis/word-status`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId, // Use dynamic user ID
          word: word
        }),
      });

      if (response.ok) {
        const result = await response.json();
        
        if (result.success && result.status) {
          setWordStatus(result.status);
        } else {
          setWordStatus(null); // Kelime henüz eklenmemiş
        }
      } else {
        console.log('[DEBUG] Word status request failed:', response.status);
      }
    } catch (err) {
      console.log('[DEBUG] Word status check failed:', err);
      setWordStatus(null);
    }
  };

  const addToVocabulary = async (status: 'known' | 'unknown' | 'learning' | 'ignore') => {
    console.log('🚀 WordExplanationPopup.addToVocabulary called with status:', status);
    
    if (!userId || !explanation) {
      console.log('❌ Missing userId or explanation:', { userId, explanation });
      return;
    }
    
    setAddingToVocabulary(true);
    try {
      const response = await fetch('http://localhost:8000/api/text-analysis/add-vocabulary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId, // Use dynamic user ID
          word: word,
          translation: explanation.turkish_meaning || '',
          status: status
        }),
      });

      const result = await response.json();
      console.log('📦 WordExplanationPopup - Backend response:', result);
      
      if (result.success) {
        const statusText = status === 'known' ? 'bilinen kelimeler' : 
                          status === 'learning' ? 'öğrenme' : 
                          status === 'unknown' ? 'öğrenme' : 
                          status === 'ignore' ? 'görmezden gelinen kelimeler' : 'bilinmeyen';
                          
        let message = `&quot;${word}&quot; kelimesi ${statusText} listesine eklendi!`;
        // Currently unused variable - kept for future use
        // const _message = message;
        
        // Status'u güncelle
        setWordStatus(status);
        
        if (result.is_new) {
          message += '\n(Yeni kelime eklendi - istatistikler güncellendi)';
        } else {
          message += '\n(Mevcut kelime güncellendi)';
        }
        
        console.log('📝 WordExplanationPopup - Vocabulary result:', result);
        console.log('📝 onVocabularyAdded callback exists?', !!onVocabularyAdded);
        console.log('📝 Should call callback?', result.is_new || result.action);
        
        // Dashboard'u refresh et - hem yeni kelime hem de güncelleme durumunda
        if (onVocabularyAdded && (result.is_new || result.action)) {
          console.log('🔄 Calling onVocabularyAdded callback...');
          try {
            await onVocabularyAdded();
            console.log('✅ onVocabularyAdded callback completed successfully');
          } catch (callbackError) {
            console.error('❌ Error in onVocabularyAdded callback:', callbackError);
          }
        } else {
          console.log('⚠️ Not calling callback - missing callback or conditions not met');
          console.log('  - onVocabularyAdded exists:', !!onVocabularyAdded);
          console.log('  - result.is_new:', result.is_new);
          console.log('  - result.action:', result.action);
        }
        
        // Başarı mesajı artık alert olarak gösterilmiyor - sadece console'da
        onClose();
      } else {
        console.error('Kelime eklenirken hata oluştu.');
      }
    } catch (err) {
      console.error('Bağlantı hatası oluştu:', err);
    } finally {
      setAddingToVocabulary(false);
    }
  };

  if (!isOpen) return null;

  const getDifficultyColor = (level: number) => {
    if (level <= 3) return 'text-green-300 bg-green-900 border border-green-600';
    if (level <= 6) return 'text-yellow-300 bg-yellow-900 border border-yellow-600';
    return 'text-red-300 bg-red-900 border border-red-600';
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
        className="fixed z-50 bg-gray-800 rounded-lg shadow-xl border border-gray-600 max-w-md w-full mx-4"
        style={{
          left: '50%',
          top: '50%',
          transform: 'translate(-50%, -50%)',
          maxHeight: '80vh',
          overflow: 'auto'
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-600">
          <h3 className="text-lg font-semibold text-blue-400">
            📝 Kelime Açıklaması: &quot;{word}&quot;
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-4">
          {loading && (
            <div className="text-center py-6">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-3"></div>
              <p className="text-gray-300">Açıklama getiriliyor...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-6">
              <div className="text-red-400 mb-2">❌ Hata</div>
              <p className="text-gray-300 mb-4">{error}</p>
              <button
                onClick={fetchWordExplanation}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors"
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
                  <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded-full text-xs border border-gray-600">
                    📚 Cache&apos;den
                  </span>
                )}
              </div>

              {/* Main content in gray box like TextAnalysis */}
              <div className="bg-gray-700 p-4 rounded-lg">
                {/* Turkish Meaning */}
                <div className="mb-4">
                  <h4 className="font-medium text-teal-400 mb-2">🇹🇷 Türkçe Anlamı:</h4>
                  <p className="text-white text-lg font-semibold">
                    {explanation.turkish_meaning}
                  </p>
                </div>

                {/* English Example */}
                <div className="mb-4">
                  <h4 className="font-medium text-teal-400 mb-2">🇬🇧 İngilizce Örnek:</h4>
                  <p className="text-gray-200 italic">
                    &quot;{explanation.english_example}&quot;
                  </p>
                </div>

                {/* Turkish Translation */}
                <div>
                  <h4 className="font-medium text-teal-400 mb-2">🔄 Örnek Çevirisi:</h4>
                  <p className="text-gray-300">
                    {explanation.example_translation}
                  </p>
                </div>
              </div>

              {/* Learning Tip */}
              <div className="bg-gradient-to-r from-purple-900 to-pink-900 p-3 rounded-lg border-l-4 border-purple-400">
                <h4 className="font-medium text-purple-300 mb-1">💡 Öğrenme İpucu:</h4>
                <p className="text-gray-300 text-sm">
                  Bu kelimeyi cümlede kullanarak pekiştirin ve benzer anlamdaki kelimelerle karşılaştırın.
                </p>
              </div>

              {/* Timestamp */}
              <div className="text-xs text-gray-500 text-center">
                {new Date(explanation.created_at).toLocaleString('tr-TR')}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-gray-600 bg-gray-750">
          {explanation ? (
            <div className="space-y-3">
              {/* Main action buttons */}
              <div className="flex gap-3">
                <button
                  onClick={() => addToVocabulary('known')}
                  disabled={addingToVocabulary || wordStatus === 'known'}
                  className={`flex-1 px-4 py-2 rounded-lg text-white font-medium transition-colors ${
                    wordStatus === 'known' 
                      ? 'bg-gray-500 cursor-not-allowed' 
                      : 'bg-green-600 hover:bg-green-700 disabled:bg-green-400'
                  }`}
                >
                  {addingToVocabulary ? '⏳' : wordStatus === 'known' ? '✅ Zaten Biliyorum' : '✅ Biliyorum'}
                </button>
                <button
                  onClick={() => addToVocabulary('learning')}
                  disabled={addingToVocabulary || wordStatus === 'learning'}
                  className={`flex-1 px-4 py-2 rounded-lg text-white font-medium transition-colors ${
                    wordStatus === 'learning' 
                      ? 'bg-gray-500 cursor-not-allowed' 
                      : 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400'
                  }`}
                >
                  {addingToVocabulary ? '⏳' : wordStatus === 'learning' ? '📚 Zaten Öğreniyorum' : '📚 Öğreniyorum'}
                </button>
                <button
                  onClick={() => addToVocabulary('unknown')}
                  disabled={addingToVocabulary || wordStatus === 'unknown'}
                  className={`flex-1 px-4 py-2 rounded-lg text-white font-medium transition-colors ${
                    wordStatus === 'unknown' 
                      ? 'bg-gray-500 cursor-not-allowed' 
                      : 'bg-red-600 hover:bg-red-700 disabled:bg-red-400'
                  }`}
                >
                  {addingToVocabulary ? '⏳' : wordStatus === 'unknown' ? '❌ Zaten Bilmiyorum' : '❌ Bilmiyorum'}
                </button>
              </div>
              
              {/* Debug info */}
              {process.env.NODE_ENV === 'development' && (
                <div className="text-xs text-gray-400 text-center">
                  Debug: wordStatus = &quot;{wordStatus}&quot;
                </div>
              )}
              
              {/* Secondary actions */}
              <div className="flex gap-2">
                <button
                  onClick={() => addToVocabulary('ignore')}
                  disabled={addingToVocabulary}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white font-medium transition-colors disabled:bg-gray-500"
                >
                  {addingToVocabulary ? '⏳' : '�️ Görmezden Gel'}
                </button>
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 bg-gray-500 hover:bg-gray-600 rounded-lg text-white font-medium transition-colors"
                >
                  📋 Kapat
                </button>
              </div>
            </div>
          ) : (
            <button
              onClick={onClose}
              className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white font-medium transition-colors"
            >
              Kapat
            </button>
          )}
        </div>
      </div>
    </>
  );
} 