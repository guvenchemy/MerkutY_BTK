"""
Metin analizi servisini test etmek için basit test scripti
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.text_analysis_service import TextAnalysisService

def test_text_analysis():
    # Test metni
    sample_text = """
    The weather is beautiful today. I am going to the park with my friends. 
    We will play football and have a picnic. Yesterday, we went to the beach and swam in the ocean.
    If it rains tomorrow, we might stay home and watch movies instead.
    The children who were playing in the garden looked very happy.
    This book is more interesting than the one I read last week.
    """
    
    # Servis oluştur
    service = TextAnalysisService()
    
    print("🔍 Metin analizi başlatılıyor...")
    print(f"📝 Test metni: {sample_text[:100]}...")
    print("\n" + "="*50)
    
    # Analiz yap
    result = service.analyze_text(sample_text)
    
    # Sonuçları yazdır
    if "error" in result:
        print(f"❌ Hata: {result['error']}")
        return
    
    print("✅ Analiz tamamlandı!")
    
    # Temel istatistikler
    stats = result['basic_statistics']
    print(f"\n📊 Temel İstatistikler:")
    print(f"   • Kelime sayısı: {stats['word_count']}")
    print(f"   • Cümle sayısı: {stats['sentence_count']}")
    print(f"   • Paragraf sayısı: {stats['paragraph_count']}")
    print(f"   • Okuma süresi: {stats['reading_time_minutes']} dakika")
    
    # Gramer analizi
    grammar = result['grammar_analysis']
    print(f"\n📚 Gramer Analizi:")
    if 'grammar_patterns' in grammar:
        print(f"   • Tespit edilen gramer yapıları: {len(grammar['grammar_patterns'])}")
        for pattern in grammar['grammar_patterns'][:3]:
            print(f"     - {pattern['pattern_name']}: {pattern['count']} örnek")
    
    # Karmaşıklık
    if 'complexity_indicators' in grammar:
        complexity = grammar['complexity_indicators']
        print(f"   • Karmaşıklık seviyesi: {complexity['average_sentence_complexity']}")
        print(f"   • Karmaşık cümle sayısı: {complexity['complex_sentence_count']}")
    
    # Gramer örnekleri
    examples = service.get_grammar_examples(sample_text)
    print(f"\n💡 Gramer Örnekleri:")
    
    if examples.get('detected_patterns'):
        print(f"   • Pattern sayısı: {len(examples['detected_patterns'])}")
        for pattern in examples['detected_patterns'][:2]:
            print(f"     - {pattern['pattern_name']}: {pattern['examples'][0] if pattern['examples'] else 'Örnek yok'}")
    
    if examples.get('tense_examples'):
        print(f"   • Zaman örnekleri: {len(examples['tense_examples'])}")
        for tense in examples['tense_examples'][:2]:
            print(f"     - {tense}")
    
    print(f"\n🤖 AI Analizi:")
    ai_analysis = result['ai_insights']
    if ai_analysis.get('ai_analysis'):
        print(f"   {ai_analysis['ai_analysis'][:200]}...")
    else:
        print("   AI analizi mevcut değil (API key gerekli)")

if __name__ == "__main__":
    test_text_analysis()
