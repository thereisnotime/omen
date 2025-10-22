#!/usr/bin/env python3
"""
SSHMFA - SSH MFA Hardening with OTP

Main management script for SSH 2FA configuration.
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from omen.common.logger import get_logger
from omen.common.system import check_root

logger = get_logger(__name__)


def main():
    """Main entry point for SSHMFA management."""
    parser = argparse.ArgumentParser(
        description="SSHMFA - SSH MFA Hardening with OTP"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Enroll command
    enroll_parser = subparsers.add_parser("enroll", help="Enroll user in 2FA")
    enroll_parser.add_argument("username", help="Username to enroll")
    
    # Bypass commands
    bypass_grant_parser = subparsers.add_parser("bypass-grant", help="Grant temporary 2FA bypass")
    bypass_grant_parser.add_argument("username", help="Username to grant bypass")
    
    bypass_revoke_parser = subparsers.add_parser("bypass-revoke", help="Revoke 2FA bypass")
    bypass_revoke_parser.add_argument("username", help="Username to revoke bypass")
    
    subparsers.add_parser("bypass-list", help="List active bypasses")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Check root privileges
    if not check_root():
        logger.error("Root privileges required")
        return 1
    
    # Use unified shell script
    script = Path(__file__).parent / "scripts" / "sshmfa.sh"
    
    if not script.exists():
        logger.error(f"SSHMFA script not found: {script}")
        return 1
    
    # Build command
    cmd = [str(script)]
    
    if args.command == "enroll":
        cmd.extend(["enroll", args.username])
    elif args.command == "bypass-grant":
        cmd.extend(["bypass-grant", args.username])
    elif args.command == "bypass-revoke":
        cmd.extend(["bypass-revoke", args.username])
    elif args.command == "bypass-list":
        cmd.append("bypass-list")
    
    # Execute command
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

