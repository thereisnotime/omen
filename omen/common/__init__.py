"""
Common utilities shared across OMEN components.
"""

from omen.common.logger import get_logger, enable_colors, disable_colors
from omen.common.config import Config
from omen.common.system import (
    check_root,
    check_ubuntu_version,
    check_python_version,
    get_service_status,
    backup_file,
    restore_file,
)

__all__ = [
    "get_logger",
    "enable_colors",
    "disable_colors",
    "Config",
    "check_root",
    "check_ubuntu_version",
    "check_python_version",
    "get_service_status",
    "backup_file",
    "restore_file",
]

