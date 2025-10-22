#!/usr/bin/env python3
"""
OMEN CLI - Command-line interface for OMEN suite.
"""

import sys
import argparse
from pathlib import Path

from omen.common.logger import get_logger, disable_colors, enable_colors
from omen.common.system import check_root, check_python_version, check_ubuntu_version
from omen.common.config import Config
from omen.components import LSHCComponent, SAMSComponent, SSHMFAComponent

logger = get_logger(__name__)


def check_prerequisites() -> bool:
    """Check system prerequisites."""
    # Python version
    success, version = check_python_version(3, 10)
    if not success:
        logger.error(f"Python 3.10+ required, found {version}")
        return False
    
    # Ubuntu version
    success, version = check_ubuntu_version("22.04")
    if not success:
        logger.warning(f"Ubuntu 22.04+ recommended, found {version}")
    
    return True


def cmd_status(args):
    """Show component status."""
    config = Config()
    
    if args.component:
        # Show specific component status
        component_name = args.component
        status = config.get_component_status(component_name)
        
        logger.info(f"Component: {component_name}")
        logger.info(f"  Installed: {status.get('installed', False)}")
        logger.info(f"  Enabled: {status.get('enabled', False)}")
        logger.info(f"  Configured: {status.get('configured', False)}")
    else:
        # Show all components
        all_status = config.get_all_status()
        
        logger.info("OMEN Component Status")
        logger.info("=" * 50)
        
        for component, status in all_status.get("components", {}).items():
            logger.info(f"\n{component.upper()}:")
            logger.info(f"  Installed: {status.get('installed', False)}")
            logger.info(f"  Enabled: {status.get('enabled', False)}")
            logger.info(f"  Configured: {status.get('configured', False)}")
            
            if status.get('install_date'):
                logger.info(f"  Install Date: {status['install_date']}")
    
    return 0


def cmd_install(args):
    """Install component(s)."""
    if not check_root():
        logger.error("Root privileges required for installation")
        return 1
    
    components = []
    
    if args.component == "all":
        components = ["lshc", "sams", "sshmfa"]
    else:
        components = [args.component]
    
    omen_root = Path("/opt/omen")
    success = True
    
    for component in components:
        logger.info(f"Installing {component.upper()}...")
        
        if component == "lshc":
            comp = LSHCComponent(omen_root)
            if not comp.install():
                logger.error(f"Failed to install {component}")
                success = False
        elif component == "sams":
            comp = SAMSComponent(omen_root)
            if not comp.install():
                logger.error(f"Failed to install {component}")
                success = False
        elif component == "sshmfa":
            comp = SSHMFAComponent(omen_root)
            if not comp.install():
                logger.error(f"Failed to install {component}")
                success = False
        else:
            logger.error(f"Unknown component: {component}")
            success = False
    
    return 0 if success else 1


def cmd_uninstall(args):
    """Uninstall component."""
    if not check_root():
        logger.error("Root privileges required for uninstallation")
        return 1
    
    component = args.component
    omen_root = Path("/opt/omen")
    
    logger.info(f"Uninstalling {component.upper()}...")
    
    if component == "lshc":
        comp = LSHCComponent(omen_root)
        success = comp.uninstall()
    elif component == "sams":
        comp = SAMSComponent(omen_root)
        success = comp.uninstall()
    elif component == "sshmfa":
        comp = SSHMFAComponent(omen_root)
        success = comp.uninstall()
    else:
        logger.error(f"Unknown component: {component}")
        return 1
    
    return 0 if success else 1


def cmd_tui(args):
    """Launch TUI interface."""
    try:
        from omen.tui import run_tui
        return run_tui()
    except ImportError as e:
        logger.error(f"Failed to load TUI: {e}")
        logger.error("Make sure 'rich' library is installed")
        return 1


def main():
    """Main entry point for OMEN CLI."""
    parser = argparse.ArgumentParser(
        description="OMEN - Observation, Monitoring, Enforcement & Notification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="OMEN 1.0.0",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show component status")
    status_parser.add_argument(
        "component",
        nargs="?",
        choices=["lshc", "sams", "sshmfa"],
        help="Specific component (optional)",
    )
    status_parser.set_defaults(func=cmd_status)
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install component")
    install_parser.add_argument(
        "component",
        choices=["lshc", "sams", "sshmfa", "all"],
        help="Component to install",
    )
    install_parser.set_defaults(func=cmd_install)
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall component")
    uninstall_parser.add_argument(
        "component",
        choices=["lshc", "sams", "sshmfa"],
        help="Component to uninstall",
    )
    uninstall_parser.set_defaults(func=cmd_uninstall)
    
    # TUI command
    tui_parser = subparsers.add_parser("tui", help="Launch interactive TUI")
    tui_parser.set_defaults(func=cmd_tui)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle color settings
    if args.no_color:
        disable_colors()
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Default to TUI if no command specified
    if not args.command:
        args.func = cmd_tui
        return cmd_tui(args)
    
    # Execute command
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

