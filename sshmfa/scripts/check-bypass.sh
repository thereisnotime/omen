#!/usr/bin/env bash
# SSHMFA Bypass Check Script - Called by PAM to check for bypass flag

set -euo pipefail

# Get username from PAM environment
USERNAME="${PAM_USER:-}"

if [[ -z "$USERNAME" ]]; then
    exit 1
fi

BYPASS_DIR="/var/run/omen/bypass"
CURRENT_TIME=$(date +%s)
MAX_AGE=3600  # 1 hour in seconds

# Check if bypass directory exists
if [[ ! -d "$BYPASS_DIR" ]]; then
    exit 1
fi

# Look for valid bypass file for this user
for bypass_file in "$BYPASS_DIR"/2fa-"$USERNAME"-*; do
    if [[ ! -f "$bypass_file" ]]; then
        continue
    fi
    
    # Extract timestamp from filename
    FILENAME=$(basename "$bypass_file")
    TIMESTAMP=$(echo "$FILENAME" | cut -d'-' -f3)
    
    # Check if bypass has expired (older than 1 hour)
    AGE=$((CURRENT_TIME - TIMESTAMP))
    if [[ $AGE -gt $MAX_AGE ]]; then
        # Expired, remove it
        rm -f "$bypass_file"
        continue
    fi
    
    # Valid bypass found - delete it (single use) and allow login
    rm -f "$bypass_file"
    
    # Log the bypass usage
    logger -t omen-sshmfa -p auth.notice "2FA bypass used for user $USERNAME"
    
    # Return success to PAM
    exit 0
done

# No valid bypass found
exit 1

