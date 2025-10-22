# SAMS - Suspicious Activity Monitoring System

Real-time security event detection and alerting for Linux systems.

## Overview

SAMS is a modular security monitoring system that detects suspicious activities and sends alerts through multiple channels. It's designed to catch security events that traditional tools might miss.

## Monitored Events

### 1. Authentication Failures ⭐⭐⭐ **Critical**

**Detects:**

- Multiple failed SSH login attempts (brute force)
- Failed sudo password attempts
- Failed su attempts

**Why it's important:**

Authentication failures are often the first sign of an attack. Detecting brute force attempts early allows you to block attackers before they succeed.

**Configuration:**

```json
"auth_failures": {
  "enabled": true,
  "threshold": 5,        // Alert after 5 failures
  "timeframe": 300       // Within 5 minutes
}
```

### 2. Privilege Escalation ⭐⭐⭐ **Critical**

**Detects:**

- Unauthorized sudo attempts (user not in sudoers)
- New SUID/SGID files (potential backdoors)
- Suspicious use of su command

**Why it's important:**

Privilege escalation is a key step in most attacks. Detecting these attempts prevents attackers from gaining root access.

**Configuration:**

```json
"privilege_escalation": {
  "enabled": true,
  "timeframe": 300,
  "check_suid": true
}
```

### 3. Suspicious Commands ⭐⭐⭐ **Critical**

**Detects:**

- Reverse shell attempts (bash, netcat, python, perl)
- Network reconnaissance (nmap, masscan)
- Remote code execution (curl/wget piped to bash)
- Credential dumping attempts
- Cryptomining software
- Obfuscated execution (base64 encoded commands)

**Why it's important:**

Attackers often use specific tools and techniques. Detecting these command patterns catches attacks in progress.

**Configuration:**

```json
"suspicious_commands": {
  "enabled": true,
  "timeframe": 300,
  "use_auditd": true
}
```

### 4. Critical File Modifications ⭐⭐⭐ **Critical**

**Detects:**

- Changes to /etc/passwd, /etc/shadow, /etc/group
- Modifications to /etc/sudoers
- SSH configuration changes
- New or modified cron jobs
- Changes to authorized_keys files

**Why it's important:**

These files control system access and security. Unauthorized changes indicate compromise or privilege escalation.

**Configuration:**

```json
"file_changes": {
  "enabled": true,
  "hash_file": "/var/lib/omen/file_hashes.json",
  "use_auditd": true,
  "timeframe": 300
}
```

### 5. Network Anomalies ⭐⭐ **Important**

**Detects:**

- New unexpected listening ports
- Connections to suspicious ports (IRC, known malware ports)
- Possible port scans (high connection attempt rates)

**Why it's important:**

Network anomalies can indicate malware, backdoors, or C2 communication. Early detection allows rapid response.

**Configuration:**

```json
"network_anomalies": {
  "enabled": true,
  "expected_ports": [22, 80, 443],
  "alert_on_new_listeners": true
}
```

## Alerting

SAMS supports multiple alert destinations:

### Slack

```json
{
  "type": "slack",
  "enabled": true,
  "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
  "channel": "#security-alerts",
  "username": "OMEN Security",
  "icon_emoji": ":shield:"
}
```

### Mattermost

```json
{
  "type": "mattermost",
  "enabled": true,
  "url": "https://mattermost.example.com/hooks/YOUR_WEBHOOK_ID",
  "channel": "security-alerts",
  "username": "OMEN Security"
}
```

### Telegram

```json
{
  "type": "telegram",
  "enabled": true,
  "bot_token": "YOUR_BOT_TOKEN",
  "chat_id": "YOUR_CHAT_ID"
}
```

### Custom Webhook

```json
{
  "type": "webhook",
  "enabled": true,
  "url": "https://example.com/webhook",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_TOKEN"
  },
  "body_template": {
    "alert_type": "security",
    "message": "{event.message}",
    "severity": "{event.severity}"
  }
}
```

## Installation

### Standalone Installation

```bash
cd /path/to/omen/sams
sudo ./install.sh
```

### Via OMEN Installer

```bash
sudo omen install sams
```

## Configuration

1. Copy the example configuration:

```bash
sudo cp /opt/omen/sams/config.json.example /opt/omen/sams/config.json
```

1. Edit the configuration:

```bash
sudo nano /opt/omen/sams/config.json
```

1. Configure at least one alerting webhook (or leave disabled for log-only mode)

## Usage

### Start/Stop Service

