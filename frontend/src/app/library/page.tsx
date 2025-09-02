'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import WordExplanationPopup from '../../components/smart/WordExplanationPopup';

interface Transcript {
  id: number;
  video_id?: string;
  video_url?: string;
  video_title?: string;
  channel_name?: string;
  duration?: number;
  language?: string;
  word_count?: number;
  adapted_word_count?: number;
  view_count?: number;
  added_by?: string;
  created_at: string;
  // Web content fields
  title?: string;
  url?: string;
  content_type?: 'youtube' | 'web';
}

interface TranscriptDetail {
  id: number;
  video_id?: string;
  video_url?: string;
  video_title?: string;
  channel_name?: string;
  duration?: number;
  original_text?: string;
  adapted_text?: string;
  language?: string;
  word_count?: number;
  adapted_word_count?: number;
  view_count?: number;
  added_by?: string;
  created_at: string;
  // Web content fields
  title?: string;
  url?: string;
  content?: string;
  content_type?: 'youtube' | 'web';
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
  
  // Word popup state
  const [wordPopup, setWordPopup] = useState<{
    word: string;
    isOpen: boolean;
    position: { x: number; y: number };
  }>({
    word: '',
    isOpen: false,
    position: { x: 0, y: 0 }
  });

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
      console.log('🔄 Starting to fetch content...');
      setLoading(true);
      const token = localStorage.getItem('token');
      console.log('🔑 Token:', token ? 'exists' : 'missing');
      
