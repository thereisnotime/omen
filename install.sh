#!/usr/bin/env bash
# OMEN Main Installation Script

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

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

log_info "Python version: $PYTHON_VERSION"

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
    log_error "Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

log_header "OMEN Installation"
log_header "================="
echo ""

# Get current directory
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/omen"

log_info "Installation directory: $INSTALL_DIR"
log_info "Source directory: $CURRENT_DIR"
echo ""

# Ask what to install
echo "What would you like to install?"
echo "  1) Complete OMEN suite (all components)"
echo "  2) LSHC - Linux Security Hardening Configurator"
echo "  3) SAMS - Suspicious Activity Monitoring System"
echo "  4) SSHMFA - SSH MFA Hardening with OTP"
echo "  5) Exit"
echo ""
read -p "Select option [1-5]: " -r INSTALL_CHOICE

case $INSTALL_CHOICE in
    5)
        log_info "Installation cancelled"
        exit 0
        ;;
    1|2|3|4)
        ;;
    *)
        log_error "Invalid choice"
        exit 1
        ;;
esac

# Create installation directory
log_info "Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy files
log_info "Copying OMEN files..."
rsync -a --exclude='.git' --exclude='test' --exclude='*.pyc' \
    "$CURRENT_DIR/" "$INSTALL_DIR/"

# Set ownership
chown -R root:root "$INSTALL_DIR"

# Make scripts executable
log_info "Setting permissions..."
find "$INSTALL_DIR" -type f -name "*.sh" -exec chmod +x {} \;
find "$INSTALL_DIR" -type f -name "*.py" -exec chmod +x {} \;

# Install Python dependencies
log_info "Installing Python dependencies..."
if [[ -f "$INSTALL_DIR/requirements.txt" ]]; then
    pip3 install -r "$INSTALL_DIR/requirements.txt" -q || \
        log_warn "Some Python packages may have failed to install"
fi

# Create directories
log_info "Creating OMEN directories..."
mkdir -p /etc/omen
mkdir -p /var/log/omen
mkdir -p /var/lib/omen
mkdir -p /var/backups/omen
mkdir -p /var/run/omen

# Create symlinks
log_info "Creating command symlinks..."
ln -sf "$INSTALL_DIR/omen/cli.py" /usr/local/bin/omen
chmod +x /usr/local/bin/omen

# Install components based on choice
case $INSTALL_CHOICE in
    1)
        # Install all components
        log_header ""
        log_header "Installing LSHC..."
        if [[ -f "$INSTALL_DIR/lshc/scripts/install.sh" ]]; then
            "$INSTALL_DIR/lshc/scripts/install.sh"
        fi
        
        log_header ""
        log_header "Installing SAMS..."
        if [[ -f "$INSTALL_DIR/sams/install.sh" ]]; then
            "$INSTALL_DIR/sams/install.sh"
        fi
        
        log_header ""
        log_header "Installing SSHMFA..."
        if [[ -f "$INSTALL_DIR/sshmfa/install.sh" ]]; then
            "$INSTALL_DIR/sshmfa/install.sh"
        fi
        ;;
    2)
        log_header ""
        log_header "Installing LSHC..."
        if [[ -f "$INSTALL_DIR/lshc/scripts/install.sh" ]]; then
            "$INSTALL_DIR/lshc/scripts/install.sh"
        fi
        ;;
    3)
        log_header ""
        log_header "Installing SAMS..."
        if [[ -f "$INSTALL_DIR/sams/install.sh" ]]; then
            "$INSTALL_DIR/sams/install.sh"
        fi
        ;;
    4)
        log_header ""
        log_header "Installing SSHMFA..."
        if [[ -f "$INSTALL_DIR/sshmfa/install.sh" ]]; then
            "$INSTALL_DIR/sshmfa/install.sh"
        fi
        ;;
esac

# Summary
echo ""
log_header "╔═══════════════════════════════════════════════════════╗"
log_header "║         OMEN Installation Complete!                  ║"
log_header "╚═══════════════════════════════════════════════════════╝"
echo ""

log_info "OMEN has been installed to: $INSTALL_DIR"
log_info ""
log_info "Quick Start:"
log_info "  • Launch TUI:     omen"
log_info "  • Show status:    omen status"
log_info "  • Get help:       omen --help"
log_info ""
log_info "Component Commands:"
log_info "  • LSHC:  cd $INSTALL_DIR/lshc && ansible-playbook playbook.yml"
log_info "  • SAMS:  systemctl start omen-sams"
log_info "  • SSHMFA: python3 $INSTALL_DIR/sshmfa/sshmfa.py --help"
log_info ""
log_info "Documentation:"
log_info "  • Main: $INSTALL_DIR/README.md"
log_info "  • LSHC: $INSTALL_DIR/lshc/README.md"
log_info "  • SAMS: $INSTALL_DIR/sams/README.md"
log_info "  • SSHMFA: $INSTALL_DIR/sshmfa/README.md"
echo ""

log_warn "Next Steps:"
if [[ $INSTALL_CHOICE == 1 ]] || [[ $INSTALL_CHOICE == 3 ]]; then
    log_warn "  • Configure SAMS: Edit $INSTALL_DIR/sams/config.json"
fi
if [[ $INSTALL_CHOICE == 1 ]] || [[ $INSTALL_CHOICE == 4 ]]; then
    log_warn "  • SSHMFA: Enroll users before enabling 2FA!"
fi
echo ""

log_info "Thank you for using OMEN!"

