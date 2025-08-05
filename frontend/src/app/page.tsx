'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import VocabularyUpload from '../components/VocabularyUpload';
import { SmartFeaturesDemo } from '../components/smart';
import Library from '../components/Library';

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

interface GrammarAnalysis {
  grammar_patterns: Array<{
    pattern: string;
    explanation: string;
    examples: string[];
    rules: string[];
    difficulty: string;
  }>;
  key_grammar_points: Array<{
    point: string;
    description: string;
    examples: string[];
    learning_tip: string;
  }>;
  vocabulary_grammar_connection: Array<{
    word: string;
    grammar_usage: string;
    examples: string[];
  }>;
  learning_recommendations: string[];
  summary: string;
}

interface GrammarAnalysisResult {
  grammar_analysis: GrammarAnalysis;
  original_text: string;
  analysis_type: string;
  total_patterns: number;
  learning_points: number;
}

export default function Home() {
  const router = useRouter();
  
  // Authentication State
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<any>(null);
  
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
  
  // Settings State - Removed target percentage (not needed)

  // Tab State
  const [activeTab, setActiveTab] = useState<'adaptation' | 'smart' | 'library'>('adaptation');
  const [smartAnalysisText, setSmartAnalysisText] = useState<string>('');

  // Grammar Analysis State - Now handled in Smart AI Teacher tab
  const [grammarAnalysisResult, setGrammarAnalysisResult] = useState<GrammarAnalysisResult | null>(null);

  // ✅ Copy to Clipboard Function
  const copyToClipboard = async (text: string, type: 'original' | 'adapted') => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
      console.log(`${type} text copied to clipboard!`);
      alert(`${type === 'original' ? 'Original' : 'AI'} text copied to clipboard!`);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      // Fallback for older browsers
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      alert(`${type === 'original' ? 'Original' : 'AI'} text copied to clipboard!`);
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
          title: type === 'original' ? 'Original Text' : 'AI Adapted Text',
          type: type
        }),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `${type}_text_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        alert(`${type === 'original' ? 'Original' : 'AI'} text PDF downloaded!`);
      } else {
        alert('PDF generation failed. Please try again.');
      }
    } catch (error) {
      console.error('PDF download error:', error);
      alert('PDF download failed. Please try again.');
    }
  };

  // No demo login - redirect to proper auth

  const handleLogout = () => {
    // Clear localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('originalText');
    localStorage.removeItem('adaptedText');
    localStorage.removeItem('youtubeUrl');
    
    // Reset state
    setCurrentUser('');
    setIsLoggedIn(false);
    setUserStats(null);
    setOriginalText('');
    setAdaptedText('');
    setAdaptationResult(null);
    setUser(null);
    setUrl('');
    setError('');
    setIsLoading(false);
    
    // Redirect to login
    router.push('/login');
  };

  // Check authentication on component mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const user = JSON.parse(userData);
        setUser(user);
        setCurrentUser(user.username);
        setIsLoggedIn(true);
        
        // Clear state on refresh - don't restore from localStorage
        setOriginalText('');
        setAdaptedText('');
        setUrl('');
        setAdaptationResult(null);
        setError('');
        setIsLoading(false);
        
      } catch (err) {
        console.error('Error parsing user data:', err);
        handleLogout();
      }
    } else {
      // Redirect to login if not authenticated
      console.log('No valid token found, redirecting to login');
      router.push('/login');
    }
  }, [router]);

  // Load user stats on component mount
  useEffect(() => {
    if (isLoggedIn && currentUser) {
      loadUserStats();
    }
  }, [currentUser, isLoggedIn]);

  const loadUserStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/adaptation/user-stats/${currentUser}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (response.ok) {
        const stats = await response.json();
        setUserStats(stats);
      } else if (response.status === 401) {
        // Unauthorized, redirect to login
        handleLogout();
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
      const token = localStorage.getItem('token');
      
      // Use library endpoint to get or create transcript
      const response = await fetch(`http://localhost:8000/api/library/transcript`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          video_url: url, 
          username: currentUser
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to process video.');
      }

      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'Failed to process video.');
      }

      const transcriptData = data.data;
      
      setOriginalText(transcriptData.original_text);
      
      // Always try to create/get AI adaptation
      let adaptedText = transcriptData.adapted_text || '';
      
      // If we don't have adapted text, or want to regenerate, create new adaptation
      if (!adaptedText || !transcriptData.from_library) {
        try {
          // Create AI adaptation using the library adaptation endpoint
          const adaptResponse = await fetch(`http://localhost:8000/api/library/transcript/video/${transcriptData.video_id}/adapt`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
              username: currentUser,
              target_unknown_percentage: 10.0
            }),
          });
          
          if (adaptResponse.ok) {
            const adaptData = await adaptResponse.json();
            if (adaptData.success) {
              adaptedText = adaptData.data.adapted_text;
            }
          }
        } catch (error) {
          console.error('Failed to create AI adaptation:', error);
        }
      }
      
      setAdaptedText(adaptedText);
      
      // Save to localStorage
      localStorage.setItem('originalText', transcriptData.original_text);
      localStorage.setItem('adaptedText', adaptedText);
      localStorage.setItem('youtubeUrl', url);
      
      // Analyze original text to get word status for coloring
      let originalWordAnalysis = null;
      let originalAnalysis = {
        total_words: transcriptData.word_count || 0,
        known_words: 0,
        unknown_words: 0,
        known_percentage: 0,
        unknown_percentage: 0,
        difficulty_level: 'unknown'
      };
      
      try {
        const analysisResponse = await fetch('http://localhost:8000/api/text-analysis/analyze', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            text: transcriptData.original_text,
            username: currentUser
          }),
        });
        
        if (analysisResponse.ok) {
          const analysisData = await analysisResponse.json();
          if (analysisData.success && analysisData.data) {
            originalWordAnalysis = analysisData.data.word_analysis;
            originalAnalysis = {
              total_words: analysisData.data.analysis?.total_unique_words_in_text || 0,
              known_words: analysisData.data.analysis?.known_words_in_text || 0,
              unknown_words: analysisData.data.analysis?.unknown_words_in_text || 0,
              known_percentage: analysisData.data.analysis?.known_percentage || 0,
              unknown_percentage: analysisData.data.analysis?.unknown_percentage || 0,
              difficulty_level: analysisData.data.analysis?.text_difficulty || 'unknown'
            };
          }
        }
      } catch (error) {
        console.error('Failed to analyze original text:', error);
      }
      
      // Analyze adapted text if available
      let adaptedWordAnalysis = null;
      let adaptedAnalysis = {
        total_words: adaptedText ? adaptedText.split(' ').length : 0,
        known_words: 0,
        unknown_words: 0,
        known_percentage: 0,
        unknown_percentage: 0,
        difficulty_level: 'unknown'
      };

      if (adaptedText && adaptedText.trim()) {
        try {
          const adaptedAnalysisResponse = await fetch('http://localhost:8000/api/text-analysis/analyze', {
            method: 'POST',
            headers: { 
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({
              text: adaptedText,
              username: currentUser
            }),
          });
          
          if (adaptedAnalysisResponse.ok) {
            const adaptedAnalysisData = await adaptedAnalysisResponse.json();
            if (adaptedAnalysisData.success && adaptedAnalysisData.data) {
              adaptedWordAnalysis = adaptedAnalysisData.data.word_analysis;
              adaptedAnalysis = {
                total_words: adaptedAnalysisData.data.analysis?.total_unique_words_in_text || 0,
                known_words: adaptedAnalysisData.data.analysis?.known_words_in_text || 0,
                unknown_words: adaptedAnalysisData.data.analysis?.unknown_words_in_text || 0,
                known_percentage: adaptedAnalysisData.data.analysis?.known_percentage || 0,
                unknown_percentage: adaptedAnalysisData.data.analysis?.unknown_percentage || 0,
                difficulty_level: adaptedAnalysisData.data.analysis?.text_difficulty || 'unknown'
              };
            }
          }
        } catch (error) {
          console.error('Failed to analyze adapted text:', error);
        }
      }

      // Create adaptation result object for compatibility
      const adaptationResult = {
        original_text: transcriptData.original_text,
        adapted_text: adaptedText,
        original_word_analysis: originalWordAnalysis,
        adapted_word_analysis: adaptedWordAnalysis,
        original_analysis: originalAnalysis,
        adapted_analysis: adaptedAnalysis,
        user_vocabulary_size: 0,
        adaptation_method: transcriptData.from_library ? 'library' : 'gemini',
        improvement: {
          unknown_percentage_change: originalAnalysis.unknown_percentage - adaptedAnalysis.unknown_percentage,
          closer_to_target: adaptedAnalysis.unknown_percentage < originalAnalysis.unknown_percentage
        }
      };
      
      setAdaptationResult(adaptationResult);
      
      // Perform word analysis for the original text
      try {
        const analysisResponse = await fetch(`http://localhost:8000/api/text-analysis/analyze`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            text: transcriptData.original_text,
            username: currentUser
          }),
        });
        
        if (analysisResponse.ok) {
          const analysisData = await analysisResponse.json();
          if (analysisData.success) {
            // Update adaptation result with word analysis
            const updatedResult = {
              ...adaptationResult,
              original_word_analysis: analysisData.data.word_analysis,
              original_analysis: {
                total_words: analysisData.data.analysis?.total_unique_words_in_text || 0,
                known_words: analysisData.data.analysis?.known_words_in_text || 0,
                unknown_words: analysisData.data.analysis?.unknown_words_in_text || 0,
                known_percentage: analysisData.data.analysis?.known_percentage || 0,
                unknown_percentage: analysisData.data.analysis?.unknown_percentage || 0,
                difficulty_level: analysisData.data.analysis?.text_difficulty || 'unknown'
              }
            };
            setAdaptationResult(updatedResult);
            
            // Reload word analysis immediately to ensure proper display
            reloadWordAnalysis();
          }
        }
      } catch (error) {
        console.error('Failed to analyze words:', error);
      }
      
      // Show success message if from library
      if (transcriptData.from_library) {
        setError('✅ Bu video kütüphaneden getirildi! Yeni transcript işlenmedi.');
      }
      
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
    if (!originalText) return;
    
    try {
      const token = localStorage.getItem('token');
      
      // Re-analyze original text with updated vocabulary
      const originalAnalysisResponse = await fetch('http://localhost:8000/api/text-analysis/analyze', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          text: originalText,
          username: currentUser
        }),
      });
      
      if (originalAnalysisResponse.ok) {
        const originalAnalysisData = await originalAnalysisResponse.json();
        
        if (originalAnalysisData.success) {
          // Update adaptation result with new word analysis
          setAdaptationResult(prev => prev ? {
            ...prev,
            original_word_analysis: originalAnalysisData.data.word_analysis,
            original_analysis: {
              total_words: originalAnalysisData.data.analysis?.total_unique_words_in_text || 0,
              known_words: originalAnalysisData.data.analysis?.known_words_in_text || 0,
              unknown_words: originalAnalysisData.data.analysis?.unknown_words_in_text || 0,
              known_percentage: originalAnalysisData.data.analysis?.known_percentage || 0,
              unknown_percentage: originalAnalysisData.data.analysis?.unknown_percentage || 0,
              difficulty_level: originalAnalysisData.data.analysis?.text_difficulty || 'unknown'
            }
          } : null);
        }
      }
      
      // If we have adapted text, also analyze it
      if (adaptedText) {
        const adaptedAnalysisResponse = await fetch('http://localhost:8000/api/text-analysis/analyze', {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            text: adaptedText,
            username: currentUser
          }),
        });
        
        if (adaptedAnalysisResponse.ok) {
          const adaptedAnalysisData = await adaptedAnalysisResponse.json();
          
          if (adaptedAnalysisData.success) {
            setAdaptationResult(prev => prev ? {
              ...prev,
              adapted_word_analysis: adaptedAnalysisData.data.word_analysis,
              adapted_analysis: {
                total_words: adaptedAnalysisData.data.analysis?.total_unique_words_in_text || 0,
                known_words: adaptedAnalysisData.data.analysis?.known_words_in_text || 0,
                unknown_words: adaptedAnalysisData.data.analysis?.unknown_words_in_text || 0,
                known_percentage: adaptedAnalysisData.data.analysis?.known_percentage || 0,
                unknown_percentage: adaptedAnalysisData.data.analysis?.unknown_percentage || 0,
                difficulty_level: adaptedAnalysisData.data.analysis?.text_difficulty || 'unknown'
              }
            } : null);
          }
        }
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
      // Clean the word/phrase - remove punctuation and extra spaces
      const cleanText = wordOrPhrase.replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim().toLowerCase();
      
      // Use the new smart API endpoint that actually works
      const response = await fetch('http://localhost:8000/api/smart/word-explanation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          word: cleanText
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Smart API explanation response:', data);
        
        if (data.success && data.data) {
          // Convert new API format to old modal format
          setWordExplanation({
            translation: data.data.turkish_meaning || "Çeviri bulunamadı",
            example: data.data.english_example || `Example: "${cleanText}" is used in sentences.`,
            example_explanation: data.data.example_translation || "Bu kelime/kelime grubu için açıklama bulunamadı."
          });
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

  const handleGrammarAnalysis = async () => {
    // Use adapted text first (shorter, user-appropriate), fallback to original
    const textToAnalyze = adaptedText || originalText;
    
    if (!textToAnalyze.trim()) {
      alert('Please provide some text to analyze (either original or adapted text)');
      return;
    }

    // Set the text for smart analysis and switch to Smart AI Teacher tab
    setSmartAnalysisText(textToAnalyze);
    setActiveTab('smart');
  };

  const isWordKnown = (word: string, wordAnalysis?: { word_status: { [key: string]: boolean } }): boolean => {
    if (!wordAnalysis || !wordAnalysis.word_status) {
      // If no word analysis available, assume unknown (safer approach)
      return false;
    }
    
    const cleanWord = word.toLowerCase().trim();
    return wordAnalysis.word_status[cleanWord] === true;
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
          
          const cleanWord = part.toLowerCase().trim();
          const known = isWordKnown(cleanWord, wordAnalysis);
          
          // Simple clickable styling - NO COLOR CODING
          let wordClass = "cursor-pointer px-1 rounded transition-colors duration-200 hover:bg-gray-600 hover:text-white";
          
          return (
            <span
              key={index}
              className={wordClass}
              onClick={() => handleWordClick(cleanWord)}
              title="Click to mark word as known/unknown/ignore"
            >
              {part}
            </span>
          );
        })}
      </div>
    );
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-0 bg-gray-900 text-white font-sans">
      <div className="w-full">
        {/* Header */}
        <header className="text-center mb-8 px-8">
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
                onClick={() => router.push('/login')}
                className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2 rounded-lg text-sm font-bold"
              >
                🔑 Login
              </button>
            )}
          </div>
        </header>

        {/* No demo login - redirect to proper auth */}

        {/* Main App Content - Only show when logged in */}
        {isLoggedIn && (
          <>
            {/* Tab Navigation */}
            <div className="mb-6 px-0">
              <div className="flex justify-center border-b border-gray-700">
                <button
                  onClick={() => setActiveTab('adaptation')}
                  className={`px-6 py-3 font-medium text-sm transition-colors ${
                    activeTab === 'adaptation'
                      ? 'text-teal-400 border-b-2 border-teal-400'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  📚 Metin Adaptasyonu
                </button>
                <button
                  onClick={() => setActiveTab('smart')}
                  className={`px-6 py-3 font-medium text-sm transition-colors ${
                    activeTab === 'smart'
                      ? 'text-teal-400 border-b-2 border-teal-400'
                      : 'text-gray-400 hover:text-gray-200'
                  }`}
                >
                  🧠 AI Öğretmen
                </button>
                {isLoggedIn && (
                  <button
                    onClick={() => setActiveTab('library')}
                    className={`px-6 py-3 font-medium text-sm transition-colors ${
                      activeTab === 'library'
                        ? 'text-blue-400 border-b-2 border-blue-400'
                        : 'text-gray-400 hover:text-blue-300'
                    }`}
                  >
                    📚 Kütüphane
                  </button>
                )}
              </div>
            </div>

            {/* Tab Content */}
            {activeTab === 'library' ? (
              <Library currentUser={currentUser} userLevel={userStats?.level || 'A1'} />
            ) : activeTab === 'adaptation' && (
              <div className="flex flex-col lg:flex-row gap-8 px-0">
                {/* Sol Taraf - Kontroller */}
                <div className="w-full lg:w-1/3 space-y-6 px-8">
                  {/* User Stats */}
                  {userStats && (
                    <div className="bg-gray-800 rounded-lg p-6">
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

                  {/* Word Interaction Guide */}
                  <div className="bg-gray-800 rounded-lg p-6">
                    <h3 className="text-lg font-bold text-teal-400 mb-3 text-center">💡 How to Use</h3>
                    <div className="text-center text-sm text-gray-300">
                      Click any word to mark it as <span className="text-green-400 font-bold">Known</span>, <span className="text-red-400 font-bold">Unknown</span>, or <span className="text-gray-400 font-bold">Ignore</span>
                    </div>
                    <div className="mt-2 text-center text-xs text-gray-400">
                      Select text with mouse for detailed explanations
                    </div>
                  </div>

                  {/* Vocabulary Upload Section */}
                  <div>
                    <VocabularyUpload 
                      username={currentUser} 
                      onUploadSuccess={loadUserStats}
                    />
                  </div>
                  
                  {/* YouTube Input Form */}
                  <form onSubmit={handleYouTubeSubmit} className="w-full">
                    <div className="flex items-center bg-gray-800 rounded-lg p-4 shadow-lg">
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



                  {/* Error Display */}
                  {error && (
                    <div className="bg-red-800 border border-red-600 text-red-200 px-4 py-3 rounded">
                      ❌ {error}
                    </div>
                  )}
                </div>

                {/* Sağ Taraf - Text Display (Her zaman görünür) */}
                <div className="w-full lg:w-2/3 px-8">
                  <div className="flex flex-col lg:flex-row space-y-8 lg:space-y-0 lg:space-x-8">
                    <div className="w-full lg:w-1/2 flex flex-col">
                      <div className="flex items-center justify-between mb-4">
                        <h2 className="text-2xl font-bold text-center text-gray-300 flex-1">
                          📝 Original Text
                        </h2>
                        {originalText && (
                          <div className="ml-3 flex gap-2">
                            <div className="relative group">
                              <button
                                onClick={() => copyToClipboard(originalText, 'original')}
                                className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors duration-200"
                              >
                                📋
                              </button>
                              <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                                Copy
                              </div>
                            </div>
                            <div className="relative group">
                              <button
                                onClick={() => downloadTextAsPDF(originalText, 'original')}
                                className="bg-red-600 hover:bg-red-700 text-white p-2 rounded-lg transition-colors duration-200"
                              >
                                📄
                              </button>
                              <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                                PDF
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                                              <div className="bg-gray-800 p-8 rounded-lg h-[700px] overflow-y-auto shadow-inner">
                          {originalText ? (
                            renderClickableText(originalText, false, adaptationResult?.original_word_analysis)
                          ) : (
                            <div className="flex items-center justify-center h-full text-gray-400 text-center">
                              <div>
                                <div className="text-4xl mb-4">📝</div>
                                <div className="text-lg font-medium mb-2">Metninizin analiz edilmesi için</div>
                                <div className="text-sm">yandan link girin</div>
                              </div>
                            </div>
                          )}
                        </div>
                    </div>
                    
                                        <div className="w-full lg:w-1/2 flex flex-col">
                      <div className="flex items-center justify-between mb-4">
                        <h2 className="text-2xl font-bold text-center text-gray-300 flex-1">
                          🎯 AI Adapted Text
                        </h2>
                        {adaptedText && (
                          <div className="ml-3 flex gap-2">
                            <div className="relative group">
                              <button
                                onClick={() => copyToClipboard(adaptedText, 'adapted')}
                                className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition-colors duration-200"
                              >
                                📋
                              </button>
                              <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                                Copy
                              </div>
                            </div>
                            <div className="relative group">
                              <button
                                onClick={() => downloadTextAsPDF(adaptedText, 'adapted')}
                                className="bg-red-600 hover:bg-red-700 text-white p-2 rounded-lg transition-colors duration-200"
                              >
                                📄
                              </button>
                            <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded px-2 py-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap">
                                PDF
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="bg-gray-800 p-8 rounded-lg h-[700px] overflow-y-auto shadow-inner">
                        {adaptedText ? (
                          renderClickableText(adaptedText, true, adaptationResult?.adapted_word_analysis)
                        ) : (
                          <div className="flex items-center justify-center h-full text-gray-400 text-center">
                            <div>
                              <div className="text-4xl mb-4">🎯</div>
                              <div className="text-lg font-medium mb-2">Metninizin analiz edilmesi için</div>
                              <div className="text-sm">yandan link girin</div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
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

            {/* Smart AI Features Tab */}
            {activeTab === 'smart' && (
              <div className="bg-gray-900">
                <SmartFeaturesDemo 
                  username={currentUser} 
                  initialText={smartAnalysisText || ""}
                />
              </div>
            )}
          </>
        )}
      </div>
    </main>
  );
}
