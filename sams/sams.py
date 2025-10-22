#!/usr/bin/env python3
"""
SAMS - Suspicious Activity Monitoring System

Main monitoring script that coordinates detectors and alerters.
"""

import sys
import os
import time
import signal
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sams.detectors import (
    AuthFailureDetector,
    PrivilegeEscalationDetector,
    SuspiciousCommandDetector,
    FileChangeDetector,
    NetworkAnomalyDetector,
)

from sams.alerters import (
    WebhookAlerter,
    SlackAlerter,
    MattermostAlerter,
    TelegramAlerter,
)


class SAMS:
    """SAMS monitoring engine."""
    
    def __init__(self, config_file: str):
        """Initialize SAMS with configuration file."""
        self.config_file = config_file
        self.config = self._load_config()
        self.running = False
        self.logger = self._setup_logging()
        
        # Initialize detectors
        self.detectors = self._initialize_detectors()
        
        # Initialize alerters
        self.alerters = self._initialize_alerters()
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            # Print to stderr before logger is initialized
            print(f"Error loading config: {e}", file=sys.stderr)
            sys.exit(1)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging to file."""
        log_file = self.config.get("log_file", "/var/log/omen/sams.log")
        log_level = self.config.get("log_level", "INFO")
        
        # Create log directory if needed
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        logger = logging.getLogger("SAMS")
        logger.setLevel(getattr(logging, log_level))
        
        # File handler for structured logs
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(message)s')  # JSON format, no extra formatting
        )
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_detectors(self) -> List:
        """Initialize all detectors based on configuration."""
        detectors = []
        detector_configs = self.config.get("detectors", {})
        
        detector_classes = {
            "auth_failures": AuthFailureDetector,
            "privilege_escalation": PrivilegeEscalationDetector,
            "suspicious_commands": SuspiciousCommandDetector,
            "file_changes": FileChangeDetector,
            "network_anomalies": NetworkAnomalyDetector,
        }
        
        for detector_name, detector_class in detector_classes.items():
            config = detector_configs.get(detector_name, {})
            if config.get("enabled", True):
                try:
                    detector = detector_class(config)
                    detectors.append(detector)
                    self.logger.info(f"Initialized detector: {detector_name}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize detector {detector_name}: {e}")
        
        return detectors
    
    def _initialize_alerters(self) -> List:
        """Initialize all alerters based on configuration."""
        alerters = []
        alerting_config = self.config.get("alerting", {})
        webhooks = alerting_config.get("webhooks", [])
        
        alerter_types = {
            "webhook": WebhookAlerter,
            "slack": SlackAlerter,
            "mattermost": MattermostAlerter,
            "telegram": TelegramAlerter,
        }
        
        for webhook_config in webhooks:
            if not webhook_config.get("enabled", True):
                continue
            
            webhook_type = webhook_config.get("type", "webhook")
            alerter_class = alerter_types.get(webhook_type, WebhookAlerter)
            
            try:
                alerter = alerter_class(webhook_config)
                if alerter.is_enabled():
                    alerters.append(alerter)
                    self.logger.info(f"Initialized alerter: {webhook_type}")
            except Exception as e:
                self.logger.error(f"Failed to initialize alerter {webhook_type}: {e}")
        
        return alerters
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _process_event(self, event):
        """Process a security event."""
        # Log event as JSON
        self.logger.info(event.to_json())
        
        # Send alerts
        for alerter in self.alerters:
            try:
                success = alerter.send_alert(event.to_dict())
                if success:
                    self.logger.debug(f"Alert sent via {alerter.name}")
                else:
                    self.logger.warning(f"Failed to send alert via {alerter.name}")
            except Exception as e:
                self.logger.error(f"Error sending alert via {alerter.name}: {e}")
    
    def run(self):
        """Main monitoring loop."""
        self.running = True
        check_interval = self.config.get("check_interval", 60)
        
        self.logger.info("SAMS started")
        self.logger.info(f"Monitoring with {len(self.detectors)} detectors")
        self.logger.info(f"Alerting via {len(self.alerters)} alerters")
        
        while self.running:
            try:
                # Run all detectors
                for detector in self.detectors:
                    if not detector.is_enabled():
                        continue
                    
                    try:
                        events = detector.detect()
                        for event in events:
                            self._process_event(event)
                    except Exception as e:
                        self.logger.error(f"Detector {detector.get_name()} error: {e}")
                
                # Sleep until next check
                if self.running:
                    time.sleep(check_interval)
            
            except Exception as e:
                self.logger.error(f"Main loop error: {e}")
                if self.running:
                    time.sleep(check_interval)
        
        self.logger.info("SAMS stopped")
    
    def test_alert(self):
        """Send a test alert."""
        from sams.detectors.base import SecurityEvent
        
        test_event = SecurityEvent(
            event_type="test",
            severity="low",
            message="This is a test alert from OMEN SAMS",
            details={
                "test": True,
                "timestamp": datetime.now().isoformat(),
            }
        )
        
        self.logger.info("Sending test alert...")
        self._process_event(test_event)
        self.logger.info("Test alert sent")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SAMS - Suspicious Activity Monitoring System"
    )
    
    parser.add_argument(
        "-c", "--config",
        default="/opt/omen/sams/config.json",
        help="Configuration file path",
    )
    
    parser.add_argument(
        "--test-alert",
        action="store_true",
        help="Send a test alert and exit",
    )
    
    args = parser.parse_args()
    
    # Check if config exists
    if not Path(args.config).exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        print("Copy config.json.example to config.json and configure it.", file=sys.stderr)
        sys.exit(1)
    
    # Initialize SAMS
    sams = SAMS(args.config)
    
    if args.test_alert:
        # Send test alert and exit
        sams.test_alert()
        sys.exit(0)
    
    # Run monitoring loop
    try:
        sams.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()

