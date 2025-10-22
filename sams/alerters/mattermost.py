#!/usr/bin/env python3
"""
SAMS Mattermost Alerter - Send alerts to Mattermost using Incoming Webhooks.

Mattermost uses Slack-compatible webhook format.
"""

from sams.alerters.slack import SlackAlerter


class MattermostAlerter(SlackAlerter):
    """
    Mattermost alerter using Incoming Webhooks.
    
    Mattermost supports Slack-compatible webhooks, so we inherit from SlackAlerter.
    """
    
    def __init__(self, config):
        """Initialize Mattermost alerter (uses Slack format)."""
        # Set default username for Mattermost
        if "username" not in config:
            config["username"] = "OMEN Security"
        
        super().__init__(config)

