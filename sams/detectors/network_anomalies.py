#!/usr/bin/env python3
"""
SAMS Network Anomaly Detector - Detects suspicious network activity.
"""

import subprocess
import re
from typing import List, Dict, Any, Set

from detectors.base import BaseDetector, SecurityEvent


class NetworkAnomalyDetector(BaseDetector):
    """Detector for network anomalies and suspicious connections."""
    
    # Well-known ports that should normally be present
    EXPECTED_PORTS = {22, 80, 443}
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize network anomaly detector.
        
        Config options:
            expected_ports: List of expected listening ports (default: [22, 80, 443])
            alert_on_new_listeners: Alert on new listening ports (default: true)
        """
        super().__init__(config)
        self.expected_ports = set(config.get("expected_ports", [22, 80, 443]))
        self.alert_on_new_listeners = config.get("alert_on_new_listeners", True)
        self.known_listeners = self._get_listening_ports()
    
    def detect(self) -> List[SecurityEvent]:
        """Detect network anomalies."""
        if not self.is_enabled():
            return []
        
        events = []
        
        # Check for new listening ports
        if self.alert_on_new_listeners:
            listener_events = self._check_listening_ports()
            if listener_events:
                events.extend(listener_events)
        
        # Check for suspicious outbound connections
        outbound_events = self._check_outbound_connections()
        if outbound_events:
            events.extend(outbound_events)
        
        # Check for port scans (connection attempts)
        scan_events = self._check_port_scans()
        if scan_events:
            events.extend(scan_events)
        
        return events
    
    def _get_listening_ports(self) -> Set[int]:
        """Get currently listening ports."""
        ports = set()
        
        try:
            # Use ss command to get listening ports
            result = subprocess.run(
                ["ss", "-tlnp"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            for line in result.stdout.split('\n'):
                # Extract port number
                match = re.search(r':(\d+)\s+', line)
                if match:
                    port = int(match.group(1))
                    ports.add(port)
        
        except Exception:
            pass
        
        return ports
    
    def _check_listening_ports(self) -> List[SecurityEvent]:
        """Check for new listening ports."""
        events = []
        
        current_ports = self._get_listening_ports()
        new_ports = current_ports - self.known_listeners
        
        for port in new_ports:
            if port not in self.expected_ports:
                # Get process information
                process_info = self._get_port_process(port)
                
                events.append(SecurityEvent(
                    event_type="network_anomaly",
                    severity="high",
                    message=f"New unexpected listening port detected: {port}",
                    details={
                        "port": port,
                        "process": process_info,
                        "anomaly_type": "new_listener",
                    }
                ))
        
        # Update known listeners
        self.known_listeners = current_ports
        
        return events
    
    def _get_port_process(self, port: int) -> str:
        """Get process name for a listening port."""
        try:
            result = subprocess.run(
                ["ss", "-tlnp", f"sport = :{port}"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            # Extract process name from output
            match = re.search(r'users:\(\("([^"]+)"', result.stdout)
            if match:
                return match.group(1)
        
        except Exception:
            pass
        
        return "unknown"
    
    def _check_outbound_connections(self) -> List[SecurityEvent]:
        """Check for suspicious outbound connections."""
        events = []
        
        try:
            # Get established connections
            result = subprocess.run(
                ["ss", "-tnp", "state", "established"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            # Look for suspicious patterns
            for line in result.stdout.split('\n'):
                # Check for connections to unusual ports (e.g., IRC, known malware ports)
                suspicious_ports = [6667, 6668, 6669, 4444, 31337, 12345]
                
                for sus_port in suspicious_ports:
                    if f':{sus_port}' in line:
                        # Extract destination
                        dest_match = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', line)
                        if dest_match:
                            dest_ip = dest_match.group(1)
                            dest_port = dest_match.group(2)
                            
                            events.append(SecurityEvent(
                                event_type="network_anomaly",
                                severity="high",
                                message=f"Suspicious outbound connection to {dest_ip}:{dest_port}",
                                details={
                                    "destination_ip": dest_ip,
                                    "destination_port": int(dest_port),
                                    "anomaly_type": "suspicious_connection",
                                }
                            ))
        
        except Exception:
            pass
        
        return events
    
    def _check_port_scans(self) -> List[SecurityEvent]:
        """Check for incoming port scans."""
        events = []
        
        try:
            # Check kernel logs for connection tracking
            result = subprocess.run(
                ["journalctl", "-k", "--since", "5 minutes ago", "--no-pager"],
                capture_output=True,
                text=True,
                check=False,
            )
            
            # Look for patterns indicating port scans
            # This is a simple heuristic - production systems should use more sophisticated methods
            connection_attempts = {}
            
            for line in result.stdout.split('\n'):
                if "SYN" in line or "NEW" in line:
                    # Extract source IP
                    ip_match = re.search(r'SRC=(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        src_ip = ip_match.group(1)
                        connection_attempts[src_ip] = connection_attempts.get(src_ip, 0) + 1
            
            # Alert on high number of connection attempts from single IP
            for src_ip, count in connection_attempts.items():
                if count > 50:  # Threshold for scan detection
                    events.append(SecurityEvent(
                        event_type="network_anomaly",
                        severity="high",
                        message=f"Possible port scan detected from {src_ip}",
                        details={
                            "source_ip": src_ip,
                            "connection_attempts": count,
                            "anomaly_type": "port_scan",
                        }
                    ))
        
        except Exception:
            pass
        
        return events

