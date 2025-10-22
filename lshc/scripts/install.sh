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
echo ""

# Check prerequisites
log_info "Checking prerequisites..."
MISSING_PKGS=()

# Check for Ansible
if ! command -v ansible &> /dev/null; then
    log_warn "  Ansible not found - will install"
    MISSING_PKGS+=("ansible")
else
    log_info "  ✓ Ansible: $(ansible --version | head -1 | cut -d' ' -f2)"
fi

# Check for ansible-galaxy
if ! command -v ansible-galaxy &> /dev/null; then
    log_warn "  ansible-galaxy not found"
    if [[ ! " ${MISSING_PKGS[@]} " =~ " ansible " ]]; then
        MISSING_PKGS+=("ansible")
    fi
else
    log_info "  ✓ ansible-galaxy: installed"
fi

# Install missing packages
if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    echo ""
    log_info "Installing missing packages: ${MISSING_PKGS[*]}"
    apt-get update -qq || {
        log_error "Failed to update package lists"
        exit 1
    }
    apt-get install -y "${MISSING_PKGS[@]}" || {
        log_error "Failed to install required packages"
        exit 1
    }
    log_info "Packages installed successfully"
else
    log_info "  ✓ All prerequisites met"
fi

echo ""

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

