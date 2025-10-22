#!/usr/bin/env bash
# SSHMFA Installation Script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
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

echo -e "${CYAN}OMEN SSHMFA Installation${NC}"
echo "=========================="
echo ""

log_info "Installing SSHMFA (SSH MFA Hardening with OTP)..."

# Install libpam-google-authenticator
log_info "Installing libpam-google-authenticator..."
apt-get update -qq
apt-get install -y libpam-google-authenticator

# Create omen-totp-admins group if it doesn't exist
if ! getent group omen-totp-admins >/dev/null; then
    log_info "Creating omen-totp-admins group..."
    groupadd omen-totp-admins
    log_info "Created omen-totp-admins group"
    log_info "Add users to this group to allow them to grant 2FA bypasses:"
    log_info "  usermod -aG omen-totp-admins <username>"
fi

# Create bypass directory
log_info "Creating bypass directory..."
mkdir -p /var/run/omen/bypass
chmod 755 /var/run/omen/bypass

# Make scripts executable
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "$SCRIPT_DIR"/scripts/*.sh

log_info "SSHMFA installation complete!"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC}"
echo "2FA is NOT yet enabled. To enable 2FA:"
echo "  1. Enroll at least one user: $SCRIPT_DIR/scripts/sshmfa.sh enroll <username>"
echo "  2. Enable 2FA: $SCRIPT_DIR/scripts/sshmfa.sh enable"
echo ""
echo "Management Commands:"
echo "  $SCRIPT_DIR/scripts/sshmfa.sh enroll <username>"
echo "  $SCRIPT_DIR/scripts/sshmfa.sh bypass-grant <username>"
echo "  $SCRIPT_DIR/scripts/sshmfa.sh bypass-revoke <username>"
echo "  $SCRIPT_DIR/scripts/sshmfa.sh bypass-list"
echo "  $SCRIPT_DIR/scripts/sshmfa.sh status"
echo ""
echo "Or use the Python wrapper:"
echo "  python3 $SCRIPT_DIR/sshmfa.py enroll <username>"
echo "  python3 $SCRIPT_DIR/sshmfa.py bypass-grant <username>"
echo ""
log_warn "WARNING: Make sure to enroll at least one user before enabling 2FA!"
log_warn "Otherwise you may lock yourself out of SSH access!"

