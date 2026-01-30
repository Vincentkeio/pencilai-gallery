#!/usr/bin/env bash
set -euo pipefail

# =========================
# Helpers
# =========================
log() { echo -e "[$(date +'%F %T')] $*"; }
die() { echo -e "ERROR: $*" >&2; exit 1; }

need_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      exec sudo -E bash "$0" "$@"
    else
      die "请用 root 执行，或先安装 sudo。"
    fi
  fi
}

has_cmd() { command -v "$1" >/dev/null 2>&1; }

detect_os() {
  if [[ -f /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    OS_ID="${ID:-unknown}"
    OS_LIKE="${ID_LIKE:-}"
    OS_VER="${VERSION_ID:-}"
  else
    OS_ID="unknown"; OS_LIKE=""; OS_VER=""
  fi
}

install_docker_debian() {
  log "Installing Docker (Debian/Ubuntu)…"
  apt-get update -y
  apt-get install -y ca-certificates curl gnupg lsb-release

  install -m 0755 -d /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
    curl -fsSL https://download.docker.com/linux/${OS_ID}/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
  fi

  ARCH="$(dpkg --print-architecture)"
  CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"
  [[ -n "$CODENAME" ]] || CODENAME="$(lsb_release -cs 2>/dev/null || true)"
  [[ -n "$CODENAME" ]] || die "无法识别发行版代号 VERSION_CODENAME。"

  cat > /etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${OS_ID} ${CODENAME} stable
EOF

  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

install_docker_rhel() {
  log "Installing Docker (RHEL/CentOS/Rocky/Alma/Fedora)…"
  if has_cmd dnf; then PM=dnf; else PM=yum; fi
  $PM -y install yum-utils curl ca-certificates
  yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo || true
  $PM -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

install_docker_fallback() {
  log "Unknown distro, fallback to get.docker.com…"
  curl -fsSL https://get.docker.com | sh
  # compose plugin may not exist on old distros; try best effort:
  if ! docker compose version >/dev/null 2>&1; then
    log "docker compose plugin missing; trying to install compose plugin via package manager…"
    if has_cmd apt-get; then
      apt-get update -y
      apt-get install -y docker-compose-plugin || true
    elif has_cmd dnf; then
      dnf -y install docker-compose-plugin || true
    elif has_cmd yum; then
      yum -y install docker-compose-plugin || true
    fi
  fi
}

ensure_docker() {
  if has_cmd docker && docker version >/dev/null 2>&1; then
    log "Docker already installed."
  else
    detect_os
    case "${OS_ID}" in
      ubuntu|debian)
        install_docker_debian
        ;;
      centos|rhel|rocky|almalinux|fedora)
        install_docker_rhel
        ;;
      *)
        # Try OS_LIKE hints
        if [[ "${OS_LIKE}" == *"debian"* ]]; then
          OS_ID="debian"
          install_docker_debian
        elif [[ "${OS_LIKE}" == *"rhel"* ]] || [[ "${OS_LIKE}" == *"fedora"* ]]; then
          install_docker_rhel
        else
          install_docker_fallback
        fi
        ;;
    esac
  fi

  # Start docker
  if has_cmd systemctl; then
    systemctl enable --now docker || true
  fi

  # Verify
  docker version >/dev/null 2>&1 || die "Docker 安装/启动失败，请检查 systemctl status docker"
  if ! docker compose version >/dev/null 2>&1; then
    # Some environments only have docker-compose (legacy)
    if has_cmd docker-compose; then
      log "Found legacy docker-compose."
    else
      die "未检测到 docker compose / docker-compose，请手动安装 compose。"
    fi
  fi
  log "Docker OK."
}

compose_up() {
  # Workdir: install/
  local here
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  cd "$here"

  if [[ ! -f docker-compose.yml && ! -f compose.yml ]]; then
    die "install/ 目录下找不到 docker-compose.yml 或 compose.yml"
  fi

  log "Starting services…"
  if docker compose version >/dev/null 2>&1; then
    docker compose up -d
  else
    docker-compose up -d
  fi

  log "Done."
  log "Open: http://localhost:8080"
  log "If on VPS: http://<YOUR_SERVER_IP>:8080"
}

main() {
  need_root "$@"
  ensure_docker
  compose_up
}

main "$@"
