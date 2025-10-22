#!/usr/bin/env bash
# LSHC Installation Script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

log_info "Installing LSHC (Linux Security Hardening Configurator)..."

# Install Ansible if not present
if ! command -v ansible &> /dev/null; then
    log_info "Installing Ansible..."
    apt-get update -qq
    apt-get install -y ansible
fi

# Install Ansible collections and roles
log_info "Installing Ansible collections..."
ansible-galaxy collection install ansible.posix community.general --force 2>/dev/null || true

# Optional: Install community hardening roles
log_info "Installing community hardening roles (optional)..."
cd "$(dirname "$0")/.." || exit 1
ansible-galaxy install -r requirements.yml --force 2>/dev/null || log_warn "Community roles installation skipped"

log_info "LSHC installation complete!"
log_info ""
log_info "To apply hardening, run:"
log_info "  cd $(dirname "$0")/.."
log_info "  ansible-playbook playbook.yml"
log_info ""
log_info "For selective hardening, use tags:"
log_info "  ansible-playbook playbook.yml --tags ssh"
log_info "  ansible-playbook playbook.yml --tags firewall"

