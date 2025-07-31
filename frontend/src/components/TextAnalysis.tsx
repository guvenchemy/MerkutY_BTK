'use client';

import React, { useState } from 'react';

interface WordTranslation {
  word: string;
  translation: string;
  explanation: string;
  success: boolean;
}

interface TextAnalysisResult {
  original_text?: string;
  basic_statistics: {
    character_count: number;
    word_count: number;
    sentence_count: number;
    paragraph_count: number;
    average_word_length: number;
    average_sentence_length: number;
    reading_time_minutes: number;
  };
  grammar_analysis: {
    part_of_speech_distribution?: { [key: string]: number };
    sentence_types?: {
      total: number;
      questions: number;
      exclamations: number;
      statements: number;
    };
    grammar_patterns?: Array<{
      pattern_name: string;
      explanation: string;
      examples: string[];
      count: number;
    }>;
    complexity_indicators?: {
      conjunction_count: number;
      complex_sentence_count: number;
      complex_sentence_examples: string[];
      subordinating_clause_count: number;
      average_sentence_complexity: string;
    };
  };
  word_analysis: {
    unique_word_count: number;
    total_word_count: number;
    lexical_diversity: number;
    most_frequent_words: [string, number][];
    long_words_count: number;
    long_words_examples: string[];
  };
  ai_insights: {
    ai_analysis: string;
    grammar_insights?: string;
    vocabulary_insights?: string;
    learning_suggestions?: string;
  };
  user_vocabulary_stats?: {
    user_level: string;
    level_score: number;
    total_known_words: number;
    total_vocabulary_entries: number;
    text_analysis: {
      total_unique_words_in_text: number;
      known_words_in_text: number;
      unknown_words_in_text: number;
      comprehension_rate: number;
      text_difficulty: string;
      unknown_word_examples: string[];
    };
  };
  adapted_text?: {
    adapted_text: string;
    adaptation_level: string;
    changes_made: string;
  } | string;
  grammar_examples?: {
    detected_patterns: Array<{
      pattern_name: string;
      explanation: string;
      detailed_info: string;
      examples: string[];
      translated_examples: Array<{
        english: string;
        turkish: string;
      }>;
      count: number;
    }>;
    tense_examples: string[];
    modal_examples: string[];
    complex_structures: string[];
  };
  video_info?: {
    title?: string;
    warning?: string;
    language?: string;
  };
}

interface AnalysisResponse {
  success: boolean;
  data?: TextAnalysisResult;
  error?: string;
}

