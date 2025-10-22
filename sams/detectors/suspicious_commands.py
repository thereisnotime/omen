#!/usr/bin/env python3
"""
SAMS Suspicious Command Detector - Detects execution of suspicious commands.
"""

import re
import subprocess
from typing import List, Dict, Any

from sams.detectors.base import BaseDetector, SecurityEvent


class SuspiciousCommandDetector(BaseDetector):
    """Detector for suspicious command execution."""
    
    # Suspicious patterns to detect
    SUSPICIOUS_PATTERNS = [
        # Reverse shells
        (r'bash\s+-i\s+>&\s+/dev/tcp/', "reverse_shell", "critical"),
        (r'nc\s+-[el]+.*\s+/bin/(ba)?sh', "reverse_shell", "critical"),
        (r'python.*socket.*subprocess', "reverse_shell", "critical"),
        (r'perl.*socket.*exec', "reverse_shell", "critical"),
        
        # Network reconnaissance
        (r'nmap\s+', "network_scan", "high"),
        (r'masscan\s+', "network_scan", "high"),
        
        # Data exfiltration
        (r'curl.*https?://.*\|\s*bash', "remote_execution", "critical"),
        (r'wget.*https?://.*\|\s*bash', "remote_execution", "critical"),
        (r'curl.*-X\s+POST.*--data', "data_exfiltration", "high"),
        
        # Credential dumping
        (r'cat\s+/etc/shadow', "credential_access", "critical"),
        (r'mimikatz', "credential_access", "critical"),
        
        # Cryptominers
        (r'xmrig|ccminer|minerd', "cryptomining", "high"),
        
        # Suspicious base64
        (r'base64\s+-d.*\|\s*bash', "obfuscated_execution", "high"),
        (r'echo.*\|\s*base64\s+-d', "obfuscated_execution", "medium"),
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize suspicious command detector.
        
        Config options:
            timeframe: Time window in seconds (default: 300)
            use_auditd: Use auditd logs if available (default: true)
        """
        super().__init__(config)
        self.timeframe = config.get("timeframe", 300)
        self.use_auditd = config.get("use_auditd", True)
    
    def detect(self) -> List[SecurityEvent]:
        """Detect suspicious command execution."""
        if not self.is_enabled():
            return []
        
        events = []
        
        # Check bash history (limited, but worth checking)
        history_events = self._check_bash_history()
        if history_events:
            events.extend(history_events)
        
        # Check auditd logs if available
        if self.use_auditd:
            auditd_events = self._check_auditd_logs()
            if auditd_events:
                events.extend(auditd_events)
        
        # Check journalctl for command execution
        journal_events = self._check_journalctl()
        if journal_events:
            events.extend(journal_events)
        
        return events
    
    def _check_bash_history(self) -> List[SecurityEvent]:
        """Check bash history for suspicious commands (limited)."""
        events = []
        
        # Note: This has limitations as history might not be written immediately
        # Better to use auditd for real-time monitoring
        
        return events
    
    def _check_auditd_logs(self) -> List[SecurityEvent]:
        """Check auditd logs for suspicious commands."""
        events = []
        
        try:
            cmd = [
                "ausearch",
                "-ts", f"recent -{self.timeframe}",
                "-m", "execve",
                "--format", "text",
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            
            if result.returncode != 0:
                return events
            
            # Parse auditd output
            for line in result.stdout.split('\n'):
                for pattern, threat_type, severity in self.SUSPICIOUS_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extract command if possible
                        cmd_match = re.search(r'cmd=(.+)', line)
                        command = cmd_match.group(1) if cmd_match else "unknown"
                        
                        events.append(SecurityEvent(
                            event_type="suspicious_command",
                            severity=severity,
                            message=f"Suspicious command detected: {threat_type}",
                            details={
                                "threat_type": threat_type,
                                "command": command,
                                "pattern_matched": pattern,
                            }
                        ))
        
        except FileNotFoundError:
            # ausearch not available
            pass
        except Exception:
            pass
        
        return events
    
    def _check_journalctl(self) -> List[SecurityEvent]:
        """Check journalctl for suspicious command patterns."""
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
            
            # Scan for suspicious patterns
            for line in result.stdout.split('\n'):
                for pattern, threat_type, severity in self.SUSPICIOUS_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        events.append(SecurityEvent(
                            event_type="suspicious_command",
                            severity=severity,
                            message=f"Suspicious command pattern detected: {threat_type}",
                            details={
                                "threat_type": threat_type,
                                "log_entry": line[:500],  # Limit length
                                "pattern_matched": pattern,
                            }
                        ))
        
        except Exception:
            pass
        
        return events

