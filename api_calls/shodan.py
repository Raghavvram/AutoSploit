#!/usr/bin/env python3
"""
AutoSploit Shodan API Module
Modernized for Python 3.12
"""

import json
from typing import Dict, List, Optional, Set

import requests

from lib.settings import start_animation
from lib.errors import AutoSploitAPIConnectionError
from lib.settings import (
    API_URLS,
    HOST_FILE,
    write_to_file
)


class ShodanAPIHook:
    """Shodan API hook, saves us from having to install another dependency."""

    def __init__(self, token: Optional[str] = None, query: Optional[str] = None, 
                 proxy: Optional[Dict[str, str]] = None, agent: Optional[Dict[str, str]] = None, 
                 save_mode: Optional[str] = None, **kwargs):
        self.token = token
        self.query = query
        self.proxy = proxy
        self.user_agent = agent
        self.host_file = HOST_FILE
        self.save_mode = save_mode

    def search(self) -> bool:
        """Connect to the API and grab all IP addresses associated with the provided query."""
        start_animation(f"searching Shodan with given query '{self.query}'")
        discovered_shodan_hosts: Set[str] = set()
        try:
            req = requests.get(
                API_URLS["shodan"].format(query=self.query, token=self.token),
                proxies=self.proxy, headers=self.user_agent, timeout=30
            )
            req.raise_for_status()
            json_data = req.json()
            for match in json_data.get("matches", []):
                discovered_shodan_hosts.add(match["ip_str"])
            write_to_file(discovered_shodan_hosts, self.host_file, mode=self.save_mode)
            return True
        except Exception as e:
            raise AutoSploitAPIConnectionError(str(e))


