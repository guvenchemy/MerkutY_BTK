'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { SmartAPI } from './api';
import { UserLevelResponse } from './types';

interface UserLevelDashboardProps {
  userId: number;
  refreshTrigger?: number; // Used to refresh when grammar knowledge changes
}

interface CurrentLevelProgress {
  vocabulary_count: number;
  vocabulary_required: number;
  vocabulary_progress: number;
  vocabulary_remaining: number;
  grammar_known: number;
  grammar_required: number;
  grammar_progress: number;
  grammar_remaining: number;
  overall_progress: number;
}

interface NextLevelProgress {
  next_level: string;
  vocabulary_progress: number;
  grammar_progress: number;
  overall_progress: number;
}

interface UserLevelExtended {
  level: string;
  score: number;
  vocabulary_strength: number;
  grammar_strength: number;
  balance: string;
  current_level_progress?: CurrentLevelProgress;
  next_level_progress?: NextLevelProgress;
  level_progress?: number; // Backward compatibility
}

interface GrammarOverviewLevel {
  known?: string[];
  practice?: string[];
  unknown?: string[];
}

interface GrammarOverview {
  overview?: Record<string, GrammarOverviewLevel>;
}

interface DashboardData {
  success?: boolean;
  grammar_overview?: {
    known_patterns?: string[];
    practice_patterns?: string[];
    unknown_patterns?: string[];
    total_patterns?: number;
    progress_percentage?: number;
    overview?: Record<string, GrammarOverviewLevel>;
  };
  user_level?: Record<string, unknown>;
  learning_path?: unknown[];
}

// Grammar pattern definitions by level (currently unused but kept for future use)
// const getA1Patterns = () => ["present_simple", "present_continuous", "basic_questions", "basic_negatives", "articles", "prepositions_place"];
// const getA2Patterns = () => ["past_simple", "future_will", "future_going_to", "basic_comparatives", "basic_modals", "time_expressions", "prepositions_time", "question_formation"];
// const getB1Patterns = () => ["present_perfect", "present_perfect_continuous", "conditionals_type1", "passive_voice_simple", "relative_clauses_basic", "modal_verbs_basic", "gerunds_infinitives", "adjective_intensifiers"];
// const getB2Patterns = () => ["past_perfect", "past_continuous", "future_continuous", "conditionals_type2", "passive_voice_advanced", "passive_voice_perfect", "reported_speech", "modal_verbs_advanced", "relative_clauses_advanced", "superlatives"];

// Grammar pattern display names
const getPatternDisplayName = (pattern: string): string => {
  const names: {[key: string]: string} = {
    'present_simple': 'Geniş Zaman',
    'present_continuous': 'Şimdiki Zaman',
    'present_perfect': 'Şimdiki Zaman (Perfect)',
    'present_perfect_continuous': 'Şimdiki Zaman (Sürekli)',
    'past_simple': 'Geçmiş Zaman',
    'past_continuous': 'Geçmiş Zaman (Sürekli)',
    'past_perfect': 'Geçmiş Zaman (Perfect)',
    'future_will': 'Gelecek Zaman (Will)',
    'future_going_to': 'Gelecek Zaman (Going to)',
    'future_continuous': 'Gelecek Zaman (Sürekli)',
    'basic_questions': 'Temel Sorular',
    'basic_negatives': 'Temel Olumsuzluk',
    'basic_comparatives': 'Karşılaştırma',
    'basic_modals': 'Temel Yardımcı Fiiller',
    'modal_verbs_basic': 'Yardımcı Fiiller',
    'modal_verbs_advanced': 'İleri Yardımcı Fiiller',
    'conditionals_type1': 'Koşul Cümleleri 1',
    'conditionals_type2': 'Koşul Cümleleri 2',
    'passive_voice_simple': 'Pasif Yapı (Basit)',
    'passive_voice_advanced': 'Pasif Yapı (İleri)',
    'passive_voice_perfect': 'Pasif Yapı (Perfect)',
    'relative_clauses_basic': 'İlgi Zamirli Cümleler',
    'relative_clauses_advanced': 'İleri İlgi Zamirli Cümleler',
    'articles': 'Tanımlık/Belirsizlik',
    'prepositions_place': 'Yer Edatları',
    'prepositions_time': 'Zaman Edatları',
    'time_expressions': 'Zaman İfadeleri',
    'question_formation': 'Soru Oluşturma',
    'gerunds_infinitives': 'Ulaç ve Mastar',
    'adjective_intensifiers': 'Sıfat Güçlendiricileri',
    'reported_speech': 'Dolaylı Anlatım',
    'superlatives': 'Üstünlük Derecesi'
  };
  return names[pattern] || pattern.replace(/_/g, ' ');
};

