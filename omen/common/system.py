#!/usr/bin/env python3
"""
OMEN System Utilities - System checks and file operations.

Provides system detection, version checking, service management,
and file backup/restore utilities.
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from omen.common.logger import get_logger

logger = get_logger(__name__)


def check_root() -> bool:
    """
    Check if running as root.

    Returns:
        True if running as root, False otherwise
    """
    return os.geteuid() == 0


def require_root() -> None:
    """Require root privileges or exit."""
    if not check_root():
        logger.error("This operation requires root privileges")
        sys.exit(1)


def check_python_version(min_major: int = 3, min_minor: int = 10) -> Tuple[bool, str]:
    """
    Check if Python version meets minimum requirements.

    Args:
        min_major: Minimum major version
        min_minor: Minimum minor version

    Returns:
        Tuple of (success, version_string)
    """
    version_info = sys.version_info
    current_version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info.major < min_major or \
       (version_info.major == min_major and version_info.minor < min_minor):
        return False, current_version
    
    return True, current_version


def check_ubuntu_version(min_version: str = "22.04") -> Tuple[bool, str]:
    """
    Check if running on Ubuntu with minimum version.

    Args:
        min_version: Minimum Ubuntu version (e.g., "22.04")

    Returns:
        Tuple of (success, version_string)
    """
    try:
        # Check if it's Ubuntu
        with open("/etc/os-release", "r") as f:
            os_info = f.read()
        
        if "Ubuntu" not in os_info:
            return False, "Not Ubuntu"
        
        # Extract version
        for line in os_info.split("\n"):
            if line.startswith("VERSION_ID="):
                version = line.split("=")[1].strip('"')
                
                # Compare versions
                min_parts = [int(x) for x in min_version.split(".")]
                current_parts = [int(x) for x in version.split(".")]
                
                if current_parts >= min_parts:
                    return True, version
                else:
                    return False, version
        
        return False, "Unknown"
    
    except Exception as e:
        logger.error(f"Failed to check Ubuntu version: {e}")
        return False, "Unknown"


def get_service_status(service_name: str) -> str:
    """
    Get systemd service status.

    Args:
        service_name: Name of the service

    Returns:
        Service status: "active", "inactive", "failed", "not-found"
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            check=False,
        )
        status = result.stdout.strip()
        return status if status else "unknown"
    
    except Exception as e:
        logger.debug(f"Failed to get service status for {service_name}: {e}")
        return "unknown"


def service_exists(service_name: str) -> bool:
    """
    Check if a systemd service exists.

    Args:
        service_name: Name of the service

    Returns:
        True if service exists, False otherwise
    """
    try:
        result = subprocess.run(
            ["systemctl", "list-unit-files", service_name],
            capture_output=True,
            text=True,
            check=False,
        )
        return service_name in result.stdout
    
    except Exception:
        return False


def start_service(service_name: str) -> bool:
    """Start a systemd service."""
    try:
        subprocess.run(
            ["systemctl", "start", service_name],
            check=True,
            capture_output=True,
        )
        logger.info(f"Started service: {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start service {service_name}: {e}")
        return False


def stop_service(service_name: str) -> bool:
    """Stop a systemd service."""
    try:
        subprocess.run(
            ["systemctl", "stop", service_name],
            check=True,
            capture_output=True,
        )
        logger.info(f"Stopped service: {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to stop service {service_name}: {e}")
        return False


def enable_service(service_name: str) -> bool:
    """Enable a systemd service."""
    try:
        subprocess.run(
            ["systemctl", "enable", service_name],
            check=True,
            capture_output=True,
        )
        logger.info(f"Enabled service: {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to enable service {service_name}: {e}")
        return False


def disable_service(service_name: str) -> bool:
    """Disable a systemd service."""
    try:
        subprocess.run(
            ["systemctl", "disable", service_name],
            check=True,
            capture_output=True,
        )
        logger.info(f"Disabled service: {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to disable service {service_name}: {e}")
        return False


def backup_file(file_path: str, backup_dir: str = "/var/backups/omen") -> Optional[str]:
    """
    Create a backup of a file.

    Args:
        file_path: Path to the file to backup
        backup_dir: Directory to store backups

    Returns:
        Path to backup file or None on failure
    """
    try:
        src_path = Path(file_path)
        if not src_path.exists():
            logger.warning(f"File does not exist, skipping backup: {file_path}")
            return None
        
        # Create backup directory
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{src_path.name}.{timestamp}.backup"
        dest_path = backup_path / backup_name
        
        # Copy file
        shutil.copy2(str(src_path), str(dest_path))
        logger.info(f"Backed up {file_path} to {dest_path}")
        
        return str(dest_path)
    
    except Exception as e:
        logger.error(f"Failed to backup {file_path}: {e}")
        return None


def restore_file(backup_path: str, original_path: str) -> bool:
    """
    Restore a file from backup.

    Args:
        backup_path: Path to backup file
        original_path: Path to restore to

    Returns:
        True on success, False on failure
    """
    try:
        src_path = Path(backup_path)
        dest_path = Path(original_path)
        
        if not src_path.exists():
            logger.error(f"Backup file does not exist: {backup_path}")
            return False
        
        # Create parent directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy file
        shutil.copy2(str(src_path), str(dest_path))
        logger.info(f"Restored {original_path} from {backup_path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Failed to restore {original_path}: {e}")
        return False


def run_command(
    cmd: list,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a shell command.

    Args:
        cmd: Command as list of strings
        check: Raise exception on non-zero exit
        capture_output: Capture stdout/stderr

    Returns:
        CompletedProcess instance
    """
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(cmd)}")
        logger.error(f"Error: {e.stderr if e.stderr else str(e)}")
        raise


def is_package_installed(package_name: str) -> bool:
    """
    Check if a package is installed via dpkg.

    Args:
        package_name: Name of the package

    Returns:
        True if installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["dpkg", "-l", package_name],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and package_name in result.stdout
    except Exception:
        return False


def install_package(package_name: str, update_cache: bool = False) -> bool:
    """
    Install a package via apt.

    Args:
        package_name: Name of the package
        update_cache: Run apt update first

    Returns:
        True on success, False on failure
    """
    try:
        if update_cache:
            logger.info("Updating apt cache...")
            subprocess.run(
                ["apt-get", "update"],
                check=True,
                capture_output=True,
            )
        
        logger.info(f"Installing package: {package_name}")
        subprocess.run(
            ["apt-get", "install", "-y", package_name],
            check=True,
            capture_output=True,
        )
        logger.info(f"Successfully installed {package_name}")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package_name}: {e}")
        return False

