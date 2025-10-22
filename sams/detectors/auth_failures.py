#!/usr/bin/env python3
"""
SAMS Auth Failure Detector - Detects authentication failures and brute force attempts.
"""

import re
import subprocess
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime, timedelta

from detectors.base import BaseDetector, SecurityEvent


class AuthFailureDetector(BaseDetector):
    """Detector for authentication failures and brute force attempts."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize auth failure detector.
        
        Config options:
            threshold: Number of failures to trigger alert (default: 5)
            timeframe: Time window in seconds (default: 300)
        """
        super().__init__(config)
        self.threshold = config.get("threshold", 5)
        self.timeframe = config.get("timeframe", 300)
        self.last_check = datetime.now() - timedelta(seconds=self.timeframe)
    
    def detect(self) -> List[SecurityEvent]:
        """Detect authentication failures from journalctl and auth.log."""
        if not self.is_enabled():
            return []
        
        events = []
        
        # Check SSH authentication failures
        ssh_failures = self._check_ssh_failures()
        if ssh_failures:
            events.extend(ssh_failures)
        
        # Check sudo authentication failures
        sudo_failures = self._check_sudo_failures()
        if sudo_failures:
            events.extend(sudo_failures)
        
        self.last_check = datetime.now()
        return events
    
    def _check_ssh_failures(self) -> List[SecurityEvent]:
        """Check for SSH authentication failures."""
        events = []
        
        try:
            # Use journalctl to get recent SSH failures
            cmd = [
                "journalctl",
                "-u", "ssh",
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
            
            # Parse failures by IP/user
            failures = defaultdict(list)
            
            for line in result.stdout.split('\n'):
                # Match failed password attempts
                if "Failed password" in line or "authentication failure" in line:
                    # Extract IP address
                    ip_match = re.search(r'from\s+(\d+\.\d+\.\d+\.\d+)', line)
                    # Extract username
                    user_match = re.search(r'for\s+(?:invalid\s+user\s+)?(\w+)', line)
                    
                    ip = ip_match.group(1) if ip_match else "unknown"
                    user = user_match.group(1) if user_match else "unknown"
                    
                    failures[(ip, user)].append(line)
            
            # Generate events for IPs exceeding threshold
            for (ip, user), failure_lines in failures.items():
                if len(failure_lines) >= self.threshold:
                    events.append(SecurityEvent(
                        event_type="auth_failure",
                        severity="high",
                        message=f"Multiple SSH authentication failures detected from {ip} for user {user}",
                        details={
                            "source_ip": ip,
                            "username": user,
                            "failure_count": len(failure_lines),
                            "threshold": self.threshold,
                            "service": "ssh",
                        }
                    ))
        
        except Exception as e:
            # Log error but don't raise
            pass
        
        return events
    
    def _check_sudo_failures(self) -> List[SecurityEvent]:
        """Check for sudo authentication failures."""
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
            
            # Parse sudo failures
            failures = defaultdict(list)
            
            for line in result.stdout.split('\n'):
                if "authentication failure" in line.lower() or "incorrect password" in line.lower():
                    # Extract username
                    user_match = re.search(r'(\w+)\s*:', line)
                    user = user_match.group(1) if user_match else "unknown"
                    
                    failures[user].append(line)
            
            # Generate events for users exceeding threshold
            for user, failure_lines in failures.items():
                if len(failure_lines) >= self.threshold:
                    events.append(SecurityEvent(
                        event_type="auth_failure",
                        severity="medium",
                        message=f"Multiple sudo authentication failures for user {user}",
                        details={
                            "username": user,
                            "failure_count": len(failure_lines),
                            "threshold": self.threshold,
                            "service": "sudo",
                        }
                    ))
        
        except Exception:
            pass
        
        return events

