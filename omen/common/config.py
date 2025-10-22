#!/usr/bin/env python3
"""
OMEN Configuration Management - Centralized configuration and state tracking.

Manages component status, configuration files, and metadata.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from omen.common.logger import get_logger

logger = get_logger(__name__)


class Config:
    """OMEN configuration and state management."""
    
    CONFIG_DIR = Path("/etc/omen")
    STATUS_FILE = CONFIG_DIR / "status.json"
    BACKUP_DIR = Path("/var/backups/omen")
    LOG_DIR = Path("/var/log/omen")
    RUN_DIR = Path("/var/run/omen")
    
    COMPONENTS = ["lshc", "sams", "sshmfa"]
    
    def __init__(self):
        """Initialize configuration manager."""
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        for directory in [self.CONFIG_DIR, self.BACKUP_DIR, self.LOG_DIR]:
            try:
                directory.mkdir(parents=True, exist_ok=True, mode=0o755)
            except Exception as e:
                logger.warning(f"Failed to create directory {directory}: {e}")
        
        # RUN_DIR needs special handling (tmpfs)
        try:
            self.RUN_DIR.mkdir(parents=True, exist_ok=True, mode=0o755)
        except Exception as e:
            logger.debug(f"Run directory creation note: {e}")
    
    def load_status(self) -> Dict[str, Any]:
        """
        Load component status from file.

        Returns:
            Status dictionary
        """
        if not self.STATUS_FILE.exists():
            return self._get_default_status()
        
        try:
            with open(self.STATUS_FILE, 'r') as f:
                status = json.load(f)
            return status
        except Exception as e:
            logger.error(f"Failed to load status file: {e}")
            return self._get_default_status()
    
    def save_status(self, status: Dict[str, Any]) -> bool:
        """
        Save component status to file.

        Args:
            status: Status dictionary

        Returns:
            True on success, False on failure
        """
        try:
            self._ensure_directories()
            with open(self.STATUS_FILE, 'w') as f:
                json.dump(status, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save status file: {e}")
            return False
    
    def _get_default_status(self) -> Dict[str, Any]:
        """Get default status structure."""
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "components": {
                component: {
                    "installed": False,
                    "enabled": False,
                    "configured": False,
                    "install_date": None,
                    "last_modified": None,
                }
                for component in self.COMPONENTS
            }
        }
    
    def get_component_status(self, component: str) -> Dict[str, Any]:
        """
        Get status of a specific component.

        Args:
            component: Component name (lshc, sams, sshmfa)

        Returns:
            Component status dictionary
        """
        status = self.load_status()
        return status.get("components", {}).get(component, {
            "installed": False,
            "enabled": False,
            "configured": False,
        })
    
    def update_component_status(
        self,
        component: str,
        installed: Optional[bool] = None,
        enabled: Optional[bool] = None,
        configured: Optional[bool] = None,
    ) -> bool:
        """
        Update component status.

        Args:
            component: Component name
            installed: Installation status
            enabled: Enabled status
            configured: Configuration status

        Returns:
            True on success, False on failure
        """
        if component not in self.COMPONENTS:
            logger.error(f"Invalid component: {component}")
            return False
        
        status = self.load_status()
        
        if component not in status["components"]:
            status["components"][component] = {
                "installed": False,
                "enabled": False,
                "configured": False,
                "install_date": None,
                "last_modified": None,
            }
        
        component_status = status["components"][component]
        
        if installed is not None:
            component_status["installed"] = installed
            if installed and component_status["install_date"] is None:
                component_status["install_date"] = datetime.now().isoformat()
        
        if enabled is not None:
            component_status["enabled"] = enabled
        
        if configured is not None:
            component_status["configured"] = configured
        
        component_status["last_modified"] = datetime.now().isoformat()
        status["last_updated"] = datetime.now().isoformat()
        
        return self.save_status(status)
    
    def is_component_installed(self, component: str) -> bool:
        """Check if a component is installed."""
        status = self.get_component_status(component)
        return status.get("installed", False)
    
    def is_component_enabled(self, component: str) -> bool:
        """Check if a component is enabled."""
        status = self.get_component_status(component)
        return status.get("enabled", False)
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all components."""
        return self.load_status()
    
    def reset_component(self, component: str) -> bool:
        """Reset component status to default."""
        if component not in self.COMPONENTS:
            return False
        
        status = self.load_status()
        status["components"][component] = {
            "installed": False,
            "enabled": False,
            "configured": False,
            "install_date": None,
            "last_modified": datetime.now().isoformat(),
        }
        status["last_updated"] = datetime.now().isoformat()
        
        return self.save_status(status)