// Grammar Pattern Checkbox Component
interface GrammarPatternCheckboxProps {
  pattern: string;
  isKnown: boolean;
  userId: number;
  onStatusChange?: (pattern: string, isKnown: boolean) => void;
}

// Currently unused component - kept for future functionality
/*
const GrammarPatternCheckbox: React.FC<GrammarPatternCheckboxProps> = ({ 
  pattern, 
  isKnown, 
  userId, 
  onStatusChange 
}) => {
  const [loading, setLoading] = useState(false);
  
  const handleToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (loading) return;
    
    setLoading(true);
    try {
      const newStatus = isKnown ? 'practice' : 'known';
      await SmartAPI.markGrammarKnowledge(userId, pattern, newStatus);
      onStatusChange?.(pattern, !isKnown);
    } catch (error) {
      console.error('Failed to update grammar status:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
      onClick={handleToggle}
    >
      <input
        type="checkbox"
        checked={isKnown}
        readOnly
        disabled={loading}
        className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500 pointer-events-none"
      />
      <span className={`text-sm ${isKnown ? 'text-green-700 font-medium' : 'text-gray-700'}`}>
        {getPatternDisplayName(pattern)}
      </span>
      {loading && <span className="text-xs text-gray-400">⏳</span>}
    </div>
  );
};
*/

// Utility: Flatten backend grammar overview into simple arrays
const TOTAL_GRAMMAR_PATTERNS = 41; // Total grammar patterns (A1:6 + A2:8 + B1:8 + B2:10 + C1:5 + C2:4)
const aggregateGrammarOverview = (overviewData: GrammarOverview | undefined) => {
  if (!overviewData || !overviewData.overview) {
    return {
      known_patterns: [] as string[],
      unknown_patterns: [] as string[],
      progress_percentage: 0,
    };
  }

  const levelEntries = Object.values(overviewData.overview) as GrammarOverviewLevel[];

  const knownSet = new Set<string>();
  levelEntries.forEach((lvl) => (lvl.known || []).forEach((p: string) => knownSet.add(p)));

  const unknownCount = Math.max(TOTAL_GRAMMAR_PATTERNS - knownSet.size, 0);

  return {
    known_patterns: Array.from(knownSet),
    unknown_patterns: Array.from({ length: unknownCount }), // placeholder array for count
    progress_percentage: (knownSet.size / TOTAL_GRAMMAR_PATTERNS) * 100,
  };
};

