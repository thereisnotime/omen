# SSHMFA - SSH MFA Hardening with OTP

SSH two-factor authentication using Google Authenticator with secure bypass mechanism.

## Overview

SSHMFA adds an additional layer of security to SSH access by requiring both an SSH key AND a one-time password (OTP). It includes a secure temporary bypass mechanism for emergency access and user enrollment.

## Features

- **Two-Factor Authentication**: SSH key + OTP required for login
- **User Enrollment**: Easy setup process with QR codes
- **Secure Bypass**: Temporary single-use bypass with full auditing
- **Group-Based Access Control**: `omen-totp-admins` group for bypass management
- **Emergency Recovery**: Backup codes and restore procedures
- **Full Auditing**: All actions logged to syslog

## How It Works

### Normal Login Flow

1. User initiates SSH connection with private key
2. SSH key is validated (first factor)
3. User is prompted for OTP code (second factor)
4. Google Authenticator generates 6-digit code
5. User enters code
6. Access granted if both factors valid

### Bypass Flow

1. Admin grants temporary bypass for user
2. Bypass flag created in `/var/run/omen/bypass/`
3. User logs in with SSH key only (no OTP required)
4. Bypass flag automatically deleted after single use or 1 hour
5. All bypass operations logged to syslog

## Installation

### Standalone Installation

```bash
cd /path/to/omen/sshmfa
sudo ./install.sh
```

### Via Main Installer Menu

From the OMEN repository root:

```bash
cd /path/to/omen
sudo ./install.sh
# Select option 4 (SSHMFA only) or option 1 (All components)
```

**Note**: Installation does NOT enable 2FA immediately. You must enroll users first.

## User Enrollment

### Enroll a User

```bash
# Using unified shell script (standalone)
sudo /opt/omen/sshmfa/scripts/sshmfa.sh enroll username

# Or using Python wrapper
sudo python3 /opt/omen/sshmfa/sshmfa.py enroll username
```

The enrollment process:

1. Generates a secret key
2. Displays QR code in terminal
3. Provides backup emergency codes
4. Creates `~/.google_authenticator` file

### User Setup Steps

