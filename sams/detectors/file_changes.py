#!/usr/bin/env python3
"""
SAMS File Change Detector - Monitors critical system files for unauthorized changes.
"""

import subprocess
from typing import List, Dict, Any
from pathlib import Path
import hashlib
import json

from sams.detectors.base import BaseDetector, SecurityEvent


class FileChangeDetector(BaseDetector):
    """Detector for critical file modifications."""
    
    # Critical files to monitor
    CRITICAL_FILES = [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/group",
        "/etc/gshadow",
        "/etc/sudoers",
        "/etc/ssh/sshd_config",
        "/root/.ssh/authorized_keys",
        "/etc/crontab",
    ]
    
    # Critical directories to monitor
    CRITICAL_DIRS = [
        "/etc/sudoers.d",
        "/etc/cron.d",
        "/etc/cron.daily",
        "/etc/cron.hourly",
        "/etc/cron.weekly",
        "/etc/cron.monthly",
    ]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize file change detector.
        
        Config options:
            hash_file: Path to store file hashes (default: /var/lib/omen/file_hashes.json)
            use_auditd: Use auditd for monitoring (default: true)
            timeframe: Time window in seconds (default: 300)
        """
        super().__init__(config)
        self.hash_file = Path(config.get("hash_file", "/var/lib/omen/file_hashes.json"))
        self.use_auditd = config.get("use_auditd", True)
        self.timeframe = config.get("timeframe", 300)
        self.file_hashes = self._load_hashes()
    
    def detect(self) -> List[SecurityEvent]:
        """Detect file changes."""
        if not self.is_enabled():
            return []
        
        events = []
        
        # Check hash changes for critical files
        hash_events = self._check_file_hashes()
        if hash_events:
            events.extend(hash_events)
        
        # Check auditd for file modifications
        if self.use_auditd:
            auditd_events = self._check_auditd_file_changes()
            if auditd_events:
                events.extend(auditd_events)
        
        return events
    
    def _load_hashes(self) -> Dict[str, str]:
        """Load stored file hashes."""
        if not self.hash_file.exists():
            # Create directory if needed
            self.hash_file.parent.mkdir(parents=True, exist_ok=True)
            return {}
        
        try:
            with open(self.hash_file, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def _save_hashes(self) -> None:
        """Save file hashes."""
        try:
            self.hash_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.hash_file, 'w') as f:
                json.dump(self.file_hashes, f, indent=2)
        except Exception:
            pass
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _check_file_hashes(self) -> List[SecurityEvent]:
        """Check for file hash changes."""
        events = []
        
        # Check critical files
        for file_path in self.CRITICAL_FILES:
            if not Path(file_path).exists():
                continue
            
            current_hash = self._get_file_hash(file_path)
            if not current_hash:
                continue
            
            stored_hash = self.file_hashes.get(file_path)
            
            if stored_hash is None:
                # First time seeing this file
                self.file_hashes[file_path] = current_hash
            elif stored_hash != current_hash:
                # File has been modified
                events.append(SecurityEvent(
                    event_type="file_change",
                    severity="critical",
                    message=f"Critical file modified: {file_path}",
                    details={
                        "file_path": file_path,
                        "previous_hash": stored_hash,
                        "current_hash": current_hash,
                    }
                ))
                
                # Update hash
                self.file_hashes[file_path] = current_hash
        
        # Check for new files in critical directories
        for dir_path in self.CRITICAL_DIRS:
            dir_obj = Path(dir_path)
            if not dir_obj.exists():
                continue
            
            try:
                for file_path in dir_obj.glob("*"):
                    if file_path.is_file():
                        file_str = str(file_path)
                        current_hash = self._get_file_hash(file_str)
                        
                        if file_str not in self.file_hashes:
                            events.append(SecurityEvent(
                                event_type="file_change",
                                severity="high",
                                message=f"New file created in critical directory: {file_str}",
                                details={
                                    "file_path": file_str,
                                    "directory": dir_path,
                                    "file_hash": current_hash,
                                }
                            ))
                            
                            self.file_hashes[file_str] = current_hash
                        elif self.file_hashes[file_str] != current_hash:
                            events.append(SecurityEvent(
                                event_type="file_change",
                                severity="high",
                                message=f"File modified in critical directory: {file_str}",
                                details={
                                    "file_path": file_str,
                                    "directory": dir_path,
                                    "previous_hash": self.file_hashes[file_str],
                                    "current_hash": current_hash,
                                }
                            ))
                            
                            self.file_hashes[file_str] = current_hash
            except Exception:
                pass
        
        # Save updated hashes
        self._save_hashes()
        
        return events
    
    def _check_auditd_file_changes(self) -> List[SecurityEvent]:
        """Check auditd logs for file modifications."""
        events = []
        
        try:
            cmd = [
                "ausearch",
                "-ts", f"recent -{self.timeframe}",
                "-k", "identity,sudoers,sshd_config",
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
            
            # Parse auditd output for file modifications
            for line in result.stdout.split('\n'):
                if "type=PATH" in line:
                    # Extract file path
                    import re
                    path_match = re.search(r'name="([^"]+)"', line)
                    if path_match:
                        file_path = path_match.group(1)
                        
                        events.append(SecurityEvent(
                            event_type="file_change",
                            severity="high",
                            message=f"Auditd detected file access: {file_path}",
                            details={
                                "file_path": file_path,
                                "source": "auditd",
                            }
                        ))
        
        except FileNotFoundError:
            pass
        except Exception:
            pass
        
        return events

