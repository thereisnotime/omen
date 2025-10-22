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
echo ""

# Check prerequisites
log_info "Checking prerequisites..."
MISSING_PKGS=()

# Check for libpam-google-authenticator
if ! dpkg -l | grep -q libpam-google-authenticator; then
    log_warn "  libpam-google-authenticator not found - will install"
    MISSING_PKGS+=("libpam-google-authenticator")
else
    log_info "  ✓ libpam-google-authenticator: installed"
fi

# Check for qrencode (for QR code generation)
if ! command -v qrencode &>/dev/null; then
    log_warn "  qrencode not found - will install (needed for QR codes)"
    MISSING_PKGS+=("qrencode")
else
    log_info "  ✓ qrencode: installed"
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

