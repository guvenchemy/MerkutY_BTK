@echo off
REM 🚀 NEXUS - CEFR Language Learning Platform
REM NAS Sunucu Windows Hızlı Kurulum Script'i

echo 🚀 NEXUS - CEFR Language Learning Platform
echo ==========================================
echo Windows NAS Sunucu Kurulum Script'i
echo.

REM Sistem kontrolü
echo 🔍 Sistem Kontrolleri...

REM Docker kontrolü
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker yüklü değil! Lütfen önce Docker Desktop'ı yükleyin.
    pause
    exit /b 1
)
echo ✅ Docker yüklü

REM Docker Compose kontrolü
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose yüklü değil! Lütfen önce Docker Desktop'ı yükleyin.
    pause
    exit /b 1
)
echo ✅ Docker Compose yüklü

echo.
echo 📝 Kurulum Bilgileri
echo ===================

set /p NAS_IP="NAS Sunucu IP adresi (örn: 192.168.1.100): "
if "%NAS_IP%"=="" (
    echo ❌ NAS IP adresi gerekli!
    pause
    exit /b 1
)

set /p GEMINI_KEY="Gemini API Key: "
if "%GEMINI_KEY%"=="" (
    echo ❌ Gemini API Key gerekli!
    pause
    exit /b 1
)

echo.
echo 📁 Dizinleri Oluşturuyor...
if not exist uploads mkdir uploads
if not exist logs mkdir logs
if not exist data mkdir data
if not exist data\redis mkdir data\redis
if not exist backups mkdir backups
echo ✅ Dizinler oluşturuldu

echo.
echo ⚙️  Environment Dosyası Oluşturuluyor...

REM .env dosyası oluştur
(
echo # Database Configuration ^(Mevcut NAS PostgreSQL 17^)
echo DATABASE_URL=postgresql://merkut_user:merkut_password_123@host.docker.internal:5432/nexus_db
echo POSTGRES_USER=merkut_user
echo POSTGRES_PASSWORD=merkut_password_123
echo POSTGRES_DB=nexus_db
echo.
echo # AI API Keys
echo GEMINI_API_KEY=%GEMINI_KEY%
echo OPENAI_API_KEY=
echo.
echo # Application Settings
echo SECRET_KEY=your_super_secret_32_character_key_here_12345
echo DEBUG=false
echo ENVIRONMENT=production
echo.
echo # Frontend Configuration
echo NEXT_PUBLIC_API_URL=http://%NAS_IP%:8000
echo.
echo # Redis Configuration
echo REDIS_URL=redis://redis:6379/0
echo.
echo # Security Settings
echo ALLOWED_HOSTS=localhost,127.0.0.1,%NAS_IP%
echo CORS_ORIGINS=http://localhost:3000,http://%NAS_IP%:3000
echo.
echo # File Upload Settings
echo MAX_UPLOAD_SIZE=100MB
echo UPLOAD_DIR=/app/uploads
echo.
echo # Logging
echo LOG_LEVEL=INFO
echo LOG_FILE=/app/logs/app.log
) > .env

echo ✅ .env dosyası oluşturuldu

echo.
echo 🗄️  PostgreSQL Database Kurulumu Gerekli!
echo ⚠️  Manuel olarak şu komutları PostgreSQL'de çalıştırın:
echo.
echo CREATE DATABASE nexus_db;
echo CREATE USER merkut_user WITH PASSWORD 'merkut_password_123';
echo GRANT ALL PRIVILEGES ON DATABASE nexus_db TO merkut_user;
echo ALTER DATABASE nexus_db OWNER TO merkut_user;
echo.
pause

echo.
echo 📦 Docker İmajları İndiriliyor...
docker-compose pull

echo.
echo 🔨 Docker İmajları Build Ediliyor...
docker-compose build

echo.
echo 🚀 Servisler Başlatılıyor...
docker-compose up -d

echo.
echo ⏳ Servisler Hazırlanıyor...
timeout /t 30 /nobreak >nul

echo.
echo 🏥 Servis Durumu Kontrolleri...

REM Backend kontrol
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Backend henüz hazır değil
) else (
    echo ✅ Backend sağlıklı
)

REM Frontend kontrol
curl -f http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Frontend henüz hazır değil
) else (
    echo ✅ Frontend sağlıklı
)

echo.
echo 🎉 Kurulum Tamamlandı!
echo =====================
echo.
echo 📱 Erişim URL'leri:
echo   Frontend: http://%NAS_IP%:3000
echo   API: http://%NAS_IP%:8000
echo   API Docs: http://%NAS_IP%:8000/docs
echo.
echo 📋 Yararlı Komutlar:
echo   Logları görüntüle: docker-compose logs -f
echo   Servisleri durdur: docker-compose down
echo   Servisleri yeniden başlat: docker-compose restart
echo   Backup al: backup.sh
echo.
echo 🔧 Kurulum Sonrası:
echo   1. Frontend'e erişip test edin
echo   2. YouTube URL'i ile CEFR analizi test edin
echo   3. PostgreSQL database'in düzgün kurulduğundan emin olun
echo.
echo 📝 Sorun yaşarsanız:
echo   - docker-compose logs komutunu kullanın
echo   - KURULUM_REHBERI.md dosyasını okuyun
echo   - PostgreSQL bağlantısını kontrol edin
echo.
echo ✅ NEXUS başarıyla kuruldu! 🎊

pause
