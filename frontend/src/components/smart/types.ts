// Smart API Types for AI Teacher System
export interface WordExplanationResponse {
  success: boolean;
  data: {
    word: string;
    turkish_meaning: string;
    english_example: string;
    example_translation: string;
    difficulty_level: number;
    created_at: string;
    from_cache?: boolean;
  };
  error: string | null;
}

export interface GrammarExample {
  sentence: string;
  analysis: string;
}

export interface PrepositionExample {
  sentence: string;
  preposition: string;
  explanation: string;
  turkish_explanation: string;
}

export interface SimpleExample {
  example: string;
  explanation: string;
}

export interface GrammarExplanation {
  pattern_name: string;
  pattern_display_name: string;
  user_level: string;
  example_from_text: string | string[] | GrammarExample[] | PrepositionExample[] | SimpleExample[];
  structure_rule: string;
  usage_purpose: string;
  text_analysis: string;
  quiz_question: string;
  hidden_answer: string;
  learning_tip: string;
  difficulty_level: string;
}

export interface SmartAnalysisResponse {
  success: boolean;
  data: {
    success: boolean;
    explanations: GrammarExplanation[];
  };
  error: string | null;
}

export interface UserLevel {
  level: string;
  score: number;
  level_progress?: number; // Progress within current level (0-100%)
  vocabulary_strength: number;
  grammar_strength: number;
  balance: string;
  level_info?: {
    current_level: string;
    progress_percentage: number;
    next_level: string;
    points_to_next: number;
  };
}

export interface UserLevelResponse {
  success: boolean;
  data: {
    success: boolean;
    user_level: UserLevel;
    scores: {
      vocabulary_score: number;
      grammar_score: number;
      total_score: number;
    };
    recommendations: string[];
  };
  error: string | null;
}

export interface GrammarMarkingResponse {
  success: boolean;
  data: {
    success: boolean;
    message: string;
    updated_level: UserLevelResponse['data'];
  };
  error: string | null;
}

export interface CacheStatsResponse {
  success: boolean;
  data: {
    total_cached_words: number;
    cache_enabled: boolean;
  };
  error: string | null;
}

export interface GrammarDashboardResponse {
  success: boolean;
  data: {
    success: boolean;
    user_level: UserLevelResponse['data'];
    grammar_overview: {
      known_patterns: string[];
      practice_patterns: string[];
      unknown_patterns: string[];
      total_patterns: number;
      progress_percentage: number;
    };
    learning_path: Array<{
      pattern: string;
      level: string;
      priority: number;
      reason: string;
    }>;
  };
  error: string | null;
} 