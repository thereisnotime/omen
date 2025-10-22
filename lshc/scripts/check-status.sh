#!/usr/bin/env bash
# LSHC Status Check Script

set -euo pipefail

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}LSHC - Security Hardening Status${NC}"
echo "===================================="
echo ""

# Check SSH Configuration
echo -e "${BLUE}SSH Configuration:${NC}"
if grep -q "^PermitRootLogin no" /etc/ssh/sshd_config 2>/dev/null; then
    echo -e "  Root login disabled: ${GREEN}✓${NC}"
else
    echo -e "  Root login disabled: ${RED}✗${NC}"
fi

if grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config 2>/dev/null; then
    echo -e "  Password auth disabled: ${GREEN}✓${NC}"
else
    echo -e "  Password auth disabled: ${RED}✗${NC}"
fi

echo ""

# Check Firewall
echo -e "${BLUE}Firewall (UFW):${NC}"
if command -v ufw &> /dev/null; then
    ufw_status=$(ufw status | head -n 1 || echo "inactive")
    if [[ $ufw_status == *"active"* ]]; then
        echo -e "  UFW enabled: ${GREEN}✓${NC}"
    else
        echo -e "  UFW enabled: ${RED}✗${NC}"
    fi
else
    echo -e "  UFW installed: ${RED}✗${NC}"
fi

echo ""

# Check Auditd
echo -e "${BLUE}Audit Framework:${NC}"
if systemctl is-active --quiet auditd 2>/dev/null; then
    echo -e "  Auditd running: ${GREEN}✓${NC}"
else
    echo -e "  Auditd running: ${RED}✗${NC}"
fi

if [[ -f /etc/audit/rules.d/omen-hardening.rules ]]; then
    echo -e "  OMEN audit rules: ${GREEN}✓${NC}"
else
    echo -e "  OMEN audit rules: ${RED}✗${NC}"
fi

echo ""

# Check Kernel Hardening
echo -e "${BLUE}Kernel Hardening:${NC}"
if [[ -f /etc/sysctl.d/99-omen-hardening.conf ]]; then
    echo -e "  OMEN sysctl config: ${GREEN}✓${NC}"
    
    # Check a few key settings
    if sysctl net.ipv4.ip_forward | grep -q "= 0" 2>/dev/null; then
        echo -e "  IP forwarding disabled: ${GREEN}✓${NC}"
    else
        echo -e "  IP forwarding disabled: ${YELLOW}?${NC}"
    fi
    
    if sysctl net.ipv4.tcp_syncookies | grep -q "= 1" 2>/dev/null; then
        echo -e "  TCP SYN cookies enabled: ${GREEN}✓${NC}"
    else
        echo -e "  TCP SYN cookies enabled: ${YELLOW}?${NC}"
    fi
else
    echo -e "  OMEN sysctl config: ${RED}✗${NC}"
fi

echo ""

# Check Password Policies
echo -e "${BLUE}Password Policies:${NC}"
if command -v pwquality &> /dev/null || dpkg -l | grep -q libpam-pwquality; then
    echo -e "  Password quality: ${GREEN}✓${NC}"
else
    echo -e "  Password quality: ${RED}✗${NC}"
fi

# Check password aging
pass_max_days=$(grep "^PASS_MAX_DAYS" /etc/login.defs | awk '{print $2}' || echo "unknown")
echo -e "  Max password age: ${pass_max_days} days"

echo ""
echo "===================================="

