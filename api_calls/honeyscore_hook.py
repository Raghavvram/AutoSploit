#!/usr/bin/env python3
"""
AutoSploit Honeyscore Hook Module
Modernized for Python 3.12
"""

from typing import Dict

import requests


class HoneyHook:
    """Hook for Shodan's honeyscore API."""

    def __init__(self, ip_addy: str, api_key: str):
        self.ip = ip_addy
        self.api_key = api_key
        self.url = "https://api.shodan.io/labs/honeyscore/{ip}?key={key}"
        self.headers = {
            "Referer": "https://honeyscore.shodan.io/",
            "Origin": "https://honeyscore.shodan.io"
        }

    def make_request(self) -> float:
        """Make a request to get the honeyscore for an IP address."""
        try:
            req = requests.get(
                self.url.format(ip=self.ip, key=self.api_key), 
                headers=self.headers, 
                timeout=30
            )
            req.raise_for_status()
            honeyscore = float(req.text)
        except Exception:
            honeyscore = 0.0
        return honeyscore
