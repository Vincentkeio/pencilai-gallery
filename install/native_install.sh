\
#!/usr/bin/env bash
set -euo pipefail

# Native (non-Docker) installer for Debian/Ubuntu
# - Installs Nginx + PHP-FPM + MariaDB
# - Downloads WordPress core
# - Copies theme files from this repo
# - Sets up Python venv for scripts
#
# Usage:
#   sudo bash native_install.sh
# Optional env:
#   DOMAIN=example.com SITE_URL=http://example.com WP_TITLE="PencilAI Gallery" WP_ADMIN_USER=admin WP_ADMIN_PASS=... WP_ADMIN_EMAIL=...

log(){ echo -e "[$(date +'%F %T')] $*"; }
die(){ echo -e "ERROR: $*" >&2; exit 1; }

need_root(){
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then exec sudo -E bash "$0" "$@"; else die "Run as root."; fi
  fi
}

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

DOMAIN="${DOMAIN:-pencilai.local}"
SITE_URL="${SITE_URL:-http://${DOMAIN}}"
WP_TITLE="${WP_TITLE:-PencilAI Gallery}"
WP_ADMIN_USER="${WP_ADMIN_USER:-admin}"
WP_ADMIN_PASS="${WP_ADMIN_PASS:-$(openssl rand -base64 12 | tr -d '=+/')}"
WP_ADMIN_EMAIL="${WP_ADMIN_EMAIL:-admin@example.com}"

DB_NAME="${DB_NAME:-wordpress}"
DB_USER="${DB_USER:-wp}"
DB_PASS="${DB_PASS:-wp_pass_$(openssl rand -hex 4)}"
DB_ROOT_PASS="${DB_ROOT_PASS:-root_pass_$(openssl rand -hex 4)}"

WP_ROOT="/var/www/${DOMAIN}"
WP_PATH="${WP_ROOT}/wordpress"

detect_php_sock(){
  local sock
  sock="$(ls -1 /run/php/php*-fpm.sock 2>/dev/null | sort -V | tail -n1 || true)"
  [[ -n "$sock" ]] || die "Cannot find PHP-FPM socket in /run/php/. Install php-fpm first."
  echo "$sock"
}

install_pkgs(){
  log "Installing packages…"
  apt-get update -y
  apt-get install -y nginx curl unzip rsync git openssl \
    mariadb-server \
    php-fpm php-cli php-mysql php-sqlite3 php-xml php-mbstring php-curl php-zip php-gd \
    python3 python3-venv
}

setup_db(){
  log "Configuring MariaDB…"
  systemctl enable --now mariadb
  # set root password (best-effort). On some installs auth_socket is enabled; we still can create db/user.
  mysql -uroot -e "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
  mysql -uroot -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';"
  mysql -uroot -e "GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost'; FLUSH PRIVILEGES;"
}

install_wordpress(){
  log "Installing WordPress core…"
  mkdir -p "$WP_PATH"
  if [[ ! -f "$WP_PATH/wp-load.php" ]]; then
    curl -fsSL https://wordpress.org/latest.zip -o /tmp/wp.zip
    unzip -q /tmp/wp.zip -d /tmp
    rsync -a /tmp/wordpress/ "$WP_PATH/"
  fi
  chown -R www-data:www-data "$WP_ROOT"
}

write_wp_config(){
  log "Writing wp-config.php…"
  if [[ -f "$WP_PATH/wp-config.php" ]]; then
    log "wp-config.php exists; skipping."
    return
  fi
  cp "$WP_PATH/wp-config-sample.php" "$WP_PATH/wp-config.php"
  sed -i "s/database_name_here/${DB_NAME}/" "$WP_PATH/wp-config.php"
  sed -i "s/username_here/${DB_USER}/" "$WP_PATH/wp-config.php"
  sed -i "s/password_here/${DB_PASS}/" "$WP_PATH/wp-config.php"
  # Replace auth salts
  local salts
  salts="$(curl -fsSL https://api.wordpress.org/secret-key/1.1/salt/)"
  perl -0777 -i -pe "s/define\('AUTH_KEY'.*?\);\s*define\('NONCE_SALT'.*?\);\n/${salts}\n/s" "$WP_PATH/wp-config.php"
}

