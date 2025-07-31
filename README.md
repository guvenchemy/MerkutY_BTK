# MerkutY BTK - AI-Powered Language Learning Platform

> **Not:** Bu proje veritabanı ola## 🔧 Sorun Giderme

### Backend "No module named 'app'" Hatası
- `cd backend` ile backend dizinine git
- Virtual environment'ı aktive et:
  - Mac/Linux: `source venv_new/bin/activate`
  - Windows: `venv_new\Scripts\Activate.ps1`
- `uvicorn app.main:app --reload` komutunu çalıştır

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
- Sonra tekrar `venv_new\Scripts\Activate.ps1` denereSQL** kullanır ve Gemini AI API entegrasyonu içerir.

## 🚀 Hızlı Kurulum (Arkadaşlar İçin)

### Ön Gereksinimler
- Python 3.9+ 
- Node.js 16+
- PostgreSQL (yüklü ve çalışır durumda olmalı!)
- Git
- Google Gemini API Key (Metin analizi için)

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

## 🔧 Sorun Giderme

### Backend "No module named 'app'" Hatası
- `cd backend` ile backend dizinine git
- `source venv_new/bin/activate` ile virtual environment'ı aktifleştir
- `uvicorn app.main:app --reload` komutunu çalıştır

### Database Bağlantı Hatası
- PostgreSQL'in çalıştığından emin ol
- `createdb merkuty_btk_db` ile database oluştur
- `.env` dosyasında `DATABASE_URL` doğru ayarlanmış mı kontrol et

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
- **processed_transcripts**: YouTube transkriptleri
- **url_content**: URL cache sistemi
- **unknown_words**: Bilinmeyen kelimeler
- **grammar_patterns**: Gramer kalıpları (YENİ!)
- **user_grammar_knowledge**: Kullanıcı gramer bilgisi takibi (YENİ!)

## 🔑 Environment Variables

`.env` dosyasında şunlar gerekli:
```env
DATABASE_URL=postgresql://localhost/nexus_db
SECRET_KEY=your-secret-key-here
GOOGLE_API_KEY=your-google-gemini-api-key-here
```

> **ÖNEMLİ:** GOOGLE_API_KEY olmadan metin analizi çalışmaz!

## ✨ Özellikler

### 🎯 Metin Adaptasyonu
- YouTube videolarından transkript çıkarma
- Kişisel kelime hazinesine göre metin adaptasyonu
- i+1 metoduna uygun zorluk seviyesi ayarlama
- Kelime öğrenme takibi

### 🔍 Metin Analizi (YENİ!)
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
- **YouTube Desteği**: Video transkriptlerinin otomatik analizi
- **Gramer Örnekleri**: Her gramer yapısı için metinden çıkarılan örnekler ve Türkçe çevirileri
- **Kullanıcı Etkileşimi**: Gramer kalıplarını "Biliyorum/Bilmiyorum/Görmezden gel" ile işaretleme
- **PDF İndirme**: Analiz raporları, orijinal metin ve adapte metin PDF formatında
- **i+1 Adaptasyon**: Metinleri kullanıcı seviyesine göre basitleştirme

## 🚨 Önemli Notlar

1. **Database**: Herkes aynı database yapısını kullanmalı
2. **Migration'lar**: `alembic upgrade head` komutunu çalıştır
3. **Virtual Environment**: Her zaman aktif olmalı
4. **Port Çakışması**: 8000 portu kullanılıyorsa 8001, 8002 dene
5. **YouTube API**: IP engeli olabilir, optimizasyon yapıldı (max 3 deneme)
6. **Gemini API**: GOOGLE_API_KEY olmadan metin analizi çalışmaz!
7. **spaCy Modeli**: Detaylı gramer analizi için `python -m spacy download en_core_web_sm`
8. **ReportLab**: PDF oluşturma için gerekli
9. **Türkçe Karakterler**: PDF'lerde Türkçe karakter desteği mevcut

## 🎯 Metin Analizi Kullanımı

### API Endpoints:
- `POST /api/analysis/analyze-text` - Metin analizi
- `POST /api/analysis/analyze-youtube` - YouTube video analizi
- `POST /api/analysis/generate-pdf` - PDF rapor oluşturma
- `POST /api/analysis/download-text` - Metin PDF'i indirme
- `POST /api/analysis/update-grammar-knowledge` - Gramer bilgisi güncelleme
- `GET /api/analysis/analysis-info` - Özellik bilgileri

### Örnek Kullanım:
```bash
# Metin analizi
curl -X POST "http://localhost:8000/api/analysis/analyze-text" \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here", "include_examples": true, "include_adaptation": true}'

# YouTube video analizi
curl -X POST "http://localhost:8000/api/analysis/analyze-youtube" \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://youtube.com/watch?v=VIDEO_ID", "include_adaptation": true}'
```

## 📚 Yeni Paketler (requirements.txt)

Bugünkü güncelleme ile eklenen paketler:
- `google-generativeai==0.8.3` - Gemini AI API
- `reportlab==3.7.1` - PDF oluşturma
- `markdown2==2.4.11` - Markdown işleme
- `spacy==3.7.2` - Detaylı dil analizi (opsiyonel)

## 📞 Yardım

Sorun yaşarsan:
1. README'yi tekrar oku
2. Virtual environment aktif mi kontrol et
3. Database bağlantısını test et
4. Port çakışması var mı kontrol et
