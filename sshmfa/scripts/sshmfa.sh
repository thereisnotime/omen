#!/usr/bin/env bash
# SSHMFA - SSH MFA Hardening with OTP
# Single unified management script

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
BYPASS_DIR="/var/run/omen/bypass"
TOTP_ADMIN_GROUP="omen-totp-admins"
SSH_CONFIG="/etc/ssh/sshd_config"
PAM_SSHD="/etc/pam.d/sshd"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_header() {
    echo -e "${CYAN}$*${NC}"
}

# Check root or admin group
check_privileges() {
    local require_root="${1:-false}"
    
    if [[ $require_root == "true" ]]; then
        if [[ $EUID -ne 0 ]]; then
            log_error "This operation requires root privileges"
            exit 1
        fi
    else
        # Check root or admin group
        if [[ $EUID -ne 0 ]] && ! groups | grep -q "$TOTP_ADMIN_GROUP"; then
            log_error "Only root or members of $TOTP_ADMIN_GROUP can perform this operation"
            exit 1
        fi
    fi
}

# Check if user exists
user_exists() {
    local username="$1"
    if ! id "$username" &>/dev/null; then
        log_error "User $username does not exist"
        return 1
    fi
    return 0
}

# Enable 2FA system-wide
cmd_enable() {
    check_privileges true
    
    log_header "Enabling SSH 2FA..."
    echo ""
    
    # Backup sshd_config
    if [[ ! -f "$SSH_CONFIG.pre-omen-2fa" ]]; then
        cp "$SSH_CONFIG" "$SSH_CONFIG.pre-omen-2fa"
        log_info "Backed up $SSH_CONFIG"
    else
        log_warn "Backup already exists: $SSH_CONFIG.pre-omen-2fa"
    fi
    
    # Configure sshd_config
    log_info "Configuring SSH daemon..."
    sed -i 's/^#*ChallengeResponseAuthentication.*/ChallengeResponseAuthentication yes/' "$SSH_CONFIG"
    sed -i 's/^#*UsePAM.*/UsePAM yes/' "$SSH_CONFIG"
    sed -i 's/^#*AuthenticationMethods.*/AuthenticationMethods publickey,keyboard-interactive/' "$SSH_CONFIG"
    
    # Add AuthenticationMethods if not present
    if ! grep -q "^AuthenticationMethods" "$SSH_CONFIG"; then
        echo "AuthenticationMethods publickey,keyboard-interactive" >> "$SSH_CONFIG"
    fi
    
    # Backup PAM configuration
    if [[ ! -f "$PAM_SSHD.pre-omen-2fa" ]]; then
        cp "$PAM_SSHD" "$PAM_SSHD.pre-omen-2fa"
        log_info "Backed up PAM configuration"
    else
        log_warn "PAM backup already exists: $PAM_SSHD.pre-omen-2fa"
    fi
    
    # Apply PAM configuration
    if [[ -f "$SCRIPT_DIR/../templates/pam.d-sshd" ]]; then
        cp "$SCRIPT_DIR/../templates/pam.d-sshd" "$PAM_SSHD"
        log_info "Applied PAM configuration"
    else
        log_error "PAM template not found: $SCRIPT_DIR/../templates/pam.d-sshd"
        exit 1
    fi
    
    # Restart SSH service
    log_info "Restarting SSH service..."
    systemctl restart sshd || systemctl restart ssh
    
    echo ""
    log_success "SSH 2FA enabled"
    echo ""
    log_warn "IMPORTANT:"
    echo "  • Users must be enrolled before they can login"
    echo "  • Use: $0 enroll <username>"
    echo "  • Make sure to enroll at least one user before logging out!"
}

# Disable 2FA
cmd_disable() {
    check_privileges true
    
    log_header "Disabling SSH 2FA..."
    echo ""
    
    # Restore sshd_config if backup exists
    if [[ -f "$SSH_CONFIG.pre-omen-2fa" ]]; then
        cp "$SSH_CONFIG.pre-omen-2fa" "$SSH_CONFIG"
        log_info "Restored $SSH_CONFIG from backup"
    else
        log_warn "No backup found for $SSH_CONFIG"
    fi
    
    # Restore PAM configuration if backup exists
    if [[ -f "$PAM_SSHD.pre-omen-2fa" ]]; then
        cp "$PAM_SSHD.pre-omen-2fa" "$PAM_SSHD"
        log_info "Restored PAM configuration from backup"
    else
        log_warn "No backup found for PAM configuration"
    fi
    
    # Restart SSH service
    log_info "Restarting SSH service..."
    systemctl restart sshd || systemctl restart ssh
    
    echo ""
    log_success "SSH 2FA disabled"
}

