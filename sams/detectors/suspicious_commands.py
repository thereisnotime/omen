#!/usr/bin/env python3
"""
SAMS Suspicious Command Detector - Detects execution of suspicious commands.
"""

import re
import subprocess
from typing import List, Dict, Any

from detectors.base import BaseDetector, SecurityEvent


class SuspiciousCommandDetector(BaseDetector):
    """Detector for suspicious command execution."""
    
    # Suspicious patterns to detect
    SUSPICIOUS_PATTERNS = [
        # Reverse shells
        (r'bash\s+-i\s+>&\s+/dev/tcp/', "reverse_shell", "critical"),
        (r'nc\s+-[el]+.*\s+/bin/(ba)?sh', "reverse_shell", "critical"),
        (r'python.*socket.*subprocess', "reverse_shell", "critical"),
        (r'perl.*socket.*exec', "reverse_shell", "critical"),
        (r'/dev/tcp/.*bash', "reverse_shell", "critical"),
        
        # Network reconnaissance
        (r'nmap\s+', "network_scan", "high"),
        (r'masscan\s+', "network_scan", "high"),
        (r'netstat.*-[tanp]', "network_recon", "medium"),
        (r'ss\s+-[tanp]', "network_recon", "medium"),
        
        # Data exfiltration - Remote execution
        (r'curl.*https?://.*\|\s*bash', "remote_execution", "critical"),
        (r'wget.*https?://.*\|\s*bash', "remote_execution", "critical"),
        (r'curl.*-X\s+POST.*--data', "data_exfiltration", "high"),
        
        # Data exfiltration - File transfers
        (r'scp\s+.*@.*:', "data_exfiltration", "high"),
        (r'rsync.*@.*:', "data_exfiltration", "high"),
        (r'curl.*-T\s+', "data_exfiltration", "high"),  # Upload with curl
        (r'wget.*--post-file', "data_exfiltration", "high"),
        (r'nc\s+.*<\s*', "data_exfiltration", "high"),  # Netcat file transfer
        (r'cat\s+.*\|\s*nc\s+', "data_exfiltration", "high"),
        (r'tar\s+.*\|\s*ssh', "data_exfiltration", "high"),
        (r'python.*requests\.post', "data_exfiltration", "medium"),
        
        # Data exfiltration - Encoding/compression
        (r'tar\s+.*\|\s*base64', "data_exfiltration", "high"),
        (r'gzip.*\|\s*base64', "data_exfiltration", "medium"),
        (r'base64.*>\s*/tmp/', "data_exfiltration", "medium"),
        
        # Credential dumping and access
        (r'cat\s+/etc/shadow', "credential_access", "critical"),
        (r'cat\s+/etc/passwd', "credential_access", "high"),
        (r'mimikatz', "credential_access", "critical"),
        (r'grep.*password.*\.bash_history', "credential_hunting", "high"),
        (r'grep.*-r.*password', "credential_hunting", "medium"),
        (r'find.*\.ssh/id_rsa', "credential_hunting", "high"),
        (r'cat.*\.aws/credentials', "credential_hunting", "high"),
        (r'env\s*\|\s*grep.*PASSWORD', "credential_hunting", "medium"),
        (r'printenv.*PASS', "credential_hunting", "medium"),
        
        # Permission/SUID reconnaissance
        (r'find.*-perm.*4000', "permission_recon", "high"),  # SUID files
        (r'find.*-perm.*2000', "permission_recon", "high"),  # SGID files
        (r'find.*-perm.*777', "permission_recon", "medium"),  # World writable
        (r'find.*-user\s+root.*-perm', "privilege_escalation_recon", "high"),
        (r'getcap\s+-r\s+/', "permission_recon", "medium"),  # Capabilities
        (r'find.*-writable', "permission_recon", "medium"),
        
        # File access from other users
        (r'find\s+/home/.*-readable', "unauthorized_access", "medium"),
        (r'cat\s+/home/[^/]+/\.(bash_history|ssh)', "unauthorized_access", "high"),
        (r'ls\s+-la\s+/home/[^/]+', "unauthorized_access", "medium"),
        
        # Cryptominers
        (r'xmrig|ccminer|minerd', "cryptomining", "high"),
        
        # Suspicious base64
        (r'base64\s+-d.*\|\s*bash', "obfuscated_execution", "high"),
        (r'echo.*\|\s*base64\s+-d', "obfuscated_execution", "medium"),
        
        # System information gathering
        (r'uname\s+-a.*\|\s*(curl|wget)', "system_recon", "medium"),
        (r'ifconfig.*\|\s*(curl|wget)', "system_recon", "medium"),
        (r'ps\s+aux.*\|\s*(curl|wget)', "system_recon", "medium"),
        
        # Persistence mechanisms
        (r'crontab.*-e|echo.*>>\s*/var/spool/cron', "persistence", "high"),
        (r'echo.*>>\s*/etc/rc\.local', "persistence", "high"),
        (r'systemctl.*daemon-reload', "persistence", "medium"),
        
        # Log tampering
        (r'rm\s+.*\.log', "log_tampering", "high"),
        (r'echo\s+>\s+/var/log', "log_tampering", "high"),
        (r'truncate.*\.log', "log_tampering", "high"),
        (r'shred.*\.log', "log_tampering", "high"),
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

