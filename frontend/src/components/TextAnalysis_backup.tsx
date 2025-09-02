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
    long_words: string[];
    word_difficulty_distribution: { [key: string]: number };
    difficult_words: string[];
    technical_terms: string[];
  };
  readability: {
    flesch_reading_ease: number;
    difficulty_level: string;
    grade_level: number;
    target_audience: string;
    improvement_suggestions: string[];
  };
  advanced_features?: {
    keyword_density: { [key: string]: number };
    phrase_analysis: Array<{ phrase: string; frequency: number; importance: number }>;
    entity_recognition: Array<{ entity: string; type: string; confidence: number }>;
  };
  adaptation?: {
    adapted_text: string;
    changes_made: string[];
    difficulty_reduced_by: number;
    simplified_vocabulary: { [key: string]: string };
    grammar_simplifications: string[];
  };
  ai_generated_content: {
    structure_analysis: string;
    content_type: string;
    purpose: string;
    strengths: string[];
    suggestions: string[];
    overall_assessment: string;
  };
  summary: {
    main_topic: string;
    key_points: string[];
    target_level: string;
    recommended_study_approach: string;
  };
  learning_insights: {
    cefr_level: string;
    learning_focus: string[];
    grammar_practice_needed: string[];
    vocabulary_to_learn: string[];
    next_steps: string[];
  };
  processing_info: {
    processing_time: number;
    analysis_timestamp: string;
    version: string;
  };
  example_sentences: {
    simple_examples: string[];
    intermediate_examples: string[];
    advanced_examples: string[];
    vocabulary_examples: string[];
    grammar_examples: string[];
    tense_examples: string[];
    modal_examples: string[];
    complex_structures: string[];
  };
  video_info?: {
    title?: string;
    warning?: string;
    language?: string;
  };
  web_info?: {
    source_url?: string;
    site_type?: string;
    domain?: string;
    content_length?: number;
    extracted_at?: string;
  };
}

interface AnalysisResponse {
  success: boolean;
  data?: TextAnalysisResult;
  error?: string;
}

