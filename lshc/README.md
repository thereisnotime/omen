# LSHC - Linux Security Hardening Configurator

Automated security hardening for Linux systems using Ansible.

## Overview

LSHC provides automated security hardening based on industry standards (CIS, STIG, NIST). It uses Ansible playbooks to apply security configurations consistently and reproducibly.

## Features

### 1. SSH Hardening ⭐⭐⭐ **Critical**

**What it does:**
- Disables root login via SSH
- Enforces public key authentication
- Disables password authentication
- Configures strong ciphers and MACs
- Sets aggressive timeout values
- Increases logging verbosity

**Why it's important:**

SSH is the primary remote access method. Hardening SSH prevents unauthorized access, brute force attacks, and reduces the attack surface.

**Trade-offs:**
- Must manage SSH keys properly
- Emergency console access required for recovery
- Stricter timeouts may disconnect legitimate users
- Some legacy clients may not support strong ciphers

### 2. Firewall (UFW) ⭐⭐⭐ **Critical**

**What it does:**
- Enables UFW firewall
- Sets default deny incoming policy
- Allows only specified ports (default: SSH on 22)
- Implements rate limiting on SSH

**Why it's important:**

A firewall is the first line of defense, blocking unauthorized network access and limiting exposure of services.

**Trade-offs:**
- May block legitimate services if not configured properly
- Requires planning before applying
- Can cause connectivity issues if SSH rules are wrong

### 3. Password Policies ⭐⭐ **Important**

**What it does:**
- Sets password aging (max 90 days, min 1 day)
- Enforces strong password complexity
- Requires minimum length of 14 characters
- Mandates digit, uppercase, lowercase, and special characters

**Why it's important:**

Strong password policies prevent credential-based attacks and enforce regular password rotation.

**Trade-offs:**
- Users may find complex requirements frustrating
- May lead to password reuse across systems
- Requires user education

### 4. Kernel Hardening ⭐⭐⭐ **Critical**

**What it does:**
- Disables IP forwarding
- Enables TCP SYN cookies (DDoS protection)
- Disables ICMP redirects and source routing
- Enables reverse path filtering
- Restricts kernel pointer and dmesg access
- Disables core dumps for SUID programs

**Why it's important:**

Kernel-level protections prevent network-based attacks, information disclosure, and privilege escalation.

**Trade-offs:**
- May break routing/NAT functionality
- Some debugging tools may not work
- Performance impact is minimal but measurable

### 5. Audit Framework ⭐⭐⭐ **Critical**

**What it does:**
- Installs and configures auditd
- Monitors critical files (/etc/passwd, /etc/shadow, /etc/sudoers)
- Tracks SSH configuration changes
- Logs time changes and hostname modifications
- Monitors cron jobs

**Why it's important:**

Auditing provides forensic evidence and real-time detection of security events. Essential for compliance.

**Trade-offs:**
- Increases disk I/O and storage requirements
- Log analysis required to be useful
- May impact performance on very busy systems

## Installation

### Standalone Installation

```bash
cd /path/to/omen/lshc
sudo ./scripts/install.sh
```

### Via Main Installer Menu

From the OMEN repository root:

```bash
cd /path/to/omen
sudo ./install.sh
# Select option 2 (LSHC only) or option 1 (All components)
```

## Configuration

Edit `/opt/omen/lshc/roles/omen-hardening/defaults/main.yml` to customize settings:

```yaml
# SSH Configuration
omen_ssh_port: 22
omen_ssh_permit_root_login: "no"
omen_ssh_password_authentication: "no"

# Firewall
omen_firewall_allowed_ports:
  - { port: 22, proto: "tcp", comment: "SSH" }
  - { port: 80, proto: "tcp", comment: "HTTP" }
  - { port: 443, proto: "tcp", comment: "HTTPS" }

# Password Policies
omen_password_max_days: 90
omen_password_min_length: 14
```

## Usage

### Apply All Hardening

```bash
cd /opt/omen/lshc
ansible-playbook playbook.yml
```

### Apply Specific Components (Tags)

```bash
# SSH hardening only
ansible-playbook playbook.yml --tags ssh

# Firewall only
ansible-playbook playbook.yml --tags firewall

# Kernel hardening only
ansible-playbook playbook.yml --tags kernel

# Audit framework only
ansible-playbook playbook.yml --tags audit
```

### Check Status

```bash
./scripts/check-status.sh
```

### Optional: Use Community Hardening Roles

Enable community roles in `playbook.yml`:

```yaml
vars:
  omen_enable_community_hardening: true
```

Then install them:

```bash
ansible-galaxy install -r requirements.yml
```

## Verification

After applying hardening, verify the changes:

```bash
# Check SSH configuration
sudo sshd -T | grep -E 'permitrootlogin|passwordauthentication'

# Check firewall status
sudo ufw status verbose

# Check sysctl settings
sysctl net.ipv4.ip_forward
sysctl net.ipv4.tcp_syncookies

# Check auditd status
sudo systemctl status auditd
sudo auditctl -l
```

