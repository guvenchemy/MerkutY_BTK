#!/bin/bash
set -e

TZ=${TZ:-Europe/Istanbul}
export TZ

WORKDIR="/workspace"
REPO_URL="https://github.com/guvenchemy/MerkutY_BTK.git"
REPO_DIR="$WORKDIR/MerkutY_BTK"
FRONTEND_DIR="$REPO_DIR/frontend"
LOCK_FILE="$WORKDIR/.repo.lock"

# Backend container IP configuration
BACKEND_HOST=${BACKEND_HOST:-172.19.0.3}
BACKEND_PORT=${BACKEND_PORT:-8000}
API_URL="http://${BACKEND_HOST}:${BACKEND_PORT}"

echo "🌐 Frontend Container Başlatılıyor..."
echo "📡 Backend API URL: $API_URL"

# Gerekli paketler
echo "📦 Sistem paketleri güncelleniyor..."
apt-get update
apt-get install -y git curl
rm -rf /var/lib/apt/lists/*

# Node.js kurulumu (Node 18+ gerekli)
echo "🟢 Node.js kurulumu kontrol ediliyor..."
if ! command -v node &> /dev/null; then
    echo "📥 Node.js kuruluyor..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
fi

echo "🔍 Node.js ve npm sürümleri:"
node -v
npm -v

# Repo yoksa klonla, varsa güncelle (aynı lock mekanizması)
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

# Frontend dizinine geç
cd "$FRONTEND_DIR"

# Environment dosyası oluştur (Docker container için)
echo "⚙️ .env.local oluşturuluyor..."
cat > .env.local <<EOT
NEXT_PUBLIC_API_URL=${API_URL}
NEXT_PUBLIC_BACKEND_HOST=${BACKEND_HOST}
NEXT_PUBLIC_BACKEND_PORT=${BACKEND_PORT}
NODE_ENV=production
EOT

# next.config.ts dosyasını Docker ortamı için güncelle
echo "🔧 next.config.ts Docker yapılandırması..."
cat > next.config.ts <<EOT
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker container için hostname ayarları
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '${API_URL}/:path*',
      },
    ];
  },
  
  // Production ayarları
  typescript: {
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
  },
  
  // Output ayarları
  output: 'standalone',
  
  // Asset optimization
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
EOT

# Package.json scripts güncelleme (Docker için)
echo "📝 package.json scripts güncelleniyor..."
if [ -f package.json ]; then
  # Backup oluştur
  cp package.json package.json.backup
  
  # Docker için scripts güncelle
  npm pkg set scripts.docker:dev="next dev -H 0.0.0.0 -p 3000"
  npm pkg set scripts.docker:build="next build"
  npm pkg set scripts.docker:start="next start -H 0.0.0.0 -p 3000"
fi

# Node bağımlılıkları kurulumu
echo "📚 Node.js paketleri kuruluyor..."
if [ -f package-lock.json ]; then
  npm ci --production=false
else
  npm install
fi

# Build işlemi (production için)
echo "🏗️ Frontend build ediliyor..."
npm run build

# Production modunda başlat
echo "🚀 Frontend başlatılıyor..."
echo "🌐 Frontend erişim adresi: http://0.0.0.0:3000"
echo "📡 Backend API: $API_URL"
echo "🔗 API Proxy: /api/* -> $API_URL/*"

# Next.js production server başlat
exec npm run docker:start
