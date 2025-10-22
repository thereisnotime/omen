#!/usr/bin/env python3
"""
SAMS Generic Webhook Alerter - Send alerts to custom webhooks.
"""

import requests
from typing import Dict, Any
import json

from alerters.base import BaseAlerter


class WebhookAlerter(BaseAlerter):
    """Generic webhook alerter with customizable headers and body."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize webhook alerter.
        
        Config options:
            url: Webhook URL (required)
            headers: Custom headers dictionary (optional)
            body_template: Custom body template (optional)
            method: HTTP method (default: POST)
            timeout: Request timeout in seconds (default: 10)
        """
        super().__init__(config)
        self.url = config.get("url")
        self.headers = config.get("headers", {"Content-Type": "application/json"})
        self.body_template = config.get("body_template")
        self.method = config.get("method", "POST").upper()
        self.timeout = config.get("timeout", 10)
        
        if not self.url:
            self.enabled = False
    
    def send_alert(self, event: Dict[str, Any]) -> bool:
        """Send alert to webhook."""
        if not self.is_enabled():
            return False
        
        try:
            # Prepare payload
            if self.body_template:
                # Use custom template
                payload = self._apply_template(self.body_template, event)
            else:
                # Use default format
                payload = self._format_default_payload(event)
            
            # Send request
            if self.method == "POST":
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout,
                )
            elif self.method == "PUT":
                response = requests.put(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout,
                )
            else:
                return False
            
            response.raise_for_status()
            return True
        
        except Exception as e:
            # Log error but don't raise
            # Note: Using print here intentionally as logger may not be configured
            # in alerter context. This goes to service journal.
            import sys
            print(f"Webhook alerter error: {e}", file=sys.stderr)
            return False
    
    def _format_default_payload(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format default webhook payload."""
        return {
            "alert": "OMEN Security Alert",
            "event": event,
        }
    
    def _apply_template(self, template: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
        """Apply template with event data."""
        # Simple template variable replacement
        # In production, you might want to use Jinja2 or similar
        result = {}
        
        for key, value in template.items():
            if isinstance(value, str):
                # Replace {event.field} with actual values
                for event_key, event_value in event.items():
                    placeholder = f"{{event.{event_key}}}"
                    if placeholder in value:
                        value = value.replace(placeholder, str(event_value))
                result[key] = value
            else:
                result[key] = value
        
        return result

