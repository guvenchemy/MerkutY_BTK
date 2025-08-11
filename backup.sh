#!/bin/bash

# CEFR Language Learning Platform - Backup Script
# This script creates backups of the database and application data

set -e

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"
DATA_BACKUP_FILE="$BACKUP_DIR/data_backup_$DATE.tar.gz"

echo "🔄 Starting backup process..."
echo "=============================="

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "💾 Creating database backup..."
# NAS PostgreSQL 17'den backup al
pg_dump -h localhost -U merkut_user -d nexus_db > $DB_BACKUP_FILE

if [ $? -eq 0 ]; then
    echo "✅ Database backup created: $DB_BACKUP_FILE"
else
    echo "❌ Database backup failed!"
    exit 1
fi

# Data backup (uploads, logs)
echo "📁 Creating data backup..."
tar -czf $DATA_BACKUP_FILE uploads/ logs/ data/ 2>/dev/null || echo "⚠️  Some directories might not exist"

if [ -f $DATA_BACKUP_FILE ]; then
    echo "✅ Data backup created: $DATA_BACKUP_FILE"
else
    echo "❌ Data backup failed!"
    exit 1
fi

# Cleanup old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete 2>/dev/null || true
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "✅ Backup process completed!"
echo "Database backup: $DB_BACKUP_FILE"
echo "Data backup: $DATA_BACKUP_FILE"
echo ""
echo "💡 To restore:"
echo "Database: psql -h localhost -U merkut_user -d nexus_db < $DB_BACKUP_FILE"
echo "Data: tar -xzf $DATA_BACKUP_FILE"