## Rollback

LSHC creates backups before making changes:

```bash
# Backups are stored in
ls -la /var/backups/omen/lshc/

# To restore SSH config
sudo cp /var/backups/omen/lshc/sshd_config.TIMESTAMP /etc/ssh/sshd_config
sudo systemctl restart sshd

# To restore sysctl
sudo cp /var/backups/omen/lshc/sysctl.conf.TIMESTAMP /etc/sysctl.conf
sudo sysctl -p
```

## Uninstallation

```bash
cd /opt/omen/lshc
sudo ./scripts/uninstall.sh
```

This removes OMEN-specific configurations. You'll need to manually restore SSH and firewall settings from backups.

## Security Notes

### Before Applying

1. **Test in a non-production environment first**
2. **Ensure you have console access** (not just SSH)
3. **Review all settings** in `defaults/main.yml`
4. **Backup your system**
5. **Have a recovery plan**

### After Applying

1. **Test SSH access immediately** before closing your current session
2. **Verify firewall rules** don't block required services
3. **Monitor audit logs** for unexpected entries
4. **Document what was changed**

### Common Issues

**Locked out of SSH:**
- Use console access or cloud provider's emergency console
- Restore `/etc/ssh/sshd_config` from backup
- Restart SSH service

**Firewall blocking services:**
- Add required ports to `omen_firewall_allowed_ports`
- Or use `sudo ufw allow <port>`

**Performance issues:**
- Check auditd log size: `du -sh /var/log/audit/`
- Adjust audit rules if needed
- Consider log rotation settings

## Compliance

LSHC implements controls from:

- **CIS Ubuntu Benchmark** - Sections 4 (Logging), 5 (Access Control)
- **STIG** - Network, system settings, audit requirements
- **NIST 800-53** - AC (Access Control), AU (Audit), SC (System Communications)

## Extensibility

To add custom hardening:

1. Create a new task file in `roles/omen-hardening/tasks/`
2. Include it in `main.yml`
3. Add configuration variables to `defaults/main.yml`
4. Tag appropriately for selective execution

Example:

```yaml
# roles/omen-hardening/tasks/custom.yml
---
- name: My custom hardening task
  ansible.builtin.lineinfile:
    path: /etc/some-config
    line: "security_option=enabled"
  tags:
    - custom
```

## Roadmap

### Hardening Rules

- [ ] SELinux/AppArmor mandatory access control
- [ ] Container security (Docker, Podman hardening)
- [ ] Kubernetes cluster hardening
- [ ] Database hardening (PostgreSQL, MySQL, MongoDB)
- [ ] Web server hardening (Apache, Nginx)
- [ ] Mail server hardening (Postfix, Dovecot)
- [ ] File integrity monitoring (AIDE, Tripwire)
- [ ] USB device restrictions
- [ ] Wireless interface hardening

### Compliance & Standards

- [ ] Automated CIS benchmark scoring
- [ ] STIG compliance reporting
- [ ] PCI-DSS compliance checks
- [ ] HIPAA security controls
- [ ] ISO 27001 alignment
- [ ] Before/after compliance reports
- [ ] Automated remediation tracking

### Operational Features

- [ ] Full rollback capability for all changes
- [ ] Incremental hardening (phased approach)
- [ ] Dry-run mode with detailed preview
- [ ] Hardening profiles (minimal, moderate, aggressive)
- [ ] Custom rule templates
- [ ] Schedule-based hardening updates
- [ ] Change approval workflows

### Integration

- [ ] Integration with Puppet/Chef/Salt
- [ ] Cloud provider integration (AWS, Azure, GCP)
- [ ] Infrastructure-as-Code templates (Terraform, CloudFormation)
- [ ] CI/CD pipeline integration
- [ ] Configuration drift detection
- [ ] Centralized policy management

### Reporting & Validation

- [ ] Detailed hardening reports (PDF, HTML)
- [ ] Continuous compliance monitoring
- [ ] Risk assessment scoring
- [ ] Historical compliance trending
- [ ] Automated vulnerability correlation
- [ ] Compliance dashboard

### Platform Support

- [ ] Debian/Ubuntu variants support
- [ ] RHEL/CentOS/Rocky Linux support
- [ ] SUSE/openSUSE support
- [ ] Fedora Server support
- [ ] ARM architecture support
- [ ] Cloud-init integration

## References

- [CIS Ubuntu Benchmark](https://www.cisecurity.org/benchmark/ubuntu_linux)
- [STIG for Ubuntu](https://public.cyber.mil/stigs/)
- [dev-sec Hardening Framework](https://dev-sec.io/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)

## Support

For issues or questions:

- Review the main [OMEN README](../README.md)
- Check Ansible playbook syntax: `ansible-playbook playbook.yml --syntax-check`
- Run in check mode first: `ansible-playbook playbook.yml --check`

