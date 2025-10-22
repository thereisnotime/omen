"""
SAMS Detectors - Modular security event detectors.
"""

from sams.detectors.base import BaseDetector
from sams.detectors.auth_failures import AuthFailureDetector
from sams.detectors.privilege_escalation import PrivilegeEscalationDetector
from sams.detectors.suspicious_commands import SuspiciousCommandDetector
from sams.detectors.file_changes import FileChangeDetector
from sams.detectors.network_anomalies import NetworkAnomalyDetector

__all__ = [
    "BaseDetector",
    "AuthFailureDetector",
    "PrivilegeEscalationDetector",
    "SuspiciousCommandDetector",
    "FileChangeDetector",
    "NetworkAnomalyDetector",
]

