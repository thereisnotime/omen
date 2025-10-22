#!/usr/bin/env python3
"""
SAMS Base Detector - Abstract base class for all detectors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class SecurityEvent:
    """Represents a detected security event."""
    
    def __init__(
        self,
        event_type: str,
        severity: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ):
        """
        Initialize security event.
        
        Args:
            event_type: Type of event (e.g., "auth_failure", "privilege_escalation")
            severity: Severity level (low, medium, high, critical)
            message: Human-readable message
            details: Additional event details
            source: Source of the event (e.g., hostname, service)
        """
        self.event_type = event_type
        self.severity = severity
        self.message = message
        self.details = details or {}
        self.source = source or "localhost"
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "severity": self.severity,
            "message": self.message,
            "source": self.source,
            "details": self.details,
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class BaseDetector(ABC):
    """Abstract base class for security event detectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize detector.
        
        Args:
            config: Detector configuration
        """
        self.config = config
        self.enabled = config.get("enabled", True)
        self.name = self.__class__.__name__
    
    @abstractmethod
    def detect(self) -> List[SecurityEvent]:
        """
        Detect security events.
        
        Returns:
            List of detected SecurityEvent objects
        """
        pass
    
    def is_enabled(self) -> bool:
        """Check if detector is enabled."""
        return self.enabled
    
    def get_name(self) -> str:
        """Get detector name."""
        return self.name