export default function UserLevelDashboard({ userId, refreshTrigger }: UserLevelDashboardProps) {
  const [levelData, setLevelData] = useState<UserLevelResponse['data'] | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Aggregated overview (flattened for easier access)
  const aggregatedOverview = useMemo(() => aggregateGrammarOverview(dashboardData?.grammar_overview), [dashboardData]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [levelResponse, dashboardResponse] = await Promise.all([
        SmartAPI.getUserLevel(userId),
        SmartAPI.getGrammarDashboard(userId)
      ]);

      let hasAnySuccess = false;
      if (levelResponse.success) {
        setLevelData(levelResponse.data);
        hasAnySuccess = true;
      }
      if (dashboardResponse.success) {
        setDashboardData(dashboardResponse.data);
        hasAnySuccess = true;
      }
      if (!hasAnySuccess) {
        setError('Kullanıcı bilgisi alınamadı');
      }
    } catch (error) {
      console.error('Fetch data error:', error);
      setError('Bağlantı hatası');
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchData();
  }, [fetchData, refreshTrigger]);

  // Handle grammar status change and refresh data (currently unused)
  /*
  const onGrammarStatusChange = async (pattern: string, isKnown: boolean) => {
    // Remember scroll position to prevent jump
    const currentScroll = window.scrollY;
    // Optimistically update UI
    setDashboardData((prev: DashboardData | null) => {
      if (!prev) return prev;
      const newOverview = { ...prev.grammar_overview };
      if (isKnown) {
        // add to known
        newOverview.known_patterns = [...(newOverview.known_patterns || []), pattern];
        // remove from practice/unknown if present
        newOverview.practice_patterns = (newOverview.practice_patterns || []).filter((p: string) => p !== pattern);
        newOverview.unknown_patterns = (newOverview.unknown_patterns || []).filter((p: string) => p !== pattern);
      } else {
        // move to practice (toggle)
        newOverview.practice_patterns = [...new Set([...(newOverview.practice_patterns || []), pattern])];
        newOverview.known_patterns = (newOverview.known_patterns || []).filter((p: string) => p !== pattern);
      }
      return { ...prev, grammar_overview: newOverview };
    });
    
    // Call backend
    await fetchData();
    window.scrollTo({ top: currentScroll });
  };
  */

  // Currently unused function - kept for future use
  /*
  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'a1': return 'bg-green-500';
      case 'a2': return 'bg-lime-500';
      case 'b1': return 'bg-yellow-500';
      case 'b2': return 'bg-orange-500';
      case 'c1': return 'bg-red-500';
      case 'c2': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };
  */

  const getLevelGradient = (level: string) => {
    switch (level.toLowerCase()) {
      case 'a1': return 'from-indigo-400 to-purple-600';
      case 'a2': return 'from-indigo-500 to-purple-600';
      case 'b1': return 'from-indigo-600 to-purple-700';
      case 'b2': return 'from-purple-500 to-indigo-700';
      case 'c1': return 'from-purple-600 to-indigo-800';
      case 'c2': return 'from-purple-700 to-indigo-900';
      default: return 'from-indigo-400 to-purple-600';
    }
  };

  const getBalanceInfo = (balance: string) => {
    switch (balance) {
      case 'vocabulary_strong':
        return {
          text: 'Kelime Bilgisi Güçlü',
          color: 'text-blue-600',
          icon: '📚',
          description: 'Gramer konularına odaklanmanız önerilir'
        };
      case 'grammar_strong':
        return {
          text: 'Gramer Bilgisi Güçlü',
          color: 'text-green-600',
          icon: '📝',
          description: 'Kelime dağarcığını geliştirmeniz önerilir'
        };
      default:
        return {
          text: 'Dengeli Gelişim',
          color: 'text-purple-600',
          icon: '⚖️',
          description: 'Kelime ve gramer dengeniz çok iyi!'
        };
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <div className="text-red-500 mb-2">❌ Hata</div>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={fetchData}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  if (!levelData || !levelData.user_level) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <div className="text-gray-500 mb-2">⚠️</div>
        <p className="text-gray-600">Kullanıcı seviye verisi bulunamadı</p>
      </div>
    );
  }

  const balanceInfo = getBalanceInfo(levelData.user_level.balance || 'balanced');
  const userLevel = levelData.user_level as UserLevelExtended;

  return (
    <div className="space-y-4">
      {/* Main Level Card */}
      <div className={`bg-gradient-to-r ${getLevelGradient(levelData.user_level.level || 'A1')} text-white rounded-lg shadow-lg p-6`}>
        <div className="flex items-center justify-between">
          <div>
                         <h3 className="text-2xl font-bold mb-1">
               {(levelData.user_level.level || 'A1').toUpperCase()} Seviyesi
             </h3>
                         <p className="text-white text-opacity-90">
               Toplam Puan: {(levelData.scores?.total_score || 0).toFixed(1)}
             </p>
          </div>
                     <div className="text-4xl">
             {(levelData.user_level.level || 'A1') === 'A1' && '🌱'}
             {(levelData.user_level.level || 'A1') === 'A2' && '🌿'}
             {(levelData.user_level.level || 'A1') === 'B1' && '🌳'}
             {(levelData.user_level.level || 'A1') === 'B2' && '🌲'}
             {(levelData.user_level.level || 'A1') === 'C1' && '🏔️'}
             {(levelData.user_level.level || 'A1') === 'C2' && '🏆'}
           </div>
        </div>

        {/* New Detailed Progress Bars */}
        <div className="mt-4 space-y-3">
          {/* Current Level Progress */}
          <div>
            <div className="flex justify-between text-sm text-white text-opacity-75 mb-1">
              <span>Mevcut Seviye İlerlemesi</span>
              <span>{Math.round(((userLevel.current_level_progress?.vocabulary_progress || 0) + (userLevel.current_level_progress?.grammar_progress || 0)) / 2)}%</span>
            </div>
            <div className="w-full bg-white bg-opacity-20 rounded-full h-2">
              <div 
                className="bg-yellow-400 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(((userLevel.current_level_progress?.vocabulary_progress || 0) + (userLevel.current_level_progress?.grammar_progress || 0)) / 2, 100)}%` }}
              ></div>
            </div>
          </div>

          {/* Vocabulary Progress for Current Level */}
          <div>
            <div className="flex justify-between text-xs text-white text-opacity-75 mb-1">
              <span>
                📚 Kelime: {userLevel.current_level_progress?.vocabulary_count || 0} / {userLevel.current_level_progress?.vocabulary_required || 0}
              </span>
              <span>{userLevel.current_level_progress?.vocabulary_progress || 0}%</span>
            </div>
            <div className="w-full bg-white bg-opacity-20 rounded-full h-1.5">
              <div 
                className="bg-yellow-400 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(userLevel.current_level_progress?.vocabulary_progress || 0, 100)}%` }}
              ></div>
            </div>
          </div>

          {/* Grammar Progress for Current Level */}
          <div>
            <div className="flex justify-between text-xs text-white text-opacity-75 mb-1">
              <span>
                📝 Gramer: {userLevel.current_level_progress?.grammar_known || 0} / {userLevel.current_level_progress?.grammar_required || 0}
              </span>
              <span>{userLevel.current_level_progress?.grammar_progress || 0}%</span>
            </div>
            <div className="w-full bg-white bg-opacity-20 rounded-full h-1.5">
              <div 
                className="bg-yellow-400 h-1.5 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(userLevel.current_level_progress?.grammar_progress || 0, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Next Level Progress Card - REMOVED */}
      {/* Kullanıcı sadece mevcut level'ini görsün, gelecek level progress'i gösterilmesin */}

      {/* Detailed Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Vocabulary Score */}
        <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-blue-400">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📚</span>
            <h4 className="font-semibold text-gray-800">Kelime Bilgisi</h4>
          </div>
                     <div className="text-2xl font-bold text-blue-600 mb-1">
             {(levelData.scores?.vocabulary_score || 0).toFixed(1)}
           </div>
           <div className="w-full bg-gray-200 rounded-full h-2">
             <div 
               className="bg-yellow-400 h-2 rounded-full transition-all duration-500"
               style={{ width: `${Math.min(levelData.scores?.vocabulary_score || 0, 100)}%` }}
             ></div>
           </div>
        </div>

        {/* Grammar Score */}
        <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-green-400">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📝</span>
            <h4 className="font-semibold text-gray-800">Gramer Bilgisi</h4>
          </div>
          <div className="text-2xl font-bold text-green-600 mb-1">
            {aggregatedOverview.progress_percentage.toFixed(1)}%
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-yellow-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(aggregatedOverview.progress_percentage, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Balance Info */}
        <div className="bg-white rounded-lg shadow-md p-4 border-l-4 border-purple-400">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">{balanceInfo.icon}</span>
            <h4 className="font-semibold text-gray-800">Denge</h4>
          </div>
          <div className={`text-sm font-medium ${balanceInfo.color} mb-1`}>
            {balanceInfo.text}
          </div>
          <p className="text-xs text-gray-600">
            {balanceInfo.description}
          </p>
        </div>
      </div>

      {/* Grammar Progress (if available) */}
      {dashboardData?.grammar_overview && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h4 className="font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <span className="text-xl">🎯</span>
            Gramer İlerleme Durumu
          </h4>
          
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {aggregatedOverview.known_patterns?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Bilinen Konular</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {aggregatedOverview.unknown_patterns?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Yeni Konular</div>
            </div>
          </div>

          <div className="w-full bg-gray-200 rounded-full h-3">
            <div 
              className="bg-yellow-400 h-3 rounded-full transition-all duration-500"
              style={{ width: `${aggregatedOverview.progress_percentage || 0}%` }}
            ></div>
          </div>
          <div className="text-center text-sm text-gray-600 mt-2">
            Toplam İlerleme: %{(aggregatedOverview.progress_percentage || 0).toFixed(1)}
          </div>
        </div>
      )}

      {/* Grammar Patterns Checklist */}
      {/* KALDIRILDI: Gramer Kuralları Kontrol Listesi ve checkbox'lar */}
    </div>
  );
} 