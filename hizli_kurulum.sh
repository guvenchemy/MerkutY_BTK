#!/bin/bash

# 🚀 NEXUS - CEFR Language Learning Platform
# NAS Sunucu Hızlı Kurulum Script'i

set -e

echo "🚀 NEXUS - CEFR Language Learning Platform"
echo "=========================================="
echo "NAS Sunucu Kurulum Script'i"
echo ""

# Renk kodları
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Hata durumunda çıkış
error_exit() {
    echo -e "${RED}❌ Hata: $1${NC}" >&2
    exit 1
}

# Başarı mesajı
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Uyarı mesajı
warning_msg() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Bilgi mesajı
info_msg() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Sistem kontrolü
echo "🔍 Sistem Kontrolleri..."

# Docker kontrolü
if ! command -v docker &> /dev/null; then
    error_exit "Docker yüklü değil! Lütfen önce Docker'ı yükleyin."
fi
success_msg "Docker yüklü ✓"

# Docker Compose kontrolü
if ! command -v docker-compose &> /dev/null; then
    error_exit "Docker Compose yüklü değil! Lütfen önce Docker Compose'u yükleyin."
fi
success_msg "Docker Compose yüklü ✓"

# PostgreSQL kontrolü
if ! command -v psql &> /dev/null; then
    warning_msg "PostgreSQL client yüklü değil. PostgreSQL server kurulu olduğundan emin olun."
else
    success_msg "PostgreSQL client yüklü ✓"
fi

# Kullanıcıdan bilgi al
echo ""
echo "📝 Kurulum Bilgileri"
echo "==================="

read -p "NAS Sunucu IP adresi (örn: 192.168.1.100): " NAS_IP
if [[ -z "$NAS_IP" ]]; then
    error_exit "NAS IP adresi gerekli!"
fi

read -p "Gemini API Key: " GEMINI_KEY
if [[ -z "$GEMINI_KEY" ]]; then
    error_exit "Gemini API Key gerekli!"
fi

read -p "PostgreSQL admin kullanıcısı (varsayılan: postgres): " PG_ADMIN
PG_ADMIN=${PG_ADMIN:-postgres}

read -s -p "PostgreSQL admin şifresi: " PG_ADMIN_PASS
echo ""

# Dizin oluştur
echo ""
echo "📁 Dizinleri Oluşturuyor..."
mkdir -p uploads logs data/redis backups
chmod 755 uploads logs data/redis backups
success_msg "Dizinler oluşturuldu"

# .env dosyası oluştur
echo ""
echo "⚙️  Environment Dosyası Oluşturuluyor..."
cat > .env << EOF
# Database Configuration (Mevcut NAS PostgreSQL 17)
DATABASE_URL=postgresql://merkut_user:merkut_password_123@host.docker.internal:5432/nexus_db
POSTGRES_USER=merkut_user
POSTGRES_PASSWORD=merkut_password_123
POSTGRES_DB=nexus_db

# AI API Keys
GEMINI_API_KEY=$GEMINI_KEY
OPENAI_API_KEY=

# Application Settings
SECRET_KEY=$(openssl rand -base64 32)
DEBUG=false
ENVIRONMENT=production

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://$NAS_IP:8000

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security Settings
ALLOWED_HOSTS=localhost,127.0.0.1,$NAS_IP
CORS_ORIGINS=http://localhost:3000,http://$NAS_IP:3000

# File Upload Settings
MAX_UPLOAD_SIZE=100MB
UPLOAD_DIR=/app/uploads

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
EOF

success_msg ".env dosyası oluşturuldu"

# PostgreSQL database kurulumu
echo ""
echo "🗄️  PostgreSQL Database Kurulumu..."

# Database oluşturma script'i
cat > setup_db.sql << EOF
-- Database oluştur
CREATE DATABASE nexus_db;

-- Kullanıcı oluştur
CREATE USER merkut_user WITH PASSWORD 'merkut_password_123';

-- İzinleri ver
GRANT ALL PRIVILEGES ON DATABASE nexus_db TO merkut_user;

-- Kullanıcıyı database owner yap
ALTER DATABASE nexus_db OWNER TO merkut_user;
EOF

# PostgreSQL'e bağlan ve database oluştur
if [[ -n "$PG_ADMIN_PASS" ]]; then
    export PGPASSWORD="$PG_ADMIN_PASS"
    psql -h localhost -U $PG_ADMIN -f setup_db.sql || warning_msg "Database zaten var olabilir, devam ediliyor..."
else
    info_msg "PostgreSQL şifresi girilmedi, manuel database kurulumu gerekebilir"
    info_msg "Manuel kurulum için şu komutları çalıştırın:"
    info_msg "psql -U $PG_ADMIN"
    cat setup_db.sql
fi

# Cleanup
rm -f setup_db.sql
unset PGPASSWORD

success_msg "Database kurulumu tamamlandı"

# Docker imajlarını çek
echo ""
echo "📦 Docker İmajları İndiriliyor..."
docker-compose pull

# Docker imajlarını build et
echo ""
echo "🔨 Docker İmajları Build Ediliyor..."
docker-compose build

# Servisleri başlat
echo ""
echo "🚀 Servisler Başlatılıyor..."
docker-compose up -d

# Servislerin başlamasını bekle
echo ""
echo "⏳ Servisler Hazırlanıyor..."
sleep 30

# Health check
echo ""
echo "🏥 Servis Durumu Kontrolleri..."

# Backend kontrol
if curl -f http://localhost:8000/health &>/dev/null; then
    success_msg "Backend sağlıklı ✓"
else
    warning_msg "Backend henüz hazır değil"
fi

# Frontend kontrol
if curl -f http://localhost:3000 &>/dev/null; then
    success_msg "Frontend sağlıklı ✓"
else
    warning_msg "Frontend henüz hazır değil"
fi

# Redis kontrol
if docker-compose exec redis redis-cli ping &>/dev/null; then
    success_msg "Redis sağlıklı ✓"
else
    warning_msg "Redis henüz hazır değil"
fi

echo ""
echo "🎉 Kurulum Tamamlandı!"
echo "====================="
echo ""
echo "📱 Erişim URL'leri:"
echo "  Frontend: http://$NAS_IP:3000"
echo "  API: http://$NAS_IP:8000"
echo "  API Docs: http://$NAS_IP:8000/docs"
echo ""
echo "📋 Yararlı Komutlar:"
echo "  Logları görüntüle: docker-compose logs -f"
echo "  Servisleri durdur: docker-compose down"
echo "  Servisleri yeniden başlat: docker-compose restart"
echo "  Backup al: ./backup.sh"
echo ""
echo "🔧 Kurulum Sonrası:"
echo "  1. Frontend'e erişip test edin"
echo "  2. YouTube URL'i ile CEFR analizi test edin"
echo "  3. Backup script'ini cron job olarak ekleyin"
echo ""
echo "📝 Sorun yaşarsanız:"
echo "  - docker-compose logs komutunu kullanın"
echo "  - KURULUM_REHBERI.md dosyasını okuyun"
echo "  - PostgreSQL bağlantısını kontrol edin"
echo ""
success_msg "NEXUS başarıyla kuruldu! 🎊"
