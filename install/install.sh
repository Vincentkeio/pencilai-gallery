#!/usr/bin/env bash
set -euo pipefail

# One-click installer (Docker Compose)
# Usage:
#   cd install
#   bash install.sh
# Optional env:
#   WP_PORT=8080 WP_SITE_URL=http://localhost:8080 WP_TITLE="PencilAI" WP_ADMIN_USER=admin WP_ADMIN_PASS=... WP_ADMIN_EMAIL=... bash install.sh

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

command -v docker >/dev/null 2>&1 || { echo "docker not found"; exit 1; }

# docker compose detection
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "docker compose not found"; exit 1
fi

# Defaults
WP_PORT="${WP_PORT:-8080}"
WP_SITE_URL="${WP_SITE_URL:-http://localhost:${WP_PORT}}"
WP_TITLE="${WP_TITLE:-PencilAI Gallery}"
WP_ADMIN_USER="${WP_ADMIN_USER:-admin}"
WP_ADMIN_PASS="${WP_ADMIN_PASS:-$(openssl rand -base64 12 | tr -d '=+/')}"
WP_ADMIN_EMAIL="${WP_ADMIN_EMAIL:-admin@example.com}"

# DB defaults
export WP_DB_NAME="${WP_DB_NAME:-wordpress}"
export WP_DB_USER="${WP_DB_USER:-wp}"
export WP_DB_PASS="${WP_DB_PASS:-wp_pass_$(openssl rand -hex 4)}"
export WP_DB_ROOT_PASS="${WP_DB_ROOT_PASS:-root_pass_$(openssl rand -hex 4)}"
export WP_PORT

mkdir -p "$HERE/tg_gallery"

cd "$HERE"
$DC -f docker-compose.yml up -d

echo "Waiting for WordPress container..."
# Simple wait
for i in $(seq 1 60); do
  if docker ps --format '{{.Names}}' | grep -q "wordpress"; then
    break
  fi
  sleep 1
done

# Try to run wp-cli install (if not installed already)
set +e
$DC -f docker-compose.yml run --rm wpcli wp core is-installed >/dev/null 2>&1
INSTALLED=$?
set -e

if [[ $INSTALLED -ne 0 ]]; then
  echo "Running wp core install..."
  $DC -f docker-compose.yml run --rm wpcli wp core install \
    --url="$WP_SITE_URL" \
    --title="$WP_TITLE" \
    --admin_user="$WP_ADMIN_USER" \
    --admin_password="$WP_ADMIN_PASS" \
    --admin_email="$WP_ADMIN_EMAIL" \
    --skip-email

  echo "Activating theme 'hamilton'..."
  $DC -f docker-compose.yml run --rm wpcli wp theme activate hamilton

  echo "Creating gallery page..."
  PAGE_ID=$($DC -f docker-compose.yml run --rm wpcli wp post create --post_type=page --post_title="Gallery" --post_status=publish --porcelain)
  # Assign template
  $DC -f docker-compose.yml run --rm wpcli wp post meta update "$PAGE_ID" _wp_page_template page-gallery.php
  # Set front page
  $DC -f docker-compose.yml run --rm wpcli wp option update show_on_front page
  $DC -f docker-compose.yml run --rm wpcli wp option update page_on_front "$PAGE_ID"
fi

echo ""
echo "✅ Done. Open: $WP_SITE_URL"
echo "Admin: $WP_SITE_URL/wp-admin"
echo "User:  $WP_ADMIN_USER"
echo "Pass:  $WP_ADMIN_PASS"
