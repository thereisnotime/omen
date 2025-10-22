#!/usr/bin/env python3
"""
SAMS Telegram Alerter - Send alerts to Telegram using Bot API.
"""

import requests
from typing import Dict, Any

from sams.alerters.base import BaseAlerter


class TelegramAlerter(BaseAlerter):
    """Telegram alerter using Bot API."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Telegram alerter.
        
        Config options:
            bot_token: Telegram Bot API token (required)
            chat_id: Telegram chat ID (required)
            parse_mode: Message parse mode (default: "HTML")
            timeout: Request timeout in seconds (default: 10)
        """
        super().__init__(config)
        self.bot_token = config.get("bot_token")
        self.chat_id = config.get("chat_id")
        self.parse_mode = config.get("parse_mode", "HTML")
        self.timeout = config.get("timeout", 10)
        
        if not self.bot_token or not self.chat_id:
            self.enabled = False
        
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    def send_alert(self, event: Dict[str, Any]) -> bool:
        """Send alert to Telegram."""
        if not self.is_enabled():
            return False
        
        try:
            message = self._format_telegram_message(event)
            
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": self.parse_mode,
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            return True
        
        except Exception as e:
            # Note: Using print here intentionally as logger may not be configured
            # in alerter context. This goes to service journal.
            import sys
            print(f"Telegram alerter error: {e}", file=sys.stderr)
            return False
    
    def _format_telegram_message(self, event: Dict[str, Any]) -> str:
        """Format Telegram message in HTML."""
        severity = event.get("severity", "unknown")
        emoji = self.format_severity_emoji(severity)
        
        # Build message
        lines = [
            f"<b>{emoji} OMEN Security Alert</b>",
            "",
            f"<b>Severity:</b> {severity.upper()}",
            f"<b>Event Type:</b> {event.get('event_type', 'unknown')}",
            f"<b>Source:</b> {event.get('source', 'localhost')}",
            "",
            f"<b>Message:</b>",
            event.get('message', 'Security event detected'),
            "",
        ]
        
        # Add details
        details = event.get("details", {})
        if details:
            lines.append("<b>Details:</b>")
            for key, value in details.items():
                key_formatted = key.replace("_", " ").title()
                lines.append(f"• {key_formatted}: {value}")
            lines.append("")
        
        # Add timestamp
        lines.append(f"<i>Time: {event.get('timestamp', 'unknown')}</i>")
        
        return "\n".join(lines)

