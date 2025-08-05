import { 
  WordExplanationResponse, 
  SmartAnalysisResponse, 
  UserLevelResponse, 
  GrammarMarkingResponse,
  CacheStatsResponse,
  GrammarDashboardResponse 
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Smart API Functions
export class SmartAPI {
  
  /**
   * Get word explanation from cache or AI
   */
  static async getWordExplanation(word: string): Promise<WordExplanationResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart/word-explanation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ word }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Word explanation API error:', error);
      return {
        success: false,
        data: {
          word,
          turkish_meaning: 'Açıklama alınamadı',
          english_example: 'Example not available',
          example_translation: 'Çeviri mevcut değil',
          difficulty_level: 1,
          created_at: new Date().toISOString(),
          is_from_cache: false,
        },
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get smart grammar analysis with AI teacher explanations
   */
  static async getSmartAnalysis(
    text: string, 
    userId: number, 
    includeGrammarExplanations: boolean = true,
    includeQuiz: boolean = true
  ): Promise<SmartAnalysisResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart/smart-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          user_id: userId,
          include_grammar_explanations: includeGrammarExplanations,
          include_quiz: includeQuiz,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Smart analysis API error:', error);
      return {
        success: false,
        data: {
          success: false,
          explanations: [],
        },
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get user level and scores
   */
  static async getUserLevel(userId: number): Promise<UserLevelResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart/user-level/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('User level API error:', error);
      return {
        success: false,
        data: {
          success: false,
          user_level: {
            level: 'A1',
            score: 0,
            vocabulary_strength: 0,
            grammar_strength: 0,
            balance: 'balanced',
          },
          scores: {
            vocabulary_score: 0,
            grammar_score: 0,
            total_score: 0,
          },
          recommendations: [],
        },
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Mark grammar pattern as known or practice
   */
  static async markGrammarKnowledge(
    userId: number, 
    grammarPattern: string, 
    status: 'known' | 'practice'
  ): Promise<GrammarMarkingResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart/mark-grammar-knowledge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          grammar_pattern: grammarPattern,
          status,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Grammar marking API error:', error);
      return {
        success: false,
        data: {
          success: false,
          message: 'Marking failed',
          updated_level: {
            success: false,
            user_level: {
              level: 'A1',
              score: 0,
              vocabulary_strength: 0,
              grammar_strength: 0,
              balance: 'balanced',
            },
            scores: {
              vocabulary_score: 0,
              grammar_score: 0,
              total_score: 0,
            },
            recommendations: [],
          },
        },
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get cache statistics
   */
  static async getCacheStats(): Promise<CacheStatsResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart/cache-stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Cache stats API error:', error);
      return {
        success: false,
        data: {
          total_cached_words: 0,
          cache_enabled: false,
        },
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get user ID from username (helper function)
   */
  static async getUserIdFromUsername(username: string): Promise<number | null> {
    try {
      // Use the new user-id endpoint to get real user ID
      const response = await fetch(`${API_BASE_URL}/api/auth/user-id/${username}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        console.error(`Failed to get user ID for ${username}: ${response.status}`);
        return null;
      }
      
      const data = await response.json();
      console.log(`✅ Found user ID for ${username}: ${data.user_id}`);
      return data.user_id;

    } catch (error) {
      console.error('Get user ID error:', error);
      return null;
    }
  }

  /**
   * Get grammar dashboard
   */
  static async getGrammarDashboard(userId: number): Promise<GrammarDashboardResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart/grammar-dashboard/${userId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Grammar dashboard API error:', error);
      return {
        success: false,
        data: {
          success: false,
          user_level: {
            success: false,
            user_level: {
              level: 'A1',
              score: 0,
              vocabulary_strength: 0,
              grammar_strength: 0,
              balance: 'balanced',
            },
            scores: {
              vocabulary_score: 0,
              grammar_score: 0,
              total_score: 0,
            },
            recommendations: [],
          },
          grammar_overview: {
            overview: {},
            total_known: 0,
            total_practicing: 0,
          },
          learning_path: [],
        },
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
} 