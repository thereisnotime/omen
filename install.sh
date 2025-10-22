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

# Check and install prerequisites
log_header "Checking Prerequisites"
log_header "======================"
echo ""

MISSING_PACKAGES=()

# Check for pip3
log_info "Checking for pip3..."
if ! command -v pip3 &>/dev/null; then
    log_warn "  pip3 not found - will install"
    MISSING_PACKAGES+=("python3-pip")
else
    log_info "  ✓ pip3: $(pip3 --version | cut -d' ' -f1-2)"
fi

# Check for rsync
log_info "Checking for rsync..."
if ! command -v rsync &>/dev/null; then
    log_warn "  rsync not found - will install"
    MISSING_PACKAGES+=("rsync")
else
    log_info "  ✓ rsync: installed"
fi

# Check for curl (needed for webhook testing)
log_info "Checking for curl..."
if ! command -v curl &>/dev/null; then
    log_warn "  curl not found - will install (needed for SAMS webhooks)"
    MISSING_PACKAGES+=("curl")
else
    log_info "  ✓ curl: installed"
fi

# Check for git (useful but not critical)
log_info "Checking for git..."
if ! command -v git &>/dev/null; then
    log_warn "  git not found (optional, but recommended for development)"
else
    log_info "  ✓ git: installed"
fi

# Check for jq (useful for JSON manipulation)
log_info "Checking for jq..."
if ! command -v jq &>/dev/null; then
    log_warn "  jq not found (optional, but useful for log analysis)"
else
    log_info "  ✓ jq: installed"
fi

# Install missing packages if any
if [[ ${#MISSING_PACKAGES[@]} -gt 0 ]]; then
    echo ""
    log_info "Installing missing packages: ${MISSING_PACKAGES[*]}"
    apt-get update -qq || log_error "Failed to update package lists"
    apt-get install -y "${MISSING_PACKAGES[@]}" || {
        log_error "Failed to install required packages"
        exit 1
    }
    log_info "Required packages installed successfully"
else
    log_info "All required packages are present"
fi

echo ""

# Ask what to install
echo "What would you like to install?"
echo ""
echo "  1) Complete OMEN suite (all components)"
echo "  2) LSHC only - Linux Security Hardening Configurator"
echo "  3) SAMS only - Suspicious Activity Monitoring System"
echo "  4) SSHMFA only - SSH MFA Hardening with OTP"
echo "  5) Exit"
echo ""
log_warn "Note: Base OMEN framework will be installed for all options"
log_info "This provides the 'omen' TUI/CLI for component management"
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

# Determine what to install
INSTALL_BASE=true
INSTALL_LSHC=false
INSTALL_SAMS=false
INSTALL_SSHMFA=false

case $INSTALL_CHOICE in
    1)
        INSTALL_LSHC=true
        INSTALL_SAMS=true
        INSTALL_SSHMFA=true
        log_info "Installing complete OMEN suite"
        ;;
    2)
        INSTALL_LSHC=true
        log_info "Installing base OMEN + LSHC component"
        ;;
    3)
        INSTALL_SAMS=true
        log_info "Installing base OMEN + SAMS component"
        ;;
    4)
        INSTALL_SSHMFA=true
        log_info "Installing base OMEN + SSHMFA component"
        ;;
esac

echo ""

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
    if command -v pip3 &>/dev/null; then
        pip3 install -r "$INSTALL_DIR/requirements.txt" -q || {
            log_error "Failed to install Python dependencies"
            log_error "Try running manually: pip3 install -r $INSTALL_DIR/requirements.txt"
            exit 1
        }
        log_info "Python dependencies installed successfully"
    else
        log_error "pip3 not available after installation attempt"
        exit 1
    fi
else
    log_warn "requirements.txt not found"
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

# Install selected components
if [[ "$INSTALL_LSHC" == "true" ]]; then
    log_header ""
    log_header "Installing LSHC Component..."
    if [[ -f "$INSTALL_DIR/lshc/scripts/install.sh" ]]; then
        "$INSTALL_DIR/lshc/scripts/install.sh"
    fi
fi

if [[ "$INSTALL_SAMS" == "true" ]]; then
    log_header ""
    log_header "Installing SAMS Component..."
    if [[ -f "$INSTALL_DIR/sams/install.sh" ]]; then
        "$INSTALL_DIR/sams/install.sh"
    fi
fi

if [[ "$INSTALL_SSHMFA" == "true" ]]; then
    log_header ""
    log_header "Installing SSHMFA Component..."
    if [[ -f "$INSTALL_DIR/sshmfa/install.sh" ]]; then
        "$INSTALL_DIR/sshmfa/install.sh"
    fi
fi

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

# Show component-specific information
if [[ "$INSTALL_LSHC" == "true" ]] || [[ "$INSTALL_SAMS" == "true" ]] || [[ "$INSTALL_SSHMFA" == "true" ]]; then
    log_info "Installed Components:"
    
    if [[ "$INSTALL_LSHC" == "true" ]]; then
        log_info ""
        log_info "  LSHC (Linux Security Hardening):"
        log_info "    • Apply hardening: cd $INSTALL_DIR/lshc && ansible-playbook playbook.yml"
        log_info "    • Check status:    $INSTALL_DIR/lshc/scripts/check-status.sh"
        log_info "    • Documentation:   $INSTALL_DIR/lshc/README.md"
    fi
    
    if [[ "$INSTALL_SAMS" == "true" ]]; then
        log_info ""
        log_info "  SAMS (Suspicious Activity Monitoring):"
        log_info "    • Configure:       nano $INSTALL_DIR/sams/config.json"
        log_info "    • Start service:   systemctl start omen-sams"
        log_info "    • View logs:       journalctl -u omen-sams -f"
        log_info "    • Documentation:   $INSTALL_DIR/sams/README.md"
    fi
    
    if [[ "$INSTALL_SSHMFA" == "true" ]]; then
        log_info ""
        log_info "  SSHMFA (SSH MFA with OTP):"
        log_info "    • Enroll user:     $INSTALL_DIR/sshmfa/scripts/sshmfa.sh enroll <username>"
        log_info "    • Enable 2FA:      $INSTALL_DIR/sshmfa/scripts/sshmfa.sh enable"
        log_info "    • Documentation:   $INSTALL_DIR/sshmfa/README.md"
    fi
fi

echo ""
log_info "Main Documentation: $INSTALL_DIR/README.md"
echo ""

# Component-specific warnings
if [[ "$INSTALL_SAMS" == "true" ]]; then
    log_warn "SAMS: Remember to configure alerting in $INSTALL_DIR/sams/config.json"
fi
if [[ "$INSTALL_SSHMFA" == "true" ]]; then
    log_warn "SSHMFA: Enroll at least one user before enabling 2FA system-wide!"
fi

if [[ "$INSTALL_SAMS" == "true" ]] || [[ "$INSTALL_SSHMFA" == "true" ]]; then
    echo ""
fi

log_info "Thank you for using OMEN!"

