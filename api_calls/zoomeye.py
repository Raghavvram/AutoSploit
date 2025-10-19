#!/usr/bin/env python3
"""
AutoSploit ZoomEye API Module
Modernized for Python 3.12
"""

import os
import base64
import json
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

from lib.settings import start_animation
from lib.errors import AutoSploitAPIConnectionError
from lib.settings import (
    API_URLS,
    HOST_FILE,
    write_to_file
)


class ZoomEyeAPIHook:
    """
    API hook for the ZoomEye API, in order to connect you need to provide a phone number
    so we're going to use some 'lifted' credentials to login for us
    """

    def __init__(self, query: Optional[str] = None, proxy: Optional[Dict[str, str]] = None, 
                 agent: Optional[Dict[str, str]] = None, save_mode: Optional[str] = None, **kwargs):
        self.query = query
        self.host_file = HOST_FILE
        self.proxy = proxy
        self.user_agent = agent
        self.user_file = str(Path(os.getcwd()) / "etc" / "text_files" / "users.lst")
        self.pass_file = str(Path(os.getcwd()) / "etc" / "text_files" / "passes.lst")
        self.save_mode = save_mode

    @staticmethod
    def __decode(filepath: str) -> str:
        """Decode the credentials from the file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = f.read()
                token, n = data.split(":")
                for _ in range(int(n.strip())):
                    token = base64.b64decode(token).decode('utf-8')
            return token.strip()
        except (FileNotFoundError, ValueError, UnicodeDecodeError):
            return ""

    def __get_auth(self) -> Dict[str, str]:
        """
        Get the authorization for the authentication token, you have to login
        before you can access the API, this is where the 'lifted' creds come into
        play.
        """
        username = self.__decode(self.user_file)
        password = self.__decode(self.pass_file)
        data = {"username": username, "password": password}
        req = requests.post(API_URLS["zoomeye"][0], json=data, timeout=30)
        req.raise_for_status()
        token = req.json()
        return token

    def search(self) -> bool:
        """
        Connect to the API and pull all the IP addresses that are associated with the
        given query
        """
        start_animation(f"searching ZoomEye with given query '{self.query}'")
        discovered_zoomeye_hosts: Set[str] = set()
        try:
            token = self.__get_auth()
            if self.user_agent is None:
                headers = {"Authorization": f"JWT {str(token['access_token'])}"}
            else:
                headers = {
                    "Authorization": f"JWT {str(token['access_token'])}",
                    "User-Agent": self.user_agent["User-Agent"]
                }
            params = {"query": self.query, "page": "1", "facet": "ipv4"}
            req = requests.get(
                API_URLS["zoomeye"][1].format(query=self.query),
                params=params, headers=headers, proxies=self.proxy, timeout=30
            )
            req.raise_for_status()
            _json_data = req.json()
            for item in _json_data.get("matches", []):
                if len(item["ip"]) > 1:
                    for ip in item["ip"]:
                        discovered_zoomeye_hosts.add(ip)
                else:
                    discovered_zoomeye_hosts.add(str(item["ip"][0]))
            write_to_file(discovered_zoomeye_hosts, self.host_file, mode=self.save_mode)
            return True
        except Exception as e:
            raise AutoSploitAPIConnectionError(str(e))

