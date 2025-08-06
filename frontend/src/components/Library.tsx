import React, { useState, useEffect } from 'react';
import WordExplanationPopup from './smart/WordExplanationPopup';

const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

// Transcript tipi - database schema'ya uygun
interface Transcript {
  id: number;
  video_id: string;
  video_title: string;
  channel_name: string;
  duration?: number;
  original_text?: string;
  adapted_text?: string;
  language: string;
  word_count: number;
  adapted_word_count?: number;
  view_count: number;
  added_by: string;
  created_at?: string;
  content_type?: 'youtube' | 'web'; // İçerik türü
  // CEFR Level fields (NEW)
  cefr_level?: string; // A1, A2, B1, B2, C1, C2
  level_confidence?: number; // 0-100%
  level_analysis?: string; // AI analysis details
  level_analyzed_at?: string; // When level was determined
}

// AI ile text level analizi yapan fonksiyon
const analyzeTextLevel = async (text: string): Promise<{ level: string; category: string }> => {
  try {
    // Basit kelime sayısı ve karmaşıklık analizi
    const words = text.split(' ').length;
    const sentences = text.split(/[.!?]+/).length;
    const avgWordsPerSentence = words / sentences;
    
    // Karmaşık kelime kontrolü (basit heuristic)
    const complexWords = text.match(/\b\w{8,}\b/g)?.length || 0;
    const complexityRatio = complexWords / words;
    
    // Level belirleme
    let level = 'A1';
    if (words > 200 && avgWordsPerSentence > 10) level = 'A2';
    if (words > 300 && avgWordsPerSentence > 12) level = 'B1';
    if (words > 400 && avgWordsPerSentence > 15) level = 'B2';
    if (words > 500 && complexityRatio > 0.1) level = 'C1';
    if (words > 600 && complexityRatio > 0.15) level = 'C2';
    
    // Kategori belirleme (basit heuristic)
    let category = 'General';
    if (text.toLowerCase().includes('technology') || text.toLowerCase().includes('computer')) category = 'Technology';
    if (text.toLowerCase().includes('science') || text.toLowerCase().includes('research')) category = 'Science';
    if (text.toLowerCase().includes('story') || text.toLowerCase().includes('character')) category = 'Fiction';
    if (text.toLowerCase().includes('news') || text.toLowerCase().includes('report')) category = 'News';
    if (text.toLowerCase().includes('business') || text.toLowerCase().includes('company')) category = 'Business';
    
    return { level, category };
  } catch (error) {
    console.error('Error analyzing text level:', error);
    return { level: 'A1', category: 'General' };
  }
};

// Gerçek AI adaptation fonksiyonu
const adaptTextWithAI = async (transcriptId: number, username: string, contentType: string = 'youtube'): Promise<string> => {
  try {
    let endpoint, body;
    
    if (contentType === 'web') {
      // Web content için direkt text adaptation kullan
      endpoint = 'http://localhost:8000/api/adaptation/adapt';
      
      // Önce web content'in metnini al
      const contentResponse = await fetch(`http://localhost:8000/api/web-content/${transcriptId}`);
      if (!contentResponse.ok) throw new Error('Web content bulunamadı');
      
      const contentData = await contentResponse.json();
      if (!contentData.success) throw new Error('Web content alınamadı');
      
      body = JSON.stringify({
        text: contentData.data.content,
        username: username,
        target_unknown_percentage: 10.0
      });
    } else {
      // YouTube transcript için eski method
      endpoint = `http://localhost:8000/api/library/transcript/${transcriptId}/adapt`;
      body = JSON.stringify({
        username: username,
        target_unknown_percentage: 10.0
      });
    }
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: body,
    });

    if (response.ok) {
      const data = await response.json();
      console.log('[DEBUG] Adaptation response:', data);
      
      if (contentType === 'web') {
        // Web content için direkt response yapısı
        if (data.success && data.adapted_text) {
          return data.adapted_text;
        } else {
          throw new Error(data.error || 'Web content adaptation failed');
        }
      } else {
        // YouTube content için wrapped response yapısı
        if (data.success && data.data) {
          return data.data.adapted_text || data.data.text;
        } else {
          throw new Error(data.error || 'YouTube adaptation failed');
        }
      }
    } else {
      throw new Error('Network error during adaptation');
    }
  } catch (error) {
    console.error('Error adapting text:', error);
    throw error;
  }
};

