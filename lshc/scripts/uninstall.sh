#!/usr/bin/env bash
# LSHC Uninstallation Script

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

log_warn "LSHC Uninstallation"
log_warn "==================="
log_warn ""
log_warn "This will remove OMEN hardening configurations."
log_warn "Backups are available in /var/backups/omen/lshc/"
log_warn ""

read -p "Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    log_info "Uninstallation cancelled"
    exit 0
fi

log_info "Removing OMEN sysctl configuration..."
rm -f /etc/sysctl.d/99-omen-hardening.conf

log_info "Removing OMEN audit rules..."
rm -f /etc/audit/rules.d/omen-hardening.rules

log_info "Reloading audit rules..."
if command -v augenrules &> /dev/null; then
    augenrules --load || true
fi

log_warn "NOTE: SSH and firewall configurations were modified."
log_warn "You may need to manually restore from backups:"
log_warn "  /var/backups/omen/lshc/"
log_warn ""
log_warn "To restore sshd_config:"
log_warn "  cp /var/backups/omen/lshc/sshd_config.* /etc/ssh/sshd_config"
log_warn "  systemctl restart ssh"

log_info "LSHC uninstallation complete"

