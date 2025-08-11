# 🚀 NAS Sunucuda Kurulum Rehberi

Bu rehber, CEFR Language Learning Platform'u NAS sunucunuzda kurmak için detaylı adımları içerir.

## 📋 Ön Gereksinimler

### 1. Sistem Gereksinimleri
- NAS sunucu (Synology, QNAP, vb.)
- Docker ve Docker Compose yüklü
- PostgreSQL 17 (zaten yüklü)
- En az 4GB RAM
- En az 10GB boş disk alanı

### 2. Kontrol Listesi
```bash
# Docker kurulu mu?
docker --version

# Docker Compose kurulu mu?
docker-compose --version

# PostgreSQL çalışıyor mu?
sudo systemctl status postgresql
# veya
ps aux | grep postgres

# PostgreSQL portu açık mı?
netstat -tlnp | grep 5432
```

## 🛠️ Kurulum Adımları

### Adım 1: Projeyi Sunucuya Kopyalama

#### Seçenek A: Git ile (Önerilen)
```bash
# Sunucuya SSH ile bağlan
ssh kullanici@nas-sunucu-ip

# Proje dizinini oluştur
mkdir -p /volume1/docker/nexus-app
cd /volume1/docker/nexus-app

# Repository'yi klonla
git clone https://github.com/guvenchemy/MerkutY_BTK.git .
```

#### Seçenek B: Manuel Kopyalama
```bash
# Yerel bilgisayardan sunucuya kopyala
scp -r ./MerkutY_BTK kullanici@nas-sunucu-ip:/volume1/docker/nexus-app/
```

### Adım 2: PostgreSQL Database Kurulumu

```bash
# PostgreSQL'e bağlan
sudo -u postgres psql

# Database ve kullanıcı oluştur
CREATE DATABASE nexus_db;
CREATE USER merkut_user WITH PASSWORD 'merkut_password_123';
GRANT ALL PRIVILEGES ON DATABASE nexus_db TO merkut_user;

# PostgreSQL ayarlarını kontrol et
\l  -- Database listesi
\q  -- Çıkış
```

#### PostgreSQL Bağlantı Ayarları (pg_hba.conf)
```bash
# PostgreSQL config dosyasını düzenle
sudo nano /etc/postgresql/17/main/pg_hba.conf

# Bu satırı ekle (Docker container'larından erişim için)
host    nexus_db        merkut_user     172.18.0.0/16           md5
host    nexus_db        merkut_user     127.0.0.1/32            md5

# PostgreSQL'i yeniden başlat
sudo systemctl restart postgresql
```

### Adım 3: Environment Dosyası Kurulumu

```bash
cd /volume1/docker/nexus-app

# .env dosyasını oluştur
cp .env.example .env

# .env dosyasını düzenle
nano .env
```

#### .env Dosyası Ayarları:
```bash
# Database Configuration
DATABASE_URL=postgresql://merkut_user:merkut_password_123@host.docker.internal:5432/nexus_db
POSTGRES_USER=merkut_user
POSTGRES_PASSWORD=merkut_password_123
POSTGRES_DB=nexus_db

# AI API Keys (ZORUNLU!)
GEMINI_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY_HERE
OPENAI_API_KEY=your_openai_api_key_here

# Application Settings
SECRET_KEY=your_super_secret_32_character_key_here_12345
DEBUG=false
ENVIRONMENT=production

# Frontend Configuration (NAS IP adresi)
NEXT_PUBLIC_API_URL=http://NAS-SUNUCU-IP:8000

# Security Settings (NAS IP adresi ekle)
ALLOWED_HOSTS=localhost,127.0.0.1,NAS-SUNUCU-IP
CORS_ORIGINS=http://localhost:3000,http://NAS-SUNUCU-IP:3000
```

### Adım 4: Gerekli Dizinleri Oluşturma

```bash
# Uygulama dizinleri
mkdir -p uploads
mkdir -p logs
mkdir -p data/redis
mkdir -p backups

# İzinleri ayarla
chmod 755 uploads logs data/redis backups
```

