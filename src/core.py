# -*- coding: utf-8 -*-

import datetime
import enum
import json
import os
import threading
import urllib
from typing import Dict, Generator, List, Optional

import pymysql
from bs4 import BeautifulSoup

from src.log import logger
from src.requst_patch import requests
from src.utils import cached_property, ignore_long_char, iter_files, plain2md5


@enum.unique
class ComponentType(enum.Enum):
    others = 0
    cms = 1
    os = 2
    middleware = 3
    database = 4
    device = 5
    service = 6
    service_provider = 7
    general = 8

    @classmethod
    def all_kinds(cls) -> List:
        return [c.name for c in cls]


class Component:
    def __init__(self, info: Dict):
        self._info = info

    @cached_property
    def type(self):
        t = self._info.get("type", None)
        if t is None:
            return ComponentType.others.name
        t = t.lower()
        if not t in ComponentType.all_kinds():
            return ComponentType.others.name
        return t

    @cached_property
    def desc(self):
        desc = self._info.get("desc")
        if not desc:
            desc = self._info.get("description")
        return desc

    def __getattr__(self, name):
        return self._info.get(name, None)

    def __str__(self):
        return "[%s] %s: %s" % (self.type, self.name, ignore_long_char(self.desc, 50))

    @classmethod
    def make(cls, path: str):
        """Make a instance of 'Component' from JSON file
        """
        try:
            with open(path, 'r', encoding="utf-8") as f:
                return cls(json.load(f))
        except Exception as err:
            logger.error("'%s' make error: %s", cls.__name__, err)
        return None


class ComponentGeneratorMixin:
    def iter_components(self, ignore_dirs=["tests"], needpath=False) -> Generator[Component, None, None]:
        """Iterate out all components in the `self.directory`
        """
        for root, filename in iter_files(self.directory, ignore_dirs):
            if not filename.endswith('.json'):
                continue
            c_path = os.path.join(root, filename)
            component = Component.make(c_path)
            if component is None:
                continue
            logger.debug("iter_components: %s", component)
            if needpath is False:
                yield component
            else:
                yield component, c_path


class ComposeURLMixin:
    @cached_property
    def target_parsed(self):
        return urllib.parse.urlparse(self.target)

    def compose_url(self, path: str) -> str:
        """compose path
        """
        return urllib.parse.urljoin(self.target, path)


class RequestManagerMixin:
    """This is a thread safe request manager with its own history
    """
    request_manager_history = {}
    request_manager_lock = threading.Lock()

    def request(self, url: str, **kwargs) -> Optional[Dict]:
        with self.request_manager_lock:
            r = self.request_manager_history.get(plain2md5(url), None)
        if not r is None:
            return r
        try:
            resp = requests.get(url, headers=self.headers,
                                timeout=self.timeout, allow_redirects=self.allow_redirect, verify=False)
        except Exception as e:
            logger.error("request error: %s" % str(e))
            return None

        script = []
        meta = {}
        p = BeautifulSoup(resp.text, "html5lib")

        for data in p.find_all("script"):
            script_src = data.get("src")
            if script_src:
                script.append(script_src)

        for data in p.find_all("meta"):
            meta_name = data.get("name")
            meta_content = data.get("content", "")
            if meta_name:
                meta[meta_name] = meta_content

        title = p.find("title")
        if title:
            title = title.text
        else:
            title = ""

        raw_headers = '\n'.join('{}: {}'.format(k, v)
                                for k, v in resp.headers.items())
        resp = {
            "url": url,
            "body": resp.text,
            "headers": resp.headers,
            "status": resp.status_code,
            "script": script,
            "meta": meta,
            "title": title,
            "cookies": resp.cookies,
            "raw_cookies": resp.headers.get("set-cookie", ""),
            "raw_response": raw_headers + resp.text,
            "raw_headers": raw_headers,
            "md5": plain2md5(resp.content),
        }
        with self.request_manager_lock:
            self.request_manager_history[plain2md5(url)] = resp
        return resp


class RemoteComponentMixin:
    def init_database(self, db,
                      user, password,
                      host="127.0.0.1", port=3306,
                      charset='utf8mb4'):
        self._cnx = pymysql.connect(host=host,
                                    port=port,
                                    user=user,
                                    password=password,
                                    db=db,
                                    charset=charset,
                                    cursorclass=pymysql.cursors.DictCursor)

    def get_count(self) -> int:
        """get components count
        """
        _count = 0
        try:
            with self._cnx.cursor() as cursor:
                cursor.execute("SELECT count(_id) FROM `component`;")
            res = cursor.fetchone()
            if res:
                _count = res['count(_id)']
        except Exception as err:
            logger.error("Select component error: %s" % err)
        return _count

    def select_components(self, limit: int = 500) -> Generator[List[Dict], None, None]:
        """select all componnents
        """
        _count = self.get_count()
        if _count == 0:
            logger.warn("Remote database no components")
            return None
        for pre in range(0, _count, limit):
            try:
                with self._cnx.cursor() as cursor:
                    sql = "SELECT `c_id`,`c_name`,`c_type`,`version`,`website`,`desc`,`producer`,`properties`,`matches`,`author`,`condition`, `implies`,`excludes`, `created_at` FROM `component` LIMIT %s,%s;"
                    cursor.execute(sql, (pre, limit))
                    yield cursor.fetchall()
            except Exception as err:
                logger.error("Select component error: %s " % err)
                break

    def select_component_with(self, c_name) -> Optional[Dict]:
        try:
            with self._cnx.cursor() as cursor:
                sql = "SELECT `c_id`,`c_name`,`created_at` FROM `component` WHERE `c_name`=%s;"
                cursor.execute(sql, (c_name,))
                return cursor.fetchone()
        except Exception as err:
            logger.error("Select component error: %s" % err)
            return None

    def update_component_with(self, c_name, **component_info) -> bool:
        now = datetime.datetime.now()
        component_info['updated_at'] = now
        component_info['c_name'] = c_name

        try:
            with self._cnx.cursor() as cursor:
                sql = "UPDATE `component` SET `c_type`=%s, `author`=%s, `desc`=%s, `producer`=%s, `properties`=%s,`matches`=%s, `condition`=%s, `implies`=%s, `excludes`=%s, `updated_at`=%s WHERE `c_name`=%s;"
                cursor.execute(sql, [component_info.get(k)
                                     for k in ('c_type', 'author', 'desc', 'producer', 'properties', 'matches', 'condition', 'implies', 'excludes', 'updated_at', 'c_name')]
                               )
                self._cnx.commit()
                return True
        except Exception as err:
            logger.error("Update component error: %s" % err)
            self._cnx.rollback()
        return False

    def insert_component(self, **component_info):
        now = datetime.datetime.now()
        component_info['created_at'] = now
        component_info['updated_at'] = now
        try:
            with self._cnx.cursor() as cursor:
                sql = "INSERT INTO `component` (`c_id`, `c_name`, `c_first`,`c_type`,`version`,`website`,`author`, `desc`, `producer`, `properties`,`matches`,`condition`, `implies`, `excludes`, `created_at`, `updated_at`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                cursor.execute(sql, [component_info.get(k)
                                     for k in ('c_id', 'c_name', 'c_first', 'c_type', 'version', 'website', 'author', 'desc', 'producer', 'properties', 'matches', 'condition', 'implies', 'excludes', 'created_at', 'updated_at')])
                self._cnx.commit()
                return True
        except Exception as err:
            logger.error("Insert component error: %s" % err)
            self._cnx.rollback()
        return False

    def cnx_close(self):
        self._cnx.close()
