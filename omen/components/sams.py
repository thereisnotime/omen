#!/usr/bin/env python3
"""
SAMS Component Interface - Suspicious Activity Monitoring System.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any

from omen.common.logger import get_logger
from omen.common.config import Config
from omen.common.system import (
    require_root,
    get_service_status,
    start_service,
    stop_service,
    enable_service,
    disable_service,
    service_exists,
)

logger = get_logger(__name__)


class SAMSComponent:
    """SAMS component interface for installation and management."""
    
    SERVICE_NAME = "omen-sams"
    
    def __init__(self, omen_root: Path = Path("/opt/omen")):
        """Initialize SAMS component."""
        self.omen_root = omen_root
        self.sams_dir = omen_root / "sams"
        self.config = Config()
    
    def is_installed(self) -> bool:
        """Check if SAMS is installed."""
        return (
            self.sams_dir.exists() and
            (self.sams_dir / "sams.py").exists() and
            service_exists(self.SERVICE_NAME)
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get SAMS status."""
        service_status = get_service_status(self.SERVICE_NAME)
        
        return {
            "installed": self.is_installed(),
            "service_status": service_status,
            "running": service_status == "active",
            "config_path": str(self.sams_dir / "config.json"),
        }
    
    def install(self) -> bool:
        """Install SAMS component."""
        require_root()
        
        try:
            logger.info("Installing SAMS component...")
            
            # Run standalone installer if available
            installer = self.sams_dir / "install.sh"
            if installer.exists():
                logger.info("Running SAMS installer...")
                result = subprocess.run(
                    [str(installer)],
                    cwd=str(self.sams_dir),
                    check=False,
                )
                if result.returncode != 0:
                    logger.error("SAMS installer failed")
                    return False
            
            # Update status
            self.config.update_component_status("sams", installed=True)
            logger.info("SAMS installed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to install SAMS: {e}")
            return False
    
    def uninstall(self) -> bool:
        """Uninstall SAMS component."""
        require_root()
        
        try:
            logger.info("Uninstalling SAMS component...")
            
            # Stop service first
            if service_exists(self.SERVICE_NAME):
                stop_service(self.SERVICE_NAME)
                disable_service(self.SERVICE_NAME)
            
            # Run standalone uninstaller if available
            uninstaller = self.sams_dir / "uninstall.sh"
            if uninstaller.exists():
                logger.info("Running SAMS uninstaller...")
                subprocess.run(
                    [str(uninstaller)],
                    cwd=str(self.sams_dir),
                    check=False,
                )
            
            # Update status
            self.config.reset_component("sams")
            logger.info("SAMS uninstalled successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to uninstall SAMS: {e}")
            return False
    
    def start(self) -> bool:
        """Start SAMS service."""
        require_root()
        
        if not self.is_installed():
            logger.error("SAMS is not installed")
            return False
        
        if start_service(self.SERVICE_NAME):
            self.config.update_component_status("sams", enabled=True)
            return True
        return False
    
    def stop(self) -> bool:
        """Stop SAMS service."""
        require_root()
        
        if not self.is_installed():
            logger.error("SAMS is not installed")
            return False
        
        if stop_service(self.SERVICE_NAME):
            self.config.update_component_status("sams", enabled=False)
            return True
        return False
    
    def enable(self) -> bool:
        """Enable SAMS service to start on boot."""
        require_root()
        
        if not self.is_installed():
            logger.error("SAMS is not installed")
            return False
        
        return enable_service(self.SERVICE_NAME)
    
    def disable(self) -> bool:
        """Disable SAMS service from starting on boot."""
        require_root()
        
        if not self.is_installed():
            logger.error("SAMS is not installed")
            return False
        
        return disable_service(self.SERVICE_NAME)
    
    def test_alert(self) -> bool:
        """Send a test alert."""
        if not self.is_installed():
            logger.error("SAMS is not installed")
            return False
        
        try:
            logger.info("Sending test alert...")
            sams_script = self.sams_dir / "sams.py"
            subprocess.run(
                ["python3", str(sams_script), "--test-alert"],
                check=True,
            )
            logger.info("Test alert sent")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to send test alert: {e}")
            return False

