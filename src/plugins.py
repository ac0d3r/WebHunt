# -*- coding: utf-8 -*-

import re
import socket
from typing import Dict


class PluginsMixin:
    def get_title(self, body: str) -> Dict:
        """get web site title
        """
        _t = re.search(r"<title>([^<]+)</title>", body, re.I)
        if _t:
            return {"name": "title", "title": _t.group(1).strip()}
        else:
            return {"name": "title", "title": ""}

    def get_ip(self, hostname_or_ip: str) -> Dict:
        try:
            return {"name": "ip", "ips": [socket.gethostbyname(hostname_or_ip)]}
        except:
            return {"name": "ip", "ips": []}
