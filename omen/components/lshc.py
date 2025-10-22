#!/usr/bin/env python3
"""
LSHC Component Interface - Linux Security Hardening Configurator.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from omen.common.logger import get_logger
from omen.common.config import Config
from omen.common.system import require_root, run_command, is_package_installed

logger = get_logger(__name__)


class LSHCComponent:
    """LSHC component interface for installation and management."""
    
    def __init__(self, omen_root: Path = Path("/opt/omen")):
        """Initialize LSHC component."""
        self.omen_root = omen_root
        self.lshc_dir = omen_root / "lshc"
        self.config = Config()
    
    def is_installed(self) -> bool:
        """Check if LSHC is installed."""
        # Check if directory exists and Ansible is available
        return (
            self.lshc_dir.exists() and
            (self.lshc_dir / "playbook.yml").exists() and
            is_package_installed("ansible")
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get LSHC status."""
        return {
            "installed": self.is_installed(),
            "ansible_available": is_package_installed("ansible"),
            "playbook_path": str(self.lshc_dir / "playbook.yml"),
        }
    
    def install(self) -> bool:
        """Install LSHC component."""
        require_root()
        
        try:
            logger.info("Installing LSHC component...")
            
            # Install Ansible if not present
            if not is_package_installed("ansible"):
                logger.info("Installing Ansible...")
                from omen.common.system import install_package
                if not install_package("ansible", update_cache=True):
                    logger.error("Failed to install Ansible")
                    return False
            
            # Run standalone installer if available
            installer = self.lshc_dir / "scripts" / "install.sh"
            if installer.exists():
                logger.info("Running LSHC installer...")
                result = subprocess.run(
                    [str(installer)],
                    cwd=str(self.lshc_dir),
                    check=False,
                )
                if result.returncode != 0:
                    logger.error("LSHC installer failed")
                    return False
            
            # Update status
            self.config.update_component_status("lshc", installed=True)
            logger.info("LSHC installed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to install LSHC: {e}")
            return False
    
    def uninstall(self) -> bool:
        """Uninstall LSHC component."""
        require_root()
        
        try:
            logger.info("Uninstalling LSHC component...")
            
            # Run standalone uninstaller if available
            uninstaller = self.lshc_dir / "scripts" / "uninstall.sh"
            if uninstaller.exists():
                logger.info("Running LSHC uninstaller...")
                subprocess.run(
                    [str(uninstaller)],
                    cwd=str(self.lshc_dir),
                    check=False,
                )
            
            # Update status
            self.config.reset_component("lshc")
            logger.info("LSHC uninstalled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to uninstall LSHC: {e}")
            return False
    
    def apply_hardening(self, tags: Optional[str] = None) -> bool:
        """
        Apply hardening configuration.
        
        Args:
            tags: Optional Ansible tags to filter tasks
        
        Returns:
            True on success, False on failure
        """
        require_root()
        
        if not self.is_installed():
            logger.error("LSHC is not installed")
            return False
        
        try:
            logger.info("Applying security hardening...")
            
            cmd = [
                "ansible-playbook",
                str(self.lshc_dir / "playbook.yml"),
                "-i", str(self.lshc_dir / "inventory.yml"),
            ]
            
            if tags:
                cmd.extend(["--tags", tags])
            
            result = subprocess.run(
                cmd,
                cwd=str(self.lshc_dir),
                check=False,
            )
            
            if result.returncode == 0:
                self.config.update_component_status("lshc", configured=True)
                logger.info("Hardening applied successfully")
                return True
            else:
                logger.error("Hardening application failed")
                return False
        
        except Exception as e:
            logger.error(f"Failed to apply hardening: {e}")
            return False
    
    def check_status_detailed(self) -> bool:
        """Check detailed hardening status."""
        if not self.is_installed():
            logger.error("LSHC is not installed")
            return False
        
        status_script = self.lshc_dir / "scripts" / "check-status.sh"
        if status_script.exists():
            subprocess.run([str(status_script)], cwd=str(self.lshc_dir))
            return True
        
        logger.warning("Status check script not found")
        return False

