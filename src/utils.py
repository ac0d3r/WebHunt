# -*- coding: utf-8 -*-

import hashlib
import os
import random
import socket
import threading
import urllib
import uuid
from typing import Generator, Tuple

import socks
import urllib3
from pypinyin import Style, pinyin

from src.log import logger


class bcolors:
    Purple = '\033[95m'
    Blue = '\033[94m'
    Green = '\033[92m'
    Yellow = '\033[93m'
    Red = '\033[91m'

    Bold = '\033[1m'
    Underline = '\033[4m'

    ENDC = '\033[0m'


class cached_property(object):
    ''' A property that is only computed once per instance and then replaces
        itself with an ordinary attribute. Deleting the attribute resets the
        property. '''

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class synchronized_property(property):
    ''' A property that is thread safety.
    '''

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func
        self.lock = threading.Lock()

    def __get__(self, obj, cls):
        if obj is None:
            return self
        with self.lock:
            return self.func(obj)


def monkeypatch_proxy(proxy_type: str,
                      addr: str,
                      port: int,
                      username: str = None,
                      password: str = None,
                      rdns: bool = True):
    _proxy_type = None
    if proxy_type == 'HTTP':
        _proxy_type = socks.PROXY_TYPE_HTTP
    elif proxy_type == 'SOCKS4':
        _proxy_type = socks.PROXY_TYPE_SOCKS4
    elif proxy_type == 'SOCKS5':
        _proxy_type = socks.PROXY_TYPE_SOCKS5
    else:
        raise Exception('不支持的代理类型 %s' % proxy_type)
    socks.set_default_proxy(
        proxy_type=_proxy_type,
        addr=addr,
        port=port,
        rdns=rdns,
        username=username,
        password=password)
    socket.socket = socks.socksocket


def fake_user_agent() -> str:
    """Fake UserAgent
    """
    agentlist = ["Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) "
                 "Chrome/23.0.1271.64 Safari/537.11",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/603.2.4 "
                 "(KHTML, like Gecko) Version/10.1.1 Safari/603.2.4",
                 "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 "
                 "(KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
                 "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 "
                 "Ubuntu/10.10 (maverick) Firefox/3.6.10"]
    return random.choice(agentlist)


def plain2md5(s: str, encoding='utf8'):
    if isinstance(s, str):
        s = s.encode(encoding)
    elif not isinstance(s, bytes):
        raise TypeError("Only str and bytes are supported")
    return hashlib.md5(s).hexdigest()


def iter_files(root_dir: str, ignore_dirs=[]) -> Generator[Tuple[str, str], None, None]:
    """Iterate all components in directory `root_dir`
    :returns (root, filename)
    """
    logger.debug("iter components: '%s'", root_dir)
    for (root, dirs, files) in os.walk(root_dir):
        for ignore_dir in ignore_dirs:
            if ignore_dir in dirs:
                dirs.remove(ignore_dir)
        for filename in files:
            yield (root, filename)


def ignore_long_char(src: str, length: int) -> str:
    """Ignore long characters in string
    """
    if src is None:
        return ""
    if len(src) < length:
        return src
    return src[:length] + '...'


def get_uuid():
    return str(uuid.uuid1())


def get_pinyin_first_letter(name: str):
    f = 'a'
    try:
        # https://github.com/mozillazg/python-pinyin
        f = pinyin(name, style=Style.INITIALS, strict=False)[0][0][0].lower()
        if ord(f) < 97:
            f = 'a'
        elif ord(f) > 122:
            f = 'z'
    # pylint: disable=bare-except
    except:
        pass
    return f


def confirm_continue(msg=None):
    if not msg:
        msg = "Do you want to continue?"
    input(msg)
