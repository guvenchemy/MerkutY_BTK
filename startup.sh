#!/bin/bash
set -e

TZ=${TZ:-Europe/Istanbul}
export TZ

WORKDIR="/workspace"
REPO_URL="https://github.com/guvenchemy/MerkutY_BTK.git"
REPO_DIR="$WORKDIR/MerkutY_BTK"
BACKEND_DIR="$REPO_DIR/backend"
LOCK_FILE="$WORKDIR/.repo.lock"

# Database configuration
DB_HOST=${DB_HOST:-192.168.1.104}
DB_PORT=${DB_PORT:-5432}
DB_ADMIN_USER=${DB_ADMIN_USER:-postgres}
DB_ADMIN_PASS=${DB_ADMIN_PASS:-4WHt1EJGZ8KateEs}
DB_NAME=${DB_NAME:-nexus_db}
DB_USER=${DB_USER:-postgres}
DB_PASS=${DB_PASS:-4WHt1EJGZ8KateEs}

# PostgreSQL database ve kullanıcı oluşturma fonksiyonu
create_database_if_not_exists() {
  echo "🗄️ Database kontrolü ve oluşturma..."
  
  # DATABASE_URL'den parametreleri parse et
  if [ -n "$DATABASE_URL" ]; then
    # postgresql://user:pass@host:port/dbname formatından parse et
    if echo "$DATABASE_URL" | grep -q "postgresql://"; then
      # URL'den bilgileri çıkar
      DB_FULL=$(echo "$DATABASE_URL" | sed 's/postgresql:\/\///')
      if echo "$DB_FULL" | grep -q "@"; then
        DB_USER_PASS=$(echo "$DB_FULL" | cut -d'@' -f1)
        DB_HOST_PORT_DB=$(echo "$DB_FULL" | cut -d'@' -f2)
        
        if echo "$DB_USER_PASS" | grep -q ":"; then
          DB_USER=$(echo "$DB_USER_PASS" | cut -d':' -f1)
          DB_PASS=$(echo "$DB_USER_PASS" | cut -d':' -f2)
        fi
        
        if echo "$DB_HOST_PORT_DB" | grep -q "/"; then
          DB_HOST_PORT=$(echo "$DB_HOST_PORT_DB" | cut -d'/' -f1)
          DB_NAME=$(echo "$DB_HOST_PORT_DB" | cut -d'/' -f2)
          
          if echo "$DB_HOST_PORT" | grep -q ":"; then
            DB_HOST=$(echo "$DB_HOST_PORT" | cut -d':' -f1)
            DB_PORT=$(echo "$DB_HOST_PORT" | cut -d':' -f2)
          else
            DB_HOST="$DB_HOST_PORT"
          fi
        fi
      fi
    fi
  fi
  
  echo "📊 Database parametreleri:"
  echo "   Host: $DB_HOST:$DB_PORT"
  echo "   Database: $DB_NAME"
  echo "   User: $DB_USER"
  
  # PostgreSQL bağlantısı test et (önce admin parolası olmadan, sonra varsa ile)
  PG_CONNECTION_OK=false
  
  # Admin parolası boşsa önce parolasız dene
  if [ -z "$DB_ADMIN_PASS" ]; then
    if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
      PG_CONNECTION_OK=true
    fi
  else
    if PGPASSWORD="$DB_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -d postgres -c "SELECT 1;" > /dev/null 2>&1; then
      PG_CONNECTION_OK=true
    fi
  fi
  
  if [ "$PG_CONNECTION_OK" = false ]; then
    echo "⚠️ PostgreSQL'e admin olarak bağlanılamadı."
    echo "   Manuel olarak database oluşturmanız gerekebilir:"
    echo "   psql -U postgres"
    echo "   CREATE DATABASE $DB_NAME;"
    echo "   CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
    echo "   GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    return 1  # Database oluşturma başarısız - durdur
  fi
  
  # PSQL komut fonksiyonu (admin parolası ile veya parolasız)
  run_psql() {
    local database="$1"
    local command="$2"
    if [ -z "$DB_ADMIN_PASS" ]; then
      psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -d "$database" -c "$command"
    else
      PGPASSWORD="$DB_ADMIN_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN_USER" -d "$database" -c "$command"
    fi
  }
  
  # Database var mı kontrol et
  DB_EXISTS=$(run_psql "postgres" "SELECT 1 FROM pg_database WHERE datname='$DB_NAME';" 2>/dev/null | grep -c "1" || echo "0")
  
  if [ "$DB_EXISTS" = "0" ]; then
    echo "🔨 Database '$DB_NAME' bulunamadı, oluşturuluyor..."
    if run_psql "postgres" "CREATE DATABASE $DB_NAME;" > /dev/null 2>&1; then
      echo "✅ Database '$DB_NAME' oluşturuldu."
    else
      echo "❌ Database oluşturulamadı!"
      return 1
    fi
  else
    echo "✅ Database '$DB_NAME' zaten mevcut."
  fi
  
  # Kullanıcı var mı kontrol et
  USER_EXISTS=$(run_psql "postgres" "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER';" 2>/dev/null | grep -c "1" || echo "0")
  
  if [ "$USER_EXISTS" = "0" ]; then
    echo "👤 Kullanıcı '$DB_USER' bulunamadı, oluşturuluyor..."
    if run_psql "postgres" "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';" > /dev/null 2>&1; then
      echo "✅ Kullanıcı '$DB_USER' oluşturuldu."
    else
      echo "❌ Kullanıcı oluşturulamadı!"
      return 1
    fi
  else
    echo "✅ Kullanıcı '$DB_USER' zaten mevcut."
    # Şifre güncellemesi (isteğe bağlı)
    run_psql "postgres" "ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';" > /dev/null 2>&1 || echo "⚠️ Şifre güncellenemedi"
  fi
  
  # İzinleri ver
  echo "🔐 Database izinleri veriliyor..."
  run_psql "postgres" "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" > /dev/null 2>&1 || echo "⚠️ Database izinleri verilemedi"
  
  # PostgreSQL 15+ için public schema izinleri
  run_psql "$DB_NAME" "GRANT ALL ON SCHEMA public TO $DB_USER;" > /dev/null 2>&1 || echo "⚠️ Schema izinleri verilemedi (normal olabilir)"
  run_psql "$DB_NAME" "GRANT CREATE ON SCHEMA public TO $DB_USER;" > /dev/null 2>&1 || echo "⚠️ CREATE izni verilemedi (normal olabilir)"
  
  # Bağlantı testi
  if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database bağlantısı başarılı!"
  else
    echo "❌ Database bağlantısı başarısız!"
    return 1
  fi
  
  return 0
}