copy_theme(){
  log "Copying theme…"
  mkdir -p "$WP_PATH/wp-content/themes/hamilton"
  rsync -a "$ROOT/wordpress/wp-content/themes/hamilton/" "$WP_PATH/wp-content/themes/hamilton/"
  chown -R www-data:www-data "$WP_PATH/wp-content/themes/hamilton"
}

link_gallery_dir(){
  log "Linking tg_gallery…"
  mkdir -p "$ROOT/tg_gallery"
  rm -rf "$WP_PATH/tg_gallery" || true
  ln -s "$ROOT/tg_gallery" "$WP_PATH/tg_gallery"
  chown -R www-data:www-data "$ROOT/tg_gallery"
}

setup_nginx(){
  log "Configuring Nginx…"
  local sock; sock="$(detect_php_sock)"
  cat > "/etc/nginx/sites-available/${DOMAIN}.conf" <<EOF
server {
  listen 80;
  server_name ${DOMAIN};
  root ${WP_PATH};
  index index.php index.html;

  location / {
    try_files \$uri \$uri/ /index.php?\$args;
  }

  location ~ \.php$ {
    include snippets/fastcgi-php.conf;
    fastcgi_pass unix:${sock};
  }

  location ~* \.(jpg|jpeg|png|gif|webp|css|js|ico)$ {
    expires 7d;
    access_log off;
  }
}
EOF
  ln -sf "/etc/nginx/sites-available/${DOMAIN}.conf" "/etc/nginx/sites-enabled/${DOMAIN}.conf"
  nginx -t
  systemctl restart nginx
  systemctl enable nginx
}

setup_wp_cli(){
  log "Setting up wp-cli…"
  if ! command -v wp >/dev/null 2>&1; then
    curl -fsSL https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar -o /usr/local/bin/wp
    chmod +x /usr/local/bin/wp
  fi
  # Install if not installed
  if ! wp core is-installed --path="$WP_PATH" --allow-root >/dev/null 2>&1; then
    wp core install \
      --path="$WP_PATH" --allow-root \
      --url="$SITE_URL" --title="$WP_TITLE" \
      --admin_user="$WP_ADMIN_USER" --admin_password="$WP_ADMIN_PASS" --admin_email="$WP_ADMIN_EMAIL"
  fi
  # Activate theme
  wp theme activate hamilton --path="$WP_PATH" --allow-root || true
  # Create gallery page and set as front page (best-effort)
  local pid
  pid="$(wp post list --post_type=page --pagename=gallery --field=ID --path="$WP_PATH" --allow-root 2>/dev/null | head -n1 || true)"
  if [[ -z "$pid" ]]; then
    pid="$(wp post create --post_type=page --post_title="Gallery" --post_status=publish --porcelain --path="$WP_PATH" --allow-root)"
  fi
  # Try set template meta (theme template file name)
  wp post meta update "$pid" _wp_page_template page-gallery.php --path="$WP_PATH" --allow-root || true
  wp option update show_on_front page --path="$WP_PATH" --allow-root || true
  wp option update page_on_front "$pid" --path="$WP_PATH" --allow-root || true
}

setup_python(){
  log "Setting up Python venv for scripts…"
  cd "$ROOT"
  python3 -m venv .venv
  ./.venv/bin/pip install -U pip
  ./.venv/bin/pip install -r scripts/requirements.txt
  if [[ ! -f scripts/config.json ]]; then
    cp scripts/config.example.json scripts/config.json
  fi
}

main(){
  need_root "$@"
  install_pkgs
  setup_db
  install_wordpress
  write_wp_config
  copy_theme
  link_gallery_dir
  setup_nginx
  setup_wp_cli
  setup_python

  log "✅ Done."
  echo
  echo "Site URL:   ${SITE_URL}"
  echo "WP Admin:   ${SITE_URL}/wp-admin"
  echo "Admin user: ${WP_ADMIN_USER}"
  echo "Admin pass: ${WP_ADMIN_PASS}"
  echo
  echo "Images dir: ${ROOT}/tg_gallery (put images here)"
  echo "Scripts venv: ${ROOT}/.venv"
}
main "$@"
