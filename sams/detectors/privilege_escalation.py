#!/usr/bin/env python3
"""
SAMS Privilege Escalation Detector - Detects unauthorized privilege escalation attempts.
"""

import re
import subprocess
from typing import List, Dict, Any
from pathlib import Path

from detectors.base import BaseDetector, SecurityEvent


class PrivilegeEscalationDetector(BaseDetector):
    """Detector for privilege escalation attempts."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize privilege escalation detector.
        
        Config options:
            timeframe: Time window in seconds (default: 300)
            check_suid: Check for SUID/SGID changes (default: true)
        """
        super().__init__(config)
        self.timeframe = config.get("timeframe", 300)
        self.check_suid = config.get("check_suid", True)
        self.known_suid_files = self._get_suid_files()
    
    def detect(self) -> List[SecurityEvent]:
        """Detect privilege escalation attempts."""
        if not self.is_enabled():
            return []
        
        events = []
        
        # Check unauthorized sudo usage
        sudo_events = self._check_unauthorized_sudo()
        if sudo_events:
            events.extend(sudo_events)
        
        # Check for SUID/SGID changes
        if self.check_suid:
            suid_events = self._check_suid_changes()
            if suid_events:
                events.extend(suid_events)
        
        # Check for suspicious su usage
        su_events = self._check_su_usage()
        if su_events:
            events.extend(su_events)
        
        return events
    
    def _check_unauthorized_sudo(self) -> List[SecurityEvent]:
        """Check for unauthorized sudo attempts."""
        events = []
        
        try:
            cmd = [
                "journalctl",
                "-t", "sudo",
                "--since", f"{self.timeframe} seconds ago",
                "--no-pager",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                return events
            
            for line in result.stdout.split('\n'):
                # Look for "not in sudoers" or "command not allowed"
                if "NOT in sudoers" in line or "command not allowed" in line:
                    user_match = re.search(r'(\w+)\s*:', line)
                    cmd_match = re.search(r'COMMAND=(.+)', line)
                    
                    user = user_match.group(1) if user_match else "unknown"
                    command = cmd_match.group(1) if cmd_match else "unknown"
                    
                    events.append(SecurityEvent(
                        event_type="privilege_escalation",
                        severity="high",
                        message=f"Unauthorized sudo attempt by user {user}",
                        details={
                            "username": user,
                            "command": command,
                            "method": "sudo",
                        }
                    ))
        
        except Exception:
            pass
        
        return events
    
    def _check_suid_changes(self) -> List[SecurityEvent]:
        """Check for new SUID/SGID files."""
        events = []
        
        try:
            current_suid = self._get_suid_files()
            new_files = current_suid - self.known_suid_files
            
            if new_files:
                events.append(SecurityEvent(
                    event_type="privilege_escalation",
                    severity="critical",
                    message=f"New SUID/SGID files detected: {len(new_files)} files",
                    details={
                        "new_files": list(new_files),
                        "method": "suid_change",
                    }
                ))
                
                # Update known files
                self.known_suid_files = current_suid
        
        except Exception:
            pass
        
        return events
    
    def _get_suid_files(self) -> set:
        """Get set of SUID/SGID files on system."""
        suid_files = set()
        
        try:
            # Find SUID files
            result = subprocess.run(
                ["find", "/", "-perm", "-4000", "-type", "f", "-print"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            suid_files.update(result.stdout.strip().split('\n'))
            
            # Find SGID files
            result = subprocess.run(
                ["find", "/", "-perm", "-2000", "-type", "f", "-print"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            suid_files.update(result.stdout.strip().split('\n'))
        
        except Exception:
            pass
        
        return {f for f in suid_files if f}
    
    def _check_su_usage(self) -> List[SecurityEvent]:
        """Check for suspicious su usage."""
        events = []
        
        try:
            cmd = [
                "journalctl",
                "--since", f"{self.timeframe} seconds ago",
                "--no-pager",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                return events
            
            for line in result.stdout.split('\n'):
                if "su:" in line and ("session opened" in line or "authentication failure" in line):
                    # Extract user information
                    user_match = re.search(r'by\s+(\w+)', line)
                    target_match = re.search(r'for\s+(\w+)', line)
                    
                    if user_match:
                        user = user_match.group(1)
                        target = target_match.group(1) if target_match else "root"
                        
                        if "session opened" in line:
                            events.append(SecurityEvent(
                                event_type="privilege_escalation",
                                severity="medium",
                                message=f"User {user} switched to {target} using su",
                                details={
                                    "username": user,
                                    "target_user": target,
                                    "method": "su",
                                }
                            ))
        
        except Exception:
            pass
        
        return events