# Enroll a user
cmd_enroll() {
    check_privileges true
    
    if [[ $# -ne 1 ]]; then
        log_error "Usage: $0 enroll <username>"
        exit 1
    fi
    
    local username="$1"
    
    if ! user_exists "$username"; then
        exit 1
    fi
    
    log_header "OMEN SSHMFA - User Enrollment"
    echo "==============================="
    echo ""
    echo "Enrolling user: $username"
    echo ""
    
    # Check if google-authenticator is installed
    if ! command -v google-authenticator &>/dev/null; then
        log_error "google-authenticator not found"
        log_error "Please install: apt-get install libpam-google-authenticator"
        exit 1
    fi
    
    # Run google-authenticator as the user
    log_info "Setting up Google Authenticator for $username..."
    log_info "Follow the prompts to configure 2FA"
    echo ""
    
    # Switch to user and run google-authenticator
    su - "$username" -c "google-authenticator -t -d -f -r 3 -R 30 -w 3"
    
    if [[ $? -eq 0 ]]; then
        echo ""
        log_success "User $username enrolled in 2FA"
        echo ""
        log_warn "IMPORTANT:"
        echo "  • The user should scan the QR code or manually enter the secret key"
        echo "  • Emergency scratch codes have been generated"
        echo "  • Configuration stored in /home/$username/.google_authenticator"
        echo "  • The user will need both SSH key AND OTP code to login"
    else
        echo ""
        log_error "Enrollment failed"
        exit 1
    fi
}

# Grant temporary 2FA bypass
cmd_bypass_grant() {
    check_privileges false
    
    if [[ $# -ne 1 ]]; then
        log_error "Usage: $0 bypass-grant <username>"
        exit 1
    fi
    
    local username="$1"
    
    if ! user_exists "$username"; then
        exit 1
    fi
    
    # Create bypass directory if it doesn't exist
    mkdir -p "$BYPASS_DIR"
    chmod 755 "$BYPASS_DIR"
    
    # Generate bypass flag file
    local timestamp=$(date +%s)
    local random_str=$(head -c 16 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 16)
    local bypass_file="${BYPASS_DIR}/2fa-${username}-${timestamp}-${random_str}"
    
    # Create bypass flag
    touch "$bypass_file"
    chmod 600 "$bypass_file"
    
    # Write metadata to file
    cat > "$bypass_file" << EOF
username: $username
granted_by: $(whoami)
granted_at: $(date --iso-8601=seconds)
expires_at: $(date --iso-8601=seconds -d '+1 hour')
EOF
    
    log_success "2FA bypass granted for user: $username"
    echo ""
    echo "Details:"
    echo "  Username: $username"
    echo "  Granted by: $(whoami)"
    echo "  Valid for: 1 hour"
    echo "  Bypass file: $bypass_file"
    echo ""
    log_warn "SECURITY NOTE:"
    echo "  • This bypass is valid for ONE login or 1 hour, whichever comes first"
    echo "  • The bypass flag will be automatically deleted after use"
    echo "  • All bypass grants are audited"
    echo ""
    
    # Log the bypass grant
    logger -t omen-sshmfa -p auth.warning "2FA bypass granted for user $username by $(whoami)"
}

# Revoke 2FA bypass
cmd_bypass_revoke() {
    check_privileges false
    
    if [[ $# -ne 1 ]]; then
        log_error "Usage: $0 bypass-revoke <username>"
        exit 1
    fi
    
    local username="$1"
    
    # Find and remove bypass files for the user
    if [[ ! -d "$BYPASS_DIR" ]]; then
        log_warn "No bypass directory found"
        exit 0
    fi
    
    local found=0
    for bypass_file in "$BYPASS_DIR"/2fa-"$username"-*; do
        if [[ -f "$bypass_file" ]]; then
            rm -f "$bypass_file"
            log_info "Revoked bypass: $(basename "$bypass_file")"
            found=1
            
            # Log the revocation
            logger -t omen-sshmfa -p auth.warning "2FA bypass revoked for user $username by $(whoami)"
        fi
    done
    
    if [[ $found -eq 0 ]]; then
        log_warn "No bypass found for user: $username"
        exit 0
    fi
    
    log_success "All bypasses revoked for user: $username"
}

# List active bypasses
cmd_bypass_list() {
    if [[ ! -d "$BYPASS_DIR" ]]; then
        log_info "No bypass directory found"
        exit 0
    fi
    
    local bypasses=("$BYPASS_DIR"/2fa-*)
    
    # Check if any bypasses exist
    if [[ ! -f "${bypasses[0]}" ]]; then
        log_info "No active bypasses"
        exit 0
    fi
    
    local count=0
    log_header "Active 2FA Bypasses:"
    echo ""
    
    for bypass_file in "${bypasses[@]}"; do
        if [[ -f "$bypass_file" ]]; then
            count=$((count + 1))
            local filename=$(basename "$bypass_file")
            local username=$(echo "$filename" | cut -d'-' -f2)
            local timestamp=$(echo "$filename" | cut -d'-' -f3)
            local granted_at=$(date -d "@$timestamp" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo "unknown")
            
            echo "  $count) User: $username"
            echo "     Granted: $granted_at"
            echo "     File: $filename"
            
            # Read metadata if available
            if grep -q "granted_by:" "$bypass_file" 2>/dev/null; then
                local granted_by=$(grep "granted_by:" "$bypass_file" | cut -d':' -f2- | xargs)
                echo "     Granted by: $granted_by"
            fi
            
            echo ""
        fi
    done
    
    if [[ $count -eq 0 ]]; then
        log_info "No active bypasses"
    else
        echo "Total: $count active bypass(es)"
    fi
}

# Status check
cmd_status() {
    log_header "SSHMFA Status"
    echo "=============="
    echo ""
    
    # Check if 2FA is enabled
    if grep -q "^AuthenticationMethods.*keyboard-interactive" "$SSH_CONFIG" 2>/dev/null; then
        log_success "2FA: Enabled"
    else
        log_warn "2FA: Disabled"
    fi
    
    # Check if google-authenticator is installed
    if command -v google-authenticator &>/dev/null; then
        log_success "google-authenticator: Installed"
    else
        log_warn "google-authenticator: Not installed"
    fi
    
    # Check if backup exists
    if [[ -f "$SSH_CONFIG.pre-omen-2fa" ]]; then
        log_info "Backup: Available"
    else
        log_warn "Backup: Not found"
    fi
    
    # Check bypass directory
    if [[ -d "$BYPASS_DIR" ]]; then
        local bypass_count=$(find "$BYPASS_DIR" -name "2fa-*" -type f 2>/dev/null | wc -l)
        if [[ $bypass_count -gt 0 ]]; then
            log_info "Active bypasses: $bypass_count"
        else
            log_info "Active bypasses: 0"
        fi
    else
        log_info "Bypass directory: Not created"
    fi
    
    # Check admin group
    if getent group "$TOTP_ADMIN_GROUP" >/dev/null 2>&1; then
        local members=$(getent group "$TOTP_ADMIN_GROUP" | cut -d':' -f4)
        if [[ -n "$members" ]]; then
            log_info "TOTP admins: $members"
        else
            log_warn "TOTP admin group exists but has no members"
        fi
    else
        log_warn "TOTP admin group: Not created"
    fi
}

# Show usage
show_usage() {
    cat << EOF
SSHMFA - SSH MFA Hardening with OTP

Usage: $0 <command> [options]

Commands:
  enable                Enable 2FA system-wide (requires root)
  disable               Disable 2FA system-wide (requires root)
  enroll <username>     Enroll a user in 2FA (requires root)
  bypass-grant <user>   Grant temporary 2FA bypass (requires root or admin group)
  bypass-revoke <user>  Revoke 2FA bypass (requires root or admin group)
  bypass-list           List active bypasses
  status                Show SSHMFA status
  help                  Show this help message

Examples:
  $0 enable
  $0 enroll alice
  $0 bypass-grant bob
  $0 bypass-list
  $0 status

Bypass Management:
  • Bypasses are single-use and expire after 1 hour
  • All bypass operations are logged to syslog
  • Only root or members of '$TOTP_ADMIN_GROUP' can manage bypasses

For more information, see: /opt/omen/sshmfa/README.md
EOF
}

# Main command dispatcher
main() {
    if [[ $# -eq 0 ]]; then
        show_usage
        exit 1
    fi
    
    local command="$1"
    shift
    
    case "$command" in
        enable)
            cmd_enable "$@"
            ;;
        disable)
            cmd_disable "$@"
            ;;
        enroll)
            cmd_enroll "$@"
            ;;
        bypass-grant)
            cmd_bypass_grant "$@"
            ;;
        bypass-revoke)
            cmd_bypass_revoke "$@"
            ;;
        bypass-list)
            cmd_bypass_list "$@"
            ;;
        status)
            cmd_status "$@"
            ;;
        help|--help|-h)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

