# Nexus - AI-Powered Language Learning Platform

> **Not:** Bu proje PostgreSQL veritabanı kullanır, Google Gemini AI API entegrasyonu içerir ve çoklu içerik tiplerini (YouTube, Medium, Wikipedia) destekler.
**Not:** Önce Nexus.pdf ve Sekmeler'i okuyunuz
## 🚀 Hızlı Kurulum (Arkadaşlar İçin)

### Ön Gereksinimler
- Python 3.9+ 
- Node.js 16+
- PostgreSQL (yüklü ve çalışır durumda olmalı!)
- Git
- Google Gemini API Key (CEFR analizi ve metin adaptasyonu için)

> **PostgreSQL Kurulum:** 
> - Windows: https://www.postgresql.org/download/windows/
> - Mac: `brew install postgresql` 
> - Linux: `sudo apt-get install postgresql`

### 1. Repository'yi Clone Et
```bash
git clone <repository-url>
cd MerkutY_BTK
```

### 2. Backend Kurulumu
```bash
cd backend

# Virtual environment oluştur
python -m venv venv_new

# Virtual environment'ı aktive et
# Mac/Linux:
source venv_new/bin/activate
# Windows (PowerShell):
venv_new\Scripts\Activate.ps1
# Windows (CMD):
venv_new\Scripts\activate.bat

# Paketleri yükle
pip install -r requirements.txt

# spaCy İngilizce modeli yükle (opsiyonel - detaylı gramer analizi için)
python -m spacy download en_core_web_sm
```

### 3. Database Kurulumu
```bash
# PostgreSQL'de database oluştur (PostgreSQL kurulu olmalı!)
createdb -U postgres nexus_db
# Eğer şifre soruyorsa PostgreSQL kurulumundaki şifreyi girin

# Environment dosyasını oluştur
cp env.example .env
# Windows'ta: copy env.example .env

# .env dosyasını bir text editör ile düzenle - ÖNEMLİ: GOOGLE_API_KEY gerekli!
# Şu değerleri ayarla:
# DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/nexus_db
# GOOGLE_API_KEY=your-google-gemini-api-key-here  
# SECRET_KEY=your-secret-key-here

# Migration'ları çalıştır
alembic upgrade head
```

### 4. Backend Server'ı Başlat
```bash
# Backend dizininde olduğundan emin ol
cd backend

# Virtual environment'ı aktive et (tekrar)
# Mac/Linux:
source venv_new/bin/activate
# Windows (PowerShell):
venv_new\Scripts\Activate.ps1
# Windows (CMD):
venv_new\Scripts\activate.bat

# Backend server'ı başlat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend Kurulumu
```bash
cd ../frontend

# Paketleri yükle
npm install

# Development server'ı başlat
npm run dev
```

## 🌐 Desteklenen Platformlar

### 📺 YouTube
- Video transkriptlerinin otomatik çıkarılması
- CEFR seviye analizi ile zorluk belirleme
- Kişisel adaptasyon ve kelime öğrenme

### 📰 Medium
- Makale içeriklerinin otomatik çıkarılması  
- AI ile seviye analizi (A1-C2)
- Öğrenme odaklı metin adaptasyonu

### 📖 Wikipedia
- Ansiklopedi makalelerinden öğrenme
- Akademik içerik seviye analizi
- Kapsamlı kelime hazinesi geliştirme

## 🎯 CEFR Seviye Sistemi

Uygulamada **Common European Framework of Reference for Languages (CEFR)** standardı kullanılır:

- **A1 (Başlangıç)**: Temel günlük ifadeler
- **A2 (Temel)**: Basit günlük konuşmalar
- **B1 (Orta-Alt)**: Günlük durumlarda etkili iletişim
- **B2 (Orta-Üst)**: Karmaşık metinleri anlama
- **C1 (İleri)**: Akıcı ve spontan dil kullanımı
- **C2 (Uzman)**: Neredeyse ana dil seviyesi

### AI Analiz Özellikleri:
- **%85+ Güvenilirlik**: Gemini AI ile doğru seviye belirleme
- **Otomatik Analiz**: Toplu içerik seviye belirleme
- **Kişisel Adaptasyon**: Kullanıcı seviyesine göre metin uyarlama
- **İlerleme Takibi**: Öğrenme sürecini izleme

## 🔧 Sorun Giderme

## 🔧 Sorun Giderme

### Backend "No module named 'app'" Hatası
- `cd backend` ile backend dizinine git
- Virtual environment'ı aktive et:
  - Mac/Linux: `source venv_new/bin/activate`
  - Windows: `venv_new\Scripts\Activate.ps1`
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` komutunu çalıştır

