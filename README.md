# OMEN

```text
   ___  __  __ _____ _   _
  / _ \|  \/  | ____| \ | |
 | | | | |\/| |  _| |  \| |
 | |_| | |  | | |___| |\  |
  \___/|_|  |_|_____|_| \_|
```

**O**bservation, **M**onitoring, **E**nforcement & **N**otification

A collection of standalone security tools for Linux systems, designed for security professionals and system administrators.

[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04+-orange.svg)](https://ubuntu.com)

## Overview

OMEN provides three **standalone** security components:

1. **LSHC** - Linux Security Hardening Configurator (Ansible-based)
2. **SAMS** - Suspicious Activity Monitoring System (Python service)
3. **SSHMFA** - SSH MFA Hardening with OTP (Shell script)

Each component is fully independent and can be installed/used separately without any dependencies on the others.

## Features

- 🎯 **Standalone Components** - Each tool works completely independently
- 📊 **Comprehensive Security** - Hardening, monitoring, and authentication
- 🔒 **Industry Standards** - Based on CIS, STIG, and security best practices
- 📱 **Multi-Platform Alerts** - Slack, Mattermost, Telegram, and custom webhooks
- 🔐 **Secure by Design** - Proper access controls, auditing, and fail-safes
- 🛠️ **Simple Installation** - Interactive menu-driven installer

## Quick Start

### Prerequisites

- Ubuntu 22.04 LTS or newer (primary target)
- Python 3.10+ (for SAMS only)
- Root/sudo access

### Installation

#### Option 1: Install All Components

```bash
# Clone the repository
git clone https://github.com/thereisnotime/omen.git
cd omen

# Run the installer and select "All components"
sudo ./install.sh
```

#### Option 2: Install Individual Components

```bash
# Clone the repository
git clone https://github.com/thereisnotime/omen.git
cd omen

# Run the installer and select the specific component you want
sudo ./install.sh

# Or install directly
sudo ./lshc/scripts/install.sh    # LSHC only
sudo ./sams/install.sh            # SAMS only
sudo ./sshmfa/install.sh          # SSHMFA only
```

### Usage

Each component has its own commands and management interface:

#### LSHC Usage

```bash
# Apply all hardening rules
cd /opt/omen/lshc
ansible-playbook playbook.yml

# Apply specific hardening (by tag)
ansible-playbook playbook.yml --tags ssh
ansible-playbook playbook.yml --tags firewall

# Check hardening status
/opt/omen/lshc/scripts/check-status.sh
```

#### SAMS Usage

```bash
# Configure monitoring
vim /opt/omen/sams/config.json

# Start monitoring service
systemctl start omen-sams

# Enable on boot
systemctl enable omen-sams

# View logs
journalctl -u omen-sams -f
```

#### SSHMFA Usage

```bash
# Enroll a user for 2FA
/opt/omen/sshmfa/scripts/sshmfa.sh enroll <username>

# Enable 2FA globally
/opt/omen/sshmfa/scripts/sshmfa.sh enable

# Grant temporary bypass
/opt/omen/sshmfa/scripts/sshmfa.sh bypass-grant <username>

# Check status
/opt/omen/sshmfa/scripts/sshmfa.sh status
```

## Components

### LSHC - Linux Security Hardening Configurator

Automated security hardening using Ansible playbooks.

**Features:**

- SSH hardening (disable root login, enforce key auth, strong ciphers)
- Firewall configuration (UFW with sensible defaults)
- Password policies (aging, complexity requirements)
- Kernel hardening (sysctl tuning for security)
- Audit framework (auditd with comprehensive rules)

**Quick usage:**

```bash
cd /opt/omen/lshc
ansible-playbook playbook.yml
```

[📖 Full LSHC Documentation](lshc/README.md)

### SAMS - Suspicious Activity Monitoring System

Real-time security event detection and alerting.

**Detects:**

- Authentication failures and brute force attempts
- Privilege escalation attempts
- Suspicious command execution
- Critical file modifications
- Network anomalies

**Alerts via:**

- Slack, Mattermost, Telegram
- Custom webhooks with templates
- Structured JSON logs for SIEM integration

**Quick usage:**

```bash
# Configure alerting
sudo nano /opt/omen/sams/config.json

# Start monitoring
sudo systemctl start omen-sams
sudo systemctl enable omen-sams
```

[📖 Full SAMS Documentation](sams/README.md)

### SSHMFA - SSH MFA Hardening with OTP

SSH two-factor authentication with secure bypass mechanism.

**Features:**

- OTP authentication using Google Authenticator
- User enrollment management
- Temporary admin bypass with audit logging
- Secure group-based access control
- Emergency recovery procedures

**Quick usage:**

```bash
# Enroll a user
sudo /opt/omen/sshmfa/scripts/sshmfa.sh enroll username

# Grant temporary bypass
sudo /opt/omen/sshmfa/scripts/sshmfa.sh bypass-grant username

# Enable 2FA system-wide
sudo /opt/omen/sshmfa/scripts/sshmfa.sh enable
```

[📖 Full SSHMFA Documentation](sshmfa/README.md)

## Architecture

OMEN is a collection of standalone security tools:

```text
/opt/omen/
├── lshc/                  # LSHC - Security hardening (Ansible)
│   ├── playbook.yml       # Main playbook
│   ├── roles/             # Hardening roles
│   │   └── omen-hardening/
│   └── scripts/           # Management scripts
│       ├── install.sh
│       ├── uninstall.sh
│       └── check-status.sh
│
├── sams/                  # SAMS - Activity monitoring (Python)
│   ├── sams.py            # Main monitoring script
│   ├── config.json        # Configuration
│   ├── detectors/         # Event detectors
│   ├── alerters/          # Alert backends
│   ├── install.sh         # Installer
│   └── systemd/           # Service files
│
└── sshmfa/                # SSHMFA - SSH MFA (Shell)
    ├── scripts/
    │   ├── sshmfa.sh      # Main management script
    │   └── check-bypass.sh  # PAM helper
    ├── templates/         # Config templates
    └── install.sh         # Installer
```

Each component is **completely independent** and has no dependencies on other components.

## Configuration

### Component Configuration

Each component has its own configuration:

- **LSHC**: `/opt/omen/lshc/roles/omen-hardening/defaults/main.yml`
- **SAMS**: `/opt/omen/sams/config.json`
- **SSHMFA**: PAM configuration and bypass flags in `/var/run/omen/bypass/`

### Logs and Data

- **LSHC**: No persistent logs (Ansible output only)
- **SAMS**: Logs to `/var/log/omen/sams.log` and systemd journal
- **SSHMFA**: Audit logs via syslog, bypass tracking in `/var/run/omen/bypass/`

## Testing

A Vagrant-based test environment is provided:

```bash
cd test
vagrant up
vagrant ssh
```

[📖 Test Environment Documentation](test/README.md)

## Security Considerations

### Important Notes

- **SSHMFA**: Always enroll at least one user before enabling 2FA system-wide
- **LSHC**: Review hardening rules before applying to production
- **SAMS**: Configure appropriate alert thresholds to avoid alert fatigue
- **Backups**: All components create backups before modifying system files

### Security Features

- All bypass mechanisms are audited via syslog
- Sensitive operations require root or specific group membership
- File modifications are backed up automatically
- Rate limiting on alerts to prevent storms

## Uninstallation

Each component can be uninstalled independently:

```bash
# Uninstall LSHC
sudo /opt/omen/lshc/scripts/uninstall.sh

# Uninstall SAMS
sudo /opt/omen/sams/uninstall.sh

# Uninstall SSHMFA
sudo /opt/omen/sshmfa/uninstall.sh

# Remove all (if you want to completely remove OMEN)
sudo rm -rf /opt/omen
```

## Troubleshooting

### Common Issues

**Component installer fails:**

- Ensure you're running Ubuntu 22.04+
- Check Python version: `python3 --version`
- Run as root: `sudo ./install.sh`

**SAMS not detecting events:**

- Check service status: `systemctl status omen-sams`
- Review logs: `journalctl -u omen-sams -f`
- Verify auditd is running: `systemctl status auditd`

**SSH 2FA lockout:**

- Use bypass mechanism from console
- Restore from backup: `/etc/ssh/sshd_config.pre-omen-2fa`

## Roadmap

Future improvements for this security toolkit collection:

### Platform Support

- [ ] Support for more Linux distributions (Debian, CentOS, RHEL, Alpine)
- [ ] ARM architecture support (Raspberry Pi, AWS Graviton)
- [ ] Test on more distributions, architectures and versions
- [ ] BSD support (FreeBSD, OpenBSD)

### Core Features

- [ ] Web-based dashboard for centralized management
- [ ] REST API for programmatic access
- [ ] Multi-server management from single control plane
- [ ] Agent-based deployment for remote systems
- [ ] Configuration profiles (development, staging, production)

### Security Enhancements

- [ ] Additional hardening rules (Docker, Kubernetes, container security)
- [ ] Integration with cloud provider security services (AWS GuardDuty, Azure Security Center)
- [ ] Automated compliance reporting (CIS, STIG, PCI-DSS, HIPAA)
- [ ] Security posture scoring and trending
- [ ] Integration with vulnerability scanners (OpenVAS, Nessus)

### LSHC Improvements

- [ ] Rollback capability for all hardening changes
- [ ] Compliance assessment before/after reports
- [ ] Custom hardening profiles per use case
- [ ] Integration with configuration management (Salt, Chef, Puppet)

### SAMS Enhancements

- [ ] Machine learning for anomaly detection
- [ ] Threat intelligence feed integration
- [ ] Correlation engine for multi-event patterns
- [ ] Plugin system for custom detectors and alerters
- [ ] Performance profiling and optimization
- [ ] Historical data analysis and reporting

### SSHMFA Features

- [ ] WebAuthn/FIDO2 support
- [ ] Hardware token support (YubiKey)
- [ ] Biometric authentication integration
- [ ] Per-user 2FA policies
- [ ] Session management and revocation

### DevOps & Automation

- [ ] Add GitHub Actions for CI/CD
- [ ] Automated testing pipeline
- [ ] Docker/container packaging
- [ ] Ansible Galaxy publication
- [ ] PyPI package publication
- [ ] Automated documentation generation

### Monitoring & Observability

- [ ] Prometheus metrics export
- [ ] Grafana dashboard templates
- [ ] OpenTelemetry integration
- [ ] Health check endpoints
- [ ] Performance metrics collection

### Documentation & Community

- [ ] Video tutorials and demos
- [ ] Security best practices guide
- [ ] Contribution guidelines
- [ ] Community forum/Discord server
- [ ] Professional security audit
- [ ] Penetration testing results publication

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Ansible](https://www.ansible.com/) and Python
- Inspired by industry security standards (CIS, STIG, NIST)
- Community hardening roles from [dev-sec.io](https://dev-sec.io/)
- Monitoring capabilities inspired by [OSSEC](https://www.ossec.net/) and [Wazuh](https://wazuh.com/)

---

**Note**: This tool is designed for legitimate security hardening and monitoring. Always ensure you have proper authorization before deploying security tools on any system.
