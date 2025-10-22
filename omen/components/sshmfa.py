#!/usr/bin/env python3
"""
SSHMFA Component Interface - SSH MFA Hardening with OTP.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List

from omen.common.logger import get_logger
from omen.common.config import Config
from omen.common.system import require_root, is_package_installed

logger = get_logger(__name__)


class SSHMFAComponent:
    """SSHMFA component interface for installation and management."""
    
    REQUIRED_PACKAGE = "libpam-google-authenticator"
    
    def __init__(self, omen_root: Path = Path("/opt/omen")):
        """Initialize SSHMFA component."""
        self.omen_root = omen_root
        self.sshmfa_dir = omen_root / "sshmfa"
        self.config = Config()
    
    def is_installed(self) -> bool:
        """Check if SSHMFA is installed."""
        return (
            self.sshmfa_dir.exists() and
            (self.sshmfa_dir / "sshmfa.py").exists() and
            is_package_installed(self.REQUIRED_PACKAGE)
        )
    
    def is_enabled(self) -> bool:
        """Check if 2FA is currently enabled."""
        # Check if PAM configuration has been modified
        pam_sshd = Path("/etc/pam.d/sshd")
        if not pam_sshd.exists():
            return False
        
        try:
            content = pam_sshd.read_text()
            return "pam_google_authenticator.so" in content
        except Exception:
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get SSHMFA status."""
        return {
            "installed": self.is_installed(),
            "enabled": self.is_enabled(),
            "package_installed": is_package_installed(self.REQUIRED_PACKAGE),
            "bypass_dir": "/var/run/omen/bypass",
        }
    
    def install(self) -> bool:
        """Install SSHMFA component."""
        require_root()
        
        try:
            logger.info("Installing SSHMFA component...")
            
            # Run standalone installer if available
            installer = self.sshmfa_dir / "install.sh"
            if installer.exists():
                logger.info("Running SSHMFA installer...")
                result = subprocess.run(
                    [str(installer)],
                    cwd=str(self.sshmfa_dir),
                    check=False,
                )
                if result.returncode != 0:
                    logger.error("SSHMFA installer failed")
                    return False
            
            # Update status
            self.config.update_component_status("sshmfa", installed=True, enabled=self.is_enabled())
            logger.info("SSHMFA installed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to install SSHMFA: {e}")
            return False
    
    def uninstall(self) -> bool:
        """Uninstall SSHMFA component."""
        require_root()
        
        try:
            logger.info("Uninstalling SSHMFA component...")
            
            # Run standalone uninstaller if available
            uninstaller = self.sshmfa_dir / "uninstall.sh"
            if uninstaller.exists():
                logger.info("Running SSHMFA uninstaller...")
                subprocess.run(
                    [str(uninstaller)],
                    cwd=str(self.sshmfa_dir),
                    check=False,
                )
            
            # Update status
            self.config.reset_component("sshmfa")
            logger.info("SSHMFA uninstalled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to uninstall SSHMFA: {e}")
            return False
    
    def enroll_user(self, username: str) -> bool:
        """
        Enroll a user in 2FA.
        
        Args:
            username: Username to enroll
        
        Returns:
            True on success, False on failure
        """
        require_root()
        
        if not self.is_installed():
            logger.error("SSHMFA is not installed")
            return False
        
        try:
            logger.info(f"Enrolling user: {username}")
            enroll_script = self.sshmfa_dir / "scripts" / "enroll-user.sh"
            
            if enroll_script.exists():
                result = subprocess.run(
                    [str(enroll_script), username],
                    check=False,
                )
                return result.returncode == 0
            else:
                logger.error("Enrollment script not found")
                return False
        
        except Exception as e:
            logger.error(f"Failed to enroll user {username}: {e}")
            return False
    
    def grant_bypass(self, username: str) -> bool:
        """
        Grant temporary 2FA bypass for a user.
        
        Args:
            username: Username to grant bypass
        
        Returns:
            True on success, False on failure
        """
        require_root()
        
        if not self.is_installed():
            logger.error("SSHMFA is not installed")
            return False
        
        try:
            logger.info(f"Granting 2FA bypass for user: {username}")
            bypass_script = self.sshmfa_dir / "scripts" / "bypass-grant.sh"
            
            if bypass_script.exists():
                result = subprocess.run(
                    [str(bypass_script), username],
                    check=False,
                )
                return result.returncode == 0
            else:
                logger.error("Bypass grant script not found")
                return False
        
        except Exception as e:
            logger.error(f"Failed to grant bypass for {username}: {e}")
            return False
    
    def revoke_bypass(self, username: str) -> bool:
        """
        Revoke 2FA bypass for a user.
        
        Args:
            username: Username to revoke bypass
        
        Returns:
            True on success, False on failure
        """
        require_root()
        
        try:
            logger.info(f"Revoking 2FA bypass for user: {username}")
            revoke_script = self.sshmfa_dir / "scripts" / "bypass-revoke.sh"
            
            if revoke_script.exists():
                result = subprocess.run(
                    [str(revoke_script), username],
                    check=False,
                )
                return result.returncode == 0
            else:
                logger.error("Bypass revoke script not found")
                return False
        
        except Exception as e:
            logger.error(f"Failed to revoke bypass for {username}: {e}")
            return False
    
    def list_bypasses(self) -> List[str]:
        """List active bypass grants."""
        bypass_dir = Path("/var/run/omen/bypass")
        
        if not bypass_dir.exists():
            return []
        
        try:
            bypasses = []
            for bypass_file in bypass_dir.glob("2fa-*"):
                # Extract username from filename
                parts = bypass_file.name.split("-")
                if len(parts) >= 2:
                    bypasses.append(parts[1])
            return bypasses
        except Exception as e:
            logger.error(f"Failed to list bypasses: {e}")
            return []
    
    def check_status_detailed(self) -> bool:
        """Check detailed SSHMFA status."""
        if not self.is_installed():
            logger.error("SSHMFA is not installed")
            return False
        
        status_script = self.sshmfa_dir / "scripts" / "sshmfa.sh"
        if status_script.exists():
            subprocess.run([str(status_script), "status"])
            return True
        
        logger.warning("Status script not found")
        return False

