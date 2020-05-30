# -*- coding: utf-8 -*-
__author__ = '@buzz'

import ssl

import requests
import urllib3
from requests.cookies import RequestsCookieJar
from requests.models import Request
from requests.sessions import Session, merge_cookies, merge_setting
from requests.utils import get_encodings_from_content


def session_request(self, method, url,
                    params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                    timeout=None,
                    allow_redirects=True, proxies=None, hooks=None, stream=None, verify=False, cert=None, json=None):
    # Create the Request.
    req = Request(
        method=method.upper(),
        url=url,
        headers=headers,
        files=files,
        data=data or {},
        json=json,
        params=params or {},
        auth=auth,
        cookies=cookies,
        hooks=hooks,
    )
    prep = self.prepare_request(req)

    proxies = proxies or {}

    settings = self.merge_environment_settings(
        prep.url, proxies, stream, verify, cert
    )

    # Send the request.
    send_kwargs = {
        'timeout': timeout,
        'allow_redirects': allow_redirects,
    }
    send_kwargs.update(settings)
    resp = self.send(prep, **send_kwargs)
    # parse coding 'ISO-8859-1'
    if resp.encoding == 'ISO-8859-1':
        encodings = get_encodings_from_content(resp.text)
        if encodings:
            encoding = encodings[0]
        else:
            encoding = resp.apparent_encoding

        resp.encoding = encoding
    return resp


def requst_patch():
    urllib3.disable_warnings()
    # remove ssl verify
    ssl._create_default_https_context = ssl._create_unverified_context
    Session.request = session_request


requst_patch()
