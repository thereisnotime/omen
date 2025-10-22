#!/usr/bin/env python3
"""
SAMS Slack Alerter - Send alerts to Slack using Incoming Webhooks.
"""

import requests
from typing import Dict, Any

from sams.alerters.base import BaseAlerter


class SlackAlerter(BaseAlerter):
    """Slack alerter using Incoming Webhooks."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Slack alerter.
        
        Config options:
            url: Slack Incoming Webhook URL (required)
            channel: Override default channel (optional)
            username: Bot username (default: "OMEN Security")
            icon_emoji: Bot icon emoji (default: ":shield:")
            timeout: Request timeout in seconds (default: 10)
        """
        super().__init__(config)
        self.url = config.get("url")
        self.channel = config.get("channel")
        self.username = config.get("username", "OMEN Security")
        self.icon_emoji = config.get("icon_emoji", ":shield:")
        self.timeout = config.get("timeout", 10)
        
        if not self.url:
            self.enabled = False
    
    def send_alert(self, event: Dict[str, Any]) -> bool:
        """Send alert to Slack."""
        if not self.is_enabled():
            return False
        
        try:
            payload = self._format_slack_message(event)
            
            response = requests.post(
                self.url,
                json=payload,
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            return True
        
        except Exception as e:
            # Note: Using print here intentionally as logger may not be configured
            # in alerter context. This goes to service journal.
            import sys
            print(f"Slack alerter error: {e}", file=sys.stderr)
            return False
    
    def _format_slack_message(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format Slack message with attachments."""
        severity = event.get("severity", "unknown")
        emoji = self.format_severity_emoji(severity)
        color = self.format_severity_color(severity)
        
        # Build fields for attachment
        fields = []
        
        # Add event type
        fields.append({
            "title": "Event Type",
            "value": event.get("event_type", "unknown"),
            "short": True,
        })
        
        # Add severity
        fields.append({
            "title": "Severity",
            "value": severity.upper(),
            "short": True,
        })
        
        # Add source
        fields.append({
            "title": "Source",
            "value": event.get("source", "localhost"),
            "short": True,
        })
        
        # Add timestamp
        fields.append({
            "title": "Timestamp",
            "value": event.get("timestamp", "unknown"),
            "short": True,
        })
        
        # Add details
        details = event.get("details", {})
        for key, value in details.items():
            if len(fields) < 10:  # Limit number of fields
                fields.append({
                    "title": key.replace("_", " ").title(),
                    "value": str(value),
                    "short": True,
                })
        
        # Build attachment
        attachment = {
            "color": color,
            "title": f"{emoji} OMEN Security Alert",
            "text": event.get("message", "Security event detected"),
            "fields": fields,
            "footer": "OMEN SAMS",
            "ts": int(event.get("timestamp", "0").replace("Z", "").split("T")[0].replace("-", "")),
        }
        
        # Build payload
        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [attachment],
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        return payload