      // Fetch YouTube transcripts
      const transcriptResponse = await fetch('http://localhost:8000/api/library/transcripts', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      // Fetch web content
      const webContentResponse = await fetch('http://localhost:8000/api/library/web-content', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      let allContent: any[] = [];

      if (transcriptResponse.ok) {
        const transcriptData = await transcriptResponse.json();
        console.log('📺 YouTube transcripts response:', transcriptData);
        const transcripts = transcriptData.data || [];
        // Add content type marker
        transcripts.forEach((transcript: any) => {
          transcript.content_type = 'youtube';
        });
        allContent = [...allContent, ...transcripts];
        console.log('📚 Total content after YouTube:', allContent.length);
      } else {
        console.error('❌ YouTube transcripts fetch failed:', transcriptResponse.status);
      }

      if (webContentResponse.ok) {
        const webData = await webContentResponse.json();
        console.log('🌐 Web content response:', webData);
        const webContents = webData.data || [];
        // Add content type marker
        webContents.forEach((content: any) => {
          content.content_type = 'web';
        });
        allContent = [...allContent, ...webContents];
        console.log('📚 Total content after web:', allContent.length);
      } else {
        console.error('❌ Web content fetch failed:', webContentResponse.status);
      }

      // Sort by created_at descending
      allContent.sort((a: any, b: any) => {
        const dateA = new Date(a.created_at || 0);
        const dateB = new Date(b.created_at || 0);
        return dateB.getTime() - dateA.getTime();
      });

      setTranscripts(allContent);
      
    } catch (error) {
      console.error('Error fetching content:', error);
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

  const fetchTranscriptDetail = async (transcriptId: number, contentType: string = 'youtube') => {
    try {
      const token = localStorage.getItem('token');
      const endpoint = contentType === 'web' 
        ? `http://localhost:8000/api/web-content/${transcriptId}`
        : `http://localhost:8000/api/library/transcript/${transcriptId}`;
        
      const response = await fetch(endpoint, {
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
      const response = await fetch(`http://localhost:8000/api/library/transcript/${selectedTranscript.id}/adapt`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          username: user.username,
          target_unknown_percentage: 10.0
        }),
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

  // Handle word click for explanation popup
  const handleWordClick = (word: string, event: React.MouseEvent) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setWordPopup({
      word: word.toLowerCase().replace(/[^\w]/g, ''), // Clean the word
      isOpen: true,
      position: {
        x: rect.left + window.scrollX,
        y: rect.bottom + window.scrollY + 5
      }
    });
  };

  // Make text clickable for word explanations
  const renderClickableText = (text: string) => {
    // Type check - eğer text string değilse boş string kullan
    const safeText = typeof text === 'string' ? text : '';
    
    if (!safeText || safeText.trim() === '') {
      return <div className="text-gray-500 italic">No text available</div>;
    }
    
    return safeText.split(/(\s+)/).map((part, index) => {
      const isWord = /\w+/.test(part);
      if (isWord) {
        return (
          <span
            key={index}
            className="cursor-pointer hover:bg-blue-100 hover:underline px-1 rounded transition-colors"
            onClick={(e) => handleWordClick(part, e)}
          >
            {part}
          </span>
        );
      }
      return part;
    });
  };

  // ✅ Copy to Clipboard Function
  const copyToClipboard = async (text: string, type: 'original' | 'adapted') => {
    try {
      await navigator.clipboard.writeText(text);
      console.log(`${type} text copied to clipboard!`);
      alert(`${type === 'original' ? 'Original' : 'AI Adapted'} text copied to clipboard!`);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      alert(`${type === 'original' ? 'Original' : 'AI Adapted'} text copied to clipboard!`);
    }
  };

  // ✅ Download Text as PDF Function  
  const downloadTextAsPDF = async (text: string, type: 'original' | 'adapted') => {
    try {
      const response = await fetch('http://localhost:8000/api/text-analysis/simple-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          title: type === 'original' ? 'Original Transcript' : 'AI Adapted Transcript',
          type: type
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${type}_transcript_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        alert(`${type === 'original' ? 'Original' : 'AI'} transcript PDF downloaded!`);
      } else {
        alert('PDF generation failed. Please try again.');
      }
    } catch (error) {
      console.error('PDF download error:', error);
      alert('PDF download failed. Please try again.');
    }
  };

  const displayTranscripts = searchQuery ? searchResults : transcripts;
  
  // Apply filters to transcripts
  const filteredTranscripts = displayTranscripts.filter(transcript => {
    if (filterMinWords > 0 && (transcript.word_count || 0) < filterMinWords) return false;
    if (filterMaxWords > 0 && (transcript.word_count || 0) > filterMaxWords) return false;
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
                        key={`${transcript.content_type || 'youtube'}-${transcript.id}`}
                        onClick={() => fetchTranscriptDetail(transcript.id, transcript.content_type)}
                        className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:shadow-md bg-white ${
                          selectedTranscript?.id === transcript.id 
                            ? 'border-blue-500 bg-blue-50 shadow-md' 
                            : 'border-gray-200 hover:border-blue-300'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-medium text-gray-900 line-clamp-2 text-sm">
                                {transcript.video_title || transcript.title}
                              </h3>
                              {/* Source label */}
                              <span className={`px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800`}>
                                {transcript.content_type === 'youtube' ? 'YouTube' : ((transcript.url || '').includes('medium.com') ? 'Medium' : ((transcript.url || '').includes('wikipedia.org') ? 'Wikipedia' : 'Web'))}
                              </span>
                            </div>
                            <p className="text-xs text-gray-600 mt-1">
                              {transcript.channel_name || transcript.url}
                            </p>
                          </div>
                          <div className="ml-2 flex flex-col items-end">
                            <div className="flex gap-2">
                              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                                {transcript.duration ? formatDuration(transcript.duration) : 'Web Article'}
                              </span>
                              {/* CEFR badge if available */}
                              {'cefr_level' in transcript && (
                                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                                  { (transcript as any).cefr_level || 'N/A' }
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between mt-3 text-xs">
                          <div className="flex items-center space-x-2">
                            <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full">
                              📝 {transcript.word_count || 0}
                            </span>
                            <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full">
                              👁️ {transcript.view_count || 0}
                            </span>
                          </div>
                          <span className="text-gray-400 text-xs">
                            {transcript.added_by || 'Unknown'}
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
                    {selectedTranscript.video_title || selectedTranscript.title}
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {selectedTranscript.channel_name || selectedTranscript.url} 
                    {selectedTranscript.duration && ` • ${formatDuration(selectedTranscript.duration)}`}
                  </p>
                  <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                    {selectedTranscript.view_count && <span>👁️ {selectedTranscript.view_count} görüntülenme</span>}
                    <span>📝 {selectedTranscript.word_count || 0} kelime</span>
                    <span>🤖 {adaptedWordCount || selectedTranscript.adapted_word_count || 0} kelime (AI)</span>
                  </div>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
                  {/* Original Transcript */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900">📄 Orijinal Transcript</h3>
                      <div className="flex gap-2">
                        <div className="relative group">
                          <button
                            onClick={() => copyToClipboard(selectedTranscript.original_text || selectedTranscript.content || '', 'original')}
                            className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors duration-200 text-sm"
                          >
                            📋
                          </button>
                          <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                            Copy
                          </div>
                        </div>
                        <div className="relative group">
                          <button
                            onClick={() => downloadTextAsPDF(selectedTranscript.original_text || selectedTranscript.content || '', 'original')}
                            className="bg-red-600 hover:bg-red-700 text-white p-2 rounded-lg transition-colors duration-200 text-sm"
                          >
                            📄
                          </button>
                          <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                            PDF
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      <div className="text-sm text-gray-700 whitespace-pre-wrap">
                        {renderClickableText(selectedTranscript.original_text || selectedTranscript.content || '')}
                      </div>
                    </div>
                  </div>

                  {/* AI Adapted Transcript */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900">🤖 AI Adaptasyonu</h3>
                      <div className="flex items-center gap-2">
                        {(adaptedText || selectedTranscript.adapted_text) && (
                          <div className="flex gap-2">
                            <div className="relative group">
                              <button
                                onClick={() => copyToClipboard(adaptedText || selectedTranscript.adapted_text || '', 'adapted')}
                                className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors duration-200 text-sm"
                              >
                                📋
                              </button>
                              <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                                Copy
                              </div>
                            </div>
                            <div className="relative group">
                              <button
                                onClick={() => downloadTextAsPDF(adaptedText || selectedTranscript.adapted_text || '', 'adapted')}
                                className="bg-red-600 hover:bg-red-700 text-white p-2 rounded-lg transition-colors duration-200 text-sm"
                              >
                                📄
                              </button>
                              <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                                PDF
                              </div>
                            </div>
                          </div>
                        )}
                        <button
                          onClick={adaptTranscriptForUser}
                          disabled={isAdapting}
                          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors text-sm"
                        >
                          {isAdapting ? 'Adaptasyon yapılıyor...' : 'Seviyeme Göre Adapt Et'}
                        </button>
                      </div>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                      <div className="text-sm text-gray-700 whitespace-pre-wrap">
                        {adaptedText || selectedTranscript.adapted_text ? 
                          renderClickableText(adaptedText || selectedTranscript.adapted_text || '') :
                          'AI adaptasyonu henüz yapılmamış. "Seviyeme Göre Adapt Et" butonuna tıklayın.'
                        }
                      </div>
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
      
      {/* Word Explanation Popup */}
      <WordExplanationPopup
        word={wordPopup.word}
        isOpen={wordPopup.isOpen}
        onClose={() => setWordPopup(prev => ({ ...prev, isOpen: false }))}
        position={wordPopup.position}
        currentUser={user?.username}
      />
    </div>
  );
}
 