#!/usr/bin/env python3
"""
OMEN TUI - Text User Interface using rich library.
"""

import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich import box

from omen.common.logger import get_logger
from omen.common.system import check_root
from omen.common.config import Config
from omen.components import LSHCComponent, SAMSComponent, SSHMFAComponent

logger = get_logger(__name__)
console = Console()


def create_status_table() -> Table:
    """Create status table for all components."""
    config = Config()
    all_status = config.get_all_status()
    
    table = Table(
        title="OMEN Component Status",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Installed", justify="center")
    table.add_column("Enabled", justify="center")
    table.add_column("Configured", justify="center")
    table.add_column("Install Date", style="dim")
    
    components = {
        "lshc": "Linux Security Hardening Configurator",
        "sams": "Suspicious Activity Monitoring System",
        "sshmfa": "SSH MFA Hardening with OTP",
    }
    
    for component, full_name in components.items():
        status = all_status.get("components", {}).get(component, {})
        
        installed = "✓" if status.get("installed") else "✗"
        enabled = "✓" if status.get("enabled") else "✗"
        configured = "✓" if status.get("configured") else "✗"
        install_date = status.get("install_date", "N/A")
        
        if install_date != "N/A":
            # Truncate ISO datetime
            install_date = install_date.split("T")[0]
        
        installed_style = "green" if status.get("installed") else "red"
        enabled_style = "green" if status.get("enabled") else "dim"
        configured_style = "green" if status.get("configured") else "dim"
        
        table.add_row(
            f"{component.upper()}\n[dim]{full_name}[/dim]",
            f"[{installed_style}]{installed}[/{installed_style}]",
            f"[{enabled_style}]{enabled}[/{enabled_style}]",
            f"[{configured_style}]{configured}[/{configured_style}]",
            install_date,
        )
    
    return table


def show_status():
    """Display component status."""
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]OMEN[/bold cyan] - Observation, Monitoring, Enforcement & Notification",
        border_style="cyan"
    ))
    console.print()
    console.print(create_status_table())
    console.print()


