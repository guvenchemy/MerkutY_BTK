'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Transcript {
  id: number;
  video_id: string;
  video_url: string;
  video_title: string;
  channel_name: string;
  duration: number;
  language: string;
  word_count: number;
  adapted_word_count: number;
  view_count: number;
  added_by: string;
  created_at: string;
}

interface TranscriptDetail {
  id: number;
  video_id: string;
  video_url: string;
  video_title: string;
  channel_name: string;
  duration: number;
  original_text: string;
  adapted_text: string;
  language: string;
  word_count: number;
  adapted_word_count: number;
  view_count: number;
  added_by: string;
  created_at: string;
}

export default function LibraryPage() {
  const router = useRouter();
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [selectedTranscript, setSelectedTranscript] = useState<TranscriptDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Transcript[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [filterMinWords, setFilterMinWords] = useState<number>(0);
  const [filterMaxWords, setFilterMaxWords] = useState<number>(0);
  const [user, setUser] = useState<any>(null);
  const [adaptedText, setAdaptedText] = useState<string>('');
  const [isAdapting, setIsAdapting] = useState(false);
  const [adaptedWordCount, setAdaptedWordCount] = useState<number>(0);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (!token || !userData) {
      router.push('/login');
      return;
    }

    try {
      const user = JSON.parse(userData);
      setUser(user);
    } catch (error) {
      console.error('Error parsing user data:', error);
      router.push('/login');
      return;
    }

    // Clear state on refresh
    setTranscripts([]);
    setSelectedTranscript(null);
    setAdaptedText('');
    setAdaptedWordCount(0);
    setSearchQuery('');
    setSearchResults([]);
    setIsSearching(false);
    setFilterMinWords(0);
    setFilterMaxWords(0);
    
    fetchTranscripts();
  }, [router]);

  const fetchTranscripts = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/library/transcripts', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTranscripts(data.data || []);
      } else {
        console.error('Failed to fetch transcripts');
      }
    } catch (error) {
      console.error('Error fetching transcripts:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchTranscripts = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        q: searchQuery,
        min_words: filterMinWords.toString(),
        max_words: filterMaxWords.toString()
      });
      
      const response = await fetch(`http://localhost:8000/api/library/search?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.data || []);
      } else {
        console.error('Failed to search transcripts');
      }
    } catch (error) {
      console.error('Error searching transcripts:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const fetchTranscriptDetail = async (transcriptId: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/library/transcript/${transcriptId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSelectedTranscript(data.data);
        setAdaptedText(''); // Reset adapted text when selecting new transcript
      } else {
        console.error('Failed to fetch transcript detail');
      }
    } catch (error) {
      console.error('Error fetching transcript detail:', error);
    }
  };

  const adaptTranscriptForUser = async () => {
    if (!selectedTranscript || !user) return;
    
    // Check if we already have cached adaptation for this transcript
    const cacheKey = `adapted_transcript_${selectedTranscript.id}_${user.username}`;
    const cachedAdaptation = localStorage.getItem(cacheKey);
    
    if (cachedAdaptation) {
      try {
        const cached = JSON.parse(cachedAdaptation);
        setAdaptedText(cached.adapted_text);
        setAdaptedWordCount(cached.adapted_word_count);
        return;
      } catch (error) {
        console.error('Error parsing cached adaptation:', error);
      }
    }
    
    setIsAdapting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/library/transcript/${selectedTranscript.id}/adapt?username=${user.username}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAdaptedText(data.data.adapted_text);
          setAdaptedWordCount(data.data.adapted_word_count || 0);
          
          // Cache the adaptation
          localStorage.setItem(cacheKey, JSON.stringify({
            adapted_text: data.data.adapted_text,
            adapted_word_count: data.data.adapted_word_count || 0,
            timestamp: Date.now()
          }));
          
          // Also save to main page cache
          localStorage.setItem('adaptedText', data.data.adapted_text);
        } else {
          console.error('Failed to adapt transcript');
        }
      } else {
        console.error('Failed to adapt transcript');
      }
    } catch (error) {
      console.error('Error adapting transcript:', error);
    } finally {
      setIsAdapting(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  const displayTranscripts = searchQuery ? searchResults : transcripts;
  
  // Apply filters to transcripts
  const filteredTranscripts = displayTranscripts.filter(transcript => {
    if (filterMinWords > 0 && transcript.word_count < filterMinWords) return false;
    if (filterMaxWords > 0 && transcript.word_count > filterMaxWords) return false;
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Kütüphane yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">📚 Transcript Kütüphanesi</h1>
              <button
                onClick={() => router.push('/')}
                className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 transition-colors"
              >
                ← Ana Sayfa
              </button>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Hoş geldin, {user?.username}
              </span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm font-medium text-red-600 hover:text-red-800 transition-colors"
              >
                Çıkış Yap
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="mb-8">
          <div className="flex space-x-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Transcript ara... (başlık, kanal, içerik)"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={searchTranscripts}
              disabled={isSearching}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSearching ? 'Aranıyor...' : 'Ara'}
            </button>
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setSearchResults([]);
                }}
                className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                Temizle
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Transcript List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">
                  {searchQuery ? 'Arama Sonuçları' : 'Tüm Transcriptler'}
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  {filteredTranscripts.length} transcript bulundu
                </p>
                
                {/* Search and Filter Section */}
                <div className="mt-4 space-y-3">
                  {/* Search */}
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Video başlığı, kanal adı veya anahtar kelime ara..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                    <button
                      onClick={searchTranscripts}
                      disabled={isSearching}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm"
                    >
                      {isSearching ? 'Aranıyor...' : 'Ara'}
                    </button>
                  </div>
                  
                  {/* Filters */}
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">🔍 Kelime Sayısı Filtreleme</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-2">Min Kelime</label>
                        <input
                          type="number"
                          value={filterMinWords || ''}
                          onChange={(e) => setFilterMinWords(Number(e.target.value) || 0)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                          placeholder="0"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-2">Max Kelime</label>
                        <input
                          type="number"
                          value={filterMaxWords || ''}
                          onChange={(e) => setFilterMaxWords(Number(e.target.value) || 0)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                          placeholder="0"
                        />
                      </div>
                    </div>
                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={() => {
                          setFilterMinWords(0);
                          setFilterMaxWords(0);
                        }}
                        className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                      >
                        Filtreleri Temizle
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div className="max-h-96 overflow-y-auto">
                {displayTranscripts.length === 0 ? (
                  <div className="text-center text-gray-500 py-8">
                    {searchQuery ? 'Arama sonucu bulunamadı.' : 'Henüz transcript yok.'}
                  </div>
                ) : (
                  <div className="p-4 space-y-3">
                    {filteredTranscripts.map((transcript) => (
                      <div
                        key={transcript.id}
                        onClick={() => fetchTranscriptDetail(transcript.id)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:shadow-md bg-white ${
                          selectedTranscript?.id === transcript.id 
                            ? 'border-blue-500 bg-blue-50 shadow-md' 
                            : 'border-gray-200 hover:border-blue-300'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900 line-clamp-2 text-sm">
                              {transcript.video_title}
                            </h3>
                            <p className="text-xs text-gray-600 mt-1">
                              {transcript.channel_name}
                            </p>
                          </div>
                          <div className="ml-2 flex flex-col items-end">
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                              {formatDuration(transcript.duration)}
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between mt-3 text-xs">
                          <div className="flex items-center space-x-2">
                            <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full">
                              📝 {transcript.word_count}
                            </span>
                            <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                              👁️ {transcript.view_count}
                            </span>
                          </div>
                          <span className="text-gray-400 text-xs">
                            {transcript.added_by}
                          </span>
                        </div>
                        
                        <div className="mt-2 text-xs text-gray-400 border-t pt-2">
                          {formatDate(transcript.created_at)}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Transcript Detail */}
          <div className="lg:col-span-2">
            {selectedTranscript ? (
              <div className="bg-white rounded-lg shadow-sm border">
                <div className="p-6 border-b">
                  <h2 className="text-xl font-semibold text-gray-900">
                    {selectedTranscript.video_title}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedTranscript.channel_name} • {formatDuration(selectedTranscript.duration)}
                  </p>
                  <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                    <span>👁️ {selectedTranscript.view_count} görüntülenme</span>
                    <span>📝 {selectedTranscript.word_count} kelime</span>
                    <span>🤖 {adaptedWordCount || selectedTranscript.adapted_word_count || 0} kelime (AI)</span>
                  </div>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
                  {/* Original Transcript */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">📄 Orijinal Transcript</h3>
                    <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {selectedTranscript.original_text}
                      </p>
                    </div>
                  </div>

                  {/* AI Adapted Transcript */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900">🤖 AI Adaptasyonu</h3>
                      <button
                        onClick={adaptTranscriptForUser}
                        disabled={isAdapting}
                        className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors text-sm"
                      >
                        {isAdapting ? 'Adaptasyon yapılıyor...' : 'Seviyeme Göre Adapt Et'}
                      </button>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      <p className="text-sm text-gray-700 whitespace-pre-wrap">
                        {adaptedText || selectedTranscript.adapted_text || 'AI adaptasyonu henüz yapılmamış. "Seviyeme Göre Adapt Et" butonuna tıklayın.'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                <div className="text-6xl mb-4">📚</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Transcript Seçin
                </h3>
                <p className="text-gray-600">
                  Sol taraftan bir transcript seçerek detaylarını görüntüleyin.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
 