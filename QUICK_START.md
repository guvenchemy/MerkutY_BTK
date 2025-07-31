# 🚀 Hızlı Başlangıç Rehberi - MerkutY BTK

## 1. Sistemi Kur
```bash
# Setup script'ini çalıştır
./setup.sh
```

## 2. Database'i Hazırla
```bash
# PostgreSQL'de database oluştur
createdb nexus_db

# Migration'ları çalıştır
cd backend
source venv_new/bin/activate
alembic upgrade head
```

## 3. Environment Variables'ları Ayarla
```bash
# backend/.env dosyasını düzenle
nano backend/.env
```

**ÖNEMLİ:** Şunları ekle:
```env
DATABASE_URL=postgresql://localhost/nexus_db
SECRET_KEY=your-secret-key-here
GOOGLE_API_KEY=your-google-gemini-api-key-here
```

> **Not:** GOOGLE_API_KEY olmadan metin analizi çalışmaz!

## 4. Sistemi Başlat
```bash
# Backend (Terminal 1)
cd backend
source venv_new/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (Terminal 2)
cd frontend
npm run dev
```

## 5. Test Et
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## 🔧 Sorun Giderme

### "No module named 'app'" Hatası
```bash
cd backend
source venv_new/bin/activate
uvicorn app.main:app --reload
```

### Database Hatası
```bash
# PostgreSQL çalışıyor mu kontrol et
brew services list | grep postgresql

# Database oluştur
createdb nexus_db

# Migration'ları çalıştır
alembic upgrade head
```

### Port Çakışması
```bash
# Farklı port dene
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## 📞 Yardım
- README.md dosyasını oku
- Virtual environment aktif mi kontrol et
- Database bağlantısını test et 