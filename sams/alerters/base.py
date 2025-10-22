#!/usr/bin/env python3
"""
SAMS Base Alerter - Abstract base class for alert delivery.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BaseAlerter(ABC):
    """Abstract base class for alerters."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize alerter.
        
        Args:
            config: Alerter configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.name = self.__class__.__name__
    
    @abstractmethod
    def send_alert(self, event: Dict[str, Any]) -> bool:
        """
        Send an alert.
        
        Args:
            event: Security event dictionary
        
        Returns:
            True if alert sent successfully, False otherwise
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if alerter is enabled."""
        return self.enabled
    
    def format_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        emojis = {
            "low": "ℹ️",
            "medium": "⚠️",
            "high": "🔥",
            "critical": "🚨",
        }
        return emojis.get(severity.lower(), "📢")
    
    def format_severity_color(self, severity: str) -> str:
        """Get color code for severity level."""
        colors = {
            "low": "#36a64f",      # Green
            "medium": "#ff9900",    # Orange
            "high": "#ff4444",      # Red
            "critical": "#cc0000",  # Dark Red
        }
        return colors.get(severity.lower(), "#808080")