1. Install Google Authenticator app on phone:
   - [Android](https://play.google.com/store/apps/details?id=com.google.android.apps.authenticator2)
   - [iOS](https://apps.apple.com/app/google-authenticator/id388497605)

2. During enrollment, scan the QR code with the app

3. Save emergency scratch codes in a secure location

4. Test OTP generation before enabling 2FA system-wide

## Enabling 2FA

**⚠️ WARNING**: Always enroll at least one user before enabling 2FA!

```bash
# Using unified shell script
sudo /opt/omen/sshmfa/scripts/sshmfa.sh enable
```

This script:

- Backs up current SSH configuration
- Modifies `/etc/ssh/sshd_config`
- Updates PAM configuration in `/etc/pam.d/sshd`
- Restarts SSH service

### What Gets Changed

**`/etc/ssh/sshd_config`:**

```text
ChallengeResponseAuthentication yes
UsePAM yes
AuthenticationMethods publickey,keyboard-interactive
```

**`/etc/pam.d/sshd`:**

- Adds bypass check module
- Adds Google Authenticator PAM module
- Configures with `nullok` for gradual rollout

## Disabling 2FA

```bash
# Using unified shell script
sudo /opt/omen/sshmfa/scripts/sshmfa.sh disable
```

This restores original configurations from backups.

## Bypass Mechanism

### Security Design

The bypass mechanism is designed with security in mind:

1. **Group-Based Access**: Only root or `omen-totp-admins` members can grant bypasses
2. **Single-Use**: Bypass is automatically deleted after one login
3. **Time-Limited**: Expires after 1 hour maximum
4. **Temporary Storage**: Flags stored in `/var/run/omen/bypass/` (tmpfs, lost on reboot)
5. **Full Auditing**: All bypass operations logged to syslog with auth facility

### Grant Bypass

```bash
# Using unified shell script (standalone)
sudo /opt/omen/sshmfa/scripts/sshmfa.sh bypass-grant username

# Or using Python wrapper
sudo python3 /opt/omen/sshmfa/sshmfa.py bypass-grant username
```

**Use Cases:**

- User lost/reset phone
- OTP app malfunction
- Emergency access needed
- New phone setup

### List Active Bypasses

```bash
# Using unified shell script
sudo /opt/omen/sshmfa/scripts/sshmfa.sh bypass-list

# Or using Python wrapper
sudo python3 /opt/omen/sshmfa/sshmfa.py bypass-list

# Or check directory manually
sudo ls -la /var/run/omen/bypass/
```

### Revoke Bypass

```bash
# Using unified shell script
sudo /opt/omen/sshmfa/scripts/sshmfa.sh bypass-revoke username

# Or using Python wrapper
sudo python3 /opt/omen/sshmfa/sshmfa.py bypass-revoke username
```

### Add Users to Bypass Admin Group

```bash
# Allow user to grant bypasses
sudo usermod -aG omen-totp-admins username

# Verify membership
groups username
```

## Emergency Recovery

### Scenario 1: Lost OTP Device

1. **If you have bypass admin access**:

   ```bash
   sudo /opt/omen/sshmfa/scripts/sshmfa.sh bypass-grant username
   ```

2. **If you have console access**:

   ```bash
   # Grant bypass from console
   sudo /opt/omen/sshmfa/scripts/sshmfa.sh bypass-grant username
   ```

3. **If you have emergency codes**:

   - Use one of the scratch codes instead of OTP

### Scenario 2: Complete Lockout

If you're locked out and can't access console:

1. **Via cloud provider console** (AWS, Azure, GCP):

   ```bash
   # Disable 2FA temporarily
   sudo /opt/omen/sshmfa/scripts/sshmfa.sh disable
   ```

2. **Boot into recovery mode**:

   ```bash
   # Mount filesystem
   mount /dev/sda1 /mnt

   # Restore SSH config
   cp /mnt/etc/ssh/sshd_config.pre-omen-2fa /mnt/etc/ssh/sshd_config
   cp /mnt/etc/pam.d/sshd.pre-omen-2fa /mnt/etc/pam.d/sshd
   ```

3. **Remove user's OTP config**:

   ```bash
   rm /home/username/.google_authenticator
   ```

### Scenario 3: Emergency Scratch Codes

During enrollment, users receive 5 scratch codes. These can be used instead of OTP:

```text
# At OTP prompt, enter a scratch code instead
Verification code: 12345678
```

Each code works once only.

## Security Considerations

### Strengths

✅ Significantly reduces risk of credential theft
✅ Protects against SSH key compromise alone
✅ Industry-standard TOTP algorithm (RFC 6238)
✅ Offline OTP generation (no network required)
✅ Bypass mechanism fully audited

### Weaknesses & Mitigations

⚠️ **User loses phone**

- Mitigation: Emergency scratch codes
- Mitigation: Bypass mechanism
- Mitigation: Multiple enrollment methods

⚠️ **Bypass could be abused**

- Mitigation: Group-based access control
- Mitigation: Single-use, time-limited
- Mitigation: Full syslog auditing
- Mitigation: Stored in tmpfs (not persistent)

⚠️ **PAM misconfiguration could lock everyone out**

- Mitigation: Backups created automatically
- Mitigation: `nullok` allows gradual rollout
- Mitigation: Console access always available

### Best Practices

1. **Enroll Administrators First**: Ensure admins are enrolled before regular users
2. **Test Thoroughly**: Test enrollment and login in dev environment
3. **Document Recovery**: Ensure all admins know recovery procedures
4. **Secure Scratch Codes**: Users should store codes securely (password manager)
5. **Monitor Bypass Usage**: Regularly review syslog for bypass activity
6. **Rotate Secrets**: Re-enroll users periodically
7. **Educate Users**: Provide clear instructions and support

## Gradual Rollout

For large deployments, use a gradual approach:

### Phase 1: Optional 2FA (`nullok`)

The default configuration uses `nullok`, allowing login without OTP if not enrolled:

```text
auth required pam_google_authenticator.so nullok
```

**Advantages:**

- Enroll users gradually
- Users can test without risk
- No service disruption

### Phase 2: Mandatory 2FA

After all users are enrolled, remove `nullok`:

```bash
sudo nano /etc/pam.d/sshd

# Remove 'nullok' from the line:

# auth required pam_google_authenticator.so
```

**Advantages:**

- Full security enforcement
- No bypasses except explicit grants

## Monitoring & Auditing

### Check Syslog for 2FA Activity

```bash
# View all SSHMFA events
sudo grep omen-sshmfa /var/log/auth.log

# View bypass grants
sudo grep "bypass granted" /var/log/auth.log

# View bypass usage
sudo grep "bypass used" /var/log/auth.log

# View OTP failures
sudo grep "google_authenticator" /var/log/auth.log
```

### Audit Events

All SSHMFA operations generate syslog entries:

```text
# Bypass granted
omen-sshmfa: 2FA bypass granted for user alice by admin

# Bypass used
omen-sshmfa: 2FA bypass used for user alice

# Bypass revoked
omen-sshmfa: 2FA bypass revoked for user alice by admin
```

## Troubleshooting

### User Can't Login After Enrolling

1. **Check if user has valid SSH key**:

   ```bash
   # Must have key in ~/.ssh/authorized_keys
   ```

2. **Verify OTP code is being generated**:

   - Codes change every 30 seconds
   - Ensure phone time is synchronized

3. **Check PAM logs**:

   ```bash
   sudo grep pam_google_authenticator /var/log/auth.log
   ```

4. **Verify `.google_authenticator` file**:

   ```bash
   ls -la /home/username/.google_authenticator

   # Should be owned by user, mode 600
   ```

### Time Synchronization Issues

OTP codes are time-based. If codes don't work:

```bash
# Check system time
timedatectl

# Sync time
sudo timedatectl set-ntp true

# Or sync manually
sudo ntpdate pool.ntp.org
```

### Wrong OTP Every Time

1. **Phone time is wrong**: Sync phone clock
2. **Wrong secret**: Re-enroll user
3. **Multiple enrollments**: Only latest `.google_authenticator` is valid

### SSH Service Won't Restart

```bash
# Check sshd configuration
sudo sshd -t

# View detailed error
sudo systemctl status sshd -l

# Restore from backup if needed
sudo cp /etc/ssh/sshd_config.pre-omen-2fa /etc/ssh/sshd_config
sudo systemctl restart sshd
```

## Uninstallation

```bash
cd /opt/omen/sshmfa
sudo ./uninstall.sh
```

This will:

1. Disable 2FA
2. Restore original configurations
3. Remove bypass directory
4. Preserve backups

**Note**: User `.google_authenticator` files are NOT deleted. Users must remove them manually if desired.

## Technical Details

### PAM Module Flow

```text
1. pam_exec.so → check-bypass.sh
   - Success: Skip OTP, allow login
   - Failure: Continue to next module

2. pam_google_authenticator.so nullok
   - Prompts for OTP
   - Validates against user's secret
   - nullok: allows login if not enrolled

3. @include common-auth
   - Standard system authentication
```

### File Locations

- User secrets: `/home/username/.google_authenticator`
- Bypass flags: `/var/run/omen/bypass/2fa-username-timestamp-random`
- SSH config: `/etc/ssh/sshd_config`
- PAM config: `/etc/pam.d/sshd`
- Backups: `/etc/ssh/sshd_config.pre-omen-2fa`, `/etc/pam.d/sshd.pre-omen-2fa`
- Scripts: `/opt/omen/sshmfa/scripts/`

### Bypass File Format

```text
username: alice
granted_by: admin
granted_at: 2024-10-22T10:30:00+00:00
expires_at: 2024-10-22T11:30:00+00:00
```

## Roadmap

### Authentication Methods

- [ ] WebAuthn/FIDO2 support (passwordless authentication)
- [ ] Hardware token support (YubiKey, Titan Security Key)
- [ ] Biometric authentication integration
- [ ] SMS-based OTP (with security warnings)
- [ ] Email-based OTP backup method
- [ ] Duo Security integration
- [ ] Push notification authentication
- [ ] Smart card (PIV/CAC) support

### User Management

- [ ] Bulk user enrollment tool
- [ ] Self-service enrollment portal
- [ ] QR code regeneration
- [ ] User 2FA status dashboard
- [ ] Per-user 2FA policies (enforce/optional/exempt)
- [ ] Grace period for new enrollments
- [ ] Automated enrollment reminders
- [ ] User authentication history

### Administration

- [ ] Web-based admin interface
- [ ] Centralized user management
- [ ] Group-based 2FA policies
- [ ] Conditional access rules (IP-based, time-based)
- [ ] Emergency bypass codes with expiration
- [ ] Admin action audit reports
- [ ] Delegated administration
- [ ] Automated compliance reports

### Security Enhancements

- [ ] Geolocation-based access control
- [ ] Device fingerprinting
- [ ] Anomaly detection (impossible travel, etc.)
- [ ] Session recording and replay
- [ ] Failed authentication alerting
- [ ] Brute force protection
- [ ] Account lockout policies
- [ ] IP whitelist/blacklist
- [ ] Time-based access restrictions

### Bypass Mechanism Improvements

- [ ] Configurable bypass duration
- [ ] Multi-approval bypass workflows
- [ ] Bypass usage notifications
- [ ] Bypass audit trail export
- [ ] Automated bypass expiration alerts
- [ ] Emergency break-glass procedures
- [ ] Bypass justification logging
- [ ] Bypass analytics and reporting

### Integration

- [ ] Active Directory / LDAP integration
- [ ] SSO (SAML, OAuth) integration
- [ ] RADIUS server support
- [ ] Centralized authentication services
- [ ] API for external enrollment systems
- [ ] Webhook notifications for events
- [ ] SIEM integration
- [ ] Cloud identity provider sync

### User Experience

- [ ] Mobile app for enrollment and OTP
- [ ] Browser extension for easier authentication
- [ ] Remember device functionality
- [ ] Push notification approval
- [ ] Automated secret backup to secure storage
- [ ] Multi-device enrollment
- [ ] OTP synchronization across devices
- [ ] Offline authentication support

### Monitoring & Reporting

- [ ] Authentication success/failure metrics
- [ ] 2FA adoption reporting
- [ ] User enrollment status dashboard
- [ ] Bypass usage analytics
- [ ] Security event timeline
- [ ] Compliance audit reports
- [ ] Real-time authentication monitoring
- [ ] Historical trend analysis

### Recovery & Business Continuity

- [ ] Automated backup of user secrets
- [ ] Disaster recovery procedures
- [ ] Secret escrow for emergencies
- [ ] Encrypted secret storage
- [ ] Multi-region backup support
- [ ] Recovery key generation
- [ ] Administrator recovery procedures

### Platform Support

- [ ] Debian/Ubuntu variants
- [ ] RHEL/CentOS/Rocky Linux
- [ ] macOS SSH server support
- [ ] Windows OpenSSH server
- [ ] Cloud provider integrations
- [ ] Container-based deployments

### Standards & Compliance

- [ ] NIST 800-63B compliance
- [ ] PCI-DSS MFA requirements
- [ ] SOC 2 compliance features
- [ ] HIPAA authentication requirements
- [ ] ISO 27001 alignment
- [ ] GDPR privacy considerations

## References

- [libpam-google-authenticator](https://github.com/google/google-authenticator-libpam)
- [RFC 6238 - TOTP](https://tools.ietf.org/html/rfc6238)
- [PAM Configuration Guide](https://www.linux-pam.org/Linux-PAM-html/)
- [OpenSSH Documentation](https://www.openssh.com/manual.html)

## Support

For issues or questions:

- Test login with verbose output: `ssh -vvv user@host`
- Check PAM logs: `grep pam /var/log/auth.log`
- Verify bypass status: `ls -la /var/run/omen/bypass/`
- Review SSHMFA logs: `grep omen-sshmfa /var/log/auth.log`
