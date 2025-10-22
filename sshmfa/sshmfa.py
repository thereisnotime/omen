#!/usr/bin/env python3
"""
SSHMFA - SSH MFA Hardening with OTP

Simple Python wrapper for the sshmfa.sh shell script.
This provides a Python interface for those who prefer it, but the
shell script (sshmfa.sh) is the primary standalone interface.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def check_root():
    """Check if running as root."""
    return os.geteuid() == 0


def main():
    """Main entry point for SSHMFA management."""
    parser = argparse.ArgumentParser(
        description="SSHMFA - SSH MFA Hardening with OTP",
        epilog="Note: This is a Python wrapper around sshmfa.sh shell script"
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
    subparsers.add_parser("status", help="Show 2FA status")
    subparsers.add_parser("enable", help="Enable 2FA system-wide")
    subparsers.add_parser("disable", help="Disable 2FA system-wide")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Check root privileges
    if not check_root():
        print("Error: Root privileges required", file=sys.stderr)
        print("Please run with: sudo python3", sys.argv[0], file=sys.stderr)
        return 1
    
    # Find the shell script
    script = Path(__file__).parent / "scripts" / "sshmfa.sh"
    
    if not script.exists():
        print(f"Error: SSHMFA script not found: {script}", file=sys.stderr)
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
    elif args.command == "status":
        cmd.append("status")
    elif args.command == "enable":
        cmd.append("enable")
    elif args.command == "disable":
        cmd.append("disable")
    
    # Execute command (pass through all output)
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except Exception as e:
        print(f"Error executing sshmfa.sh: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