const PAGE_SIZE = 5;

interface LibraryProps {
  currentUser: string;
  userLevel: string;
}

const Library = ({ currentUser, userLevel }: LibraryProps) => {
  // State
  const [activeTab, setActiveTab] = useState<'library' | 'discover'>('library');
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [discoverContent, setDiscoverContent] = useState<Transcript[]>([]);
  const [discoverTotal, setDiscoverTotal] = useState(0);
  const [libraryTotal, setLibraryTotal] = useState(0);
  const [selectedTranscript, setSelectedTranscript] = useState<Transcript | null>(null);
  const [notification, setNotification] = useState<{type: 'success' | 'error', message: string} | null>(null);
  const [adaptedText, setAdaptedText] = useState('');
  const [filter, setFilter] = useState({ 
    channel: '', 
    keyword: '', 
    minWords: '', 
    maxWords: '',
    cefrLevel: '' // CEFR level filter
  });
  const [page, setPage] = useState(1);
  const [discoverPage, setDiscoverPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [adaptationLoading, setAdaptationLoading] = useState(false);
  
  // Word explanation popup state
  const [wordPopup, setWordPopup] = useState<{
    word: string;
    isOpen: boolean;
    position: { x: number; y: number };
  }>({
    word: '',
    isOpen: false,
    position: { x: 0, y: 0 }
  });

  // Handle word click for explanation
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

  // Close word popup
  const closeWordPopup = () => {
    setWordPopup(prev => ({ ...prev, isOpen: false }));
  };

  // Make text clickable for word explanations
  const renderClickableText = (text: string) => {
    return text.split(/(\s+)/).map((part, index) => {
      const isWord = /\w+/.test(part);
      if (isWord) {
        return (
          <span
            key={index}
            className="cursor-pointer hover:bg-blue-100 hover:underline px-1 rounded transition-colors"
            onClick={(e) => handleWordClick(part, e)}
            title="Kelime açıklaması için tıklayın"
          >
            {part}
          </span>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  // Database'den transcript'leri çek
  useEffect(() => {
    if (activeTab === 'library') {
      fetchTranscripts();
    } else {
      fetchDiscoverContent();
    }
  }, [activeTab, discoverPage, currentUser]);

  // Filter değiştiğinde discoverPage'i reset et
  useEffect(() => {
    if (activeTab === 'discover') {
      setDiscoverPage(1);
    }
  }, [filter, activeTab]);

  // Discover content boşsa otomatik yükle
  useEffect(() => {
    if (activeTab === 'discover' && discoverContent.length === 0 && currentUser) {
      fetchDiscoverContent();
    }
  }, [activeTab, currentUser, discoverContent.length]);



  // Auto-hide notification after 5 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  const fetchDiscoverContent = async () => {
    try {
      setLoading(true);
      console.log('🔍 Fetching discover content...');
      
      // Keşfet içeriğini getir (tüm içerik, filtreleme client-side yapılacak)
      const discoverResponse = await fetch(`http://localhost:8000/api/library/discover?limit=1000&offset=0`);
      
      if (discoverResponse.ok) {
        const discoverData = await discoverResponse.json();
        if (discoverData.success && discoverData.data) {
          console.log('🔍 Backend total:', discoverData.total);
          setDiscoverTotal(discoverData.total || 0);
          const discoverContentWithLevels = discoverData.data.map((content: any) => {
            return {
              id: content.id,
              video_id: content.video_id,
              video_title: content.video_title || 'Untitled Content',
              channel_name: content.channel_name || 'Unknown Source',
              duration: content.duration,
              original_text: content.original_text,
              adapted_text: content.adapted_text,
              language: content.language || 'en',
              word_count: content.word_count || 0,
              adapted_word_count: content.adapted_word_count,
              view_count: content.view_count || 0,
              added_by: content.added_by || 'Unknown',
              created_at: content.created_at,
              content_type: content.content_type || 'youtube',
              cefr_level: content.cefr_level,
              level_confidence: content.level_confidence,
              level_analysis: content.level_analysis,
              level_analyzed_at: content.level_analyzed_at
            };
          });
          
          console.log('🔍 Discover content loaded:', discoverContentWithLevels.length, 'items');
          console.log('🔍 First item:', discoverContentWithLevels[0]);
          setDiscoverContent(discoverContentWithLevels);
        }
      }
    } catch (error) {
      console.error('Error fetching discover content:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTranscripts = async () => {
    try {
      setLoading(true);
      
      // YouTube transcripts'leri getir (sadece kullanıcının kendi videoları)
      const transcriptResponse = await fetch(`http://localhost:8000/api/library/transcripts?limit=50&offset=0&username=${currentUser}`);
      
      // Web content'leri getir
      const webContentResponse = await fetch('http://localhost:8000/api/library/web-content?limit=50&offset=0');
      
      let allTranscripts: any[] = [];
      
      // YouTube transcripts'leri işle
      if (transcriptResponse.ok) {
        const transcriptData = await transcriptResponse.json();
        if (transcriptData.success && transcriptData.data) {
          // Backend'den gelen CEFR level verilerini kullan
          const transcriptsWithLevels = transcriptData.data.map((transcript: any) => {
            return {
              id: transcript.id,
              video_id: transcript.video_id,
              video_title: transcript.video_title || 'Untitled Video',
              channel_name: transcript.channel_name || 'Unknown Channel',
              duration: transcript.duration,
              original_text: transcript.original_text,
              adapted_text: transcript.adapted_text,
              language: transcript.language || 'en',
              word_count: transcript.word_count || 0,
              adapted_word_count: transcript.adapted_word_count,
              view_count: transcript.view_count || 0,
              added_by: transcript.added_by || 'Unknown',
              created_at: transcript.created_at,
              content_type: 'youtube' as const,
              // Backend'den gelen CEFR level verileri (NEW)
              cefr_level: transcript.cefr_level,
              level_confidence: transcript.level_confidence,
              level_analysis: transcript.level_analysis,
              level_analyzed_at: transcript.level_analyzed_at
            };
          });
          
          allTranscripts = [...allTranscripts, ...transcriptsWithLevels];
        }
      }
      
      // Web content'leri işle
      if (webContentResponse.ok) {
        const webData = await webContentResponse.json();
        if (webData.success && webData.data) {
          const webContentsWithLevels = await Promise.all(
            webData.data.map(async (content: any) => {
              // Backend'den gelen CEFR verilerini kullan
              let level = content.cefr_level || 'N/A';
              let category = 'Web Article';
              
              return {
                id: content.id,
                video_id: null,
                video_title: content.title || 'Web Article',
                channel_name: content.url || 'Web Source',
                duration: null,
                original_text: null, // Detayda alınacak
                adapted_text: null,
                language: 'en',
                word_count: content.word_count || 0,
                adapted_word_count: 0,
                view_count: 0,
                added_by: 'User',
                created_at: content.created_at,
                level: level,
                category: category,
                content_type: 'web',
                // CEFR data from backend
                cefr_level: content.cefr_level,
                level_confidence: content.level_confidence,
                level_analysis: content.level_analysis,
                level_analyzed_at: content.level_analyzed_at
              };
            })
          );
          allTranscripts = [...allTranscripts, ...webContentsWithLevels];
        }
      }
      
      // Tarihe göre sırala
      allTranscripts.sort((a, b) => {
        const dateA = new Date(a.created_at || 0);
        const dateB = new Date(b.created_at || 0);
        return dateB.getTime() - dateA.getTime();
      });
      
      setTranscripts(allTranscripts);
      setLibraryTotal(allTranscripts.length);
    } catch (error) {
      console.error('Error fetching transcripts:', error);
    } finally {
      setLoading(false);
    }
  };

  // AI ile mevcut transcript'lerin seviyelerini analiz et
  const analyzeLevels = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/library/analyze-levels', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert(`✅ ${data.analyzed_count} transcript analiz edildi!`);
          // Refresh transcript list to show updated levels
          await fetchTranscripts();
        } else {
          alert(`❌ Analiz hatası: ${data.error}`);
        }
      } else {
        alert('❌ Sunucu hatası occurred during analysis');
      }
    } catch (error) {
      console.error('Error analyzing levels:', error);
      alert('❌ Analiz sırasında bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  // Filtreleme
  const filteredTranscripts = transcripts.filter(t => {
    const channelMatch = filter.channel ? t.channel_name.toLowerCase().includes(filter.channel.toLowerCase()) : true;
    const keywordMatch = filter.keyword ? t.video_title.toLowerCase().includes(filter.keyword.toLowerCase()) : true;
    const minMatch = filter.minWords ? t.word_count >= parseInt(filter.minWords) : true;
    const maxMatch = filter.maxWords ? t.word_count <= parseInt(filter.maxWords) : true;
    const cefrMatch = filter.cefrLevel ? t.cefr_level === filter.cefrLevel : true;
    return channelMatch && keywordMatch && minMatch && maxMatch && cefrMatch;
  });

  // Keşfet için filtreleme (client-side, kütüphanem gibi)
  const filteredDiscoverContent = discoverContent.filter(t => {
    const channelMatch = filter.channel ? t.channel_name.toLowerCase().includes(filter.channel.toLowerCase()) : true;
    const keywordMatch = filter.keyword ? t.video_title.toLowerCase().includes(filter.keyword.toLowerCase()) : true;
    const minMatch = filter.minWords ? t.word_count >= parseInt(filter.minWords) : true;
    const maxMatch = filter.maxWords ? t.word_count <= parseInt(filter.maxWords) : true;
    const cefrMatch = filter.cefrLevel ? t.cefr_level === filter.cefrLevel : true;
    
    return channelMatch && keywordMatch && minMatch && maxMatch && cefrMatch;
  });

  // Keşfet için pagination
  const paginatedDiscoverContent = filteredDiscoverContent.slice((discoverPage - 1) * PAGE_SIZE, discoverPage * PAGE_SIZE);

  // Sayfalama
  const totalPages = Math.ceil(filteredTranscripts.length / PAGE_SIZE);
  const paginatedTranscripts = filteredTranscripts.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Seçili transcript değişince adaptedText'i sıfırla
  useEffect(() => {
    setAdaptedText('');
  }, [selectedTranscript]);

  // Transcript seçildiğinde tam içeriği çek
  const handleTranscriptSelect = async (transcript: Transcript) => {
    setSelectedTranscript(transcript);
    
    // Eğer transcript'te full content yoksa API'den çek
    if (!transcript.original_text && transcript.id) {
      try {
        let response;
        
        // Content türüne göre farklı endpoint kullan
        if (transcript.content_type === 'web') {
          response = await fetch(`http://localhost:8000/api/web-content/${transcript.id}`);
        } else {
          response = await fetch(`http://localhost:8000/api/library/transcript/${transcript.id}`);
        }
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.data) {
            const contentField = transcript.content_type === 'web' ? data.data.content : data.data.original_text;
            const fullTranscript = { ...transcript, original_text: contentField };
            setSelectedTranscript(fullTranscript);
          }
        }
      } catch (error) {
        console.error('Error fetching full content:', error);
      }
    }
  };

  // Gerçek AI adaptation
  const handleAdaptText = async () => {
    if (!selectedTranscript) return;
    
    try {
      setAdaptationLoading(true);
      const adaptedResult = await adaptTextWithAI(
        selectedTranscript.id, 
        currentUser,
        selectedTranscript.content_type || 'youtube'
      );
      setAdaptedText(adaptedResult);
    } catch (error) {
      console.error('Adaptation failed:', error);
      alert(`Adaptasyon başarısız: ${error}`);
    } finally {
      setAdaptationLoading(false);
    }
  };

  // Kopyala fonksiyonu
  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Metin kopyalandı!');
    } catch (err) {
      console.error('Failed to copy text: ', err);
    }
  };

  // Kütüphaneme ekleme fonksiyonu
  const handleAddToMyLibrary = async (content: Transcript) => {
    try {
      const token = localStorage.getItem('token');
      console.log('🔑 Token:', token);
      
      if (!token) {
        setNotification({ type: 'error', message: '❌ Oturum bulunamadı. Lütfen tekrar giriş yapın.' });
        return;
      }
      
      const response = await fetch('http://localhost:8000/api/library/add-to-my-library', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          content_id: content.id,
          content_type: content.content_type || 'youtube'
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setNotification({ type: 'success', message: '✅ İçerik kütüphanene eklendi!' });
        } else {
          setNotification({ type: 'error', message: `❌ ${data.error}` });
        }
      } else {
        setNotification({ type: 'error', message: '❌ Sunucu hatası' });
      }
    } catch (error) {
      console.error('Error adding to library:', error);
      setNotification({ type: 'error', message: '❌ İçerik eklenirken hata oluştu' });
    }
  };

  // PDF olarak indir fonksiyonu (gerçek implementation)
  const handleDownloadPDF = async (text: string, type: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/text-analysis/simple-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          filename: `${type}_transcript_${Date.now()}.pdf`
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${type}_transcript_${Date.now()}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        alert('PDF başarıyla indirildi!');
      } else {
        throw new Error('PDF oluşturulamadı');
      }
    } catch (error) {
      console.error('PDF download error:', error);
      alert('PDF indirme başarısız: ' + error);
    }
  };

  if (loading) {
    return (
      <div className="flex w-full min-h-[80vh] bg-gray-900 text-white items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-400 mx-auto mb-4"></div>
          <p className="text-gray-400">Kütüphane yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full min-h-[80vh] bg-gray-900 text-white">
      {/* Notification */}
      {notification && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 ${
          notification.type === 'success' 
            ? 'bg-green-500 text-white' 
            : 'bg-red-500 text-white'
        }`}>
          <div className="flex items-center gap-2">
            <span>{notification.message}</span>
            <button 
              onClick={() => setNotification(null)}
              className="ml-2 text-white hover:text-gray-200"
            >
              ✕
            </button>
          </div>
        </div>
      )}
      {/* Sol Panel: Transcript Listesi ve Filtreler */}
      <div className="w-full max-w-md bg-gray-800 p-6 border-r border-gray-700 flex flex-col">
        {/* Tab Sistemi */}
        <div className="mb-6">
          <div className="flex bg-gray-700 rounded-lg p-1 mb-4">
            <button
              onClick={() => {
                setActiveTab('library');
                setPage(1);
              }}
              className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
                activeTab === 'library'
                  ? 'bg-teal-500 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              📚 Kütüphanem ({libraryTotal})
            </button>
            <button
              onClick={() => {
                setActiveTab('discover');
                setDiscoverPage(1);
              }}
              className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
                activeTab === 'discover'
                  ? 'bg-teal-500 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              🔍 Keşfet ({activeTab === 'discover' ? filteredDiscoverContent.length : discoverContent.length})
            </button>
          </div>
        </div>

        {/* Filtreler */}
        <div className="mb-6">
          <h3 className="text-lg font-bold text-teal-400 mb-4">🔍 Filtreler</h3>
          
          {/* Kullanıcı Seviyesi Gösterimi */}
          <div className="mb-4 p-3 rounded-lg bg-gray-700 border border-gray-600">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-300">Sizin Seviyeniz:</span>
              <span 
                className="text-sm px-3 py-1 rounded-full font-bold"
                style={{ 
                  backgroundColor: userLevel === 'A1' ? '#10b981' : 
                                  userLevel === 'A2' ? '#3b82f6' : 
                                  userLevel === 'B1' ? '#f59e0b' : 
                                  userLevel === 'B2' ? '#ef4444' : 
                                  userLevel === 'C1' ? '#8b5cf6' : '#ec4899',
                  color: 'white'
                }}
              >
                {userLevel || 'N/A'}
              </span>
            </div>
          </div>

          {/* CEFR Level Filtresi */}
          <select
            key="cefr-level-select"
            className="w-full mb-3 p-3 rounded-lg border border-gray-600 bg-gray-700 text-white focus:outline-none focus:border-teal-400"
            value={filter.cefrLevel}
            onChange={e => setFilter(f => ({ ...f, cefrLevel: e.target.value }))}
          >
            <option value="">Tüm seviyeler</option>
            <option value="A1">A1 - Başlangıç</option>
            <option value="A2">A2 - Temel</option>
            <option value="B1">B1 - Orta Alt</option>
            <option value="B2">B2 - Orta Üst</option>
            <option value="C1">C1 - İleri</option>
            <option value="C2">C2 - Üst Düzey</option>
          </select>

          <input
            key="channel-input"
            type="text"
            placeholder="Kanal adı..."
            className="w-full mb-3 p-3 rounded-lg border border-gray-600 bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:border-teal-400"
            value={filter.channel}
            onChange={e => setFilter(f => ({ ...f, channel: e.target.value }))}
          />
          <input
            key="keyword-input"
            type="text"
            placeholder="Anahtar kelime..."
            className="w-full mb-3 p-3 rounded-lg border border-gray-600 bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:border-teal-400"
            value={filter.keyword}
            onChange={e => setFilter(f => ({ ...f, keyword: e.target.value }))}
          />
          <div className="flex gap-2">
            <input
              key="min-words-input"
              type="number"
              placeholder="Min kelime"
              className="w-1/2 p-3 rounded-lg border border-gray-600 bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:border-teal-400"
              value={filter.minWords}
              onChange={e => setFilter(f => ({ ...f, minWords: e.target.value }))}
            />
            <input
              key="max-words-input"
              type="number"
              placeholder="Max kelime"
              className="w-1/2 p-3 rounded-lg border border-gray-600 bg-gray-700 text-white placeholder-gray-400 focus:outline-none focus:border-teal-400"
              value={filter.maxWords}
              onChange={e => setFilter(f => ({ ...f, maxWords: e.target.value }))}
            />
          </div>

          {/* AI Level Analysis Button - REMOVED */}
        </div>

        {/* Transcript Listesi */}
        <div className="flex-1 overflow-y-auto">
          <h3 className="text-lg font-bold text-teal-400 mb-4">
            {activeTab === 'library' ? '📚 Kütüphanem' : '🔍 Keşfet'} ({activeTab === 'library' ? filteredTranscripts.length : filteredDiscoverContent.length})
          </h3>
          {(activeTab === 'library' ? paginatedTranscripts : filteredDiscoverContent).length === 0 ? (
            <div className="text-center text-gray-400 mt-8">
              <p>{activeTab === 'library' ? 'Hiç transcript bulunamadı.' : 'Hiç içerik bulunamadı.'}</p>
              <p className="text-sm mt-2">
                {activeTab === 'library' 
                  ? 'Filtrelerinizi kontrol edin veya yeni içerik ekleyin.' 
                  : 'Filtrelerinizi kontrol edin veya daha sonra tekrar deneyin.'
                }
              </p>
            </div>
          ) : (
            (activeTab === 'library' ? paginatedTranscripts : paginatedDiscoverContent).map((t: Transcript) => (
              <div
                key={`${t.content_type || 'youtube'}-${t.id}`}
                className={`mb-4 rounded-lg shadow-lg p-4 cursor-pointer border-2 transition-all duration-200 ${
                  selectedTranscript && selectedTranscript.id === t.id && selectedTranscript.content_type === t.content_type
                    ? 'border-teal-400 bg-teal-900 bg-opacity-30' 
                    : 'border-gray-600 bg-gray-700 hover:border-gray-500 hover:bg-gray-600'
                }`}
                onClick={() => handleTranscriptSelect(t)}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span 
                    className="text-xs px-2 py-1 rounded-full font-bold"
                    style={{ 
                      backgroundColor: t.cefr_level === 'A1' ? '#10b981' : 
                                      t.cefr_level === 'A2' ? '#3b82f6' : 
                                      t.cefr_level === 'B1' ? '#f59e0b' : 
                                      t.cefr_level === 'B2' ? '#ef4444' : 
                                      t.cefr_level === 'C1' ? '#8b5cf6' : '#ec4899',
                      color: 'white'
                    }}
                  >
                    {t.cefr_level || 'N/A'}
                  </span>
                  {t.level_confidence && (
                    <span className="text-xs px-2 py-1 rounded-full font-bold bg-gray-600 text-white">
                      {t.level_confidence}% confident
                    </span>
                  )}
                </div>
                <h4 className="font-semibold text-white mb-1 line-clamp-2">{t.video_title}</h4>
                <div className="text-xs text-gray-300 mb-2">
                  <span>{t.channel_name}</span> • <span>{t.added_by}</span> • <span>{t.word_count} kelime</span>
                </div>
                
                {/* Progress Bar */}
                <div className="h-2 rounded-full bg-gray-600 overflow-hidden mb-2">
                  <div 
                    className="h-2 rounded-full bg-teal-400" 
                    style={{ width: `${Math.min(100, (t.word_count / 500) * 100)}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-gray-400">{t.view_count} görüntülenme</span>
                  <div className="flex items-center gap-2">
                    {activeTab === 'discover' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAddToMyLibrary(t);
                        }}
                        className="text-xs bg-teal-500 hover:bg-teal-600 text-white px-2 py-1 rounded transition-colors"
                        title="Kütüphaneme Ekle"
                      >
                        📚 Ekle
                      </button>
                    )}
                    <span className="text-xs text-gray-400 cursor-pointer hover:text-red-400">❤️</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {activeTab === 'library' && totalPages > 1 && (
          <div className="flex flex-col items-center gap-2 mt-6 pt-4 border-t border-gray-700">
            <div className="text-sm text-gray-400 mb-2">
              Sayfa {page}'de {paginatedTranscripts.length} içerik, toplam {libraryTotal} içerik
            </div>
            <div className="flex justify-center items-center gap-2">
              {Array.from({ length: totalPages }, (_, i) => (
                <button
                  key={i}
                  className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                    page === i + 1 
                      ? 'bg-teal-500 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                  onClick={() => setPage(i + 1)}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* Keşfet Pagination */}
        {activeTab === 'discover' && filteredDiscoverContent.length > 0 && (
          <div className="flex flex-col items-center gap-2 mt-6 pt-4 border-t border-gray-700">
            <div className="text-sm text-gray-400 mb-2">
              Sayfa {discoverPage}'de {paginatedDiscoverContent.length} içerik, toplam {filteredDiscoverContent.length} içerik
            </div>
            <div className="flex justify-center items-center gap-2">
              {Array.from({ length: Math.ceil(filteredDiscoverContent.length / PAGE_SIZE) }, (_, i) => (
                <button
                  key={i}
                  className={`px-3 py-2 rounded-lg font-medium transition-colors ${
                    discoverPage === i + 1 
                      ? 'bg-teal-500 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                  onClick={() => setDiscoverPage(i + 1)}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Sağ Panel: Orijinal ve AI Adapted Kutuları */}
      <div className="flex-1 flex flex-col gap-8 p-8">
        {/* Orijinal Metin Kutusu */}
        <div className="bg-gray-800 rounded-lg shadow-lg p-6 h-[350px] flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-white">📝 Orijinal Metin</h2>
            {selectedTranscript && selectedTranscript.original_text && (
              <div className="flex gap-2">
                <button 
                  onClick={() => handleCopy(selectedTranscript.original_text!)} 
                  className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  📋 Kopyala
                </button>
                <button 
                  onClick={() => handleDownloadPDF(selectedTranscript.original_text!, 'original')} 
                  className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  📄 PDF
                </button>
              </div>
            )}
          </div>
          <div className="flex-1 text-gray-200 whitespace-pre-line overflow-y-auto bg-gray-700 rounded-lg p-4">
            {selectedTranscript && selectedTranscript.original_text ? (
              <div className="leading-relaxed">
                {renderClickableText(selectedTranscript.original_text)}
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <span className="text-gray-400 text-center">
                  📖 Metninizin görüntülenmesi için soldan bir transkript seçin
                </span>
              </div>
            )}
          </div>
        </div>

        {/* AI Adapted Kutusu - Sadece Kütüphanem tab'ında göster */}
        {activeTab === 'library' && (
          <div className="bg-gray-800 rounded-lg shadow-lg p-6 h-[350px] flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-white">🤖 AI Adapted Text</h2>
              {selectedTranscript && selectedTranscript.original_text && (
                <div className="flex gap-2">
                  <button 
                    onClick={() => handleCopy(adaptedText)} 
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed" 
                    disabled={!adaptedText}
                  >
                    📋 Kopyala
                  </button>
                  <button 
                    onClick={() => handleDownloadPDF(adaptedText, 'adapted')} 
                    className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed" 
                    disabled={!adaptedText}
                  >
                    📄 PDF
                  </button>
                  <button 
                    onClick={handleAdaptText}
                    className="bg-teal-500 hover:bg-teal-600 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                    disabled={adaptationLoading}
                  >
                    {adaptationLoading ? '⏳ Adapte ediliyor...' : '🎯 Adapt et'}
                  </button>
                </div>
              )}
            </div>
            <div className="flex-1 text-gray-200 whitespace-pre-line overflow-y-auto bg-gray-700 rounded-lg p-4">
              {adaptationLoading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-400 mx-auto mb-2"></div>
                    <span className="text-gray-400">AI metni adapte ediyor...</span>
                  </div>
                </div>
              ) : adaptedText ? (
                <div className="leading-relaxed">
                  {renderClickableText(adaptedText)}
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <span className="text-gray-400 text-center">
                    {selectedTranscript && selectedTranscript.original_text
                      ? "🎯 Metni seviyenize uyarlamak için 'Adapt et' butonuna basın" 
                      : "📖 Önce soldan bir metin seçin, sonra 'Adapt et' butonuna basın"
                    }
                  </span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Word Explanation Popup */}
      <WordExplanationPopup
        word={wordPopup.word}
        isOpen={wordPopup.isOpen}
        onClose={closeWordPopup}
        position={wordPopup.position}
        currentUser={currentUser}
      />
    </div>
  );
};

export default Library; 