#!/usr/bin/env bash
# OMEN Simple Installation Menu
# This script helps install standalone security components

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
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

log_header() {
    echo -e "${CYAN}$*${NC}"
}

# Banner
clear
echo -e "${BLUE}"
cat << "EOF"
   ___  __  __ _____ _   _ 
  / _ \|  \/  | ____| \ | |
 | | | | |\/| |  _| |  \| |
 | |_| | |  | | |___| |\  |
  \___/|_|  |_|_____|_| \_|
                            
 Observation, Monitoring,
 Enforcement & Notification
 
 Standalone Security Tools
EOF
echo -e "${NC}"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    log_error "Please run: sudo $0"
    exit 1
fi

# Check Ubuntu version
if [[ -f /etc/os-release ]]; then
    source /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_warn "This tool is designed for Ubuntu"
        log_warn "Detected OS: $ID $VERSION_ID"
        read -p "Continue anyway? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
            exit 1
        fi
    else
        log_info "Detected: $PRETTY_NAME"
    fi
fi

# Get current directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/omen"

log_info "Components will be installed to: $INSTALL_DIR"
echo ""

# Installation menu
log_header "What would you like to install?"
echo ""
echo "  1) All components (LSHC + SAMS + SSHMFA)"
echo "  2) LSHC  - Linux Security Hardening Configurator"
echo "  3) SAMS  - Suspicious Activity Monitoring System"
echo "  4) SSHMFA - SSH MFA Hardening with OTP"
echo "  5) Exit"
echo ""
read -p "Select option [1-5]: " -r INSTALL_CHOICE

case $INSTALL_CHOICE in
    1|2|3|4)
        ;;
    5)
        log_info "Installation cancelled"
        exit 0
        ;;
    *)
        log_error "Invalid option"
        exit 1
        ;;
esac

echo ""

# Determine what to install
INSTALL_LSHC=false
INSTALL_SAMS=false
INSTALL_SSHMFA=false

case $INSTALL_CHOICE in
    1)
        INSTALL_LSHC=true
        INSTALL_SAMS=true
        INSTALL_SSHMFA=true
        log_info "Installing all components"
        ;;
    2)
        INSTALL_LSHC=true
        log_info "Installing LSHC"
        ;;
    3)
        INSTALL_SAMS=true
        log_info "Installing SAMS"
        ;;
    4)
        INSTALL_SSHMFA=true
        log_info "Installing SSHMFA"
        ;;
esac

echo ""

# Create base directory
log_info "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Install LSHC
if [[ "$INSTALL_LSHC" == "true" ]]; then
    log_header ""
    log_header "╔═══════════════════════════════════════╗"
    log_header "║  Installing LSHC Component            ║"
    log_header "╚═══════════════════════════════════════╝"
    echo ""
    
    # Copy LSHC files
    log_info "Copying LSHC files..."
    rsync -a --exclude='*.pyc' --exclude='__pycache__' \
        "$CURRENT_DIR/lshc/" "$INSTALL_DIR/lshc/"
    
    # Run LSHC installer
    if [[ -f "$INSTALL_DIR/lshc/scripts/install.sh" ]]; then
        chmod +x "$INSTALL_DIR/lshc/scripts/install.sh"
        "$INSTALL_DIR/lshc/scripts/install.sh"
    else
        log_error "LSHC installer not found"
    fi
fi

# Install SAMS
if [[ "$INSTALL_SAMS" == "true" ]]; then
    log_header ""
    log_header "╔═══════════════════════════════════════╗"
    log_header "║  Installing SAMS Component            ║"
    log_header "╚═══════════════════════════════════════╝"
    echo ""
    
    # Copy SAMS files
    log_info "Copying SAMS files..."
    rsync -a --exclude='*.pyc' --exclude='__pycache__' \
        "$CURRENT_DIR/sams/" "$INSTALL_DIR/sams/"
    
    # Run SAMS installer
    if [[ -f "$INSTALL_DIR/sams/install.sh" ]]; then
        chmod +x "$INSTALL_DIR/sams/install.sh"
        "$INSTALL_DIR/sams/install.sh"
    else
        log_error "SAMS installer not found"
    fi
fi

# Install SSHMFA
if [[ "$INSTALL_SSHMFA" == "true" ]]; then
    log_header ""
    log_header "╔═══════════════════════════════════════╗"
    log_header "║  Installing SSHMFA Component          ║"
    log_header "╚═══════════════════════════════════════╝"
    echo ""
    
    # Copy SSHMFA files
    log_info "Copying SSHMFA files..."
    rsync -a --exclude='*.pyc' --exclude='__pycache__' \
        "$CURRENT_DIR/sshmfa/" "$INSTALL_DIR/sshmfa/"
    
    # Run SSHMFA installer
    if [[ -f "$INSTALL_DIR/sshmfa/install.sh" ]]; then
        chmod +x "$INSTALL_DIR/sshmfa/install.sh"
        "$INSTALL_DIR/sshmfa/install.sh"
    else
        log_error "SSHMFA installer not found"
    fi
fi

# Installation summary
echo ""
log_header ""
log_header "╔═══════════════════════════════════════════════════════╗"
log_header "║         Installation Complete!                        ║"
log_header "╚═══════════════════════════════════════════════════════╝"
echo ""

log_info "Components installed to: $INSTALL_DIR"
echo ""

# Show component-specific info
if [[ "$INSTALL_LSHC" == "true" ]]; then
    log_header "LSHC - Linux Security Hardening"
    log_info "  Location:     $INSTALL_DIR/lshc"
    log_info "  Apply:        cd $INSTALL_DIR/lshc && ansible-playbook playbook.yml"
    log_info "  Status:       $INSTALL_DIR/lshc/scripts/check-status.sh"
    log_info "  Documentation: $INSTALL_DIR/lshc/README.md"
    echo ""
fi

if [[ "$INSTALL_SAMS" == "true" ]]; then
    log_header "SAMS - Suspicious Activity Monitoring"
    log_info "  Location:     $INSTALL_DIR/sams"
    log_info "  Configure:    $INSTALL_DIR/sams/config.json"
    log_info "  Start:        systemctl start omen-sams"
    log_info "  Enable:       systemctl enable omen-sams"
    log_info "  Logs:         journalctl -u omen-sams -f"
    log_info "  Documentation: $INSTALL_DIR/sams/README.md"
    log_warn "  ⚠ Configure $INSTALL_DIR/sams/config.json before starting!"
    echo ""
fi

if [[ "$INSTALL_SSHMFA" == "true" ]]; then
    log_header "SSHMFA - SSH MFA with OTP"
    log_info "  Location:     $INSTALL_DIR/sshmfa"
    log_info "  Enroll user:  $INSTALL_DIR/sshmfa/scripts/sshmfa.sh enroll <username>"
    log_info "  Enable 2FA:   $INSTALL_DIR/sshmfa/scripts/sshmfa.sh enable"
    log_info "  Status:       $INSTALL_DIR/sshmfa/scripts/sshmfa.sh status"
    log_info "  Documentation: $INSTALL_DIR/sshmfa/README.md"
    log_warn "  ⚠ Enroll at least one user before enabling 2FA!"
    echo ""
fi

log_info "Thank you for using OMEN!"
echo ""
