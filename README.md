# OMEN

OMEN (Observation, Monitoring, Enforcement & Notification) is a simple tool for basic Linux hardening and security monitoring.

The tool consists of three main components:

1. Linux security hardeninng configurator (LSHC).
2. Suspicious activity monitoring system (SAMS).
3. SSH MFA hardening with OTP `via libpam-google-authenticator` (SHMFA).

**NOTE:** This is a work in progress and is not yet ready for production use.
**NOTE:** Currently for some specific reasons it has been tested only on Ubuntu 22.04.

Each tool can be installed/setup independently or via the OMEN installer.

## Table of Contents

- [OMEN](#omen)
  - [Table of Contents](#table-of-contents)
  - [Component:Linux Security Hardening Configurator (LSHC)](#componentlinux-security-hardening-configurator-lshc)
  - [Component: Suspicious Activity Monitoring System (SAMS)](#component-suspicious-activity-monitoring-system-sams)
  - [Component: SSH MFA Hardening with OTP (SHMFA)](#component-ssh-mfa-hardening-with-otp-shmfa)
  - [Roadmap](#roadmap)

## Component:Linux Security Hardening Configurator (LSHC)

For more information please check the [LSHC README](lshc/README.md).

## Component: Suspicious Activity Monitoring System (SAMS)

For more information please check the [SAMS README](sams/README.md).

## Component: SSH MFA Hardening with OTP (SHMFA)

For more information please check the [SHMFA README](shmfa/README.md).

## Roadmap

When daydreaming about the future of OMEN, I envision a tool that can be used to:

- [ ] Test on more distributions, architectures and versions.
- [ ] Do proper uninstall of the hardening configuration.
- [ ] Add multiple testing machines.
- [ ] Add GH Actions to lint/validate Vagrant/Bash/Ansible and the rest of the setup.
