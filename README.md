# OMEN

```text
   ___  __  __ _____ _   _
  / _ \|  \/  | ____| \ | |
 | | | | |\/| |  _| |  \| |
 | |_| | |  | | |___| |\  |
  \___/|_|  |_|_____|_| \_|
```

**O**bservation, **M**onitoring, **E**nforcement & **N**otification

A comprehensive security tooling suite for Linux systems, designed for security professionals and system administrators.

[![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-22.04+-orange.svg)](https://ubuntu.com)

## Overview

OMEN provides three integrated security components that can be used independently or together:

1. **LSHC** - Linux Security Hardening Configurator
2. **SAMS** - Suspicious Activity Monitoring System
3. **SSHMFA** - SSH MFA Hardening with OTP

Each component is designed to address specific security concerns while maintaining ease of use and flexibility.

## Features

- 🎯 **Modular Design** - Use components independently or as a complete suite
- 🖥️ **Interactive TUI** - Beautiful terminal interface using Rich library
- 🔧 **CLI Support** - Full command-line interface for automation
- 📊 **Comprehensive Monitoring** - Real-time security event detection
- 🔒 **Industry Standards** - Based on CIS, STIG, and security best practices
- 📱 **Multi-Platform Alerts** - Slack, Mattermost, Telegram, and custom webhooks
- 🔐 **Secure by Design** - Proper access controls, auditing, and fail-safes

## Quick Start

### Prerequisites

- Ubuntu 22.04 LTS or newer
- Python 3.10+
- Root/sudo access

### Installation

```bash
# Clone the repository
git clone https://github.com/thereisnotime/omen.git
cd omen

# Run the installer
sudo ./install.sh
```

The installer will guide you through installing OMEN and its components.

### Usage

Launch the interactive TUI:

```bash
sudo omen
```

Or use CLI commands:

```bash
# Show status of all components
sudo omen status

# Install a specific component
sudo omen install lshc

# Install all components
sudo omen install all
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
sudo python3 /opt/omen/sshmfa/sshmfa.py enroll username

# Grant temporary bypass
sudo python3 /opt/omen/sshmfa/sshmfa.py bypass-grant username

# Enable 2FA system-wide
sudo /opt/omen/sshmfa/scripts/enable-2fa.sh
```

[📖 Full SSHMFA Documentation](sshmfa/README.md)

## Architecture

```text
OMEN
├── omen/              # Main Python package
│   ├── cli.py        # Command-line interface
│   ├── tui.py        # Terminal UI
│   ├── common/       # Shared utilities
│   └── components/   # Component interfaces
├── lshc/             # Security hardening
│   ├── playbook.yml
│   └── roles/
├── sams/             # Activity monitoring
│   ├── sams.py
│   ├── detectors/
│   └── alerters/
└── sshmfa/           # SSH MFA
    ├── sshmfa.py
    ├── scripts/
    └── templates/
```

## Configuration

### OMEN System Configuration

Configuration and state tracking:

- Status: `/etc/omen/status.json`
- Logs: `/var/log/omen/`
- Backups: `/var/backups/omen/`

### Component Configuration

Each component has its own configuration:

- LSHC: `/opt/omen/lshc/roles/omen-hardening/defaults/main.yml`
- SAMS: `/opt/omen/sams/config.json`
- SSHMFA: PAM and sshd_config modifications

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

## Troubleshooting

### Common Issues

**Installation fails:**

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

If for somereason I decide to spend more time on this project, here are some ideas:

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

- Built with [Ansible](https://www.ansible.com/)
- TUI powered by [Rich](https://github.com/Textualize/rich)
- Inspired by industry security standards (CIS, STIG, NIST)
- Community hardening roles from [dev-sec.io](https://dev-sec.io/)

---

**Note**: This tool is designed for legitimate security hardening and monitoring. Always ensure you have proper authorization before deploying security tools on any system.