# Gerekli paketler (git, derleyiciler, libpq, postgresql-client)
echo "📦 Sistem paketleri güncelleniyor..."
apt-get update
apt-get install -y git build-essential libpq-dev curl postgresql-client
rm -rf /var/lib/apt/lists/*

# Repo yoksa klonla, varsa güncelle (race condition önlemi için basit lock)
mkdir -p "$WORKDIR"
if [ ! -d "$REPO_DIR/.git" ]; then
  echo "📁 Repo bulunamadı, klonlanıyor..."
  while ! ( set -o noclobber; echo "$$" > "$LOCK_FILE" ) 2> /dev/null; do
    echo "⏳ Başka bir süreç klonluyor, bekleniyor..."
    sleep 2
  done
  trap 'rm -f "$LOCK_FILE"; exit $?' INT TERM EXIT
  if [ ! -d "$REPO_DIR/.git" ]; then
    git clone "$REPO_URL" "$REPO_DIR"
  fi
  rm -f "$LOCK_FILE"
  trap - INT TERM EXIT
else
  echo "🔄 Repo mevcut, güncelleniyor..."
  cd "$REPO_DIR"
  git reset --hard
  git pull --ff-only origin main || true
fi

# Backend dizinine geç
cd "$BACKEND_DIR"

# .env yoksa container env'den üret
if [ ! -f ".env" ]; then
  echo "⚙️ .env oluşturuluyor..."
  cat > .env <<EOT
DATABASE_URL=${DATABASE_URL}
GOOGLE_API_KEY=${GOOGLE_API_KEY}
SECRET_KEY=${SECRET_KEY}
EOT
fi

echo "🐍 Python ve pip sürümleri kontrol ediliyor..."
python -V || true
pip -V || true
python -m pip install --upgrade pip

# 🔥 ÖNEMLİ: Eski psycopg2 paketlerini kaldır ve cache temizle
echo "🧹 Eski psycopg paketlerini temizleniyor..."
pip uninstall -y psycopg2-binary psycopg2 || true
pip cache purge

# Python bağımlılıkları (cache'siz yükle)
echo "📚 Python paketleri kuruluyor (cache temizlenerek)..."
pip install --no-cache-dir -r requirements.txt

# Yüklenen psycopg paketlerini kontrol et
echo "🔍 Yüklenen psycopg paketlerini kontrol ediliyor..."
pip list | grep psycopg || echo "⚠️ psycopg paketi bulunamadı"

# spaCy modeli indirme
echo "🧠 spaCy dil modeli kontrol ediliyor..."
if ! python -c "import spacy; spacy.load('en_core_web_sm')" > /dev/null 2>&1; then
  echo "📥 spaCy en_core_web_sm modeli indiriliyor..."
  python -m spacy download en_core_web_sm || echo "⚠️ spaCy modeli indirilemedi, devam ediliyor..."
else
  echo "✅ spaCy en_core_web_sm modeli zaten mevcut."
fi

# Database otomatik oluşturma (ZORUNLU)
echo "🗃️ Database durumu kontrol ediliyor..."
if ! create_database_if_not_exists; then
  echo "❌ Database oluşturma başarısız! Container durduruluyor."
  exit 1
fi

# Alembic migration (alembic.ini varsa)
if [ -f "alembic.ini" ]; then
  echo "🔄 Alembic migration çalışıyor..."
  if ! alembic upgrade head; then
    echo "❌ Alembic migration başarısız! Container durduruluyor."
    exit 1
  fi
else
  echo "⚠️ alembic.ini bulunamadı, migration atlanıyor"
fi

echo "🚀 Backend (Uvicorn) başlatılıyor..."
echo "🌐 Server erişim adresi: http://0.0.0.0:8000"
echo "📚 API Dokumentasyonu: http://0.0.0.0:8000/docs"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