### Database Bağlantı Hatası
- PostgreSQL'in çalıştığından emin ol
- `createdb nexus_db` ile database oluştur
- `.env` dosyasında `DATABASE_URL` doğru ayarlanmış mı kontrol et
- PostgreSQL şifresi varsa DATABASE_URL'de belirt

### Virtual Environment Hatası (Windows)
- PowerShell execution policy hatası alıyorsan:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Sonra tekrar `venv_new\Scripts\Activate.ps1` dene

### Gemini API Hatası
- `GOOGLE_API_KEY` environment variable'ı ayarlanmış mı kontrol et
- API key'in geçerli olduğundan emin ol
- "gemini-2.0-flash" modeli kullanılıyor

### YouTube Transcript Hatası
- Bu normal, YouTube IP engeli uyguluyor (optimizasyon yapıldı - max 3 deneme)
- Farklı video ID'leri dene
- VPN kullanmayı dene

### PDF Oluşturma Hatası
- ReportLab paketi yüklü mü kontrol et: `pip install reportlab`
- Türkçe karakterler için sistem fontları kontrol ediliyor

## 📁 Önemli Dosyalar

### Backend
- `backend/requirements.txt` - Python paketleri
- `backend/env.example` - Environment template
- `backend/alembic/versions/` - Database migration'ları
- `backend/app/` - Ana uygulama kodu

### Frontend
- `frontend/package.json` - Node.js paketleri
- `frontend/src/app/page.tsx` - Ana sayfa

## 🗄️ Database Yapısı

> **Kullanılan veritabanı:** PostgreSQL

### Tablolar:
- **users**: Kullanıcı bilgileri
- **vocabularies**: Kelime listesi
- **user_vocabularies**: Kullanıcı-kelime ilişkisi
- **processed_transcripts**: YouTube transkriptleri (CEFR seviye analizi ile)
- **url_content**: Web içeriği cache sistemi (Medium, Wikipedia - CEFR seviye analizi ile)
- **unknown_words**: Bilinmeyen kelimeler
- **grammar_patterns**: Gramer kalıpları
- **user_grammar_knowledge**: Kullanıcı gramer bilgisi takibi
- **word_definitions**: Kelime tanımları cache sistemi

## 🔑 Environment Variables

`.env` dosyasında şunlar gerekli:
```env
DATABASE_URL=postgresql://localhost/nexus_db
SECRET_KEY=your-secret-key-here
GOOGLE_API_KEY=your-google-gemini-api-key-here
```

> **ÖNEMLİ:** GOOGLE_API_KEY olmadan metin analizi çalışmaz!

## ✨ Özellikler

### 🎯 Akıllı İçerik Adaptasyonu
- **Çoklu Platform Desteği**: YouTube, Medium, Wikipedia linklerinden otomatik içerik çıkarma
- **CEFR Seviye Analizi**: AI ile A1-C2 seviye belirleme (%85+ güvenilirlik)
- **Kişisel Adaptasyon**: Kullanıcının mevcut seviyesine göre metin adaptasyonu
- **Kelime Öğrenme Takibi**: Bilinmeyen kelimeleri işaretleme ve öğrenme
- **İçerik Kütüphanesi**: Seviyeye göre filtrelenebilir içerik arşivi

### 🔍 Gelişmiş Metin Analizi
- **CEFR Seviye Belirleme**: Gemini AI ile otomatik dil seviyesi analizi
- **Temel İstatistikler**: Kelime sayısı, cümle sayısı, okuma süresi
- **Gramer Analizi**: 
  - Zaman formları (Present, Past, Future, Present Perfect)
  - Modal fiiller (can, could, must, should, vb.)
  - Şartlı cümleler (if-clauses)
  - Edilgen çatı (Passive Voice)
  - İlgi zamirli cümleler (Relative Clauses)
  - Karşılaştırma ifadeleri (Comparatives & Superlatives)
- **Kelime Analizi**: Kelime çeşitliliği, sık kullanılan kelimeler
- **AI Değerlendirmesi**: Gemini AI ile Türkçe açıklamalı dil seviyesi ve öğrenme önerileri
- **Gramer Örnekleri**: Her gramer yapısı için metinden çıkarılan örnekler ve Türkçe çevirileri
- **Kullanıcı Etkileşimi**: Gramer kalıplarını "Biliyorum/Bilmiyorum/Görmezden gel" ile işaretleme
- **PDF İndirme**: Analiz raporları, orijinal metin ve adapte metin PDF formatında

