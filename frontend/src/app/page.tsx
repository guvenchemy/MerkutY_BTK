'use client';

import { useState, useEffect } from 'react';
import VocabularyUpload from '../components/VocabularyUpload';

// Types for our API responses
interface UserStats {
  username: string;
  vocabulary_size: number;
  level: string;
  level_score: number;
  known_words_sample: string[];
  vocabulary_stats?: {
    known_words: number;
    unknown_words: number;
    ignored_words: number;
    total_managed: number;
  };
  krashen_readiness: {
    can_handle_i_plus_1: boolean;
    recommended_unknown_percentage: number;
    next_milestone: number;
  };
}

interface AdaptationResult {
  original_text: string;
  adapted_text: string;
  original_analysis: {
    total_words: number;
    known_words: number;
    unknown_words: number;
    known_percentage: number;
    unknown_percentage: number;
    difficulty_level: string;
  };
  adapted_analysis: {
    total_words: number;
    known_words: number;
    unknown_words: number;
    known_percentage: number;
    unknown_percentage: number;
    difficulty_level: string;
  };
  original_word_analysis?: {
    word_status: { [key: string]: boolean };
    known_words_list: string[];
    total_known_words: number;
  };
  adapted_word_analysis?: {
    word_status: { [key: string]: boolean };
    known_words_list: string[];
    total_known_words: number;
  };
  user_vocabulary_size: number;
  adaptation_method: string;
  improvement: {
    unknown_percentage_change: number;
    closer_to_target: boolean;
  };
}

interface WordExplanation {
  translation: string;
  example: string;
  example_explanation: string;
}