const TextAnalysis: React.FC = () => {
  const [text, setText] = useState('');
  const [url, setUrl] = useState(''); // Tek URL input (YouTube, Medium, Wikipedia için)
  const [analysisResult, setAnalysisResult] = useState<TextAnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'text' | 'url'>('text');
  const [includeAdaptation, setIncludeAdaptation] = useState(false);
  // const [pdfGenerating, setPdfGenerating] = useState(false); // Currently unused
  const [userId] = useState<number>(1); // Geçici user ID
  // const [grammarUpdating, setGrammarUpdating] = useState<string | null>(null); // Currently unused
  // const [selectedWord, setSelectedWord] = useState<string | null>(null); // Currently unused
  // const [wordTranslation, setWordTranslation] = useState<WordTranslation | null>(null); // Currently unused
  // const [translationLoading, setTranslationLoading] = useState(false); // Currently unused
  // const [userKnownWords, setUserKnownWords] = useState<string[]>([]); // Currently unused

  // URL tipini otomatik algıla
  const detectUrlType = (url: string): 'youtube' | 'medium' | 'wikipedia' | 'unsupported' => {
    if (!url) return 'unsupported';
    
    const cleanUrl = url.toLowerCase().trim();
    
    if (cleanUrl.includes('youtube.com') || cleanUrl.includes('youtu.be')) {
      return 'youtube';
    } else if (cleanUrl.includes('medium.com')) {
      return 'medium';
    } else if (cleanUrl.includes('wikipedia.org')) {
      return 'wikipedia';
    }
    
    return 'unsupported';
  };

  // Text analysis
  const analyzeText = async () => {
    if (!text.trim()) {
      setError('Metin giriniz');
      return;
    }

    if (text.length < 10) {
      setError('En az 10 karakter gerekli');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/text-analysis/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: text,
          include_examples: true,
          include_adaptation: includeAdaptation,
          user_id: userId,
          username: `user_${userId}`
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

  // URL analysis (YouTube, Medium, Wikipedia)
  const analyzeUrl = async () => {
    if (!url.trim()) {
      setError('URL giriniz');
      return;
    }

    const urlType = detectUrlType(url);
    
    if (urlType === 'unsupported') {
      setError('Sadece YouTube, Medium ve Wikipedia linkleri desteklenmektedir');
      return;
    }

    setLoading(true);
    setError('');

    try {
      let endpoint = '';
      const requestBody: Record<string, unknown> = {
        include_examples: true,
        include_adaptation: includeAdaptation,
        user_id: userId
      };

      // URL tipine göre endpoint ve request body'yi ayarla
      if (urlType === 'youtube') {
        endpoint = 'http://localhost:8000/api/analysis/analyze-youtube';
        requestBody.video_url = url;
      } else if (urlType === 'medium' || urlType === 'wikipedia') {
        endpoint = 'http://localhost:8000/api/text-analysis/analyze-web';
        requestBody.web_url = url;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const result: AnalysisResponse = await response.json();

      if (result.success && result.data) {
        setAnalysisResult(result.data);
        
        // YouTube IP block uyarısı kontrolü
        if (urlType === 'youtube' && result.data.video_info?.warning) {
          setError(`⚠️ ${result.data.video_info.warning}`);
        }
      } else {
        // Hata durumları
        if (urlType === 'youtube' && (result.error?.includes('IP engeli') || result.error?.includes('IP block'))) {
          setError(`🚫 ${result.error}\n\n💡 Çözüm önerileri:\n• VPN kullanın\n• Farklı internet bağlantısı deneyin\n• Daha sonra tekrar deneyin`);
        } else {
          setError(result.error || `${urlType.charAt(0).toUpperCase() + urlType.slice(1)} analizi sırasında bir hata oluştu`);
        }
      }
    } catch (err) {
      setError('Sunucuya bağlanırken hata oluştu');
      console.error('URL analysis error:', err);
    } finally {
      setLoading(false);
    }
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
          onClick={() => setActiveTab('url')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'url'
              ? 'text-teal-400 border-b-2 border-teal-400'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          🔗 Link Analizi (YouTube, Medium, Wikipedia)
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
              URL Linki:
            </label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="YouTube, Medium veya Wikipedia linki yapıştırın..."
              className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:ring-2 focus:ring-teal-500 focus:border-transparent"
            />
            <div className="text-sm text-gray-400 mt-2 space-y-1">
              <p>🔗 <strong>Desteklenen linkler:</strong></p>
              <div className="ml-2 space-y-1">
                <p>• <span className="text-red-400">🎥 YouTube:</span> youtube.com, youtu.be</p>
                <p>• <span className="text-orange-400">📝 Medium:</span> medium.com makale linkleri</p>
                <p>• <span className="text-blue-400">📚 Wikipedia:</span> wikipedia.org sayfaları</p>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                💡 URL tipini otomatik algılar ve ona göre içeriği çeker
              </p>
            </div>
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
            onClick={activeTab === 'text' ? analyzeText : analyzeUrl}
            disabled={loading}
            className="bg-teal-600 text-white px-6 py-2 rounded-md hover:bg-teal-700 disabled:bg-teal-800 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? '⏳ Analiz ediliyor...' : '🔍 Analiz Et'}
          </button>
          
          {analysisResult && (
            <button
              onClick={() => {
                setAnalysisResult(null);
                setError('');
                setText('');
                setUrl('');
              }}
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
          {/* Source Info (Video/Web) */}
          {(analysisResult.video_info || analysisResult.web_info) && (
            <div className="bg-blue-700/30 p-4 rounded-lg border border-blue-500/30">
              {analysisResult.video_info && (
                <>
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
                </>
              )}
              
              {analysisResult.web_info && (
                <>
                  <h3 className="text-lg font-semibold text-blue-400 mb-2">🌐 Web Sitesi Bilgileri</h3>
                  {analysisResult.web_info.site_type && (
                    <p className="text-gray-200 mb-2">
                      <span className="font-medium">Site Tipi:</span> {analysisResult.web_info.site_type}
                    </p>
                  )}
                  {analysisResult.web_info.source_url && (
                    <p className="text-gray-200 mb-2">
                      <span className="font-medium">Kaynak:</span> 
                      <a href={analysisResult.web_info.source_url} target="_blank" rel="noopener noreferrer" className="text-teal-400 hover:text-teal-300 ml-1">
                        {analysisResult.web_info.domain}
                      </a>
                    </p>
                  )}
                  {analysisResult.web_info.content_length && (
                    <p className="text-gray-200 mb-2">
                      <span className="font-medium">İçerik Uzunluğu:</span> {analysisResult.web_info.content_length.toLocaleString()} karakter
                    </p>
                  )}
                </>
              )}
            </div>
          )}

          {/* Basic Statistics */}
          <div className="bg-gray-700 p-6 rounded-lg">
            <h3 className="text-xl font-semibold text-teal-400 mb-4">📊 Temel İstatistikler</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{analysisResult.basic_statistics.word_count}</div>
                <div className="text-gray-400">Kelime</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{analysisResult.basic_statistics.sentence_count}</div>
                <div className="text-gray-400">Cümle</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{analysisResult.basic_statistics.paragraph_count}</div>
                <div className="text-gray-400">Paragraf</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-white">{analysisResult.basic_statistics.reading_time_minutes}</div>
                <div className="text-gray-400">Dk okuma</div>
              </div>
            </div>
          </div>

          {/* Readability */}
          <div className="bg-gray-700 p-6 rounded-lg">
            <h3 className="text-xl font-semibold text-teal-400 mb-4">📖 Okunabilirlik</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-lg font-medium text-white">{analysisResult.readability.difficulty_level}</div>
                <div className="text-gray-400">Zorluk Seviyesi</div>
              </div>
              <div>
                <div className="text-lg font-medium text-white">{analysisResult.readability.grade_level}. Sınıf</div>
                <div className="text-gray-400">Seviye</div>
              </div>
              <div>
                <div className="text-lg font-medium text-white">{analysisResult.readability.target_audience}</div>
                <div className="text-gray-400">Hedef Kitle</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TextAnalysis;
