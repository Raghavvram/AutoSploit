#!/usr/bin/env python3
"""
AutoSploit Censys API Module
Modernized for Python 3.12
"""

from typing import Dict, List, Optional, Set

import requests

import lib.settings
from lib.errors import AutoSploitAPIConnectionError
from lib.settings import (
    HOST_FILE,
    API_URLS,
    write_to_file
)


class CensysAPIHook:
    """Censys API hook."""

    def __init__(self, identity: Optional[str] = None, token: Optional[str] = None, 
                 query: Optional[str] = None, proxy: Optional[Dict[str, str]] = None, 
                 agent: Optional[Dict[str, str]] = None, save_mode: Optional[str] = None, **kwargs):
        self.id = identity
        self.token = token
        self.query = query
        self.proxy = proxy
        self.user_agent = agent
        self.host_file = HOST_FILE
        self.save_mode = save_mode

    def search(self) -> bool:
        """Connect to the Censys API and pull all IP addresses from the provided query."""
        discovered_censys_hosts: Set[str] = set()
        try:
            lib.settings.start_animation(f"searching Censys with given query '{self.query}'")
            req = requests.post(
                API_URLS["censys"], auth=(self.id, self.token),
                json={"query": self.query}, headers=self.user_agent,
                proxies=self.proxy, timeout=30
            )
            req.raise_for_status()
            json_data = req.json()
            for item in json_data.get("results", []):
                discovered_censys_hosts.add(str(item["ip"]))
            write_to_file(discovered_censys_hosts, self.host_file, mode=self.save_mode)
            return True
        except Exception as e:
            raise AutoSploitAPIConnectionError(str(e))