```bash
# Start SAMS
sudo systemctl start omen-sams

# Stop SAMS
sudo systemctl stop omen-sams

# Enable on boot
sudo systemctl enable omen-sams

# Check status
sudo systemctl status omen-sams
```

### View Logs

```bash
# View service logs
sudo journalctl -u omen-sams -f

# View security event logs (JSON format)
sudo tail -f /var/log/omen/sams.log

# Parse JSON logs
sudo jq '.' /var/log/omen/sams.log

# Filter by severity
sudo jq 'select(.severity == "critical")' /var/log/omen/sams.log
```

### Test Alert

```bash
# Send a test alert to verify alerting configuration
sudo python3 /opt/omen/sams/sams.py --test-alert
```

### Manual Run (for testing)

```bash
# Run once without systemd
sudo python3 /opt/omen/sams/sams.py -c /opt/omen/sams/config.json
```

## SIEM Integration

SAMS logs are in structured JSON format for easy ingestion by SIEMs:

### Splunk

```bash
# Configure Splunk Universal Forwarder
[monitor:///var/log/omen/sams.log]
sourcetype = _json
index = security
```

### Elastic Stack (ELK)

```yaml
# Filebeat configuration
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/omen/sams.log
  json.keys_under_root: true
  json.add_error_key: true
```

### Telegraf

```toml
# Telegraf configuration
[[inputs.tail]]
  files = ["/var/log/omen/sams.log"]
  data_format = "json"
  json_string_fields = ["message", "event_type", "source"]
  tag_keys = ["severity", "event_type"]
```

## Event Format

Events are logged in JSON format:

```json
{
  "timestamp": "2024-10-22T10:30:45.123456Z",
  "event_type": "auth_failure",
  "severity": "high",
  "message": "Multiple SSH authentication failures detected from 192.168.1.100",
  "source": "localhost",
  "details": {
    "source_ip": "192.168.1.100",
    "username": "admin",
    "failure_count": 5,
    "threshold": 5,
    "service": "ssh"
  }
}
```

## Extending SAMS

### Adding a Custom Detector

1. Create a new detector in `detectors/`:

    ```python
    # detectors/custom_detector.py
    from sams.detectors.base import BaseDetector, SecurityEvent

    class CustomDetector(BaseDetector):
        def detect(self):
            if not self.is_enabled():
                return []

            events = []

            # Your detection logic here

            return events
    ```

2. Register in `sams.py`:

    ```python
    from sams.detectors.custom_detector import CustomDetector

    # In _initialize_detectors():
    "custom_detector": CustomDetector,
    ```

3. Add configuration:

    ```json
    "detectors": {
    "custom_detector": {
        "enabled": true
    }
    }
    ```

### Adding a Custom Alerter

1. Create a new alerter in `alerters/`:

    ```python
    # alerters/custom_alerter.py
    from sams.alerters.base import BaseAlerter

    class CustomAlerter(BaseAlerter):
        def send_alert(self, event):

            # Your alerting logic here
            return True
    ```

2. Register in `sams.py`:

    ```python
    from sams.alerters.custom_alerter import CustomAlerter

    # In _initialize_alerters():
    "custom": CustomAlerter,
    ```

## Performance Tuning

### Adjust Check Interval

```json
{
  "check_interval": 60  // Check every 60 seconds
}
```

Longer intervals reduce CPU usage but increase detection latency.

### Disable Expensive Detectors

```json
{
  "detectors": {
    "network_anomalies": {
      "enabled": false  // Disable if not needed
    }
  }
}
```

### Rate Limiting

SAMS automatically implements rate limiting to prevent alert storms. Configure thresholds per detector.

## Troubleshooting

### SAMS Not Starting

```bash
# Check for errors
sudo journalctl -u omen-sams -n 50

# Verify configuration
sudo python3 /opt/omen/sams/sams.py -c /opt/omen/sams/config.json --test-alert

# Check permissions
ls -la /var/log/omen/sams.log
```

### No Events Being Detected

```bash
# Verify auditd is running
sudo systemctl status auditd

# Check if detectors are enabled
sudo jq '.detectors' /opt/omen/sams/config.json

# Test manually
sudo python3 /opt/omen/sams/sams.py -c /opt/omen/sams/config.json
```

### Alerts Not Sending

```bash
# Test alert delivery
sudo python3 /opt/omen/sams/sams.py --test-alert

# Check webhook configuration
sudo jq '.alerting.webhooks' /opt/omen/sams/config.json

# Verify network connectivity
curl -X POST https://your-webhook-url
```

## Uninstallation

```bash
cd /opt/omen/sams
sudo ./uninstall.sh
```

