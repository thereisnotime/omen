"""
SAMS Detectors - Modular security event detectors.
"""

from detectors.base import BaseDetector
from detectors.auth_failures import AuthFailureDetector
from detectors.privilege_escalation import PrivilegeEscalationDetector
from detectors.suspicious_commands import SuspiciousCommandDetector
from detectors.file_changes import FileChangeDetector
from detectors.network_anomalies import NetworkAnomalyDetector

__all__ = [
    "BaseDetector",
    "AuthFailureDetector",
    "PrivilegeEscalationDetector",
    "SuspiciousCommandDetector",
    "FileChangeDetector",
    "NetworkAnomalyDetector",
]

