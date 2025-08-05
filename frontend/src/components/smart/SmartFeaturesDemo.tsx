'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { 
  WordExplanationPopup, 
  SmartGrammarExplanation, 
  UserLevelDashboard, 
  SmartAPI 
} from './index';
import type { GrammarExplanation } from './types';

interface SmartFeaturesDemoProps {
  username: string;
  initialText?: string;
}

export default function SmartFeaturesDemo({ username, initialText }: SmartFeaturesDemoProps) {
  // Real user ID state (fetched from username)
  const [userId, setUserId] = useState<number | null>(null);
  const [userIdLoading, setUserIdLoading] = useState(true);
  
  // Demo text samples - use initialText if provided, otherwise default
  const [demoText, setDemoText] = useState(
    initialText && initialText.trim() 
      ? initialText 
      : "I have been learning English for two years and it is amazing"
  );
  
  // Fetch user ID on component mount
  useEffect(() => {
    const fetchUserId = async () => {
      setUserIdLoading(true);
      try {
        const id = await SmartAPI.getUserIdFromUsername(username);
        setUserId(id);
      } catch (error) {
        console.error('Failed to fetch user ID:', error);
      } finally {
        setUserIdLoading(false);
      }
    };
    
    if (username) {
      fetchUserId();
    }
  }, [username]);

  // Update demo text when initialText changes
  useEffect(() => {
    if (initialText && initialText.trim()) {
      setDemoText(initialText);
    }
  }, [initialText]);
  
  // Smart analysis state
  const [smartAnalysis, setSmartAnalysis] = useState<GrammarExplanation[]>([]);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  
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
  
  // Dashboard refresh trigger
  const [dashboardRefresh, setDashboardRefresh] = useState(0);

  // Grammar knowledge state
  const [grammarKnowledge, setGrammarKnowledge] = useState<{ [key: string]: boolean }>({});
  const [grammarLoading, setGrammarLoading] = useState(true);

  // Fetch grammar knowledge from backend
  useEffect(() => {
    const fetchGrammarKnowledge = async () => {
      if (!userId) return;
      
      setGrammarLoading(true);
      try {
        // Direct database query for grammar knowledge
        const response = await fetch(`http://localhost:8000/api/smart/grammar-overview/${userId}`);
        const data = await response.json();
        
        if (data.success && data.data?.overview) {
          const overview = data.data.overview;
          const knownPatterns = new Set<string>();
          
          // Extract known patterns from all levels
          Object.values(overview).forEach((level: any) => {
            if (level.known) {
              level.known.forEach((pattern: string) => knownPatterns.add(pattern));
            }
          });
          
          // Create grammar knowledge state
          const grammarState: { [key: string]: boolean } = {};
          knownPatterns.forEach(pattern => {
            grammarState[pattern] = true;
          });
          
          console.log('Fetched grammar patterns:', Array.from(knownPatterns));
          setGrammarKnowledge(grammarState);
        }
      } catch (error) {
        console.error('Failed to fetch grammar knowledge:', error);
      } finally {
        setGrammarLoading(false);
      }
    };
    
    fetchGrammarKnowledge();
  }, [userId, dashboardRefresh]);

  // Handle grammar checkbox change
  const handleGrammarCheckboxChange = async (pattern: string, newCheckedState: boolean) => {
    if (!userId) return;
    
    const oldCheckedState = grammarKnowledge[pattern];
    
    try {
      // Update local state immediately for better UX
      setGrammarKnowledge(prev => ({
        ...prev,
        [pattern]: newCheckedState
      }));
      
      // Call API to update backend
      const status = newCheckedState ? 'known' : 'practice';
      
      const response = await SmartAPI.markGrammarKnowledge(userId, pattern, status);
      
      if (response.success) {
        // Refresh dashboard immediately
        setDashboardRefresh(prev => prev + 1);
        
        // Also refresh grammar knowledge from backend after a short delay
        setTimeout(async () => {
          try {
            const grammarResponse = await fetch(`http://localhost:8000/api/smart/grammar-overview/${userId}`);
            const grammarData = await grammarResponse.json();
            
            if (grammarData.success && grammarData.data?.overview) {
              const overview = grammarData.data.overview;
              const knownPatterns = new Set<string>();
              
              Object.values(overview).forEach((level: any) => {
                if (level.known) {
                  level.known.forEach((pattern: string) => knownPatterns.add(pattern));
                }
              });
              
              const grammarState: { [key: string]: boolean } = {};
              knownPatterns.forEach(pattern => {
                grammarState[pattern] = true;
              });
              
              setGrammarKnowledge(grammarState);
            }
          } catch (error) {
            console.error('Failed to refresh grammar knowledge:', error);
          }
        }, 300); // Wait 300ms for backend to update
        
        console.log('Grammar pattern updated:', pattern, 'checked:', newCheckedState, 'status:', status);
      } else {
        // Revert local state if API call failed
        setGrammarKnowledge(prev => ({
          ...prev,
          [pattern]: oldCheckedState
        }));
        console.error('Failed to update grammar pattern:', response.error);
      }
    } catch (error) {
      // Revert local state if API call failed
      setGrammarKnowledge(prev => ({
        ...prev,
        [pattern]: oldCheckedState
      }));
      console.error('Error updating grammar pattern:', error);
    }
  };

  // Run smart analysis
  const runSmartAnalysis = async () => {
    if (!demoText.trim() || !userId) return;
    
    setAnalysisLoading(true);
    try {
      const response = await SmartAPI.getSmartAnalysis(
        demoText,
        userId,
        true, // include grammar explanations
        true  // include quiz
      );
      
      if (response.success && response.data.explanations) {
        setSmartAnalysis(response.data.explanations);
      } else {
        console.error('Smart analysis failed:', response.error);
      }
    } catch (error) {
      console.error('Smart analysis error:', error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  // Handle word click for explanation
  const handleWordClick = useCallback((word: string, event: React.MouseEvent) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setWordPopup({
      word: word.toLowerCase().replace(/[^\w]/g, ''), // Clean the word
      isOpen: true,
      position: {
        x: rect.left + window.scrollX,
        y: rect.bottom + window.scrollY + 5
      }
    });
  }, []);

  // Handle grammar marking
  const handleGrammarMarked = useCallback((pattern: string, status: 'known' | 'practice', newLevel?: any) => {
    console.log('Grammar marked:', pattern, status, newLevel);
    // Refresh dashboard to show updated scores
    setDashboardRefresh(prev => prev + 1);
  }, []);

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

  // Show loading while fetching user ID
  if (userIdLoading || !userId) {
    return (
      <div className="max-w-6xl mx-auto p-6 space-y-8">
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg p-6">
          <h1 className="text-3xl font-bold mb-2">🚀 Smart AI Features Demo</h1>
          <p className="text-blue-100">
            Yeni AI öğretmen sistemi, kelime cache'leme ve kullanıcı seviye takibi özellikleri.
          </p>
        </div>
        
        <div className="text-center py-12">
          {userIdLoading ? (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-300">Kullanıcı bilgileri yükleniyor...</p>
            </>
          ) : (
            <div className="text-red-400">
              <p className="mb-4">❌ Kullanıcı bilgisi alınamadı</p>
              <p className="text-sm">Lütfen giriş yapıp tekrar deneyin.</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="w-full px-0">
      {/* Main Layout - İki Satır Düzen */}
      {/* Üst Satır: Dashboard ve Gramer Konuları */}
      <div className="flex flex-col lg:flex-row gap-6 px-8">
        {/* Sol Taraf - Dashboard */}
        <div className="w-full lg:w-1/2">
        <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
          <span className="text-2xl">📊</span>
          Kullanıcı Seviye Dashboard'u
        </h2>
        <UserLevelDashboard 
          userId={userId} 
          refreshTrigger={dashboardRefresh}
        />
      </div>

        {/* Sağ Taraf - Gramer Konuları */}
        <div className="w-full lg:w-1/2">
          <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
            <span className="text-2xl">📚</span>
            Gramer Kuralları Kontrol Listesi
          </h2>
          <div className="bg-gray-800 rounded-lg p-6 max-h-[520px] overflow-y-auto">
            <p className="text-gray-300 text-sm mb-4">
              İşaretli kurallar metinlerde açıklanmaz. İşaretli olmayanlar AI öğretmen tarafından açıklanır.
            </p>
            
            {/* A1 Temel Seviye */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">A1 Temel Seviye</h3>
              <div className="space-y-2">
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.present_simple || false}
                    onChange={(e) => handleGrammarCheckboxChange('present_simple', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Geniş Zaman (Present Simple)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.present_continuous || false}
                    onChange={(e) => handleGrammarCheckboxChange('present_continuous', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Şimdiki Zaman (Present Continuous)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.basic_questions || false}
                    onChange={(e) => handleGrammarCheckboxChange('basic_questions', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Temel Sorular (Basic Questions)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.basic_negatives || false}
                    onChange={(e) => handleGrammarCheckboxChange('basic_negatives', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Temel Olumsuzluk (Basic Negatives)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.articles || false}
                    onChange={(e) => handleGrammarCheckboxChange('articles', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Tanımlık/Belirsizlik (Definite/Indefinite Articles)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.prepositions_place || false}
                    onChange={(e) => handleGrammarCheckboxChange('prepositions_place', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Yer Edatları (Prepositions of Place)</span>
                </label>
              </div>
            </div>

            {/* A2 Temel Üstü Seviye */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-green-400 mb-2">A2 Temel Üstü Seviye</h3>
              <div className="space-y-2">
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.past_simple || false}
                    onChange={(e) => handleGrammarCheckboxChange('past_simple', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Geçmiş Zaman (Past Simple)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.future_will || false}
                    onChange={(e) => handleGrammarCheckboxChange('future_will', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Gelecek Zaman (Will)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.future_going_to || false}
                    onChange={(e) => handleGrammarCheckboxChange('future_going_to', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Gelecek Zaman (Going to)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.basic_comparatives || false}
                    onChange={(e) => handleGrammarCheckboxChange('basic_comparatives', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Karşılaştırma (Basic Comparatives)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.basic_modals || false}
                    onChange={(e) => handleGrammarCheckboxChange('basic_modals', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Modal Fiiller (Basic Modals)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.prepositions_time || false}
                    onChange={(e) => handleGrammarCheckboxChange('prepositions_time', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Zaman Edatları (Prepositions of Time)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.time_expressions || false}
                    onChange={(e) => handleGrammarCheckboxChange('time_expressions', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Zaman İfadeleri (Time Expressions)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.question_formation || false}
                    onChange={(e) => handleGrammarCheckboxChange('question_formation', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Soru Oluşturma (Question Formation)</span>
                </label>
              </div>
            </div>

            {/* B1 Orta Seviye */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-yellow-400 mb-2">B1 Orta Seviye</h3>
              <div className="space-y-2">
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.present_perfect || false}
                    onChange={(e) => handleGrammarCheckboxChange('present_perfect', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Şimdiki Mükemmel Zaman (Present Perfect)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.past_continuous || false}
                    onChange={(e) => handleGrammarCheckboxChange('past_continuous', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Geçmiş Sürekli Zaman (Past Continuous)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.conditionals_type1 || false}
                    onChange={(e) => handleGrammarCheckboxChange('conditionals_type1', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Koşullu Cümleler - Type 1 (First Conditional)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.passive_voice_simple || false}
                    onChange={(e) => handleGrammarCheckboxChange('passive_voice_simple', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Edilgen Çatı - Basit (Passive Voice - Simple)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.reported_speech || false}
                    onChange={(e) => handleGrammarCheckboxChange('reported_speech', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Dolaylı Anlatım (Reported Speech)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.modal_verbs_basic || false}
                    onChange={(e) => handleGrammarCheckboxChange('modal_verbs_basic', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Modal Fiiller - Temel (Basic Modal Verbs)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.present_perfect_continuous || false}
                    onChange={(e) => handleGrammarCheckboxChange('present_perfect_continuous', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Şimdiki Mükemmel Sürekli (Present Perfect Continuous)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.relative_clauses_basic || false}
                    onChange={(e) => handleGrammarCheckboxChange('relative_clauses_basic', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Temel Sıfat Cümleleri (Basic Relative Clauses)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.gerunds_infinitives || false}
                    onChange={(e) => handleGrammarCheckboxChange('gerunds_infinitives', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Ulaç ve Mastar (Gerunds and Infinitives)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.adjective_intensifiers || false}
                    onChange={(e) => handleGrammarCheckboxChange('adjective_intensifiers', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Sıfat Güçlendiricileri (Adjective Intensifiers)</span>
                </label>
              </div>
            </div>

            {/* B2 Orta-Üst Seviye */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-orange-400 mb-2">B2 Orta-Üst Seviye</h3>
              <div className="space-y-2">
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.past_perfect || false}
                    onChange={(e) => handleGrammarCheckboxChange('past_perfect', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Geçmiş Mükemmel Zaman (Past Perfect)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.future_perfect || false}
                    onChange={(e) => handleGrammarCheckboxChange('future_perfect', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Gelecek Mükemmel Zaman (Future Perfect)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.second_conditional || false}
                    onChange={(e) => handleGrammarCheckboxChange('second_conditional', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Koşullu Cümleler - Type 2 (Second Conditional)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.relative_clauses || false}
                    onChange={(e) => handleGrammarCheckboxChange('relative_clauses', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Sıfat Cümleleri (Relative Clauses)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.reported_speech_complex || false}
                    onChange={(e) => handleGrammarCheckboxChange('reported_speech_complex', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Dolaylı Anlatım - Karmaşık (Reported Speech - Complex)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.modal_speculation || false}
                    onChange={(e) => handleGrammarCheckboxChange('modal_speculation', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Tahmin Modal Fiilleri (Modals of Speculation)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.relative_clauses_advanced || false}
                    onChange={(e) => handleGrammarCheckboxChange('relative_clauses_advanced', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>İleri Sıfat Cümleleri (Advanced Relative Clauses)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.modal_verbs_advanced || false}
                    onChange={(e) => handleGrammarCheckboxChange('modal_verbs_advanced', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>İleri Modal Fiiller (Advanced Modal Verbs)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.superlatives || false}
                    onChange={(e) => handleGrammarCheckboxChange('superlatives', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Üstünlük Derecesi (Superlatives)</span>
                </label>
              </div>
            </div>

            {/* C1 İleri Seviye */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-red-400 mb-2">C1 İleri Seviye</h3>
              <div className="space-y-2">
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.third_conditional || false}
                    onChange={(e) => handleGrammarCheckboxChange('third_conditional', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Koşullu Cümleler - Type 3 (Third Conditional)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.mixed_conditionals || false}
                    onChange={(e) => handleGrammarCheckboxChange('mixed_conditionals', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Karışık Koşullu Cümleler (Mixed Conditionals)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.advanced_passive || false}
                    onChange={(e) => handleGrammarCheckboxChange('advanced_passive', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Gelişmiş Edilgen Çatı (Advanced Passive)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.inversion || false}
                    onChange={(e) => handleGrammarCheckboxChange('inversion', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>İnversion (Ters Çevirme)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.cleft_sentences || false}
                    onChange={(e) => handleGrammarCheckboxChange('cleft_sentences', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Cleft Sentences (Vurgulu Cümleler)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.participle_clauses || false}
                    onChange={(e) => handleGrammarCheckboxChange('participle_clauses', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Gelişmiş Participle Clauses</span>
                </label>
              </div>
            </div>

            {/* C2 Usta Seviye */}
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-purple-400 mb-2">C2 Usta Seviye</h3>
              <div className="space-y-2">
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.subjunctive || false}
                    onChange={(e) => handleGrammarCheckboxChange('subjunctive', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Gelişmiş Subjunctive (Dilek Kipi)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.elliptical_structures || false}
                    onChange={(e) => handleGrammarCheckboxChange('elliptical_structures', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Eliptik Yapılar (Elliptical Structures)</span>
                </label>
                <label className="flex items-center text-sm cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={grammarKnowledge.superlative_advanced || false}
                    onChange={(e) => handleGrammarCheckboxChange('superlative_advanced', e.target.checked)}
                    className="mr-2" 
                  />
                  <span>Üstünlük Derecesi</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Alt Kısım: Smart Grammar Analysis - Sağdan soldan 5cm padding */}
      <div className="w-full px-20 mt-8">
        <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          Smart Grammar Analysis
        </h2>
        <div className="bg-white rounded-lg shadow-md p-6">
          {/* Text Input - Küçültülmüş */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Analiz edilecek metin:
            </label>
                         <textarea
               value={demoText}
               onChange={(e) => setDemoText(e.target.value)}
               className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-800"
              rows={3}
               placeholder="İngilizce metin girin..."
             />
          </div>

          {/* Analyze Button */}
          <div className="mb-6">
            <button
              onClick={runSmartAnalysis}
              disabled={analysisLoading || !demoText.trim()}
              className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {analysisLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  AI Analiz Yapıyor...
                </>
              ) : (
                <>
                  <span className="text-lg">🔍</span>
                  Smart Analiz Yap
                </>
              )}
            </button>
          </div>

          {/* Smart Grammar Analysis Results */}
          {smartAnalysis.length > 0 && (
            <SmartGrammarExplanation
              explanations={smartAnalysis}
              userId={userId}
              onGrammarMarked={handleGrammarMarked}
            />
          )}
        </div>
      </div>

      {/* Word Explanation Popup */}
      <WordExplanationPopup
        word={wordPopup.word}
        isOpen={wordPopup.isOpen}
        onClose={() => setWordPopup(prev => ({ ...prev, isOpen: false }))}
        position={wordPopup.position}
      />
    </div>
  );
} 