#!/usr/bin/env bash
# SAMS Installation Script

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

log_info "Installing SAMS (Suspicious Activity Monitoring System)..."
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check prerequisites
log_info "Checking prerequisites..."
MISSING_PKGS=()

# Check for pip3
if ! command -v pip3 &>/dev/null; then
    log_warn "  pip3 not found - will install"
    MISSING_PKGS+=("python3-pip")
else
    log_info "  ✓ pip3: installed"
fi

# Check for auditd
if ! command -v auditd &>/dev/null && ! systemctl is-active --quiet auditd; then
    log_warn "  auditd not found - will install"
    MISSING_PKGS+=("auditd" "audispd-plugins")
else
    log_info "  ✓ auditd: installed"
fi

# Install system packages if needed
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
    log_info "  ✓ All system packages present"
fi

echo ""

# Install Python dependencies
log_info "Installing Python dependencies..."
if command -v pip3 &>/dev/null; then
    pip3 install requests watchdog psutil -q || {
        log_error "Failed to install Python dependencies"
        exit 1
    }
    log_info "Python dependencies installed successfully"
else
    log_error "pip3 not available"
    exit 1
fi

# Create log directory
log_info "Creating log directory..."
mkdir -p /var/log/omen
chmod 755 /var/log/omen

# Create lib directory for file hashes
mkdir -p /var/lib/omen
chmod 755 /var/lib/omen

# Copy configuration if it doesn't exist
if [[ ! -f "$SCRIPT_DIR/config.json" ]]; then
    log_info "Creating default configuration..."
    cp "$SCRIPT_DIR/config.json.example" "$SCRIPT_DIR/config.json"
    log_warn "Please edit $SCRIPT_DIR/config.json to configure alerting"
fi

# Install systemd service
log_info "Installing systemd service..."
cp "$SCRIPT_DIR/systemd/sams.service" /etc/systemd/system/omen-sams.service
systemctl daemon-reload

log_info "SAMS installation complete!"
log_info ""
log_info "Next steps:"
log_info "1. Edit configuration: $SCRIPT_DIR/config.json"
log_info "2. Start service: systemctl start omen-sams"
log_info "3. Enable on boot: systemctl enable omen-sams"
log_info "4. Check status: systemctl status omen-sams"
log_info "5. View logs: journalctl -u omen-sams -f"

