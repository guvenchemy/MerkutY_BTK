'use client';

import React, { useState } from 'react';

interface TextAnalysisResult {
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
  };
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
          include_examples: true
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
          include_examples: true
        }),
      });

      const result: AnalysisResponse = await response.json();

      if (result.success && result.data) {
        setAnalysisResult(result.data);
      } else {
        setError(result.error || 'YouTube analizi sırasında bir hata oluştu');
      }
    } catch (err) {
      setError('Sunucuya bağlanırken hata oluştu');
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
              YouTube video URL'sini girin (transkripti olan videolar için)
            </p>
          </div>
        )}
        
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
        <div className="mb-6 p-4 bg-red-800 border border-red-600 text-red-200 rounded-md">
          {error}
        </div>
      )}

      {/* Results Section */}
      {analysisResult && (
        <div className="space-y-6">
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
                          "{example}"
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

          {/* AI Insights */}
          {analysisResult.ai_insights?.ai_analysis && (
            <div className="bg-gray-700 p-4 rounded-lg">
              <h3 className="text-xl font-semibold text-teal-400 mb-3">🤖 AI Değerlendirmesi</h3>
              <p className="text-sm text-gray-300 leading-relaxed">
                {analysisResult.ai_insights.ai_analysis}
              </p>
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
                          <div>
                            <h4 className="font-semibold text-teal-300 text-sm">{pattern.pattern_name}</h4>
                            <p className="text-xs text-gray-400">{pattern.detailed_info}</p>
                          </div>
                          <span className="text-xs bg-teal-600 px-2 py-1 rounded">{pattern.count} örnek</span>
                        </div>
                        
                        <p className="text-xs text-gray-300 mb-3 leading-relaxed">{pattern.explanation}</p>
                        
                        <div className="space-y-2">
                          <p className="text-xs font-medium text-teal-400">📝 Örnekler ve Çevirileri:</p>
                          {pattern.translated_examples && pattern.translated_examples.map((example, exIndex) => (
                            <div key={exIndex} className="bg-gray-900 p-3 rounded">
                              <p className="text-xs text-gray-100 mb-1">
                                🇺🇸 <span className="italic">"{example.english}"</span>
                              </p>
                              <p className="text-xs text-gray-300">
                                🇹🇷 <span className="italic">"{example.turkish}"</span>
                              </p>
                            </div>
                          ))}
                          
                          {/* Fallback to regular examples if translations not available */}
                          {(!pattern.translated_examples || pattern.translated_examples.length === 0) && pattern.examples.map((example, exIndex) => (
                            <p key={exIndex} className="text-xs text-gray-200 bg-gray-900 p-2 rounded italic">
                              "{example}"
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
                        "{example}"
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Complex Structures */}
              {analysisResult.grammar_examples.complex_structures && analysisResult.grammar_examples.complex_structures.length > 0 && (
                <div>
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
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TextAnalysis;