This stops the service and removes the systemd unit file. Logs and configuration are preserved.

## Security Notes

- SAMS runs as root to access system logs and auditd
- All configuration is stored in `/opt/omen/sams/config.json` (sensitive!)
- Webhook URLs may contain secrets - protect the config file
- Logs contain security-sensitive information
- Consider encrypting logs at rest in production

## Best Practices

1. **Alert Fatigue**: Configure thresholds to avoid too many alerts
2. **Test First**: Use `--test-alert` to verify alerting before deploying
3. **Monitor SAMS**: Set up monitoring for the SAMS service itself
4. **Log Retention**: Configure log rotation for `/var/log/omen/sams.log`
5. **Review Regularly**: Periodically review alert patterns and adjust thresholds
6. **Incident Response**: Have a playbook for each alert type

## Roadmap

### Detection Capabilities

- [ ] Process behavior analysis (unusual parent-child relationships)
- [ ] Memory analysis for rootkit detection
- [ ] Container escape detection
- [ ] Cryptojacking detection (CPU patterns, mining pools)
- [ ] Data exfiltration detection (large uploads, DNS tunneling)
- [ ] Lateral movement detection
- [ ] Persistence mechanism detection
- [ ] Web shell detection
- [ ] SQL injection attempt detection
- [ ] Log tampering detection

### Machine Learning & AI

- [ ] Baseline behavior learning
- [ ] Anomaly detection using ML models
- [ ] User behavior analytics (UEBA)
- [ ] Automated threat classification
- [ ] Predictive threat detection
- [ ] False positive reduction using ML

### Threat Intelligence

- [ ] Integration with threat intelligence feeds (AlienVault OTX, etc.)
- [ ] IP reputation checking
- [ ] Domain reputation checking
- [ ] Known malware hash checking
- [ ] CVE correlation with detected activities
- [ ] IOC (Indicators of Compromise) matching

### Alerting & Response

- [ ] PagerDuty integration
- [ ] ServiceNow integration
- [ ] Jira automatic ticket creation
- [ ] Email alerting
- [ ] SMS alerting
- [ ] Voice call alerts for critical events
- [ ] Alert grouping and deduplication
- [ ] Automated response actions (block IP, kill process)
- [ ] Incident timeline generation

### Performance & Scale

- [ ] Distributed deployment support
- [ ] Event buffering and queuing
- [ ] Database backend for event storage
- [ ] Event indexing and search
- [ ] Performance monitoring and tuning
- [ ] Resource usage optimization
- [ ] Multi-threaded detection
- [ ] Event sampling for high-volume systems

### Integration & Interoperability

- [ ] Splunk forwarder integration
- [ ] Elasticsearch native output
- [ ] Kafka event streaming
- [ ] Syslog output format
- [ ] CEF (Common Event Format) support
- [ ] STIX/TAXII threat intelligence import
- [ ] SOAR platform integration
- [ ] Cloud SIEM integration (AWS Security Hub, Azure Sentinel)

### User Interface

- [ ] Web dashboard for event viewing
- [ ] Real-time event streaming UI
- [ ] Alert management interface
- [ ] Detector configuration UI
- [ ] Rule builder interface
- [ ] Historical event search
- [ ] Reporting and analytics dashboard
- [ ] Mobile app for alerts

### Analysis & Reporting

- [ ] Attack chain reconstruction
- [ ] Security posture reports
- [ ] Compliance reporting
- [ ] Trend analysis and visualization
- [ ] Executive summaries
- [ ] Forensic timeline generation
- [ ] Threat hunting queries
- [ ] IOC extraction from events

### Rule Management

- [ ] Sigma rule support
- [ ] YARA rule integration
- [ ] Custom rule language
- [ ] Rule testing framework
- [ ] Rule version control
- [ ] Community rule sharing
- [ ] Automated rule updates

### Deployment & Operations

- [ ] Docker container packaging
- [ ] Kubernetes deployment manifests
- [ ] High availability setup
- [ ] Backup and restore procedures
- [ ] Upgrade path documentation
- [ ] Health monitoring
- [ ] Audit logging of SAMS itself

## References

- [MITRE ATT&CK Framework](https://attack.mitre.org/)
- [Linux Auditd](https://linux-audit.com/configuring-and-auditing-linux-systems-with-audit-daemon/)
- [Webhook.site](https://webhook.site/) - For testing webhooks

## Support

For issues or questions:

- Review service logs: `journalctl -u omen-sams -f`
- Check event logs: `tail -f /var/log/omen/sams.log`
- Test configuration: `python3 sams.py --test-alert`
