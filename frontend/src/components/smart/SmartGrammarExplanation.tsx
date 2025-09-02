'use client';

import React, { useState } from 'react';
import { SmartAPI } from './api';
import { GrammarExplanation } from './types';
// import dynamic from 'next/dynamic'; // Currently unused
// import robotoNormalBase64 from '../../config/fonts'; // Currently unused

interface SmartGrammarExplanationProps {
  explanations: GrammarExplanation[];
  userId: number;
  onGrammarMarked?: (pattern: string, status: 'known' | 'practice', newLevel?: { level: string; score: number }) => void;
}

export default function SmartGrammarExplanation({
  explanations,
  userId,
  onGrammarMarked
}: SmartGrammarExplanationProps) {
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());
  const [showQuizAnswers, setShowQuizAnswers] = useState<Set<string>>(new Set());
  const [markingStatus, setMarkingStatus] = useState<{ [key: string]: boolean }>({});

  // Debug logging to catch the object issue
  console.log('🔍 SmartGrammarExplanation - explanations:', explanations);
  
  explanations.forEach((exp, idx) => {
    console.log(`🔍 Explanation ${idx}:`, exp);
    console.log(`🔍 example_from_text type:`, typeof exp.example_from_text);
    console.log(`🔍 example_from_text value:`, exp.example_from_text);
  });

  const toggleCard = (patternName: string) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(patternName)) {
      newExpanded.delete(patternName);
    } else {
      newExpanded.add(patternName);
    }
    setExpandedCards(newExpanded);
  };

  const toggleQuizAnswer = (patternName: string) => {
    const newShowQuiz = new Set(showQuizAnswers);
    if (newShowQuiz.has(patternName)) {
      newShowQuiz.delete(patternName);
    } else {
      newShowQuiz.add(patternName);
    }
    setShowQuizAnswers(newShowQuiz);
  };

  const markGrammarKnowledge = async (pattern: string, status: 'known' | 'practice') => {
    setMarkingStatus(prev => ({ ...prev, [pattern]: true }));
    
    try {
      const response = await SmartAPI.markGrammarKnowledge(userId, pattern, status);
      
      if (response.success) {
        const levelData = {
          level: response.data.updated_level.user_level?.level || 'A1',
          score: response.data.updated_level.scores?.total_score || 0
        };
        onGrammarMarked?.(pattern, status, levelData);
      }
    } catch (error) {
      console.error('Error marking grammar:', error);
    } finally {
      setMarkingStatus(prev => ({ ...prev, [pattern]: false }));
    }
  };

  const getDifficultyColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'a1': return 'bg-green-100 text-green-800 border-green-200';
      case 'a2': return 'bg-lime-100 text-lime-800 border-lime-200';
      case 'b1': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'b2': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'c1': return 'bg-red-100 text-red-800 border-red-200';
      case 'c2': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'unknown': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const loadCustomFont = async () => {
    try {
      const response = await fetch('/fonts/Roboto-Regular.ttf');
      const fontBytes = await response.arrayBuffer();
      return fontBytes;
    } catch (error) {
      console.error('Error loading font:', error);
      return null;
    }
  };

  // Helper function to encode Turkish characters
  const encodeTurkishChars = (text: string): string => {
    const turkishChars: { [key: string]: string } = {
      'ğ': 'g', 'Ğ': 'G',
      'ü': 'u', 'Ü': 'U',
      'ş': 's', 'Ş': 'S',
      'ı': 'i', 'İ': 'I',
      'ö': 'o', 'Ö': 'O',
      'ç': 'c', 'Ç': 'C'
    };
    return text.replace(/[ğĞüÜşŞıİöÖçÇ]/g, match => turkishChars[match] || match);
  };

  const downloadPdf = async () => {
    if (!explanations || explanations.length === 0) return;
    
    try {
      const { default: jsPDF } = await import('jspdf');
      const doc = new jsPDF({
        orientation: 'p',
        unit: 'mm',
        format: 'a4',
      });

      // Use built-in font
      doc.setFont('helvetica', 'normal');

      // Set initial position and styles
      let y = 20;
      const margin = 20;
      const pageWidth = 210;
      const contentWidth = pageWidth - (margin * 2);

      // Helper for adding text with proper line breaks
      const addText = (text: string, fontSize: number = 11) => {
        doc.setFontSize(fontSize);
        // Encode Turkish characters before adding to PDF
        const encodedText = encodeTurkishChars(text);
        const lines = doc.splitTextToSize(encodedText, contentWidth);
        doc.text(lines, margin, y);
        y += (lines.length * fontSize * 0.3527) + 5; // Convert pt to mm

        // Add new page if needed
        if (y > 270) {
          doc.addPage();
          y = 20;
        }
      };

      explanations.forEach((exp, idx) => {
        // Title and Level
        addText(`${idx + 1}. ${exp.pattern_display_name} (${exp.difficulty_level.toUpperCase()})`, 16);
        
        // Structure Rule
        addText(`Yapi Kurali:\n${exp.structure_rule}`);
        
        // Usage Purpose
        addText(`Kullanim Amaci:\n${exp.usage_purpose}`);

        // Examples with Analysis
        if (Array.isArray(exp.example_from_text)) {
          addText('Metindeki Ornekler:', 12);
          exp.example_from_text.forEach((example, idx) => {
            if (typeof example === 'string') {
              addText(`Ornek ${idx + 1}: "${example}"`);
            } else if (example && typeof example === 'object') {
              if ('sentence' in example && 'analysis' in example) {
                // GrammarExample type
                addText(`Ornek ${idx + 1}: "${String(example.sentence || '')}"`);
                y -= 3;
                addText(`    ${String(example.analysis || '')}`, 10);
              } else if ('sentence' in example && 'preposition' in example) {
                // PrepositionExample type
                addText(`Ornek ${idx + 1}: "${String(example.sentence || '')}"`);
                y -= 3;
                addText(`    Edat: ${String(example.preposition || '')}`, 10);
                if (example.explanation) {
                  y -= 3;
                  addText(`    Aciklama: ${String(example.explanation)}`, 10);
                }
                if (example.turkish_explanation) {
                  y -= 3;
                  addText(`    Turkce: ${String(example.turkish_explanation)}`, 10);
                }
              } else if ('example' in example && 'explanation' in example) {
                // SimpleExample type
                addText(`Ornek ${idx + 1}: "${String(example.example || '')}"`);
                if (example.explanation) {
                  y -= 3;
                  addText(`    Aciklama: ${String(example.explanation)}`, 10);
                }
              } else {
                // Generic object - try to extract text
                const values = Object.values(example).filter(val => 
                  typeof val === 'string' && val.trim().length > 0
                );
                addText(`Ornek ${idx + 1}: "${values[0] || 'Gecersiz ornek'}"`);
                if (values.length > 1) {
                  y -= 3;
                  addText(`    ${values.slice(1).join(' - ')}`, 10);
                }
              }
            } else {
              addText(`Ornek ${idx + 1}: "${String(example || 'Gecersiz ornek')}"`);
            }
          });
        } else if (typeof exp.example_from_text === 'string') {
          addText(`Metindeki Ornek:\n"${exp.example_from_text}"`);
        }

        // Text Analysis
        addText(`Metin Analizi:\n${exp.text_analysis}`);
        
        // Learning Tip
        addText(`Ogrenme Ipucu:\n${exp.learning_tip}`);
        
        // Add separator between patterns
        if (idx < explanations.length - 1) {
          doc.setLineWidth(0.5);
          doc.line(margin, y, pageWidth - margin, y);
          y += 10;
        }
      });

      doc.save('grammar_explanations.pdf');
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
  };

  if (!explanations || explanations.length === 0) {
    return (
      <div className="text-center py-8 bg-gray-50 rounded-lg">
        <div className="text-gray-500 mb-2">🤖</div>
        <p className="text-gray-600">Metinde analiz edilecek gramer yapısı bulunamadı.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border-l-4 border-blue-400">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">
          🧠 AI Öğretmen Açıklamaları
        </h3>
        <button
          onClick={downloadPdf}
          className="ml-auto bg-teal-500 hover:bg-teal-600 text-white text-sm px-3 py-1 rounded flex items-center gap-1"
        >
          ⬇️ PDF İndir
        </button>
        <p className="text-blue-700 text-sm">
          Size özel hazırlanmış gramer açıklamaları ve pratik soruları.
        </p>
      </div>

      {explanations.map((explanation, index) => (
        <div key={`${explanation.pattern_name}-${index}`} className="bg-white rounded-lg shadow-md border border-gray-200">
          {/* Header */}
          <div 
            className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
            onClick={() => toggleCard(explanation.pattern_name)}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getDifficultyColor(explanation.difficulty_level)}`}>
                  {explanation.difficulty_level.toUpperCase()}
                </span>
                <h4 className="font-semibold text-gray-800">
                  {explanation.pattern_display_name}
                </h4>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">
                  👤 {explanation.user_level} seviyesi için
                </span>
                <svg 
                  className={`w-5 h-5 transition-transform ${
                    expandedCards.has(explanation.pattern_name) ? 'rotate-180' : ''
                  }`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            {/* Example from text - always visible */}
            <div className="mt-3 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Metindeki örnekler:
              </p>
              {typeof explanation.example_from_text === 'string' ? (
                <p className="text-sm text-gray-700">&quot;{explanation.example_from_text}&quot;</p>
              ) : Array.isArray(explanation.example_from_text) ? (
                <div className="space-y-2">
                  {explanation.example_from_text.map((example, idx) => {
                    // Debug logging
                    console.log(`🔍 Example ${idx}:`, example, typeof example);
                    
                    // Safe type checking for different object types
                    if (typeof example === 'string') {
                      return (
                        <p key={idx} className="text-gray-700">
                          <span className="font-medium">Örnek {idx + 1}:</span> &quot;{example}&quot;
                        </p>
                      );
                    } else if (example && typeof example === 'object') {
                      // Check for different object structures
                      if ('sentence' in example && 'analysis' in example) {
                        // GrammarExample type
                        return (
                          <div key={idx} className="text-sm">
                            <p className="text-gray-700">
                              <span className="font-medium">Örnek {idx + 1}:</span> &quot;{String(example.sentence || '')}&quot;
                            </p>
                            {example.analysis && (
                              <p className="text-gray-600 text-xs mt-1 pl-4">
                                {String(example.analysis)}
                              </p>
                            )}
                          </div>
                        );
                      } else if ('sentence' in example && 'preposition' in example) {
                        // PrepositionExample type
                        return (
                          <div key={idx} className="text-sm">
                            <p className="text-gray-700">
                              <span className="font-medium">Örnek {idx + 1}:</span> &quot;{String(example.sentence || '')}&quot;
                            </p>
                            <div className="mt-1 pl-4 space-y-1">
                              <p className="text-blue-600 text-xs">
                                <span className="font-medium">Edat:</span> {String(example.preposition || '')}
                              </p>
                              {example.explanation && (
                                <p className="text-gray-600 text-xs">
                                  <span className="font-medium">Açıklama:</span> {String(example.explanation)}
                                </p>
                              )}
                              {example.turkish_explanation && (
                                <p className="text-green-600 text-xs">
                                  <span className="font-medium">Türkçe:</span> {String(example.turkish_explanation)}
                                </p>
                              )}
                            </div>
                          </div>
                        );
                      } else if ('example' in example && 'explanation' in example) {
                        // SimpleExample type
                        return (
                          <div key={idx} className="text-sm">
                            <p className="text-gray-700">
                              <span className="font-medium">Örnek {idx + 1}:</span> &quot;{String(example.example || '')}&quot;
                            </p>
                            {example.explanation && (
                              <p className="text-gray-600 text-xs mt-1 pl-4">
                                <span className="font-medium">Açıklama:</span> {String(example.explanation)}
                              </p>
                            )}
                          </div>
                        );
                      } else {
                        // Generic object handling - try to extract meaningful text
                        const objectValues = Object.values(example).filter(val => 
                          typeof val === 'string' && val.trim().length > 0
                        );
                        
                        return (
                          <div key={idx} className="text-sm">
                            <p className="text-gray-700">
                              <span className="font-medium">Örnek {idx + 1}:</span> 
                              {objectValues.length > 0 ? ` "${objectValues[0]}"` : ' Geçersiz örnek'}
                            </p>
                            {objectValues.length > 1 && (
                              <p className="text-gray-600 text-xs mt-1 pl-4">
                                {objectValues.slice(1).join(' • ')}
                              </p>
                            )}
                          </div>
                        );
                      }
                    } else {
                      // Fallback for unknown types
                      return (
                        <p key={idx} className="text-gray-700">
                          <span className="font-medium">Örnek {idx + 1}:</span> &quot;{String(example || 'Geçersiz örnek')}&quot;
                        </p>
                      );
                    }
                  })}
                </div>
              ) : (
                <p className="text-sm text-gray-700 italic">Örnek bulunamadı</p>
              )}
            </div>
          </div>

          {/* Expanded Content */}
          {expandedCards.has(explanation.pattern_name) && (
            <div className="px-4 pb-4 space-y-4">
              {/* Structure Rule */}
              <div className="bg-green-50 p-4 rounded-lg">
                <h5 className="font-medium text-green-800 mb-2">📘 Yapı Kuralı:</h5>
                <p className="text-gray-700">{explanation.structure_rule}</p>
              </div>

              {/* Usage Purpose */}
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h5 className="font-medium text-yellow-800 mb-2">🎯 Kullanım Amacı:</h5>
                <p className="text-gray-700">{explanation.usage_purpose}</p>
              </div>

              {/* Text Analysis */}
              <div className="bg-purple-50 p-4 rounded-lg">
                <h5 className="font-medium text-purple-800 mb-2">🔍 Metin Analizi:</h5>
                <p className="text-gray-700">{explanation.text_analysis}</p>
              </div>

              {/* Learning Tip */}
              <div className="bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-400">
                <h5 className="font-medium text-indigo-800 mb-2">💡 Öğrenme İpucu:</h5>
                <p className="text-gray-700">{explanation.learning_tip}</p>
              </div>

              {/* Interactive Quiz */}
              <div className="bg-gradient-to-r from-pink-50 to-rose-50 p-4 rounded-lg border border-pink-200">
                <h5 className="font-medium text-pink-800 mb-3">🎯 Pratik Sorusu:</h5>
                <div className="space-y-3">
                  <p className="text-gray-700 font-medium">
                    Aşağıdaki cümleyi Türkçe&apos;ye çevirin:
                  </p>
                  <div className="bg-white p-3 rounded border-2 border-pink-200">
                    <p className="italic text-gray-800">&quot;{explanation.quiz_question}&quot;</p>
                  </div>
                  
                  <div className="flex gap-2">
                    <button
                      onClick={() => toggleQuizAnswer(explanation.pattern_name)}
                      className="px-4 py-2 bg-pink-500 text-white rounded hover:bg-pink-600 transition-colors"
                    >
                      {showQuizAnswers.has(explanation.pattern_name) ? '🙈 Cevabı Gizle' : '👁️ Cevabı Göster'}
                    </button>
                  </div>

                  {/* Quiz Answer */}
                  {showQuizAnswers.has(explanation.pattern_name) && (
                    <div className="bg-green-100 p-3 rounded border border-green-200">
                      <p className="font-medium text-green-800 mb-1">✅ Doğru Cevap:</p>
                      <p className="text-gray-800">&quot;{explanation.hidden_answer}&quot;</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons Removed - Tick system on dashboard */}
            </div>
          )}
        </div>
      ))}
    </div>
  );
} 