const TextAnalysis: React.FC = () => {
  const [text, setText] = useState('');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [analysisResult, setAnalysisResult] = useState<TextAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'text' | 'youtube'>('text');
  const [includeAdaptation, setIncludeAdaptation] = useState(false);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const [userId] = useState<number>(1); // Geçici user ID
  const [grammarUpdating, setGrammarUpdating] = useState<string | null>(null);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [wordTranslation, setWordTranslation] = useState<WordTranslation | null>(null);
  const [translationLoading, setTranslationLoading] = useState(false);
  const [userKnownWords, setUserKnownWords] = useState<string[]>([]);

  // Kullanıcının bilinen kelimelerini yükle
  const loadUserKnownWords = React.useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/analysis/user-vocabulary/${userId}`);
      const result = await response.json();
      
      if (result.success && result.known_words) {
        setUserKnownWords(result.known_words);
      }
    } catch (err) {
      console.error('Failed to load user known words:', err);
    }
  }, [userId]);

  // Component mount olduğunda bilinen kelimeleri yükle
  React.useEffect(() => {
    loadUserKnownWords();
  }, [userId, loadUserKnownWords]);

  // Kelimenin bilinip bilinmediğini kontrol et
  const isWordKnown = (word: string): boolean => {
    const cleanWord = word.toLowerCase();
    return userKnownWords.some(knownWord => 
      knownWord.toLowerCase() === cleanWord
    );
  };

  const analyzeText = async () => {
    if (!text.trim() || text.trim().length < 10) {
      setError('Metin en az 10 karakter olmalıdır');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/analysis/analyze-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          include_examples: true,
          include_adaptation: includeAdaptation,
          user_id: userId
        }),
      });

      const result: AnalysisResponse = await response.json();

      if (result.success && result.data) {
        setAnalysisResult(result.data);
      } else {
        setError(result.error || 'Analiz sırasında bir hata oluştu');
      }
    } catch (err) {
      setError('Sunucuya bağlanırken hata oluştu');
      console.error('Analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const analyzeYoutube = async () => {
    if (!youtubeUrl.trim()) {
      setError('YouTube URL giriniz');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/analysis/analyze-youtube', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_url: youtubeUrl,
          include_examples: true,
          include_adaptation: includeAdaptation,
          user_id: userId
        }),
      });

      const result: AnalysisResponse = await response.json();

      if (result.success && result.data) {
        setAnalysisResult(result.data);
        
        // IP block uyarısı kontrolü
        if (result.data.video_info?.warning) {
          setError(`⚠️ ${result.data.video_info.warning}`);
        }
      } else {
        // IP block özel durumu
        if (result.error?.includes('IP engeli') || result.error?.includes('IP block')) {
          setError(`🚫 ${result.error}\n\n💡 Çözüm önerileri:\n• VPN kullanın\n• Farklı internet bağlantısı deneyin\n• Daha sonra tekrar deneyin`);
        } else {
          setError(result.error || 'YouTube analizi sırasında bir hata oluştu');
        }
      }
    } catch (err) {
      setError('Sunucuya bağlanırken hata oluştu. YouTube API\'sine erişim engellenmiş olabilir.');
      console.error('YouTube analysis error:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setAnalysisResult(null);
    setError('');
    setText('');
    setYoutubeUrl('');
  };

  const translateWord = async (word: string) => {
    if (!word || word.trim().length < 1) return;
    
    setTranslationLoading(true);
    setSelectedWord(word);
    
    try {
      const response = await fetch('http://localhost:8000/api/analysis/translate-word', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          word: word.trim(),
          user_id: userId
        }),
      });

      const result = await response.json();
      
      if (result.success && result.data) {
        setWordTranslation(result.data);
      } else {
        setWordTranslation({
          word: word,
          translation: 'Çeviri bulunamadı',
          explanation: result.error || 'Çeviri hatası',
          success: false
        });
      }
    } catch (err) {
      console.error('Word translation error:', err);
      setWordTranslation({
        word: word,
        translation: 'Bağlantı hatası',
        explanation: 'Sunucuya bağlanırken hata oluştu',
        success: false
      });
    } finally {
      setTranslationLoading(false);
    }
  };

  const closeWordTranslation = () => {
    setSelectedWord(null);
    setWordTranslation(null);
  };

  // Özel isim kontrolü - cümle başını kontrol eden gelişmiş versiyonu
  const isProperNoun = (word: string, text: string, wordIndex: number): boolean => {
    const properNouns = new Set([
      // Kişi adları
      'john', 'mary', 'david', 'sarah', 'michael', 'jennifer', 'james', 'lisa',
      'robert', 'susan', 'william', 'karen', 'richard', 'nancy', 'thomas', 'betty',
      'charles', 'helen', 'christopher', 'sandra', 'daniel', 'donna', 'matthew', 'carol',
      
      // Yer adları
      'london', 'paris', 'tokyo', 'newyork', 'california', 'texas', 'florida', 'chicago',
      'boston', 'washington', 'seattle', 'atlanta', 'miami', 'denver', 'phoenix', 'dallas',
      'england', 'france', 'germany', 'italy', 'spain', 'japan', 'china', 'brazil',
      'canada', 'australia', 'india', 'mexico', 'russia', 'turkey', 'america', 'europe',
      
      // Şirket/Marka adları
      'google', 'apple', 'microsoft', 'amazon', 'facebook', 'twitter', 'instagram',
      'youtube', 'netflix', 'disney', 'coca', 'cola', 'mcdonald', 'walmart', 'nike',
      
      // Günler ve aylar
      'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
      'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
      'september', 'october', 'november', 'december',
      
      // Diller ve milletler
      'english', 'spanish', 'french', 'german', 'italian', 'chinese', 'japanese',
      'american', 'british', 'turkish'
    ]);
    
    const wordLower = word.toLowerCase();
    
    // Bilinen özel isimler listesinde mi?
    if (properNouns.has(wordLower)) {
      return true;
    }
    
    // Büyük harfle başlamıyorsa özel isim değil
    if (word[0] !== word[0].toUpperCase()) {
      return false;
    }
    
    // Tamamen büyük harfse (ACRONYM) özel isim değil
    if (word === word.toUpperCase()) {
      return false;
    }
    
    // Cümle başında mı kontrol et (nokta, ünlem, soru işareti sonrası)
    const parts = text.split(/(\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b|\s+|[^\w\s])/);
    let currentWordIndex = 0;
    let foundSentenceStart = false;
    
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      const isWord = /^[a-zA-Z]+(?:'[a-zA-Z]+)?$/.test(part);
      
      if (isWord && part.length > 1) {
        if (currentWordIndex === wordIndex) {
          // Bu kelimeyi bulduğumuzda, cümle başında mı kontrol et
          // Önceki parçalarda noktalama işareti var mı?
          for (let j = i - 1; j >= 0; j--) {
            const prevPart = parts[j];
            if (/^[a-zA-Z]+/.test(prevPart)) {
              // Başka bir kelime buldu, cümle başında değil
              foundSentenceStart = false;
              break;
            } else if (/[.!?]/.test(prevPart)) {
              // Cümle sonu işareti buldu, cümle başında
              foundSentenceStart = true;
              break;
            }
          }
          break;
        }
        currentWordIndex++;
      }
    }
    
    // Eğer cümle başındaysa ve yaygın kelime değilse özel isim olmayabilir
    if (foundSentenceStart || wordIndex === 0) {
      const commonWords = new Set([
        'the', 'this', 'that', 'there', 'then', 'they', 'them', 'these', 'those',
        'when', 'where', 'what', 'who', 'why', 'how', 'which', 'while', 'with',
        'will', 'would', 'was', 'were', 'are', 'and', 'but', 'for', 'not', 'all',
        'from', 'to', 'in', 'on', 'at', 'by', 'about', 'over', 'under', 'after'
      ]);
      if (commonWords.has(wordLower)) {
        return false; // Yaygın kelime, özel isim değil
      }
    }
    
    // Büyük harfle başlıyor ve 2+ karakterli ama yaygın kelime değilse özel isim olabilir
    if (word.length > 2) {
      const commonCapitalized = new Set([
        'the', 'this', 'that', 'there', 'then', 'they', 'them', 'these', 'those',
        'when', 'where', 'what', 'who', 'why', 'how', 'which', 'while', 'with',
        'will', 'would', 'was', 'were', 'are', 'and', 'but', 'for', 'not', 'all',
        'from', 'to', 'in', 'on', 'at', 'by'
      ]);
      if (!commonCapitalized.has(wordLower) && !foundSentenceStart && wordIndex !== 0) {
        return true;
      }
    }
    
    return false;
  };

  const handleWordKnowledge = async (status: 'known' | 'unknown' | 'ignored' | 'learning') => {
    if (!wordTranslation) return;
    
    try {
      const response = await fetch('http://localhost:8000/api/analysis/add-vocabulary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          word: wordTranslation.word,
          translation: wordTranslation.translation,
          status: status
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        console.log(`✅ '${wordTranslation.word}' kelimesi '${status}' olarak işaretlendi`);
        
        // Bilinen kelimeleri yeniden yükle
        if (status === 'known' || status === 'learning') {
          loadUserKnownWords();
        }
        
        // Kelime durumu değiştiğinde kullanıcı istatistiklerini yeniden hesapla
        if (analysisResult && text) {
          console.log('🔄 Refreshing user vocabulary statistics...');
          // Mevcut analiz sonucunu koruyarak sadece user_vocabulary_stats'i güncelle
          await refreshUserVocabularyStats();
        }
        
      } else {
        console.error('❌ Kelime kaydedilemedi:', result.error);
      }
    } catch (err) {
      console.error('❌ Kelime kaydetme hatası:', err);
    } finally {
      closeWordTranslation();
    }
  };

  // Kullanıcı vocabulary istatistiklerini yeniden hesapla
  const refreshUserVocabularyStats = async () => {
    if (!text || !userId) return;
    
    try {
      const response = await fetch('http://localhost:8000/api/analysis/analyze-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          user_id: userId,
          include_ai_analysis: false, // Sadece istatistikler için
          include_grammar: false,
          include_adaptation: false
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Sadece user_vocabulary_stats'i güncelle
        if (data.user_vocabulary_stats && analysisResult) {
          setAnalysisResult({
            ...analysisResult,
            user_vocabulary_stats: data.user_vocabulary_stats
          });
          console.log('✅ User vocabulary statistics refreshed');
        }
      }
    } catch (error) {
      console.error('❌ Error refreshing user vocabulary stats:', error);
    }
  };

  // Metin seçimi fonksiyonu - çoklu kelime seçimi için
  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      const selectedText = selection.toString().trim();
      
      // Sadece noktalama işaretlerini temizle, kelimeleri ayırma
      const cleanedText = selectedText.replace(/^[^\w\s]+|[^\w\s]+$/g, '').trim();
      
      // En az bir kelime varsa ve makul uzunlukta ise çeviri al
      if (cleanedText.length > 0 && cleanedText.length < 100) {
        // Birden fazla kelime seçilmişse veya tek kelime seçilmişse çeviri al
        const wordCount = cleanedText.split(/\s+/).length;
        if (wordCount >= 1) {
          translateWord(cleanedText); // Temizlenmiş metni aynen gönder
        }
      }
    }
  };

  const renderClickableText = (text: string, isAdapted: boolean = false) => {
    // Metni kelimelere böl ama noktalama işaretlerini koru
    const parts = text.split(/(\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b|\s+|[^\w\s])/);
    let wordIndex = 0;
    
    return (
      <div 
        style={{ userSelect: 'text' }}
        className="leading-relaxed"
        onMouseUp={() => setTimeout(handleTextSelection, 10)}
      >
        {parts.map((part, index) => {
          // Sadece harflerden oluşan kelimeleri tıklanabilir yap
          const isWord = /^[a-zA-Z]+(?:'[a-zA-Z]+)?$/.test(part);
          
          if (isWord && part.length > 1) {
            const cleanWord = part.toLowerCase();
            const known = isWordKnown(cleanWord);
            const isProperNounWord = isProperNoun(part, text, wordIndex);
            wordIndex++; // Sonraki kelime için index'i artır
            
            // Özel isimler için farklı stil
            if (isProperNounWord) {
              return (
                <span
                  key={index}
                  className="text-blue-300 cursor-pointer hover:text-blue-100 transition-colors"
                  onClick={() => translateWord(part)}
                  title={'Özel isim - Çeviri için tıklayın'}
                >
                  {part}
                </span>
              );
            }
            
            // Renk kodlaması bilgi durumuna göre
            let wordClass = "cursor-pointer px-1 rounded transition-colors duration-200 ";
            
            if (isAdapted) {
              // Adapte metinde: Bilinen kelimeler normal, bilinmeyen pembe
              if (known) {
                wordClass += "hover:bg-gray-600 hover:text-white";
              } else {
                wordClass += "hover:bg-pink-600 hover:text-white bg-pink-500 bg-opacity-50 text-pink-200 font-bold";
              }
            } else {
              // Orijinal metinde: Bilinen kelimeler normal, bilinmeyen sarı
              if (known) {
                wordClass += "hover:bg-gray-600 hover:text-white";
              } else {
                wordClass += "hover:bg-yellow-600 hover:text-white bg-yellow-500 bg-opacity-40 text-yellow-200";
              }
            }
            
            return (
              <span
                key={index}
                className={wordClass}
                onClick={() => translateWord(part)}
                title={`${known ? 'Bilinen' : 'Bilinmeyen'} kelime - Çeviri için tıklayın`}
              >
                {part}
              </span>
            );
          } else {
            return <span key={index}>{part}</span>;
          }
        })}
      </div>
    );
  };

  const downloadPDF = async () => {
    if (!analysisResult) return;
    
    setPdfGenerating(true);
    try {
      const response = await fetch('http://localhost:8000/api/analysis/generate-pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          analysis_data: analysisResult,
          include_adaptation: includeAdaptation
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'text_analysis_report.pdf';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('PDF indirme başarısız oldu');
      }
    } catch (err) {
      setError('PDF oluşturma sırasında hata oluştu');
      console.error('PDF generation error:', err);
    } finally {
      setPdfGenerating(false);
    }
  };

  const downloadText = async (textType: 'original' | 'adapted') => {
    if (!analysisResult) return;
    
    try {
      let textContent = '';
      
      if (textType === 'original') {
        textContent = analysisResult.original_text || '';
      } else if (textType === 'adapted' && analysisResult.adapted_text) {
        const adaptedData = analysisResult.adapted_text;
        if (typeof adaptedData === 'object' && adaptedData.adapted_text) {
          textContent = adaptedData.adapted_text;
        } else {
          textContent = String(adaptedData);
        }
      }
      
      if (!textContent) {
        setError('İndirilecek metin bulunamadı');
        return;
      }

      // Backend'e PDF oluşturma isteği gönder
      const response = await fetch('http://localhost:8000/api/analysis/download-text', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text_type: textType,
          text_content: textContent
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${textType}_text.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        setError('PDF indirme başarısız oldu');
      }
    } catch (err) {
      setError('Metin indirme sırasında hata oluştu');
      console.error('Text download error:', err);
    }
  };

  const updateGrammarKnowledge = async (patternKey: string, status: 'known' | 'unknown' | 'ignored') => {
    setGrammarUpdating(patternKey);
    try {
      const response = await fetch('http://localhost:8000/api/analysis/update-grammar-knowledge', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          pattern_key: patternKey,
          status: status
        }),
      });

      if (response.ok) {
        // Başarılı update sonrası analizi yenile (opsiyonel)
        console.log(`Grammar pattern ${patternKey} marked as ${status}`);
        
        // Pattern'ı UI'dan kaldır (bilinen veya görmezden gelinen)
        if (status === 'known' || status === 'ignored') {
          if (analysisResult && analysisResult.grammar_examples) {
            const updatedPatterns = analysisResult.grammar_examples.detected_patterns.filter(
              pattern => getPatternKey(pattern.pattern_name) !== patternKey
            );
            
            setAnalysisResult({
              ...analysisResult,
              grammar_examples: {
                ...analysisResult.grammar_examples,
                detected_patterns: updatedPatterns
              }
            });
          }
        }
      } else {
        setError('Gramer bilgisi güncellenirken hata oluştu');
      }
    } catch (err) {
      setError('Gramer güncelleme sırasında hata oluştu');
      console.error('Grammar update error:', err);
    } finally {
      setGrammarUpdating(null);
    }
  };

  const getPatternKey = (patternName: string): string => {
    // Pattern name'den pattern key'i çıkar
    const mapping: { [key: string]: string } = {
      "Present Perfect Tense": "present_perfect",
      "Passive Voice": "passive_voice",
      "Modal Verbs": "modal_verbs",
      "Conditional Sentences": "conditional",
      "Relative Clauses": "relative_clauses",
      "Comparative and Superlative": "comparative",
      "Future Tense": "future_tense",
      "Past Perfect Tense": "past_perfect",
      "Present Tense": "present_tense",
      "Past Tense": "past_tense"
    };
    
    return mapping[patternName] || patternName.toLowerCase().replace(/\s+/g, '_');
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gray-800 rounded-lg shadow-lg text-white">
      <h2 className="text-3xl font-bold text-teal-400 mb-6">🔍 Metin Analizi</h2>
      
      {/* Tab Navigation */}
      <div className="flex mb-6 border-b border-gray-600">
        <button
          onClick={() => setActiveTab('text')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'text'
              ? 'text-teal-400 border-b-2 border-teal-400'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          📝 Metin Analizi
        </button>
        <button
          onClick={() => setActiveTab('youtube')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'youtube'
              ? 'text-teal-400 border-b-2 border-teal-400'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          🎥 YouTube Video Analizi
        </button>
      </div>

      {/* Input Section */}
      <div className="mb-6">
        {activeTab === 'text' ? (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Analiz edilecek metin:
            </label>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Analiz etmek istediğiniz metni buraya yazın..."
              className="w-full h-32 p-3 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
            <p className="text-sm text-gray-400 mt-1">
              Minimum 10 karakter gerekli. Mevcut: {text.length} karakter
            </p>
          </div>
        ) : (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              YouTube Video URL:
            </label>
            <input
              type="url"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
            <p className="text-sm text-gray-400 mt-1">
              YouTube video URL&apos;sini girin (transkripti olan videolar için)
            </p>
          </div>
        )}
        
        {/* Options */}
        <div className="mt-4 p-4 bg-gray-700 rounded-lg">
          <h4 className="text-lg font-medium text-gray-200 mb-3">📋 Analiz Seçenekleri</h4>
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={includeAdaptation}
              onChange={(e) => setIncludeAdaptation(e.target.checked)}
              className="w-4 h-4 text-teal-600 bg-gray-600 border-gray-500 rounded focus:ring-teal-500 focus:ring-2"
            />
            <span className="text-gray-300">
              🔄 i+1 Seviyesinde Adapte Edilmiş Metin Oluştur
              <span className="block text-sm text-gray-400">
                Metni daha basit ve öğretici hale getirir
              </span>
            </span>
          </label>
        </div>
        
        <div className="flex gap-3 mt-4">
          <button
            onClick={activeTab === 'text' ? analyzeText : analyzeYoutube}
            disabled={loading}
            className="bg-teal-600 text-white px-6 py-2 rounded-md hover:bg-teal-700 disabled:bg-teal-800 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '⏳ Analiz ediliyor...' : '🔍 Analiz Et'}
          </button>
          
          {analysisResult && (
            <button
              onClick={clearResults}
              className="bg-gray-600 text-white px-6 py-2 rounded-md hover:bg-gray-700 transition-colors"
            >
              🗑️ Temizle
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-800 border border-red-600 text-red-200 rounded-md whitespace-pre-line">
          {error}
        </div>
      )}

      {/* Results Section */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Video Info (if YouTube analysis) */}
          {analysisResult.video_info && (
            <div className="bg-blue-700/30 p-4 rounded-lg border border-blue-500/30">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">📺 Video Bilgileri</h3>
              {analysisResult.video_info.title && (
                <p className="text-gray-200 mb-2">
                  <span className="font-medium">Başlık:</span> {analysisResult.video_info.title}
                </p>
              )}
              {analysisResult.video_info.language && (
                <p className="text-gray-200 mb-2">
                  <span className="font-medium">Dil:</span> {analysisResult.video_info.language}
                </p>
              )}
              {analysisResult.video_info.warning && (
                <div className="mt-3 p-3 bg-yellow-800/50 border border-yellow-500/50 rounded text-yellow-200">
                  ⚠️ {analysisResult.video_info.warning}
                </div>
              )}
            </div>
          )}

          {/* Download Options */}
          <div className="bg-blue-700/30 p-4 rounded-lg border border-blue-500/30 mb-6">
            <h3 className="text-lg font-semibold text-blue-400 mb-3">📥 İndirme Seçenekleri</h3>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={downloadPDF}
                disabled={pdfGenerating}
                className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:opacity-50 rounded-lg text-white font-medium transition-colors"
              >
                📄 {pdfGenerating ? 'PDF Oluşturuluyor...' : 'PDF Raporu İndir'}
              </button>
              
              {analysisResult.original_text && (
                <button
                  onClick={() => downloadText('original')}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white font-medium transition-colors"
                >
                  📝 Orijinal Metin (PDF)
                </button>
              )}
              
              {analysisResult.adapted_text && (
                <button
                  onClick={() => downloadText('adapted')}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white font-medium transition-colors"
                >
                  🔄 Adapte Metin (PDF)
                </button>
              )}
            </div>
          </div>

          {/* Original Text */}
          {analysisResult.original_text && (
            <div className="bg-gray-700 p-4 rounded-lg mb-6">
              <h3 className="text-xl font-semibold text-teal-400 mb-3">📝 Orijinal Metin</h3>
              <div className="bg-gray-800 p-4 rounded border-l-4 border-teal-500 max-h-64 overflow-y-auto">
                <div className="text-gray-200 whitespace-pre-wrap leading-relaxed">
                  {renderClickableText(analysisResult.original_text, false)}
                </div>
              </div>
              <div className="text-xs text-teal-200 mt-2 space-y-1">
                <div>💡 <strong>İpucu:</strong> <span className="bg-yellow-500 bg-opacity-40 text-yellow-200 px-1 rounded">Sarı kelimeler</span> bilinmeyen, 
                <span className="text-blue-300 px-1">mavi kelimeler</span> özel isim, normal kelimeler bilinen kelimeleri gösterir</div>
                <div>🔤 <strong>Çoklu Seçim:</strong> Birden fazla kelimeyi mouse ile seçip çevirisini görebilirsiniz</div>
              </div>
            </div>
          )}

          {/* Adapted Text */}
          {analysisResult.adapted_text && (
            <div className="bg-purple-700/30 p-4 rounded-lg border border-purple-500/30 mb-6">
              <h3 className="text-xl font-semibold text-purple-400 mb-3">🔄 i+1 Seviyesinde Adapte Edilmiş Metin</h3>
              <div className="bg-gray-800 p-4 rounded border-l-4 border-purple-500 max-h-64 overflow-y-auto mb-4">
                <div className="text-gray-200 whitespace-pre-wrap leading-relaxed">
                  {renderClickableText(
                    typeof analysisResult.adapted_text === 'object' 
                      ? analysisResult.adapted_text.adapted_text 
                      : analysisResult.adapted_text,
                    true // isAdapted = true
                  )}
                </div>
              </div>
              <div className="text-xs text-purple-200 mb-3 space-y-1">
                <div>💡 <strong>İpucu:</strong> <span className="bg-pink-500 bg-opacity-50 text-pink-200 px-1 rounded">Pembe kelimeler</span> öğrenmeniz gereken, 
                <span className="text-blue-300 px-1">mavi kelimeler</span> özel isimdir. Kelimelerin üstüne tıklayarak çevirisini görebilirsiniz.</div>
                <div>🔤 <strong>Çoklu Seçim:</strong> Birden fazla kelimeyi mouse ile seçip çevirisini görebilirsiniz</div>
              </div>
              {typeof analysisResult.adapted_text === 'object' && (
                <div className="text-sm text-purple-300">
                  <p><strong>Seviye:</strong> {analysisResult.adapted_text.adaptation_level}</p>
                  <p><strong>Yapılan Değişiklikler:</strong> {analysisResult.adapted_text.changes_made}</p>
                </div>
              )}
            </div>
          )}

          {/* Basic Statistics */}
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="text-xl font-semibold text-teal-400 mb-3">📊 Temel İstatistikler</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-teal-400">{analysisResult.basic_statistics.word_count}</p>
                <p className="text-sm text-gray-300">Kelime</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-400">{analysisResult.basic_statistics.sentence_count}</p>
                <p className="text-sm text-gray-300">Cümle</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-400">{analysisResult.basic_statistics.paragraph_count}</p>
                <p className="text-sm text-gray-300">Paragraf</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-400">{analysisResult.basic_statistics.reading_time_minutes}</p>
                <p className="text-sm text-gray-300">Dakika Okuma</p>
              </div>
            </div>
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <p className="text-sm text-gray-300">
                <span className="font-medium text-teal-400">Ortalama kelime uzunluğu:</span> {analysisResult.basic_statistics.average_word_length} karakter
              </p>
              <p className="text-sm text-gray-300">
                <span className="font-medium text-teal-400">Ortalama cümle uzunluğu:</span> {analysisResult.basic_statistics.average_sentence_length} kelime
              </p>
            </div>
          </div>

          {/* Word Analysis */}
          <div className="bg-gray-700 p-4 rounded-lg">
            <h3 className="text-xl font-semibold text-teal-400 mb-3">📝 Kelime Analizi</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-300 mb-2">
                  <span className="font-medium text-teal-400">Benzersiz kelime sayısı:</span> {analysisResult.word_analysis.unique_word_count}
                </p>
                <p className="text-sm text-gray-300 mb-2">
                  <span className="font-medium text-teal-400">Kelime çeşitliliği:</span> {analysisResult.word_analysis.lexical_diversity}
                </p>
                <p className="text-sm text-gray-300">
                  <span className="font-medium text-teal-400">Uzun kelimeler:</span> {analysisResult.word_analysis.long_words_count}
                </p>
              </div>
              <div>
                <p className="font-medium text-sm text-teal-400 mb-2">En sık kullanılan kelimeler:</p>
                <div className="space-y-1">
                  {analysisResult.word_analysis.most_frequent_words.slice(0, 5).map(([word, count], index) => (
                    <p key={index} className="text-xs text-gray-300">
                      {word}: {count} kez
                    </p>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* User Vocabulary Statistics */}
          {analysisResult.user_vocabulary_stats && (
            <div className="bg-gradient-to-r from-indigo-700/30 to-blue-700/30 p-4 rounded-lg border border-indigo-500/30">
              <h3 className="text-xl font-semibold text-indigo-400 mb-3">👤 Kişisel Kelime İstatistikleriniz</h3>
              
              {/* User Level and Stats */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="bg-indigo-800/40 p-3 rounded">
                  <h4 className="font-medium text-indigo-300 mb-2">🎯 Seviyeniz</h4>
                  <p className="text-lg font-bold text-indigo-200">{analysisResult.user_vocabulary_stats.user_level}</p>
                  <p className="text-sm text-indigo-300">Toplam Bilinen Kelime: {analysisResult.user_vocabulary_stats.total_known_words}</p>
                </div>
                <div className="bg-blue-800/40 p-3 rounded">
                  <h4 className="font-medium text-blue-300 mb-2">📈 Genel İstatistikler</h4>
                  <p className="text-sm text-blue-200">Kelime Deposu: {analysisResult.user_vocabulary_stats.total_vocabulary_entries}</p>
                  <p className="text-sm text-blue-200">Seviye Puanı: {analysisResult.user_vocabulary_stats.level_score}/5</p>
                </div>
              </div>

              {/* Text Analysis for User */}
              {analysisResult.user_vocabulary_stats.text_analysis && (
                <div className="bg-gray-800/50 p-3 rounded">
                  <h4 className="font-medium text-indigo-300 mb-3">📊 Bu Metindeki Kelime Durumunuz</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                    <div className="text-center">
                      <p className="text-xl font-bold text-green-400">{analysisResult.user_vocabulary_stats.text_analysis.known_words_in_text}</p>
                      <p className="text-xs text-gray-300">Bildiğiniz Kelime</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold text-red-400">{analysisResult.user_vocabulary_stats.text_analysis.unknown_words_in_text}</p>
                      <p className="text-xs text-gray-300">Bilinmeyen Kelime</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xl font-bold text-blue-400">{analysisResult.user_vocabulary_stats.text_analysis.comprehension_rate}%</p>
                      <p className="text-xs text-gray-300">Anlama Oranı</p>
                    </div>
                    <div className="text-center">
                      <p className={`text-xl font-bold ${
                        analysisResult.user_vocabulary_stats.text_analysis.text_difficulty === 'Kolay' ? 'text-green-400' :
                        analysisResult.user_vocabulary_stats.text_analysis.text_difficulty === 'Uygun' ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        {analysisResult.user_vocabulary_stats.text_analysis.text_difficulty}
                      </p>
                      <p className="text-xs text-gray-300">Metin Zorluğu</p>
                    </div>
                  </div>
                  
                  {/* Unknown words examples */}
                  {analysisResult.user_vocabulary_stats.text_analysis.unknown_word_examples.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-indigo-300 mb-2">🎯 Öğrenebileceğiniz kelimeler:</p>
                      <div className="flex flex-wrap gap-2">
                        {analysisResult.user_vocabulary_stats.text_analysis.unknown_word_examples.slice(0, 8).map((word, index) => (
                          <span 
                            key={index} 
                            className="bg-red-500/20 text-red-200 px-2 py-1 rounded text-xs cursor-pointer hover:bg-red-500/30 transition-colors"
                            onClick={() => translateWord(word)}
                            title={'Çeviri için tıklayın'}
                          >
                            {word}
                          </span>
                        ))}
                        {analysisResult.user_vocabulary_stats.text_analysis.unknown_word_examples.length > 8 && (
                          <span className="text-xs text-gray-400">+{analysisResult.user_vocabulary_stats.text_analysis.unknown_word_examples.length - 8} daha...</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Grammar Analysis */}
          {analysisResult.grammar_analysis && (
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-xl font-semibold text-teal-400 mb-3">📚 Gramer Analizi</h3>
              
              {/* Sentence Types */}
              {analysisResult.grammar_analysis.sentence_types && (
                <div className="mb-4">
                  <p className="font-medium text-sm text-teal-400 mb-2">Cümle türleri:</p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <p className="text-xs text-gray-300">Toplam: {analysisResult.grammar_analysis.sentence_types.total}</p>
                    <p className="text-xs text-gray-300">Soru: {analysisResult.grammar_analysis.sentence_types.questions}</p>
                    <p className="text-xs text-gray-300">Ünlem: {analysisResult.grammar_analysis.sentence_types.exclamations}</p>
                    <p className="text-xs text-gray-300">Bildirme: {analysisResult.grammar_analysis.sentence_types.statements}</p>
                  </div>
                </div>
              )}

              {/* Grammar Patterns */}
              {analysisResult.grammar_analysis.grammar_patterns && analysisResult.grammar_analysis.grammar_patterns.length > 0 && (
                <div className="mb-4">
                  <p className="font-medium text-sm text-teal-400 mb-2">Tespit edilen gramer yapıları:</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {analysisResult.grammar_analysis.grammar_patterns.slice(0, 6).map((pattern, index) => (
                      <div key={index} className="bg-gray-800 p-2 rounded text-xs">
                        <span className="text-teal-300 font-medium">{pattern.pattern_name}</span>
                        <span className="text-gray-400"> ({pattern.count} örnek)</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Complexity Indicators */}
              {analysisResult.grammar_analysis.complexity_indicators && (
                <div className="mb-4">
                  <p className="font-medium text-sm text-teal-400 mb-2">Karmaşıklık göstergeleri:</p>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    <p className="text-xs text-gray-300">
                      Bağlaç sayısı: {analysisResult.grammar_analysis.complexity_indicators.conjunction_count}
                    </p>
                    <p className="text-xs text-gray-300">
                      Karmaşık cümleler: {analysisResult.grammar_analysis.complexity_indicators.complex_sentence_count}
                    </p>
                    <p className="text-xs text-gray-300">
                      Seviye: {analysisResult.grammar_analysis.complexity_indicators.average_sentence_complexity}
                    </p>
                  </div>
                  {analysisResult.grammar_analysis.complexity_indicators.complex_sentence_examples && (
                    <div className="mt-2">
                      <p className="text-xs text-teal-400 mb-1">Karmaşık cümle örnekleri:</p>
                      {analysisResult.grammar_analysis.complexity_indicators.complex_sentence_examples.slice(0, 2).map((example, index) => (
                        <p key={index} className="text-xs text-gray-300 bg-gray-800 p-1 rounded mb-1 italic">
                          &quot;{example}&quot;
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              {/* Part of Speech Distribution */}
              {analysisResult.grammar_analysis.part_of_speech_distribution && (
                <div>
                  <p className="font-medium text-sm text-teal-400 mb-2">Kelime türleri dağılımı:</p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {Object.entries(analysisResult.grammar_analysis.part_of_speech_distribution).slice(0, 8).map(([pos, count]) => (
                      <p key={pos} className="text-xs text-gray-300">{pos}: {count}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* AI Insights - Türkçe Açıklamalar */}
          {analysisResult.ai_insights && (
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-xl font-semibold text-teal-400 mb-3">🤖 AI Değerlendirmesi (Türkçe)</h3>
              
              {analysisResult.ai_insights.ai_analysis && (
                <div className="mb-4 p-4 bg-gray-800 rounded border-l-4 border-blue-500">
                  <h4 className="font-medium text-blue-400 mb-2">📊 Genel Değerlendirme</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">
                    {analysisResult.ai_insights.ai_analysis}
                  </p>
                </div>
              )}
              
              {analysisResult.ai_insights.grammar_insights && (
                <div className="mb-4 p-4 bg-gray-800 rounded border-l-4 border-green-500">
                  <h4 className="font-medium text-green-400 mb-2">🔍 Gramer Yapıları</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">
                    {analysisResult.ai_insights.grammar_insights}
                  </p>
                </div>
              )}
              
              {analysisResult.ai_insights.vocabulary_insights && (
                <div className="mb-4 p-4 bg-gray-800 rounded border-l-4 border-purple-500">
                  <h4 className="font-medium text-purple-400 mb-2">📚 Kelime Hazinesi</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">
                    {analysisResult.ai_insights.vocabulary_insights}
                  </p>
                </div>
              )}
              
              {analysisResult.ai_insights.learning_suggestions && (
                <div className="mb-4 p-4 bg-gray-800 rounded border-l-4 border-orange-500">
                  <h4 className="font-medium text-orange-400 mb-2">💡 Öğrenme Önerileri</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">
                    {analysisResult.ai_insights.learning_suggestions}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Grammar Examples */}
          {analysisResult.grammar_examples && (
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-xl font-semibold text-teal-400 mb-3">💡 Gramer Örnekleri ve Açıklamaları</h3>
              
              {/* Detected Grammar Patterns */}
              {analysisResult.grammar_examples.detected_patterns && analysisResult.grammar_examples.detected_patterns.length > 0 && (
                <div className="mb-6">
                  <p className="font-medium text-sm text-teal-400 mb-3">🔍 Tespit Edilen Gramer Yapıları:</p>
                  <div className="space-y-4">
                    {analysisResult.grammar_examples.detected_patterns.map((pattern, index) => (
                      <div key={index} className="bg-gray-800 p-4 rounded border-l-4 border-teal-400">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <h4 className="font-semibold text-teal-300 text-sm">{pattern.pattern_name}</h4>
                            <p className="text-xs text-gray-400">{pattern.detailed_info}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs bg-teal-600 px-2 py-1 rounded">{pattern.count} örnek</span>
                            
                            {/* Grammar Knowledge Buttons */}
                            <div className="flex gap-1">
                              <button
                                onClick={() => updateGrammarKnowledge(getPatternKey(pattern.pattern_name), 'known')}
                                disabled={grammarUpdating === getPatternKey(pattern.pattern_name)}
                                className="px-2 py-1 text-xs bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded transition-colors"
                                title={'Bu gramer yapısını biliyorum'}
                              >
                                ✅ Biliyorum
                              </button>
                              <button
                                onClick={() => updateGrammarKnowledge(getPatternKey(pattern.pattern_name), 'unknown')}
                                disabled={grammarUpdating === getPatternKey(pattern.pattern_name)}
                                className="px-2 py-1 text-xs bg-red-600 hover:bg-red-700 disabled:opacity-50 rounded transition-colors"
                                title={'Bu gramer yapısını bilmiyorum'}
                              >
                                ❌ Bilmiyorum
                              </button>
                              <button
                                onClick={() => updateGrammarKnowledge(getPatternKey(pattern.pattern_name), 'ignored')}
                                disabled={grammarUpdating === getPatternKey(pattern.pattern_name)}
                                className="px-2 py-1 text-xs bg-gray-600 hover:bg-gray-700 disabled:opacity-50 rounded transition-colors"
                                title={'Bu gramer yapısını görmezden gel'}
                              >
                                ⏭️ Görmezden Gel
                              </button>
                            </div>
                          </div>
                        </div>
                        
                        <p className="text-xs text-gray-300 mb-3 leading-relaxed">{pattern.explanation}</p>
                        
                        <div className="space-y-2">
                          <p className="text-xs font-medium text-teal-400">📝 Örnekler ve Çevirileri:</p>
                          {pattern.translated_examples && pattern.translated_examples.map((example, exIndex) => (
                            <div key={exIndex} className="bg-gray-900 p-3 rounded">
                              <p className="text-xs text-gray-100 mb-1">
                                🇺🇸 <span className="italic">&quot;{example.english}&quot;</span>
                              </p>
                              <p className="text-xs text-gray-300">
                                🇹🇷 <span className="italic">&quot;{example.turkish}&quot;</span>
                              </p>
                            </div>
                          ))}
                          
                          {/* Fallback to regular examples if translations not available */}
                          {(!pattern.translated_examples || pattern.translated_examples.length === 0) && pattern.examples.map((example, exIndex) => (
                            <p key={exIndex} className="text-xs text-gray-200 bg-gray-900 p-2 rounded italic">
                              &quot;{example}&quot;
                            </p>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tense Examples */}
              {analysisResult.grammar_examples.tense_examples && analysisResult.grammar_examples.tense_examples.length > 0 && (
                <div className="mb-4">
                  <p className="font-medium text-sm text-teal-400 mb-2">⏰ Zaman Formları:</p>
                  <div className="space-y-1">
                    {analysisResult.grammar_examples.tense_examples.slice(0, 4).map((example, index) => (
                      <p key={index} className="text-xs text-gray-300 bg-gray-800 p-2 rounded border-l-2 border-blue-400">
                        {example}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Modal Examples */}
              {analysisResult.grammar_examples.modal_examples && analysisResult.grammar_examples.modal_examples.length > 0 && (
                <div className="mb-4">
                  <p className="font-medium text-sm text-teal-400 mb-2">🎯 Modal Fiiller:</p>
                  <div className="space-y-1">
                    {analysisResult.grammar_examples.modal_examples.slice(0, 3).map((example, index) => (
                      <p key={index} className="text-xs text-gray-300 bg-gray-800 p-2 rounded border-l-2 border-purple-400">
                        &quot;{example}&quot;
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Complex Structures */}
              {analysisResult.grammar_examples.complex_structures && analysisResult.grammar_examples.complex_structures.length > 0 && (
                <div className="mb-4">
                  <p className="font-medium text-sm text-teal-400 mb-2">🏗️ Karmaşık Yapılar:</p>
                  <div className="space-y-1">
                    {analysisResult.grammar_examples.complex_structures.slice(0, 4).map((example, index) => (
                      <p key={index} className="text-xs text-gray-300 bg-gray-800 p-2 rounded border-l-2 border-orange-400">
                        {example}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Idioms and Expressions */}
              {analysisResult.grammar_examples.detected_patterns && analysisResult.grammar_examples.detected_patterns.some(p => p.pattern_name.includes('Idiom') || p.pattern_name.includes('Expression') || p.pattern_name.includes('Phrasal') || p.pattern_name.includes('Collocation')) && (
                <div className="mb-4">
                  <p className="font-medium text-sm text-purple-400 mb-3">🎭 Kalıp İfadeler ve Deyimler:</p>
                  <div className="grid gap-3">
                    {/* Idioms */}
                    {analysisResult.grammar_examples.detected_patterns.filter(p => p.pattern_name.includes('Idiom')).map((pattern, index) => (
                      <div key={`idiom-${index}`} className="bg-gradient-to-r from-purple-800/30 to-purple-700/30 p-3 rounded border-l-4 border-purple-400">
                        <h5 className="font-semibold text-purple-300 text-sm mb-1">🎭 {pattern.pattern_name}</h5>
                        <p className="text-xs text-gray-300 mb-2">{pattern.explanation}</p>
                        {pattern.examples && pattern.examples.length > 0 && (
                          <div className="space-y-1">
                            {pattern.examples.slice(0, 2).map((example, exIndex) => (
                              <p 
                                key={exIndex} 
                                className="text-xs text-purple-200 bg-purple-900/40 p-2 rounded italic cursor-pointer hover:bg-purple-800/50 transition-colors"
                                onClick={() => translateWord(example)}
                                title={'Çeviri için tıklayın'}
                              >
                                &quot;{example}&quot;
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Phrasal Verbs */}
                    {analysisResult.grammar_examples.detected_patterns.filter(p => p.pattern_name.includes('Phrasal')).map((pattern, index) => (
                      <div key={`phrasal-${index}`} className="bg-gradient-to-r from-blue-800/30 to-blue-700/30 p-3 rounded border-l-4 border-blue-400">
                        <h5 className="font-semibold text-blue-300 text-sm mb-1">⚡ {pattern.pattern_name}</h5>
                        <p className="text-xs text-gray-300 mb-2">{pattern.explanation}</p>
                        {pattern.examples && pattern.examples.length > 0 && (
                          <div className="space-y-1">
                            {pattern.examples.slice(0, 3).map((example, exIndex) => (
                              <p 
                                key={exIndex} 
                                className="text-xs text-blue-200 bg-blue-900/40 p-2 rounded font-medium cursor-pointer hover:bg-blue-800/50 transition-colors"
                                onClick={() => translateWord(example)}
                                title="Çeviri için tıklayın"
                              >
                                &quot;{example}&quot;
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Collocations */}
                    {analysisResult.grammar_examples.detected_patterns.filter(p => p.pattern_name.includes('Collocation')).map((pattern, index) => (
                      <div key={`collocation-${index}`} className="bg-gradient-to-r from-green-800/30 to-green-700/30 p-3 rounded border-l-4 border-green-400">
                        <h5 className="font-semibold text-green-300 text-sm mb-1">🔗 {pattern.pattern_name}</h5>
                        <p className="text-xs text-gray-300 mb-2">{pattern.explanation}</p>
                        {pattern.examples && pattern.examples.length > 0 && (
                          <div className="space-y-1">
                            {pattern.examples.slice(0, 3).map((example, exIndex) => (
                              <p 
                                key={exIndex} 
                                className="text-xs text-green-200 bg-green-900/40 p-2 rounded cursor-pointer hover:bg-green-800/50 transition-colors"
                                onClick={() => translateWord(example)}
                                title="Çeviri için tıklayın"
                              >
                                &quot;{example}&quot;
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}

                    {/* Fixed Expressions */}
                    {analysisResult.grammar_examples.detected_patterns.filter(p => p.pattern_name.includes('Expression')).map((pattern, index) => (
                      <div key={`expression-${index}`} className="bg-gradient-to-r from-yellow-800/30 to-yellow-700/30 p-3 rounded border-l-4 border-yellow-400">
                        <h5 className="font-semibold text-yellow-300 text-sm mb-1">📝 {pattern.pattern_name}</h5>
                        <p className="text-xs text-gray-300 mb-2">{pattern.explanation}</p>
                        {pattern.examples && pattern.examples.length > 0 && (
                          <div className="space-y-1">
                            {pattern.examples.slice(0, 2).map((example, exIndex) => (
                              <p 
                                key={exIndex} 
                                className="text-xs text-yellow-200 bg-yellow-900/40 p-2 rounded cursor-pointer hover:bg-yellow-800/50 transition-colors"
                                onClick={() => translateWord(example)}
                                title="Çeviri için tıklayın"
                              >
                                &quot;{example}&quot;
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Word Translation Modal */}
      {(selectedWord || wordTranslation) && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-600 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-blue-400">
                📝 {wordTranslation && wordTranslation.word.includes(' ') ? 'İfade Çevirisi' : 'Kelime Çevirisi'}
              </h3>
              <button
                onClick={closeWordTranslation}
                className="text-gray-400 hover:text-white text-xl"
              >
                ✕
              </button>
            </div>
            
            {translationLoading ? (
              <div className="text-center py-6">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-3"></div>
                <p className="text-gray-300">Çeviri yapılıyor...</p>
              </div>
            ) : wordTranslation ? (
              <div>
                <div className="bg-gray-700 p-4 rounded-lg mb-4">
                  <p className="text-white font-semibold text-lg mb-2">
                    &quot;{wordTranslation.word}&quot;
                  </p>
                  <p className="text-teal-400 text-lg mb-2">
                    {wordTranslation.translation}
                  </p>
                  {wordTranslation.explanation && (
                    <p className="text-gray-300 text-sm">
                      {wordTranslation.explanation}
                    </p>
                  )}
                </div>
                
                {/* Kelime bilgisi butonları - sadece tek kelime için göster */}
                {!wordTranslation.word.includes(' ') && (
                  <>
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleWordKnowledge('known')}
                        className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg text-white font-medium transition-colors"
                      >
                        ✅ Biliyorum
                      </button>
                      <button
                        onClick={() => handleWordKnowledge('learning')}
                        className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors"
                      >
                        📚 Öğreniyorum
                      </button>
                      <button
                        onClick={() => handleWordKnowledge('unknown')}
                        className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white font-medium transition-colors"
                      >
                        ❌ Bilmiyorum
                      </button>
                    </div>
                    
                    <button
                      onClick={() => handleWordKnowledge('ignored')}
                      className="w-full mt-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white font-medium transition-colors"
                    >
                      👁️ Görmezden Gel
                    </button>
                  </>
                )}
                
                {/* Çoklu kelime için sadece kapat butonu */}
                {wordTranslation.word.includes(' ') && (
                  <div className="mt-4">
                    <p className="text-sm text-gray-400 text-center mb-3">
                      💡 İfade çevirisi - Kelime takibi sadece tek kelimeler için yapılır
                    </p>
                    <button
                      onClick={closeWordTranslation}
                      className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium transition-colors"
                    >
                      📋 Tamam
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-gray-300">Çeviri bulunamadı</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TextAnalysis;
