# CEFR Language Learning Platform - Docker Setup

Bu rehber, CEFR dil öğrenme platformununu Docker kullanarak NAS sunucunuzda nasıl kuracağınızı anlatır.

## Gereksinimler

- Docker ve Docker Compose
- PostgreSQL 17 (NAS sunucuda zaten yüklü)
- En az 4GB RAM
- En az 10GB disk alanı
- (Opsiyonel) Portainer

## Ön Hazırlık - PostgreSQL 17 Database Setup

NAS sunucunuzda PostgreSQL 17 zaten yüklü olduğu için, sadece veritabanını ve kullanıcıyı oluşturmanız gerekiyor:

```sql
-- PostgreSQL'e bağlanın
psql -U postgres

-- Database oluştur
CREATE DATABASE nexus_db;

-- Kullanıcı oluştur
CREATE USER merkut_user WITH PASSWORD 'merkut_password_123';

-- İzinleri ver
GRANT ALL PRIVILEGES ON DATABASE nexus_db TO merkut_user;

-- Çıkış
\q
```

## Hızlı Başlangıç

### 1. Depoyu Klonlayın
```bash
git clone <repository-url>
cd MerkutY_BTK
```

### 2. Ortam Değişkenlerini Ayarlayın
```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin ve aşağıdaki değişkenleri ayarlayın:
- `GEMINI_API_KEY`: Google Gemini API anahtarınız (gerekli)
- `SECRET_KEY`: Güvenli bir gizli anahtar (gerekli)
- `OPENAI_API_KEY`: OpenAI API anahtarınız (opsiyonel)

### 3. Uygulamayı Başlatın

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows:**
```batch
deploy.bat
```

### 4. Erişim

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Dokümantasyonu**: http://localhost:8000/docs

## Docker Compose Servisleri

### 🗄️ PostgreSQL Database (Host)
- Port: 5432 (NAS sunucuda mevcut PostgreSQL 17)
- Veritabanı: nexus_db
- Kullanıcı: merkut_user
- **Not**: Docker container'ı değil, mevcut PostgreSQL 17 kullanılıyor

### 🔧 Backend (FastAPI)
- Port: 8000
- Python 3.11
- CEFR analiz servisleri
- YouTube transcript işleme
- Web içerik analizi
- Host PostgreSQL'e bağlanır

### 📱 Frontend (Next.js)
- Port: 3000
- React tabanlı kullanıcı arayüzü
- CEFR seviye gösterimi
- Metin uyarlama özellikleri

### 🔄 Redis Cache
- Port: 6379
- Önbellekleme ve oturum yönetimi

### 🌐 Nginx Reverse Proxy
- Port: 80
- Load balancing
- Static dosya servisi
- Güvenlik başlıkları

## Portainer ile Kurulum

### 1. Portainer'ı Kurun
```bash
docker volume create portainer_data
docker run -d -p 8000:8000 -p 9000:9000 --name=portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce
```

### 2. Stack Olarak Ekleyin
1. Portainer UI'ya gidin (http://localhost:9000)
2. Stacks > Add stack
3. `docker-compose.yml` içeriğini yapıştırın
4. Environment variables kısmında `.env` değişkenlerini ayarlayın
5. Deploy stack

## Yapılandırma

### Veritabanı Ayarları
```env
# Mevcut NAS PostgreSQL 17'ye bağlanır
DATABASE_URL=postgresql://merkut_user:merkut_password_123@host.docker.internal:5432/nexus_db
POSTGRES_USER=merkut_user
POSTGRES_PASSWORD=merkut_password_123
POSTGRES_DB=nexus_db
```

### AI API Ayarları
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Güvenlik Ayarları
```env
SECRET_KEY=your_super_secret_key_here_minimum_32_characters
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
```

## Yedekleme

### Otomatik Yedekleme
```bash
chmod +x backup.sh
./backup.sh
```

Bu komut aşağıdakileri yedekler:
- PostgreSQL veritabanı
- Yüklenmiş dosyalar
- Loglar
- Uygulama verileri

### Manuel Veritabanı Yedeği
```bash
# Host PostgreSQL 17'den backup
pg_dump -h localhost -U merkut_user -d nexus_db > backup.sql
```

### Veritabanı Geri Yükleme
```bash
# Host PostgreSQL 17'ye restore
psql -h localhost -U merkut_user -d nexus_db < backup.sql
```

## İzleme ve Bakım

### Logları Görüntüleme
```bash
# Tüm servislerin logları
docker-compose logs -f

# Belirli bir servisin logları
docker-compose logs -f backend
```

### Servis Durumu
```bash
docker-compose ps
```

### Servisleri Yeniden Başlatma
```bash
# Tüm servisleri yeniden başlat
docker-compose restart

# Belirli bir servisi yeniden başlat
docker-compose restart backend
```

### Güncellemeler
```bash
docker-compose pull
docker-compose up -d
```

## Güvenlik

### SSL/HTTPS
Üretim ortamında SSL sertifikası kullanın:

```yaml
# docker-compose.yml içinde nginx servisi
ports:
  - "443:443"
volumes:
  - ./ssl:/etc/nginx/ssl
```

### Firewall
Gerekli portları açın:
- 80 (HTTP)
- 443 (HTTPS)
- 9000 (Portainer - sadece güvenli ağ)

### Düzenli Güvenlik Güncellemeleri
```bash
# Docker imajlarını güncelle
docker-compose pull
docker-compose up -d

# Sistem güncellemeleri
apt update && apt upgrade -y  # Ubuntu/Debian
yum update -y                 # CentOS/RHEL
```

## Sorun Giderme

### Servislerin Başlamaması
1. Docker loglarını kontrol edin: `docker-compose logs`
2. Portların kullanımda olup olmadığını kontrol edin: `netstat -tlnp`
3. Disk alanını kontrol edin: `df -h`

### Veritabanı Bağlantı Sorunları
1. PostgreSQL 17'nin çalıştığını kontrol edin: `systemctl status postgresql`
2. PostgreSQL'in 5432 portunda çalıştığını kontrol edin: `netstat -tlnp | grep 5432`
3. Database ve kullanıcının oluşturulduğunu kontrol edin
4. Backend container'ının host.docker.internal'e erişebildiğini test edin: `docker-compose exec backend ping host.docker.internal`

### Frontend Erişim Sorunları
1. Nginx konfigürasyonunu kontrol edin
2. CORS ayarlarını kontrol edin
3. API URL'lerini kontrol edin

## Performans Optimizasyonu

### Kaynak Sınırları
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### Veritabanı Optimizasyonu
- PostgreSQL için uygun shared_buffers ayarı
- Düzenli VACUUM ve ANALYZE işlemleri
- İndeks optimizasyonu

### Redis Önbellek
- TTL değerlerini optimize edin
- Memory kullanımını izleyin
- Eviction policy ayarlayın

## Destek

Sorunlarla karşılaştığınızda:
1. GitHub Issues sayfasını kontrol edin
2. Logları toplayın ve paylaşın
3. Sistem bilgilerini (Docker version, OS) ekleyin