export default function Home() {
  // Authentication State
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginUsername, setLoginUsername] = useState('');
  const [showLoginForm, setShowLoginForm] = useState(true);
  
  // User Management State
  const [currentUser, setCurrentUser] = useState('');
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  
  // YouTube Processing State
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Text Content State
  const [originalText, setOriginalText] = useState('');
  const [adaptedText, setAdaptedText] = useState('');
  const [adaptationResult, setAdaptationResult] = useState<AdaptationResult | null>(null);
  
  // Interactive Features State
  const [selectedText, setSelectedText] = useState<string | null>(null);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [wordExplanation, setWordExplanation] = useState<WordExplanation | null>(null);
  const [showExplanationModal, setShowExplanationModal] = useState(false);
  const [isLoadingExplanation, setIsLoadingExplanation] = useState(false);
  const [isAddingWord, setIsAddingWord] = useState(false);
  
  // Settings State
  const [targetUnknownPercentage, setTargetUnknownPercentage] = useState(10);

  // Handle login
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginUsername.trim()) {
      alert('Please enter a username');
      return;
    }
    
    setCurrentUser(loginUsername.trim());
    setIsLoggedIn(true);
    setShowLoginForm(false);
  };

  const handleLogout = () => {
    setCurrentUser('');
    setIsLoggedIn(false);
    setShowLoginForm(true);
    setUserStats(null);
    setOriginalText('');
    setAdaptedText('');
    setAdaptationResult(null);
  };

  // Load user stats on component mount
  useEffect(() => {
    if (isLoggedIn && currentUser) {
      loadUserStats();
    }
  }, [currentUser, isLoggedIn]);

  const loadUserStats = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/adaptation/user-stats/${currentUser}`);
      if (response.ok) {
        const stats = await response.json();
        setUserStats(stats);
      }
    } catch (err) {
      console.error('Failed to load user stats:', err);
    }
  };

  const handleYouTubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    setOriginalText('');
    setAdaptedText('');
    setAdaptationResult(null);

    if (!url) {
      setError('Please enter a YouTube URL.');
      setIsLoading(false);
      return;
    }

    try {
      const endpoint = '/api/adaptation/youtube';
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          youtube_url: url, 
          username: currentUser,
          target_unknown_percentage: targetUnknownPercentage
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process video.');
      }

      const data = await response.json();
      
      setOriginalText(data.original_transcript || data.original_text);
      setAdaptedText(data.adapted_text);
      setAdaptationResult(data);
      
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim()) {
      let selectedText = selection.toString().trim();
      
      // Clean the selected text: remove leading/trailing spaces and normalize
      selectedText = selectedText.replace(/^\s+|\s+$/g, '').replace(/\s+/g, ' ');
      
      console.log('Selected text:', selectedText);
      setSelectedText(selectedText);
      setSelectedWord(selectedText);
      handleWordExplanation(selectedText);
      
      // Reload word analysis from backend to include selected text
      if (adaptationResult && originalText) {
        reloadWordAnalysis();
      }
    }
  };

  const reloadWordAnalysis = async () => {
    if (!adaptationResult || !originalText) return;
    
    try {
      // Re-analyze both original and adapted texts with updated vocabulary
      const originalAnalysisResponse = await fetch('http://localhost:8000/api/adaptation/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: originalText,
          username: currentUser
        }),
      });
      
      const adaptedAnalysisResponse = await fetch('http://localhost:8000/api/adaptation/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: adaptationResult.adapted_text,
          username: currentUser
        }),
      });
      
      if (originalAnalysisResponse.ok && adaptedAnalysisResponse.ok) {
        const originalAnalysisData = await originalAnalysisResponse.json();
        const adaptedAnalysisData = await adaptedAnalysisResponse.json();
        
        // Update adaptation result with new word analysis for both texts
        setAdaptationResult(prev => prev ? {
          ...prev,
          original_word_analysis: originalAnalysisData.word_analysis,
          adapted_word_analysis: adaptedAnalysisData.word_analysis
        } : null);
      }
    } catch (analysisErr) {
      console.error('Failed to reload word analysis:', analysisErr);
    }
  };

  const handleWordClick = (word: string) => {
    setSelectedWord(word);
    handleWordExplanation(word);
  };

  const handleWordExplanation = async (wordOrPhrase: string) => {
    setShowExplanationModal(true);
    setIsLoadingExplanation(true);
    setWordExplanation(null);
    
    try {
      // Clean the word/phrase but preserve spaces for phrases
      const cleanText = wordOrPhrase.replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
      
      const response = await fetch('http://localhost:8000/api/adaptation/explain', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          words: [cleanText], 
          username: currentUser 
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Explanation response:', data);
        
        if (data.explanations && data.explanations[cleanText]) {
          setWordExplanation(data.explanations[cleanText]);
        } else {
          // Fallback explanation
          setWordExplanation({
            translation: "Çeviri bulunamadı",
            example: `Example: "${cleanText}" is used in sentences.`,
            example_explanation: "Bu kelime/kelime grubu için açıklama bulunamadı."
          });
        }
      } else {
        throw new Error('Failed to get explanation');
      }
    } catch (err) {
      console.error('Failed to get word explanation:', err);
      setWordExplanation({
        translation: "Bağlantı hatası",
        example: `"${wordOrPhrase}" için açıklama alınamadı.`,
        example_explanation: "Açıklama servisi şu anda kullanılamıyor."
      });
    } finally {
      setIsLoadingExplanation(false);
    }
  };

  const handleAddWordToVocabulary = async (word: string, action: 'known' | 'unknown' | 'ignore') => {
    setIsAddingWord(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/vocabulary/add-word', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          username: currentUser, 
          word: word.toLowerCase(),
          action: action 
        }),
      });

      if (response.ok) {
        // Reload user stats to reflect changes
        await loadUserStats();
        
        // If we have adaptation result, reload word analysis to update colors
        if (adaptationResult && originalText) {
          await reloadWordAnalysis();
        }
        
        // Close modal
        setShowExplanationModal(false);
        
        // Show success message
        const responseData = await response.json();
        const actionText = action === 'known' ? 'bildiğin kelimeler listesine' : action === 'unknown' ? 'öğrenme listesine' : 'görmezden gelinen kelimeler listesine';
        const verb = responseData.updated ? 'güncellendi' : 'eklendi';
        alert(`"${word}" ${actionText} ${verb}!`);
      } else {
        throw new Error('Failed to add word');
      }
    } catch (err) {
      console.error('Failed to add word:', err);
      alert('Kelime eklenirken hata oluştu.');
    } finally {
      setIsAddingWord(false);
    }
  };

  const isWordKnown = (word: string, wordAnalysis?: { word_status: { [key: string]: boolean } }): boolean => {
    if (!wordAnalysis) {
      // Fallback to userStats if no word analysis available
      if (!userStats) return true;
      const cleanWord = word.toLowerCase();
      return userStats.known_words_sample.some(knownWord => 
        knownWord.toLowerCase() === cleanWord
      );
    }
    
    const cleanWord = word.toLowerCase();
    return wordAnalysis.word_status[cleanWord] || false;
  };

  const renderClickableText = (text: string, isAdapted: boolean = false, wordAnalysis?: { word_status: { [key: string]: boolean } }) => {
    // Smart word splitting that preserves contractions and common phrases
    const parts = text.split(/(\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b|\s+|[^\w\s])/);
    
    return (
      <div 
        className="text-gray-300 whitespace-pre-wrap leading-relaxed select-text"
        onMouseUp={handleTextSelection}
      >
        {parts.map((part, index) => {
          // Check if this part is a word (letters + apostrophes)
          const isWord = /^[a-zA-Z]+(?:'[a-zA-Z]+)?$/.test(part);
          
          if (!isWord || part.trim() === '') {
            return <span key={index}>{part}</span>;
          }
          
          const cleanWord = part.toLowerCase();
          const known = isWordKnown(cleanWord, wordAnalysis);
          
          // Color coding based on knowledge
          let wordClass = "cursor-pointer px-1 rounded transition-colors duration-200 ";
          
          if (isAdapted) {
            // In adapted text: No color for known, Pink for unknown (learning targets)
            if (known) {
              wordClass += "hover:bg-gray-600 hover:text-white";
            } else {
              wordClass += "hover:bg-pink-600 hover:text-white bg-pink-500 bg-opacity-50 text-pink-200 font-bold";
            }
          } else {
            // In original text: No color for known, Yellow for unknown
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
              onClick={() => handleWordClick(cleanWord)}
              title={`${known ? 'Known' : 'Unknown'} word - Click for explanation`}
            >
              {part}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-4 md:p-12 bg-gray-900 text-white font-sans">
      <div className="w-full max-w-7xl">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-extrabold text-teal-400">Nexus</h1>
          <p className="text-lg text-gray-400 mt-2">
            AI-Powered Language Learning with i+1 Theory
          </p>
          
          {/* Login/Logout Button */}
          <div className="mt-4">
            {isLoggedIn ? (
              <div className="flex items-center justify-center gap-4">
                <span className="text-teal-400 font-bold">👤 {currentUser}</span>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm"
                >
                  🚪 Logout
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowLoginForm(true)}
                className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2 rounded-lg text-sm font-bold"
              >
                🔑 Login
              </button>
            )}
          </div>
        </header>

        {/* Login Form */}
        {showLoginForm && !isLoggedIn && (
          <div className="bg-gray-800 rounded-lg p-6 max-w-md mx-auto mb-8">
            <h2 className="text-2xl font-bold text-teal-400 mb-4 text-center">🔑 Login to Nexus</h2>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Username
                </label>
                <input
                  type="text"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-teal-500"
                  placeholder="Enter your username"
                  required
                />
              </div>
              <button
                type="submit"
                className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-300"
              >
                🚀 Start Learning
              </button>
            </form>
            <div className="mt-4 text-center text-sm text-gray-400">
              💡 Enter any username to start. New users will be created automatically.
            </div>
          </div>
        )}

        {/* Main App Content - Only show when logged in */}
        {isLoggedIn && (
          <>
            {userStats && (
              <div className="mt-4 bg-gray-800 rounded-lg p-4 max-w-4xl mx-auto">
                <div className="flex flex-wrap justify-center gap-4 text-sm mb-3">
                  <span className="bg-teal-600 px-3 py-1 rounded-full">
                    👤 {userStats.username}
                  </span>
                  <span className="bg-blue-600 px-3 py-1 rounded-full">
                    📚 {userStats.vocabulary_size} words
                  </span>
                  <span className="bg-purple-600 px-3 py-1 rounded-full">
                    🎯 {userStats.level}
                  </span>
                  <span className="bg-green-600 px-3 py-1 rounded-full">
                    🧠 i+1 Ready: {userStats.krashen_readiness.can_handle_i_plus_1 ? '✅' : '❌'}
                  </span>
                </div>
                
                {/* Detailed Vocabulary Stats */}
                {userStats.vocabulary_stats && (
                  <div className="border-t border-gray-700 pt-3">
                    <h4 className="text-center text-gray-300 font-bold mb-2">📊 Vocabulary Management</h4>
                    <div className="flex flex-wrap justify-center gap-3 text-xs">
                      <span className="bg-green-600 px-2 py-1 rounded">
                        ✅ Known: {userStats.vocabulary_stats.known_words}
                      </span>
                      <span className="bg-yellow-500 bg-opacity-40 text-yellow-200 px-2 py-1 rounded">
                        ❌ Unknown: {userStats.vocabulary_stats.unknown_words}
                      </span>
                      <span className="bg-gray-600 px-2 py-1 rounded">
                        ⏭️ Ignored: {userStats.vocabulary_stats.ignored_words}
                      </span>
                      <span className="bg-blue-600 px-2 py-1 rounded">
                        📝 Total Managed: {userStats.vocabulary_stats.total_managed}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Color Legend */}
            <div className="bg-gray-800 rounded-lg p-4 mb-6 max-w-4xl mx-auto">
              <h3 className="text-lg font-bold text-teal-400 mb-3 text-center">🎨 Color Guide</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-bold text-gray-300 mb-2">Original Text:</h4>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="bg-yellow-500 bg-opacity-40 text-yellow-200 px-2 py-1 rounded">Unknown words</span>
                      <span className="text-gray-400">- Learn these</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h4 className="font-bold text-gray-300 mb-2">Adapted Text:</h4>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="bg-pink-500 bg-opacity-50 text-pink-200 px-2 py-1 rounded font-bold">Learning targets</span>
                      <span className="text-gray-400">- Focus here!</span>
                    </div>
                  </div>
                </div>
              </div>
              <div className="mt-3 text-center text-xs text-gray-400">
                💡 Click any word OR select text with mouse for explanations
              </div>
            </div>

            {/* Vocabulary Upload Section */}
            <div className="max-w-4xl mx-auto">
              <VocabularyUpload 
                username={currentUser} 
                onUploadSuccess={loadUserStats}
              />
            </div>

            {/* Settings Panel */}
            <div className="bg-gray-800 rounded-lg p-4 mb-6 max-w-4xl mx-auto">
              <div className="flex flex-wrap justify-center gap-4 items-center">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-teal-400 font-bold">
                    🤖 AI-Powered Adaptation
                  </span>
                </div>
                
                <div className="flex items-center gap-2">
                  <label className="text-sm text-gray-300">Target Unknown %:</label>
                  <input
                    type="range"
                    min="5"
                    max="20"
                    value={targetUnknownPercentage}
                    onChange={(e) => setTargetUnknownPercentage(Number(e.target.value))}
                    className="w-20"
                  />
                  <span className="text-teal-400 text-sm font-bold">{targetUnknownPercentage}%</span>
                </div>
              </div>
            </div>
            
            {/* YouTube Input Form */}
            <form onSubmit={handleYouTubeSubmit} className="w-full max-w-3xl mx-auto mb-8">
              <div className="flex items-center bg-gray-800 rounded-lg p-2 shadow-lg">
                <input
                  className="appearance-none bg-transparent border-none w-full text-gray-200 placeholder-gray-500 mr-3 py-2 px-4 leading-tight focus:outline-none"
                  type="text"
                  placeholder="Enter a YouTube URL for i+1 adaptation..."
                  aria-label="YouTube URL"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                />
                <button
                  className="flex-shrink-0 bg-teal-500 hover:bg-teal-600 border-teal-500 hover:border-teal-600 text-sm font-bold border-4 text-white py-2 px-6 rounded-lg transition-colors duration-300 disabled:opacity-50"
                  type="submit"
                  disabled={isLoading}
                >
                  {isLoading ? '🔄 Processing...' : '🎯 Adapt to i+1'}
                </button>
              </div>
            </form>

            {error && (
              <div className="bg-red-800 border border-red-600 text-red-200 px-4 py-3 rounded max-w-3xl mx-auto mb-6">
                ❌ {error}
              </div>
            )}

            {/* Adaptation Results */}
            {adaptationResult && (
              <div className="mb-6 max-w-4xl mx-auto">
                <div className="bg-gray-800 rounded-lg p-4">
                  <h3 className="text-xl font-bold text-teal-400 mb-2">📊 Adaptation Analysis</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="bg-gray-700 p-3 rounded">
                      <div className="font-bold text-red-400">Original</div>
                      <div>{adaptationResult.original_analysis.unknown_percentage.toFixed(1)}% unknown</div>
                      <div className="text-xs text-gray-400">{adaptationResult.original_analysis.difficulty_level}</div>
                    </div>
                    <div className="bg-gray-700 p-3 rounded">
                      <div className="font-bold text-green-400">Adapted</div>
                      <div>{adaptationResult.adapted_analysis.unknown_percentage.toFixed(1)}% unknown</div>
                      <div className="text-xs text-gray-400">{adaptationResult.adapted_analysis.difficulty_level}</div>
                    </div>
                    <div className="bg-gray-700 p-3 rounded">
                      <div className="font-bold text-blue-400">Improvement</div>
                      <div>{adaptationResult.improvement.unknown_percentage_change.toFixed(1)}% change</div>
                      <div className="text-xs text-gray-400">
                        {adaptationResult.improvement.closer_to_target ? '✅ Better' : '❌ Needs work'}
                      </div>
                    </div>
                    <div className="bg-gray-700 p-3 rounded">
                      <div className="font-bold text-purple-400">Method</div>
                      <div className="text-xs">{adaptationResult.adaptation_method}</div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Side-by-Side Text Display */}
            {originalText && (
              <div className="flex flex-col lg:flex-row space-y-6 lg:space-y-0 lg:space-x-6">
                <div className="w-full lg:w-1/2">
                  <h2 className="text-2xl font-bold mb-4 text-center text-gray-300">
                    📝 Original Text
                    {adaptationResult && (
                      <span className="block text-sm font-normal text-red-400 mt-1">
                        {adaptationResult.original_analysis.unknown_percentage.toFixed(1)}% unknown words
                      </span>
                    )}
                  </h2>
                  <div className="bg-gray-800 p-6 rounded-lg h-96 overflow-y-auto shadow-inner">
                    {renderClickableText(originalText, false, adaptationResult?.original_word_analysis)}
                  </div>
                </div>
                
                <div className="w-full lg:w-1/2">
                  <h2 className="text-2xl font-bold mb-4 text-center text-gray-300">
                    🎯 i+1 Adapted Text
                    {adaptationResult && (
                      <span className="block text-sm font-normal text-green-400 mt-1">
                        {adaptationResult.adapted_analysis.unknown_percentage.toFixed(1)}% unknown words
                      </span>
                    )}
                  </h2>
                  <div className="bg-gray-800 p-6 rounded-lg h-96 overflow-y-auto shadow-inner">
                    {renderClickableText(adaptedText, true, adaptationResult?.adapted_word_analysis)}
                  </div>
                </div>
              </div>
            )}

            {/* Word Explanation Modal */}
            {showExplanationModal && (
              <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold text-teal-400">
                      📚 "{selectedWord}"
                    </h3>
                    <button
                      onClick={() => setShowExplanationModal(false)}
                      className="text-gray-400 hover:text-white text-2xl"
                    >
                      ✕
                    </button>
                  </div>
                  
                  {isLoadingExplanation ? (
                    <div className="text-center py-4">
                      <div className="animate-spin text-3xl">⏳</div>
                      <p className="text-gray-400 mt-2">Loading explanation...</p>
                    </div>
                  ) : wordExplanation ? (
                    <div className="space-y-4">
                      <div>
                        <span className="font-bold text-blue-400">🇹🇷 Türkçe:</span>
                        <p className="text-gray-300 mt-1">{wordExplanation.translation}</p>
                      </div>
                      <div>
                        <span className="font-bold text-green-400">📝 Example:</span>
                        <p className="text-gray-300 mt-1 italic">"{wordExplanation.example}"</p>
                      </div>
                      <div>
                        <span className="font-bold text-purple-400">💡 Açıklama:</span>
                        <p className="text-gray-300 mt-1">{wordExplanation.example_explanation}</p>
                      </div>
                      
                      {/* Word Action Buttons */}
                      <div className="border-t border-gray-600 pt-4 mt-4">
                        <p className="text-sm text-gray-400 mb-3 text-center">
                          Bu kelimeyi nasıl işaretlemek istiyorsun?
                        </p>
                        <div className="flex flex-col gap-2">
                          <button
                            onClick={() => handleAddWordToVocabulary(selectedWord!, 'known')}
                            disabled={isAddingWord}
                            className="bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2"
                          >
                            {isAddingWord ? '⏳' : '✅'} Biliyorum
                          </button>
                          <button
                            onClick={() => handleAddWordToVocabulary(selectedWord!, 'unknown')}
                            disabled={isAddingWord}
                            className="bg-red-600 hover:bg-red-700 disabled:bg-red-800 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2"
                          >
                            {isAddingWord ? '⏳' : '❌'} Bilmiyorum (Öğren)
                          </button>
                          <button
                            onClick={() => handleAddWordToVocabulary(selectedWord!, 'ignore')}
                            disabled={isAddingWord}
                            className="bg-gray-600 hover:bg-gray-700 disabled:bg-gray-800 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2"
                          >
                            {isAddingWord ? '⏳' : '🚫'} Görmezden Gel (İsim, yer adı vb.)
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-4">
                      <p className="text-red-400">Failed to load explanation</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
