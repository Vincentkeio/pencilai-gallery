#!/usr/bin/env bash
set -euo pipefail

# PencilAI Gallery bootstrap (Docker)
# - Installs Docker (and compose plugin) if missing
# - Clones the repo to /opt/pencilai-gallery (or uses current dir)
# - Runs install/install.sh

REPO_URL="${REPO_URL:-https://github.com/Vincentkeio/pencilai-gallery.git}"
DEST="${DEST:-/opt/pencilai-gallery}"

log(){ echo -e "[$(date +'%F %T')] $*"; }
die(){ echo -e "ERROR: $*" >&2; exit 1; }

need_root(){
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    if command -v sudo >/dev/null 2>&1; then
      exec sudo -E bash "$0" "$@"
    else
      die "Please run as root (or install sudo)."
    fi
  fi
}

has(){ command -v "$1" >/dev/null 2>&1; }

install_docker_debian(){
  log "Installing Docker (Debian/Ubuntu)…"
  apt-get update -y
  apt-get install -y ca-certificates curl gnupg lsb-release git openssl
  install -m 0755 -d /etc/apt/keyrings
  if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg || \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
  fi
  ARCH="$(dpkg --print-architecture)"
  CODENAME="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"
  [[ -n "$CODENAME" ]] || CODENAME="$(lsb_release -cs 2>/dev/null || true)"
  [[ -n "$CODENAME" ]] || die "Cannot detect distro codename"
  OS_ID="$(. /etc/os-release && echo "${ID:-debian}")"
  cat > /etc/apt/sources.list.d/docker.list <<EOF
deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${OS_ID} ${CODENAME} stable
EOF
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

install_docker_rhel(){
  log "Installing Docker (RHEL/CentOS/Rocky/Alma/Fedora)…"
  if has dnf; then PM=dnf; else PM=yum; fi
  $PM -y install yum-utils curl ca-certificates git openssl
  yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo || true
  $PM -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

install_docker_fallback(){
  log "Fallback Docker install via get.docker.com…"
  curl -fsSL https://get.docker.com | sh
  if ! docker compose version >/dev/null 2>&1; then
    log "compose plugin not found; try to install docker-compose-plugin"
    if has apt-get; then apt-get update -y && apt-get install -y docker-compose-plugin || true; fi
    if has dnf; then dnf -y install docker-compose-plugin || true; fi
    if has yum; then yum -y install docker-compose-plugin || true; fi
  fi
}

ensure_docker(){
  if has docker && docker version >/dev/null 2>&1; then
    log "Docker already installed."
  else
    if [[ -f /etc/os-release ]]; then
      . /etc/os-release
      case "${ID:-}" in
        debian|ubuntu) install_docker_debian ;;
        rhel|centos|rocky|almalinux|fedora) install_docker_rhel ;;
        *) 
          if [[ "${ID_LIKE:-}" == *"debian"* ]]; then install_docker_debian
          elif [[ "${ID_LIKE:-}" == *"rhel"* ]] || [[ "${ID_LIKE:-}" == *"fedora"* ]]; then install_docker_rhel
          else install_docker_fallback
          fi
          ;;
      esac
    else
      install_docker_fallback
    fi
  fi
  if has systemctl; then systemctl enable --now docker || true; fi
  docker version >/dev/null 2>&1 || die "Docker not working"
  if ! docker compose version >/dev/null 2>&1 && ! has docker-compose; then
    die "docker compose not available"
  fi
}

ensure_repo(){
  if [[ -d "$DEST/.git" ]]; then
    log "Repo exists: $DEST (pulling)…"
    git -C "$DEST" pull --rebase || true
  else
    log "Cloning repo to $DEST…"
    rm -rf "$DEST"
    git clone "$REPO_URL" "$DEST"
  fi
}

main(){
  need_root "$@"
  ensure_docker
  ensure_repo
  log "Running installer…"
  cd "$DEST/install"
  bash install.sh
}

main "$@"