### 📚 İçerik Kütüphanesi
- **YouTube İçerikleri**: Video transkriptleri ile dil öğrenme
- **Web Makaleleri**: Medium ve Wikipedia makalelerinden öğrenme
- **CEFR Filtreleme**: A1-C2 seviyelerine göre içerik filtreleme
- **Kullanıcı Seviyesi**: Kişisel seviye göstergesi ve uygun içerik önerileri
- **AI Analiz Butonu**: Tüm içeriklerin seviyelerini toplu analiz etme

## 🚨 Önemli Notlar

1. **Database**: Herkes aynı database yapısını kullanmalı
2. **Migration'lar**: `alembic upgrade head` komutunu çalıştır
3. **Virtual Environment**: Her zaman aktif olmalı
4. **Port Çakışması**: 8000 portu kullanılıyorsa 8001, 8002 dene
5. **YouTube API**: IP engeli olabilir, optimizasyon yapıldı (max 3 deneme)
6. **Gemini API**: GOOGLE_API_KEY olmadan CEFR analizi ve metin adaptasyonu çalışmaz!
7. **spaCy Modeli**: Detaylı gramer analizi için `python -m spacy download en_core_web_sm`
8. **ReportLab**: PDF oluşturma için gerekli
9. **Türkçe Karakterler**: PDF'lerde Türkçe karakter desteği mevcut
10. **Web Scraping**: Medium ve Wikipedia içerikleri otomatik çıkarılır
11. **CEFR Analizi**: Content Ready durumu için yeterli kelime hazinesi gerekli

## 🎯 API Kullanımı

### Ana Özellikler:
- `POST /api/adaptation/adapt-text` - Metin adaptasyonu (current level)
- `POST /api/analysis/analyze-text` - Metin analizi ve CEFR seviye belirleme
- `POST /api/analysis/analyze-youtube` - YouTube video analizi
- `GET /api/library/transcripts` - YouTube içerik kütüphanesi
- `GET /api/library/web-content` - Web içerik kütüphanesi (Medium, Wikipedia)
- `POST /api/library/analyze-levels` - Toplu CEFR seviye analizi
- `POST /api/analysis/generate-pdf` - PDF rapor oluşturma
- `POST /api/web-library/add-url` - Web içeriği ekleme

### Örnek Kullanım:
```bash
# Desteklenen platformlardan içerik analizi
curl -X POST "http://localhost:8000/api/analysis/analyze-text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here", "include_examples": true, "include_adaptation": true}'

# YouTube video analizi
curl -X POST "http://localhost:8000/api/analysis/analyze-youtube" \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://youtube.com/watch?v=VIDEO_ID", "include_adaptation": true}'

# Web içeriği ekleme (Medium, Wikipedia)
curl -X POST "http://localhost:8000/api/web-library/add-url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://medium.com/article-url"}'

# Kütüphanedeki içeriklerin CEFR seviyelerini analiz etme
curl -X POST "http://localhost:8000/api/library/analyze-levels" \
  -H "Content-Type: application/json"
```

## 📚 Yeni Paketler ve Teknolojiler

### AI ve ML:
- `google-generativeai==0.8.3` - Gemini AI API (CEFR analizi)
- `spacy==3.7.2` - Detaylı dil analizi (opsiyonel)

### Web Scraping:
- `beautifulsoup4==4.12.2` - Web içerik çıkarma
- `requests==2.31.0` - HTTP istekleri
- `yt-dlp==2023.7.6` - YouTube transkript çıkarma

### Database ve Backend:
- `alembic==1.13.1` - Database migration
- `sqlalchemy==2.0.25` - ORM
- `fastapi==0.104.1` - API framework
- `uvicorn==0.24.0` - ASGI server

### PDF ve Raporlama:
- `reportlab==3.7.1` - PDF oluşturma
- `markdown2==2.4.11` - Markdown işleme

### Önemli Özellikler:
- **CEFR Seviye Analizi**: A1-C2 otomatik seviye belirleme
- **Çoklu Platform**: YouTube, Medium, Wikipedia desteği
- **Current Level Adaptation**: Kullanıcı seviyesine uygun adaptasyon
- **İçerik Kütüphanesi**: Seviyeye göre filtrelenebilir arşiv
- **AI Teacher**: Gemini AI ile kişiselleştirilmiş öğrenme

## 📞 Yardım

Sorun yaşarsan:
1. README'yi tekrar oku
2. Virtual environment aktif mi kontrol et
3. Database bağlantısını test et
4. Port çakışması var mı kontrol et
