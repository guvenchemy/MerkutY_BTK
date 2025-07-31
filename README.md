# Nexus - AI-Powered Language Learning Platform

## 🚀 Hızlı Kurulum (Arkadaşlar İçin)

### Ön Gereksinimler
- Python 3.9+ 
- Node.js 16+
- PostgreSQL
- Git

### 1. Repository'yi Clone Et
```bash
git clone <repository-url>
cd btk_hackathon
```

### 2. Backend Kurulumu
```bash
cd backend

# Virtual environment oluştur
python -m venv venv_new

# Aktive et (Mac/Linux)
source venv_new/bin/activate
# VEYA (Windows)
# venv_new\Scripts\activate

# Paketleri yükle
pip install -r requirements.txt
```

### 3. Database Kurulumu
```bash
# PostgreSQL'de database oluştur
createdb nexus_db

# Environment dosyasını oluştur
cp env.example .env

# .env dosyasını düzenle (DATABASE_URL ve OPENAI_API_KEY gerekli)
# DATABASE_URL=postgresql://localhost/nexus_db
# OPENAI_API_KEY=your-openai-api-key-here

# Migration'ları çalıştır
alembic upgrade head
```

### 4. Backend Server'ı Başlat
```bash
# Backend dizininde olduğundan emin ol
cd backend
source venv_new/bin/activate
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
- `createdb nexus_db` ile database oluştur
- `.env` dosyasında `DATABASE_URL` doğru ayarlanmış mı kontrol et

### YouTube Transcript Hatası
- Bu normal, YouTube IP engeli uyguluyor
- Farklı video ID'leri dene
- VPN kullanmayı dene

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

### Tablolar:
- **users**: Kullanıcı bilgileri
- **vocabularies**: Kelime listesi
- **user_vocabularies**: Kullanıcı-kelime ilişkisi
- **processed_transcripts**: YouTube transkriptleri
- **url_content**: URL cache sistemi
- **unknown_words**: Bilinmeyen kelimeler

## 🔑 Environment Variables

`.env` dosyasında şunlar gerekli:
```env
DATABASE_URL=postgresql://localhost/nexus_db
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

## 🚨 Önemli Notlar

1. **Database**: Herkes aynı database yapısını kullanmalı
2. **Migration'lar**: `alembic upgrade head` komutunu çalıştır
3. **Virtual Environment**: Her zaman aktif olmalı
4. **Port Çakışması**: 8000 portu kullanılıyorsa 8001, 8002 dene
5. **YouTube API**: IP engeli olabilir, normal

## 📞 Yardım

Sorun yaşarsan:
1. README'yi tekrar oku
2. Virtual environment aktif mi kontrol et
3. Database bağlantısını test et
4. Port çakışması var mı kontrol et