### Adım 5: Deployment Script'ini Çalıştırma

```bash
# Script'e çalıştırma izni ver
chmod +x deploy.sh

# Deployment'ı başlat
./deploy.sh
```

### Adım 6: Servisleri Kontrol Etme

```bash
# Container'ların durumunu kontrol et
docker-compose ps

# Logları kontrol et
docker-compose logs -f

# Spesifik servis logları
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🌐 Erişim URL'leri

Kurulum tamamlandıktan sonra:

- **Frontend**: http://NAS-SUNUCU-IP:3000
- **API**: http://NAS-SUNUCU-IP:8000
- **API Docs**: http://NAS-SUNUCU-IP:8000/docs
- **Nginx (Reverse Proxy)**: http://NAS-SUNUCU-IP:80

## 🔧 Portainer ile Yönetim (Opsiyonel)

### Portainer Kurulumu:
```bash
# Portainer volume oluştur
docker volume create portainer_data

# Portainer'ı çalıştır
docker run -d -p 8000:8000 -p 9000:9000 \
  --name=portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  portainer/portainer-ce
```

### Portainer'da Stack Ekleme:
1. http://NAS-SUNUCU-IP:9000 adresine git
2. Stacks > Add stack
3. `docker-compose.yml` içeriğini yapıştır
4. Environment variables ekle
5. Deploy stack

## 🚨 Sorun Giderme

### Backend Container Başlamıyor
```bash
# Logları kontrol et
docker-compose logs backend

# Database bağlantısını test et
docker-compose exec backend ping host.docker.internal

# Container içinde database test
docker-compose exec backend python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://merkut_user:merkut_password_123@host.docker.internal:5432/nexus_db')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

### PostgreSQL Bağlantı Sorunu
```bash
# PostgreSQL'in çalıştığını kontrol et
sudo systemctl status postgresql

# Port kontrolü
netstat -tlnp | grep 5432

# PostgreSQL logları
sudo tail -f /var/log/postgresql/postgresql-17-main.log
```

### Docker Network Sorunu
```bash
# Docker network'leri listele
docker network ls

# Network detayları
docker network inspect nexus-app_merkut_network
```

## 🔒 Güvenlik Ayarları

### Firewall Kuralları:
```bash
# Gerekli portları aç
sudo ufw allow 3000  # Frontend
sudo ufw allow 8000  # Backend API
sudo ufw allow 80    # Nginx
sudo ufw allow 9000  # Portainer (opsiyonel)
```

### SSL Sertifikası (Üretim için):
```bash
# Let's Encrypt kurulumu
sudo apt install certbot

# SSL sertifikası al
sudo certbot certonly --standalone -d your-domain.com
```

## 🔄 Yedekleme ve Bakım

### Otomatik Yedekleme:
```bash
# Backup script'ini çalıştır
chmod +x backup.sh
./backup.sh

# Cron job olarak ekle
crontab -e
# Her gün 02:00'da backup al
0 2 * * * cd /volume1/docker/nexus-app && ./backup.sh
```

### Güncelleme:
```bash
# Git'ten güncellemeleri çek
git pull origin main

# Container'ları yeniden build et
docker-compose build

# Servisleri yeniden başlat
docker-compose up -d
```

## ✅ Kurulum Tamamlandı!

Kurulum başarılı olduysa:
1. ✅ PostgreSQL database oluşturuldu
2. ✅ Docker container'ları çalışıyor
3. ✅ Frontend erişilebilir
4. ✅ API çalışıyor
5. ✅ Gemini API bağlantısı kuruldu

### Test Etme:
- Frontend'e git: http://NAS-SUNUCU-IP:3000
- YouTube URL'i test et
- CEFR analizi çalışıyor mu kontrol et

## 📞 Destek

Sorun yaşarsanız:
1. `docker-compose logs` ile logları kontrol edin
2. PostgreSQL bağlantısını test edin
3. Environment variables'ları kontrol edin
4. Network ayarlarını kontrol edin
