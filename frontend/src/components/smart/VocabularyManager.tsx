'use client';

import React, { useState, useEffect } from 'react';
import WordExplanationPopup from './WordExplanationPopup';

interface VocabularyWord {
  id: number;
  word: string;
  translation: string;
  status: 'known' | 'unknown' | 'ignore' | 'learning';
  created_at: string;
  updated_at: string;
}

interface VocabularyManagerProps {
  currentUser: string;
  onVocabularyUpdated?: () => void;
}

export default function VocabularyManager({ currentUser, onVocabularyUpdated }: VocabularyManagerProps) {
  const [knownWords, setKnownWords] = useState<VocabularyWord[]>([]);
  const [unknownWords, setUnknownWords] = useState<VocabularyWord[]>([]);
  const [ignoredWords, setIgnoredWords] = useState<VocabularyWord[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'known' | 'unknown' | 'ignored'>('known');
  
  // Word popup state
  const [selectedWord, setSelectedWord] = useState<string>('');
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  
  // Filter and sort states
  const [searchTerm, setSearchTerm] = useState('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | 'date-new' | 'date-old'>('asc');
  const [groupByCategory, setGroupByCategory] = useState(false);
  
  // Accordion state for categories
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (currentUser) {
      fetchVocabulary();
    }
  }, [currentUser]);

  const fetchVocabulary = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      console.log('🔄 Fetching vocabulary for user:', currentUser);
      const url = `http://localhost:8000/api/vocabulary/user-words/${currentUser}`;
      console.log('🔄 Request URL:', url);
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('📦 Response status:', response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log('📦 Response data:', data);
        
        // Kelimeleri status'a göre grupla
        const known = data.filter((word: VocabularyWord) => word.status === 'known');
        const unknown = data.filter((word: VocabularyWord) => word.status === 'unknown' || word.status === 'learning'); // Learning kelimelerini de ekle
        const ignored = data.filter((word: VocabularyWord) => word.status === 'ignore');
        
        setKnownWords(known);
        setUnknownWords(unknown);
        setIgnoredWords(ignored);
        
        console.log('📊 Words grouped:', { known: known.length, unknown: unknown.length, ignored: ignored.length });
      } else {
        const errorText = await response.text();
        console.error('❌ Failed to fetch vocabulary. Status:', response.status, 'Error:', errorText);
      }
    } catch (error) {
      console.error('❌ Error fetching vocabulary:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleWordClick = (word: string, event: React.MouseEvent) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setPopupPosition({
      x: rect.left + rect.width / 2,
      y: rect.bottom + 10
    });
    setSelectedWord(word);
    setIsPopupOpen(true);
  };

  // Kelime kategorisi belirleme fonksiyonu
  const getWordCategory = (word: string): string => {
    const lowerWord = word.toLowerCase();
    
    // Basit kategori belirleme
    if (lowerWord.endsWith('ing') || lowerWord.endsWith('ed') || ['go', 'come', 'do', 'make', 'have', 'get', 'take', 'give', 'run', 'walk', 'talk'].includes(lowerWord)) {
      return '🏃 Fiil (Verb)';
    } else if (lowerWord.endsWith('ly')) {
      return '⚡ Zarf (Adverb)';
    } else if (lowerWord.endsWith('tion') || lowerWord.endsWith('ness') || lowerWord.endsWith('ment') || ['book', 'house', 'car', 'person', 'time'].includes(lowerWord)) {
      return '📦 İsim (Noun)';
    } else if (lowerWord.endsWith('ful') || lowerWord.endsWith('less') || lowerWord.endsWith('able') || lowerWord.endsWith('ive') || ['good', 'bad', 'big', 'small'].includes(lowerWord)) {
      return '🎨 Sıfat (Adjective)';
    } else if (['the', 'and', 'but', 'for', 'nor', 'yet', 'or', 'so', 'in', 'on', 'at', 'by'].includes(lowerWord)) {
      return '🔗 Bağlaç/Edat';
    } else {
      // Kelime uzunluğuna göre genel kategori
      if (lowerWord.length <= 4) {
        return '🔤 Kısa Kelimeler';
      } else if (lowerWord.length <= 7) {
        return '📝 Orta Kelimeler';
      } else {
        return '📚 Uzun Kelimeler';
      }
    }
  };

  // Filtreleme ve sıralama fonksiyonu
  const getFilteredAndSortedWords = () => {
    let words = getCurrentWords();
    
    // Arama filtrelemesi
    if (searchTerm) {
      words = words.filter(word => 
        word.word.toLowerCase().includes(searchTerm.toLowerCase()) ||
        word.translation.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Sıralama
    switch (sortOrder) {
      case 'asc':
        words.sort((a, b) => a.word.localeCompare(b.word));
        break;
      case 'desc':
        words.sort((a, b) => b.word.localeCompare(a.word));
        break;
      case 'date-new':
        words.sort((a, b) => new Date(b.created_at || '').getTime() - new Date(a.created_at || '').getTime());
        break;
      case 'date-old':
        words.sort((a, b) => new Date(a.created_at || '').getTime() - new Date(b.created_at || '').getTime());
        break;
    }
    
    return words;
  };

  // Kategoriye göre gruplandırma
  const getGroupedWords = () => {
    const words = getFilteredAndSortedWords();
    
    if (!groupByCategory) {
      return { 'Tüm Kelimeler': words };
    }
    
    const grouped: { [key: string]: VocabularyWord[] } = {};
    
    words.forEach(word => {
      const category = getWordCategory(word.word);
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(word);
    });
    
    // Kategorileri alfabetik olarak sırala
    const sortedGrouped: { [key: string]: VocabularyWord[] } = {};
    Object.keys(grouped).sort().forEach(key => {
      sortedGrouped[key] = grouped[key];
    });
    
    return sortedGrouped;
  };

  // Kategori accordion toggle fonksiyonu
  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  // Tüm kategorileri aç/kapat
  const toggleAllCategories = () => {
    const allCategories = Object.keys(getGroupedWords());
    if (expandedCategories.size === allCategories.length) {
      setExpandedCategories(new Set()); // Hepsini kapat
    } else {
      setExpandedCategories(new Set(allCategories)); // Hepsini aç
    }
  };

  const handleVocabularyAdded = async () => {
    // Kelime listesini yenile ve parent component'i bilgilendir
    await fetchVocabulary();
    if (onVocabularyUpdated) {
      onVocabularyUpdated();
    }
  };

  const getTabCount = (tab: string) => {
    switch (tab) {
      case 'known': return knownWords.length;
      case 'unknown': return unknownWords.length;
      case 'ignored': return ignoredWords.length;
      default: return 0;
    }
  };

  const getCurrentWords = () => {
    switch (activeTab) {
      case 'known': return knownWords;
      case 'unknown': return unknownWords;
      case 'ignored': return ignoredWords;
      default: return [];
    }
  };

  const getTabColor = (tab: string) => {
    switch (tab) {
      case 'known': return 'text-green-400 border-green-400';
      case 'unknown': return 'text-red-400 border-red-400';
      case 'ignored': return 'text-gray-400 border-gray-400';
      default: return 'text-gray-400 border-gray-400';
    }
  };

  const getTabIcon = (tab: string) => {
    switch (tab) {
      case 'known': return '✅';
      case 'unknown': return '❌';
      case 'ignored': return '🙈';
      default: return '';
    }
  };

  const getTabTitle = (tab: string) => {
    switch (tab) {
      case 'known': return 'Bildiğim Kelimeler';
      case 'unknown': return 'Öğrenmek İstediklerim (Bilmediğim + Öğrendiklerim)';
      case 'ignored': return 'Görmezden Geldiğim Kelimeler';
      default: return '';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mr-3"></div>
        <span className="text-gray-300">Kelime defteriniz yükleniyor...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h2 className="text-2xl font-bold text-white mb-2">📚 Kelime Defterim</h2>
        <p className="text-gray-400">
          Toplam {knownWords.length + unknownWords.length + ignoredWords.length} kelime koleksiyonunuz
        </p>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-gray-800 p-1 rounded-lg">
        {['known', 'unknown', 'ignored'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-md font-medium transition-all duration-200 ${
              activeTab === tab 
                ? `bg-gray-700 ${getTabColor(tab)}` 
                : 'text-gray-400 hover:text-gray-300 hover:bg-gray-700'
            }`}
          >
            <span className="text-lg">{getTabIcon(tab)}</span>
            <span className="hidden sm:inline">{getTabTitle(tab)}</span>
            <span className="bg-gray-600 text-white text-xs px-2 py-1 rounded-full">
              {getTabCount(tab)}
            </span>
          </button>
        ))}
      </div>

      {/* Filtreleme ve Sıralama Kontrolleri */}
      <div className="bg-gray-800 rounded-lg p-4 space-y-4">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Arama */}
          <div className="flex-1 min-w-64">
            <div className="relative">
              <input
                type="text"
                placeholder="Kelime veya çeviri ara..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-gray-700 text-white px-4 py-2 pl-10 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
              <span className="absolute left-3 top-2.5 text-gray-400">🔍</span>
            </div>
          </div>

          {/* Sıralama */}
          <div className="flex items-center gap-2">
            <span className="text-gray-300 text-sm font-medium">📊 Sırala:</span>
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value as any)}
              className="bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
            >
              <option value="asc">A → Z</option>
              <option value="desc">Z → A</option>
              <option value="date-new">🕒 Yeni → Eski</option>
              <option value="date-old">🕒 Eski → Yeni</option>
            </select>
          </div>

          {/* Gruplandırma */}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="groupByCategory"
              checked={groupByCategory}
              onChange={(e) => {
                setGroupByCategory(e.target.checked);
                // Gruplandırma açıldığında tüm kategorileri aç
                if (e.target.checked) {
                  setTimeout(() => {
                    setExpandedCategories(new Set(Object.keys(getGroupedWords())));
                  }, 100);
                } else {
                  setExpandedCategories(new Set());
                }
              }}
              className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
            />
            <label htmlFor="groupByCategory" className="text-gray-300 text-sm font-medium cursor-pointer">
              🏷️ Kategoriye Göre Grupla
            </label>
          </div>
        </div>

        {/* Aktif Filtreler Göstergesi */}
        {(searchTerm || sortOrder !== 'asc' || groupByCategory) && (
          <div className="flex flex-wrap gap-2 pt-2 border-t border-gray-600">
            <span className="text-gray-400 text-sm">Aktif filtreler:</span>
            {searchTerm && (
              <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
                🔍 "{searchTerm}"
              </span>
            )}
            {sortOrder !== 'asc' && (
              <span className="bg-green-600 text-white text-xs px-2 py-1 rounded-full">
                📊 {sortOrder === 'desc' ? 'Z→A' : sortOrder === 'date-new' ? 'Yeni→Eski' : 'Eski→Yeni'}
              </span>
            )}
            {groupByCategory && (
              <span className="bg-purple-600 text-white text-xs px-2 py-1 rounded-full">
                🏷️ Gruplandırma
              </span>
            )}
            <button
              onClick={() => {
                setSearchTerm('');
                setSortOrder('asc');
                setGroupByCategory(false);
              }}
              className="text-red-400 hover:text-red-300 text-xs underline"
            >
              Filtreleri Temizle
            </button>
          </div>
        )}
      </div>

      {/* Word List */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className={`text-lg font-semibold mb-4 ${getTabColor(activeTab)}`}>
          {getTabIcon(activeTab)} {getTabTitle(activeTab)} 
          <span className="ml-2 text-sm font-normal text-gray-400">
            ({getFilteredAndSortedWords().length} kelime {searchTerm && `"${searchTerm}" aramasında`})
          </span>
        </h3>

        {getFilteredAndSortedWords().length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <div className="text-4xl mb-4">📝</div>
            {searchTerm ? (
              <>
                <p>"{searchTerm}" aramasına uygun kelime bulunamadı.</p>
                <p className="text-sm mt-2">Farklı kelimeler aramayı deneyin!</p>
              </>
            ) : (
              <>
                <p>Bu kategoride henüz kelime yok.</p>
                <p className="text-sm mt-2">Metin analizinde kelimeler ekleyerek listelerinizi oluşturun!</p>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {groupByCategory && Object.keys(getGroupedWords()).length > 1 && (
              <div className="flex items-center justify-between mb-4">
                <span className="text-gray-400 text-sm">
                  {Object.keys(getGroupedWords()).length} kategori bulundu
                </span>
                <button
                  onClick={toggleAllCategories}
                  className="text-blue-400 hover:text-blue-300 text-sm font-medium px-3 py-1 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
                >
                  {expandedCategories.size === Object.keys(getGroupedWords()).length ? '📕 Hepsini Kapat' : '📖 Hepsini Aç'}
                </button>
              </div>
            )}

            {Object.entries(getGroupedWords()).map(([category, words]) => (
              <div key={category} className="bg-gray-700 rounded-lg overflow-hidden">
                {groupByCategory && Object.keys(getGroupedWords()).length > 1 ? (
                  <>
                    {/* Kategori Başlığı - Tıklanabilir */}
                    <button
                      onClick={() => toggleCategory(category)}
                      className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-600 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-medium text-gray-200">{category}</span>
                        <span className="bg-gray-600 text-white text-xs px-3 py-1 rounded-full">
                          {words.length} kelime
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <div className="text-xs text-gray-400">
                          {expandedCategories.has(category) ? 'Gizle' : 'Göster'}
                        </div>
                        <div className={`transform transition-transform duration-200 ${
                          expandedCategories.has(category) ? 'rotate-180' : 'rotate-0'
                        }`}>
                          <span className="text-gray-400 text-xl">⌄</span>
                        </div>
                      </div>
                    </button>

                    {/* Kategori İçeriği - Açılır Kapanır */}
                    <div className={`transition-all duration-300 ease-in-out ${
                      expandedCategories.has(category) 
                        ? 'max-h-[2000px] opacity-100' 
                        : 'max-h-0 opacity-0 overflow-hidden'
                    }`}>
                      <div className="p-4 pt-0 border-t border-gray-600">
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                          {words.map((wordItem) => (
                            <div
                              key={wordItem.id}
                              className={`
                                bg-gray-800 rounded-lg p-4 cursor-pointer transition-all duration-200 
                                hover:scale-105 hover:shadow-lg border-l-4
                                ${activeTab === 'known' ? 'border-green-400 hover:bg-green-900' : ''}
                                ${activeTab === 'unknown' ? 'border-red-400 hover:bg-red-900' : ''}
                                ${activeTab === 'ignored' ? 'border-gray-400 hover:bg-gray-600' : ''}
                              `}
                              onClick={(e) => handleWordClick(wordItem.word, e)}
                            >
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-2">
                                  <h4 className="font-semibold text-white text-lg">{wordItem.word}</h4>
                                  {wordItem.status === 'learning' && (
                                    <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded-full">
                                      📚
                                    </span>
                                  )}
                                </div>
                                <span className="text-xs text-gray-400">
                                  {wordItem.created_at ? new Date(wordItem.created_at).toLocaleDateString('tr-TR') : ''}
                                </span>
                              </div>
                              
                              <p className="text-gray-300 text-sm line-clamp-2">
                                {wordItem.translation}
                              </p>
                              
                              {activeTab === 'unknown' && (
                                <div className="mt-3 pt-3 border-t border-gray-600">
                                  <div className="flex items-center text-xs text-yellow-400">
                                    <span className="mr-1">💡</span>
                                    Tıklayarak detaylı açıklama görün
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  // Gruplandırma yoksa normal grid görünümü
                  <div className="p-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                      {words.map((wordItem) => (
                        <div
                          key={wordItem.id}
                          className={`
                            bg-gray-800 rounded-lg p-4 cursor-pointer transition-all duration-200 
                            hover:scale-105 hover:shadow-lg border-l-4
                            ${activeTab === 'known' ? 'border-green-400 hover:bg-green-900' : ''}
                            ${activeTab === 'unknown' ? 'border-red-400 hover:bg-red-900' : ''}
                            ${activeTab === 'ignored' ? 'border-gray-400 hover:bg-gray-600' : ''}
                          `}
                          onClick={(e) => handleWordClick(wordItem.word, e)}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold text-white text-lg">{wordItem.word}</h4>
                              {wordItem.status === 'learning' && (
                                <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded-full">
                                  📚 Öğreniyorum
                                </span>
                              )}
                            </div>
                            <span className="text-xs text-gray-400">
                              {wordItem.created_at ? new Date(wordItem.created_at).toLocaleDateString('tr-TR') : 'Tarih yok'}
                            </span>
                          </div>
                          
                          <p className="text-gray-300 text-sm line-clamp-2">
                            {wordItem.translation}
                          </p>
                          
                          {activeTab === 'unknown' && (
                            <div className="mt-3 pt-3 border-t border-gray-600">
                              <div className="flex items-center text-xs text-yellow-400">
                                <span className="mr-1">💡</span>
                                Tıklayarak detaylı açıklama görün
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-green-900 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400">{knownWords.length}</div>
          <div className="text-green-300 text-sm">Bildiğim</div>
          {activeTab === 'known' && searchTerm && (
            <div className="text-xs text-green-200 mt-1">
              {getFilteredAndSortedWords().length} görüntüleniyor
            </div>
          )}
        </div>
        <div className="bg-red-900 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-red-400">{unknownWords.length}</div>
          <div className="text-red-300 text-sm">Öğreneceklerim</div>
          <div className="text-xs text-red-200 mt-1">
            ({unknownWords.filter(w => w.status === 'unknown').length} bilmediğim + {unknownWords.filter(w => w.status === 'learning').length} öğrendiğim)
          </div>
          {activeTab === 'unknown' && searchTerm && (
            <div className="text-xs text-red-200 mt-1 border-t border-red-800 pt-1">
              {getFilteredAndSortedWords().length} görüntüleniyor
            </div>
          )}
        </div>
        <div className="bg-gray-700 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-gray-400">{ignoredWords.length}</div>
          <div className="text-gray-300 text-sm">Görmezden Geldiğim</div>
          {activeTab === 'ignored' && searchTerm && (
            <div className="text-xs text-gray-200 mt-1">
              {getFilteredAndSortedWords().length} görüntüleniyor
            </div>
          )}
        </div>
      </div>

      {/* Kategori İstatistikleri (Sadece gruplandırma aktifken) */}
      {groupByCategory && Object.keys(getGroupedWords()).length > 1 && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h4 className="text-lg font-semibold text-gray-300 mb-3 flex items-center gap-2">
            🏷️ Kategori Dağılımı
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(getGroupedWords()).map(([category, words]) => (
              <div key={category} className="bg-gray-700 rounded p-3 text-center">
                <div className="text-sm font-medium text-gray-300 mb-1">
                  {category}
                </div>
                <div className="text-lg font-bold text-blue-400">
                  {words.length}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Word Explanation Popup */}
      <WordExplanationPopup
        word={selectedWord}
        isOpen={isPopupOpen}
        onClose={() => setIsPopupOpen(false)}
        position={popupPosition}
        currentUser={currentUser}
        onVocabularyAdded={handleVocabularyAdded}
      />
    </div>
  );
}
