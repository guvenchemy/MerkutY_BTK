import re
from typing import Dict, Any


class BasicStatistics:
    """
    Metin için temel istatistik hesaplama sınıfı
    """
    
    @staticmethod
    def get_basic_statistics(text: str) -> Dict[str, Any]:
        """
        Metinin temel istatistiklerini hesaplar
        """
        sentences = re.split(r'[.!?]+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words = re.findall(r'\b\w+\b', text.lower())
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Ortalama kelime uzunluğu
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        # Ortalama cümle uzunluğu
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        return {
            "character_count": len(text),
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "average_word_length": round(avg_word_length, 2),
            "average_sentence_length": round(avg_sentence_length, 2),
            "reading_time_minutes": round(len(words) / 200, 1)  # Ortalama okuma hızı 200 kelime/dakika
        } 