def menu_lshc():
    """LSHC component menu."""
    omen_root = Path("/opt/omen")
    lshc = LSHCComponent(omen_root)
    
    while True:
        console.clear()
        console.print(Panel("[bold]LSHC - Linux Security Hardening Configurator[/bold]"))
        console.print()
        
        status = lshc.get_status()
        console.print(f"Status: {'[green]Installed[/green]' if status['installed'] else '[red]Not Installed[/red]'}")
        console.print()
        
        options = []
        if not status['installed']:
            options.append("1) Install LSHC")
        else:
            options.append("2) Apply Hardening")
            options.append("3) Check Status")
            options.append("4) Uninstall LSHC")
        options.append("0) Back to Main Menu")
        
        for option in options:
            console.print(option)
        
        choice = Prompt.ask("\nSelect option", default="0")
        
        if choice == "1" and not status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            console.print("\n[yellow]Installing LSHC...[/yellow]")
            if lshc.install():
                console.print("[green]✓ LSHC installed successfully[/green]")
            else:
                console.print("[red]✗ Installation failed[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "2" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            tags = Prompt.ask("Enter tags (optional, comma-separated)", default="")
            tags = tags if tags else None
            
            console.print("\n[yellow]Applying hardening...[/yellow]")
            if lshc.apply_hardening(tags):
                console.print("[green]✓ Hardening applied successfully[/green]")
            else:
                console.print("[red]✗ Failed to apply hardening[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "3" and status['installed']:
            lshc.check_status_detailed()
            Prompt.ask("Press Enter to continue")
        
        elif choice == "4" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            if Confirm.ask("[red]Are you sure you want to uninstall LSHC?[/red]"):
                console.print("\n[yellow]Uninstalling LSHC...[/yellow]")
                if lshc.uninstall():
                    console.print("[green]✓ LSHC uninstalled successfully[/green]")
                else:
                    console.print("[red]✗ Uninstallation failed[/red]")
                Prompt.ask("Press Enter to continue")
        
        elif choice == "0":
            break


def menu_sams():
    """SAMS component menu."""
    omen_root = Path("/opt/omen")
    sams = SAMSComponent(omen_root)
    
    while True:
        console.clear()
        console.print(Panel("[bold]SAMS - Suspicious Activity Monitoring System[/bold]"))
        console.print()
        
        status = sams.get_status()
        console.print(f"Status: {'[green]Installed[/green]' if status['installed'] else '[red]Not Installed[/red]'}")
        if status['installed']:
            service_status = status.get('service_status', 'unknown')
            status_color = "green" if service_status == "active" else "red"
            console.print(f"Service: [{status_color}]{service_status}[/{status_color}]")
        console.print()
        
        options = []
        if not status['installed']:
            options.append("1) Install SAMS")
        else:
            if not status['running']:
                options.append("2) Start SAMS")
            else:
                options.append("3) Stop SAMS")
            options.append("4) Enable SAMS (start on boot)")
            options.append("5) Disable SAMS")
            options.append("6) Test Alert")
            options.append("7) Uninstall SAMS")
        options.append("0) Back to Main Menu")
        
        for option in options:
            console.print(option)
        
        choice = Prompt.ask("\nSelect option", default="0")
        
        if choice == "1" and not status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            console.print("\n[yellow]Installing SAMS...[/yellow]")
            if sams.install():
                console.print("[green]✓ SAMS installed successfully[/green]")
            else:
                console.print("[red]✗ Installation failed[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "2" and status['installed'] and not status['running']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            console.print("\n[yellow]Starting SAMS...[/yellow]")
            if sams.start():
                console.print("[green]✓ SAMS started[/green]")
            else:
                console.print("[red]✗ Failed to start[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "3" and status['installed'] and status['running']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            console.print("\n[yellow]Stopping SAMS...[/yellow]")
            if sams.stop():
                console.print("[green]✓ SAMS stopped[/green]")
            else:
                console.print("[red]✗ Failed to stop[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "4" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            if sams.enable():
                console.print("[green]✓ SAMS enabled[/green]")
            else:
                console.print("[red]✗ Failed to enable[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "5" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            if sams.disable():
                console.print("[green]✓ SAMS disabled[/green]")
            else:
                console.print("[red]✗ Failed to disable[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "6" and status['installed']:
            console.print("\n[yellow]Sending test alert...[/yellow]")
            if sams.test_alert():
                console.print("[green]✓ Test alert sent[/green]")
            else:
                console.print("[red]✗ Failed to send test alert[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "7" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            if Confirm.ask("[red]Are you sure you want to uninstall SAMS?[/red]"):
                console.print("\n[yellow]Uninstalling SAMS...[/yellow]")
                if sams.uninstall():
                    console.print("[green]✓ SAMS uninstalled successfully[/green]")
                else:
                    console.print("[red]✗ Uninstallation failed[/red]")
                Prompt.ask("Press Enter to continue")
        
        elif choice == "0":
            break


def menu_sshmfa():
    """SSHMFA component menu."""
    omen_root = Path("/opt/omen")
    sshmfa = SSHMFAComponent(omen_root)
    
    while True:
        console.clear()
        console.print(Panel("[bold]SSHMFA - SSH MFA Hardening with OTP[/bold]"))
        console.print()
        
        status = sshmfa.get_status()
        console.print(f"Status: {'[green]Installed[/green]' if status['installed'] else '[red]Not Installed[/red]'}")
        if status['installed']:
            enabled = status.get('enabled', False)
            console.print(f"2FA: {'[green]Enabled[/green]' if enabled else '[yellow]Disabled[/yellow]'}")
        console.print()
        
        options = []
        if not status['installed']:
            options.append("1) Install SSHMFA")
        else:
            options.append("2) Enroll User")
            options.append("3) Grant Bypass")
            options.append("4) List Bypasses")
            options.append("5) Revoke Bypass")
            options.append("6) Uninstall SSHMFA")
        options.append("0) Back to Main Menu")
        
        for option in options:
            console.print(option)
        
        choice = Prompt.ask("\nSelect option", default="0")
        
        if choice == "1" and not status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            console.print("\n[yellow]Installing SSHMFA...[/yellow]")
            if sshmfa.install():
                console.print("[green]✓ SSHMFA installed successfully[/green]")
            else:
                console.print("[red]✗ Installation failed[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "2" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            username = Prompt.ask("Enter username to enroll")
            console.print(f"\n[yellow]Enrolling user: {username}...[/yellow]")
            if sshmfa.enroll_user(username):
                console.print("[green]✓ User enrolled successfully[/green]")
            else:
                console.print("[red]✗ Enrollment failed[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "3" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            username = Prompt.ask("Enter username for bypass")
            console.print(f"\n[yellow]Granting bypass for: {username}...[/yellow]")
            if sshmfa.grant_bypass(username):
                console.print("[green]✓ Bypass granted (valid for 1 hour)[/green]")
            else:
                console.print("[red]✗ Failed to grant bypass[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "4" and status['installed']:
            bypasses = sshmfa.list_bypasses()
            if bypasses:
                console.print("\n[yellow]Active bypasses:[/yellow]")
                for username in bypasses:
                    console.print(f"  - {username}")
            else:
                console.print("\n[dim]No active bypasses[/dim]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "5" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            username = Prompt.ask("Enter username to revoke bypass")
            console.print(f"\n[yellow]Revoking bypass for: {username}...[/yellow]")
            if sshmfa.revoke_bypass(username):
                console.print("[green]✓ Bypass revoked[/green]")
            else:
                console.print("[red]✗ Failed to revoke bypass[/red]")
            Prompt.ask("Press Enter to continue")
        
        elif choice == "6" and status['installed']:
            if not check_root():
                console.print("[red]Root privileges required[/red]")
                Prompt.ask("Press Enter to continue")
                continue
            
            if Confirm.ask("[red]Are you sure you want to uninstall SSHMFA?[/red]"):
                console.print("\n[yellow]Uninstalling SSHMFA...[/yellow]")
                if sshmfa.uninstall():
                    console.print("[green]✓ SSHMFA uninstalled successfully[/green]")
                else:
                    console.print("[red]✗ Uninstallation failed[/red]")
                Prompt.ask("Press Enter to continue")
        
        elif choice == "0":
            break


def run_tui() -> int:
    """Run the TUI main loop."""
    try:
        while True:
            show_status()
            
            console.print("[bold]Main Menu[/bold]")
            console.print("1) LSHC - Linux Security Hardening Configurator")
            console.print("2) SAMS - Suspicious Activity Monitoring System")
            console.print("3) SSHMFA - SSH MFA Hardening with OTP")
            console.print("4) Install All Components")
            console.print("0) Exit")
            console.print()
            
            choice = Prompt.ask("Select option", default="0")
            
            if choice == "1":
                menu_lshc()
            elif choice == "2":
                menu_sams()
            elif choice == "3":
                menu_sshmfa()
            elif choice == "4":
                if not check_root():
                    console.print("[red]Root privileges required[/red]")
                    Prompt.ask("Press Enter to continue")
                    continue
                
                if Confirm.ask("Install all OMEN components?"):
                    omen_root = Path("/opt/omen")
                    
                    console.print("\n[yellow]Installing all components...[/yellow]\n")
                    
                    # Install LSHC
                    console.print("[cyan]Installing LSHC...[/cyan]")
                    lshc = LSHCComponent(omen_root)
                    if lshc.install():
                        console.print("[green]✓ LSHC installed[/green]\n")
                    else:
                        console.print("[red]✗ LSHC installation failed[/red]\n")
                    
                    # Install SAMS
                    console.print("[cyan]Installing SAMS...[/cyan]")
                    sams = SAMSComponent(omen_root)
                    if sams.install():
                        console.print("[green]✓ SAMS installed[/green]\n")
                    else:
                        console.print("[red]✗ SAMS installation failed[/red]\n")
                    
                    # Install SSHMFA
                    console.print("[cyan]Installing SSHMFA...[/cyan]")
                    sshmfa = SSHMFAComponent(omen_root)
                    if sshmfa.install():
                        console.print("[green]✓ SSHMFA installed[/green]\n")
                    else:
                        console.print("[red]✗ SSHMFA installation failed[/red]\n")
                    
                    console.print("[green]Installation complete![/green]")
                    Prompt.ask("Press Enter to continue")
            
            elif choice == "0":
                console.print("\n[cyan]Thank you for using OMEN![/cyan]")
                return 0
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Interrupted by user[/yellow]")
        return 0
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(run_tui())

