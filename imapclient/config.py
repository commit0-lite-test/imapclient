import argparse
import configparser
import json
import os
import ssl
import urllib.parse
import urllib.request
from typing import Any, Callable, Dict, Optional, Tuple, TYPE_CHECKING, TypeVar
import imapclient

def parse_config_file(filename: str) -> argparse.Namespace:
    """Parse INI files containing IMAP connection details.

    Used by livetest.py and interact.py
    """
    config = configparser.ConfigParser()
    config.read(filename)

    if 'DEFAULT' not in config:
        raise ValueError(f"Config file {filename} must have a DEFAULT section")

    ns = argparse.Namespace()
    ns.host = config.get('DEFAULT', 'host')
    ns.port = config.getint('DEFAULT', 'port', fallback=None)
    ns.ssl = config.getboolean('DEFAULT', 'ssl', fallback=True)
    ns.username = config.get('DEFAULT', 'username')
    ns.password = config.get('DEFAULT', 'password', fallback=None)
    ns.oauth2 = config.getboolean('DEFAULT', 'oauth2', fallback=False)
    ns.oauth2_client_id = config.get('DEFAULT', 'oauth2_client_id', fallback=None)
    ns.oauth2_client_secret = config.get('DEFAULT', 'oauth2_client_secret', fallback=None)
    ns.oauth2_refresh_token = config.get('DEFAULT', 'oauth2_refresh_token', fallback=None)

    return ns
T = TypeVar('T')
OAUTH2_REFRESH_URLS = {'imap.gmail.com': 'https://accounts.google.com/o/oauth2/token', 'imap.mail.yahoo.com': 'https://api.login.yahoo.com/oauth2/get_token'}
_oauth2_cache: Dict[Tuple[str, str, str, str], str] = {}
