# -*- coding: utf-8 -*-
__author__ = '@buzz'

import datetime
import enum
import json
import os
import queue
import re
import shutil
import threading
import urllib
from collections import OrderedDict
from typing import Dict, Generator, Iterable, List, Optional, Set, Tuple

import click
import pymysql
from bs4 import BeautifulSoup

from .condition import Condition
from .log import logger
from .requst_patch import requests
from .utils import (bcolors, cached_property, fake_user_agent,
                    get_pinyin_first_letter, get_uuid, ignore_long_char,
                    iter_files, monkeypatch_proxy, plain2md5,
                    synchronized_property)


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
            logger.debug("'%s' make error: %s", cls.__name__, err)
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
            logger.error("%sSelect component error: %s %s",
                         bcolors.FAIL, err, bcolors.ENDC)
        return _count

    def select_components(self, limit: int = 500) -> Generator[List[Dict], None, None]:
        """select all componnents
        """
        _count = self.get_count()
        if _count == 0:
            logger.info("%sNo components%s",
                        bcolors.HEADER, bcolors.ENDC)
            return None
        for pre in range(0, _count, limit):
            try:
                with self._cnx.cursor() as cursor:
                    sql = "SELECT `c_id`,`c_name`,`c_type`,`version`,`website`,`desc`,`producer`,`properties`,`matches`,`author`,`condition`, `implies`,`excludes`, `created_at` FROM `component` LIMIT %s,%s;"
                    cursor.execute(sql, (pre, limit))
                    yield cursor.fetchall()
            except Exception as err:
                logger.error("%sSelect component error: %s %s",
                             bcolors.FAIL, err, bcolors.ENDC)
                break

    def select_component_with(self, c_name) -> Optional[Dict]:
        try:
            with self._cnx.cursor() as cursor:
                sql = "SELECT `c_id`,`c_name`,`created_at` FROM `component` WHERE `c_name`=%s;"
                cursor.execute(sql, (c_name,))
                return cursor.fetchone()
        except Exception as err:
            logger.error("%sSelect component error: %s %s",
                         bcolors.FAIL, err, bcolors.ENDC)
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
            logger.error("%sUpdate component error: %s %s",
                         bcolors.FAIL, err, bcolors.ENDC)
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
            logger.error("%sInsert component error: %s %s",
                         bcolors.FAIL, err, bcolors.ENDC)
            self._cnx.rollback()
        return False

    def cnx_close(self):
        self._cnx.close()


class ComponentManager(ComponentGeneratorMixin, RemoteComponentMixin):
    def __init__(self, directory: str):
        self.directory = directory

    def lists(self):
        count = {}
        for c in self.iter_components():
            count.setdefault(c.type, 0)
            count[c.type] += 1
            click.echo("%s- %s%s" % (bcolors.OKBLUE, c, bcolors.ENDC))
        click.echo("%s*Count: %s%s" %
                   (bcolors.OKGREEN, " ".join("%s: %d" % (k, v) for k, v in count.items()), bcolors.ENDC))

    def _create_component_file(self, path: str, component_data: Dict):
        component_file = os.path.join(
            path, component_data['c_name']) + '.json'
        if os.path.exists(component_file):
            click.echo("%sUpdate this component '%s' content %s" % (
                bcolors.WARNING, component_file, bcolors.ENDC))
            os.system("rm -f '%s'" % component_file)
        else:
            click.echo("%sCreate component '%s' %s" % (
                bcolors.OKBLUE, component_file, bcolors.ENDC))
        c_ = OrderedDict()
        c_['name'] = component_data.pop('c_name')
        c_['type'] = component_data.pop('c_type')
        c_['author'] = component_data.pop('author')
        c_['version'] = component_data.pop('version')
        c_['desc'] = component_data.pop('desc')
        c_['website'] = component_data.pop('website')
        c_['producer'] = component_data.pop('producer')
        c_['condition'] = component_data.pop('condition')
        for k in ('properties', 'matches', 'implies', 'excludes'):
            v = component_data[k]
            if v is None:
                c_[k] = v
                continue
            c_[k] = json.loads(v)
        raw_data = json.dumps(c_, ensure_ascii=False, indent=2)
        with open(component_file, 'w') as f:
            f.write(raw_data)

    def pull_from_remote_database(self, db, user, password, host="127.0.0.1", port=3306):
        """Pull custom components from remote database
        """
        _custom = os.path.join(self.directory, 'custom/')
        click.echo("%sThis operation will overwrite all components in the current directory '%s'!%s" % (
            bcolors.WARNING, _custom, bcolors.ENDC))

        self.init_database(db, user, password, host, port)
        for components in self.select_components():
            for c_data in components:
                if not c_data:
                    continue
                path = os.path.join(_custom, c_data['c_type'])
                self._create_component_file(path, c_data)

    def pull_from_webanalyzer(self):
        """Pull components from 'https://github.com/webanalyzer/rules'
        """
        logger.info("%sStart update components from 'https://github.com/webanalyzer/rules' ...%s",
                    bcolors.HEADER, bcolors.ENDC)
        root = os.path.dirname(self.directory)
        _tmp = os.path.join(root, '.update-tmp')
        if not os.path.exists(_tmp):
            os.mkdir(_tmp)
            # git clone repo
            os.system('git clone https://github.com/webanalyzer/rules %s' % _tmp)
        else:
            # git pull repo
            os.system('cd %s && git pull' % _tmp)
        # update components
        for pth in ('fofa', 'wappalyzer', 'whatweb'):
            _dst = os.path.join(
                self.directory, 'thirdparty', pth)
            if os.path.exists(_dst):
                os.system("rm -rf %s" % _dst)
            shutil.copytree(os.path.join(_tmp, pth), _dst)
        click.echo("%s*Update '%s' Finished%s" % (
            bcolors.OKGREEN,
            os.path.join(self.directory, 'thirdparty'),
            bcolors.ENDC))

    def sync(self, db, user, password, host="127.0.0.1", port=3306, updating=False):
        count = {"new": 0, "updated": 0}
        logger.info("%sStart sync component info to database...%s",
                    bcolors.HEADER, bcolors.ENDC)
        self.init_database(db, user, password, host, port)
        for c in self.iter_components():
            c_info = self.select_component_with(c.name)
            if c_info is None:
                info = {
                    "c_id": get_uuid(),
                    "c_name": c.name,
                    "c_first": get_pinyin_first_letter(c.name),
                    "c_type": c.type,
                    'author': c.author,
                    'version': c.version,
                    'website': c.website,
                    "desc": c.desc,
                    "producer": c.producer,
                    "properties": c.properties if c.properties is None else json.dumps(c.properties, ensure_ascii=False),
                    "matches": json.dumps(c.matches, ensure_ascii=False),
                    "condition": c.condition,
                    "implies": c.implies if c.implies is None else json.dumps(c.implies, ensure_ascii=False),
                    "excludes": c.excludes if c.excludes is None else json.dumps(c.excludes, ensure_ascii=False)
                }
                logger.info("%sAdd new component: %s%s",
                            bcolors.OKBLUE, c, bcolors.ENDC)
                flag = self.insert_component(**info)
                if flag:
                    count["new"] += 1
            elif updating:
                info = {
                    "c_type": c.type,
                    "desc": c.desc,
                    "producer": c.producer,
                    "properties": c.properties,
                    "matches": json.dumps(c.matches, ensure_ascii=False),
                    "condition": c.condition,
                    "implies": c.implies if c.implies is None else json.dumps(c.implies, ensure_ascii=False),
                    "excludes": c.excludes if c.excludes is None else json.dumps(c.excludes, ensure_ascii=False)
                }
                logger.info("%sUpdate component: %s%s",
                            bcolors.OKBLUE, c, bcolors.ENDC)
                flag = self.update_component_with(c.name, **info)
                if flag:
                    count["updated"] += 1
        self.cnx_close()
        click.echo("%s*Count: %s%s" %
                   (bcolors.OKGREEN, " ".join("%s: %d" % (k, v) for k, v in count.items()), bcolors.ENDC))

    def search(self, components: Tuple[str]):
        count = 0
        for c, c_path in self.iter_components(needpath=True):
            for c_name in components:
                if c.name.lower() in c_name.lower():
                    click.echo("%sIN '%s'%s" %
                               (bcolors.WARNING, c_path, bcolors.ENDC))
                    click.echo("%s - %s%s" %
                               (bcolors.OKBLUE, c, bcolors.ENDC))
                    count += 1
        click.echo("%s*Count: %s%s" %
                   (bcolors.OKGREEN, count, bcolors.ENDC))


class ComponentSniffer(ComponentGeneratorMixin, RequestManagerMixin, ComposeURLMixin):
    def __init__(self, target: str, directory: str):
        self.target = target
        self.directory = directory

        self.aggression = False
        self.timeout = 30
        self.allow_redirect = True
        self.max_threads = 8

        self._headers = {
            "user-agent": fake_user_agent()
        }
        self._cond_parser = Condition()
        # threading lock variable
        self._results = []
        self._implies = set()
        self._excludes = set()

    @ property
    def headers(self):
        return self._headers

    @ headers.setter
    def headers(self, value):
        if isinstance(value, str) and ":" in value:
            k, v = value.split(':', 1)
            self._headers[k] = v
        if isinstance(value, Iterable):
            for h in value:
                if not(isinstance(h, str) and ":" in h):
                    continue
                k, v = h.split(':', 1)
                self._headers[k] = v

    @ property
    def user_agent(self):
        return self._headers["user-agent"]

    @ user_agent.setter
    def user_agent(self, value):
        if not isinstance(value, str):
            raise TypeError(
                "'%s' object 'user_agent' type must be str", self.__class__.__name__)
        self._headers["user-agent"] = value

    @ synchronized_property
    def results(self) -> List:
        return self._results

    @ synchronized_property
    def implies(self) -> Set:
        return self._implies

    @ synchronized_property
    def excludes(self) -> Set:
        return self._excludes

    def set_proxy(self, proxy, rdns: bool):
        if isinstance(proxy, str):
            # "type/username@password/addr:port"
            items = proxy.split("/")
            if len(items) < 2:
                raise ValueError("Set Proxy must need 'type/addr:port'")
            proxy = {}
            if len(items) == 2:
                if not ":" in items[1]:
                    raise ValueError("Set Proxy must need 'addr:port'")
                addr, port = items[1].split(":")
                proxy["addr"] = addr
                try:
                    proxy["port"] = int(port)
                except ValueError:
                    raise ValueError(
                        "Set Proxy 'port' type must be int '%s'", port)
            proxy["proxy_type"] = items[0]
        monkeypatch_proxy(**proxy, rdns=rdns)

    def _check_match(self, match: Dict) -> Tuple[bool, Optional[str]]:
        """check match
        :returns flag, version
        """
        s = {"regexp", "text", "md5", "status"}
        if not s.intersection(list(match.keys())):
            return False, None
        # parse url
        resp = self.request(self.target)
        if "url" in match:
            if match['url'] == '/':  # 优化处理
                pass
            elif self.aggression:
                resp = self.request(self.compose_url(match['url']))
            else:
                logger.debug(
                    "match has url(%s) field, but aggression is false" % match['url'])
                return False, None
        # parse search
        search_context = resp['body']
        if 'search' in match:
            if match['search'] == 'all':
                search_context = resp['raw_response']
            elif match['search'] == 'headers':
                search_context = resp['raw_headers']
            elif match['search'] == 'script':
                search_context = resp['script']
            elif match['search'] == 'title':
                search_context = resp['title']
            elif match['search'] == 'cookies':
                search_context = resp['raw_cookies']
            elif match['search'].endswith(']'):
                # headers[key], meta[key], cookies[key]
                for i in ('headers', 'meta', 'cookies'):
                    if not match['search'].startswith('%s[' % i):
                        continue

                    key = match['search'][len('%s[' % i):-1]
                    if key not in resp[i]:
                        return False, None
                    search_context = resp[i].get(key, "")
            match.pop('search')
        # version
        version = match.get('version', None)
        # status,md5,text,regexp
        for key in list(match.keys()):
            if key == 'status':
                if match[key] != resp[key]:
                    return False, None

            if key == 'md5':
                if resp[key] != match[key]:
                    return False, None

            if key == 'text':
                if isinstance(search_context, str):
                    if match[key] not in search_context:
                        return False, None
                else:
                    for _context in search_context:
                        if match[key] not in search_context:
                            continue
                        break
                    else:
                        return False, None

            if key == 'regexp':
                _searchs = search_context
                if isinstance(search_context, str):
                    _searchs = [search_context]

                for search_context in _searchs:
                    regex = re.compile(match[key], re.I)
                    result = regex.findall(search_context)
                    if not result:
                        continue

                    if 'offset' in match:
                        if isinstance(result[0], str):
                            version = result[0]
                        elif isinstance(result[0], tuple):
                            if len(result[0]) > match['offset']:
                                version = result[0][match['offset']]
                            else:
                                version = ''.join(result[0])
                    break
                else:
                    return False, None

        return True, version

    def _check_matches(self, component: Component) -> Optional[Dict]:
        """check component matches
        """
        cond_map = {}
        result = {"name": component.name}
        # TODO  当 condition 为 OR 时匹配出信息直接退出 减少检测次数
        for index, match in enumerate(component.matches):
            is_match, ver = self._check_match(match)
            cond_map[str(index)] = is_match
            if ver:
                result['version'] = ver
        # default or
        if not component.condition:
            if any(cond_map.values()):
                return result
            return None
        # calculation condition
        if self._cond_parser.parse(component.condition, cond_map):
            return result
        return None

    def _update_set_data(self, src: Set, value):
        if not value:
            return
        if isinstance(value, str):
            src.add(value)
        else:
            src.update(value)

    def _update_result(self, c_name: str, value: Dict):
        if c_name in self.excludes:
            return
        self.results.append(value)

    def _process_check_matches_result(self, component):
        result = self._check_matches(component)
        if not result:
            return
        # Handling dependent and non dependent components of components
        self._update_set_data(self.implies, component.implies)
        self._update_set_data(self.excludes, component.excludes)
        self._update_result(component.name, result)

    def _process_implies(self):
        for imply in self.implies:
            _result = {
                'name': imply
            }
            for component in self.iter_components():
                if component.name != imply:
                    continue
                self._update_set_data(self.excludes, component.excludes)
            self._update_result(component.name, _result)

    def _multi_check_matches(self):
        """Multi-thread check component matching
        """
        def _worker():
            nonlocal _task_q
            while True:
                component_or_signal = _task_q.get()
                if component_or_signal == "QUIT":
                    break
                component = component_or_signal
                try:
                    self._process_check_matches_result(component)
                except Exception as err:
                    logger.debug("in _worker %s" % err)
                    continue
        _task_q = queue.Queue(maxsize=50)
        _ts = []
        for _ in range(self.max_threads):
            _t = threading.Thread(target=_worker)
            _t.start()
            _ts.append(_t)
        # queue put task
        for component in self.iter_components():
            _task_q.put(component)
        # queue put QUIT
        for _ in range(self.max_threads):
            _task_q.put("QUIT")
        # waiting workers finished
        for _t in _ts:
            _t.join()
        del _ts, _task_q

    def test(self, components: Tuple[str]):
        for component in self.iter_components():
            if not component.name in components:
                continue
            logger.debug("test '%s' check matches", component.name)
            self._process_check_matches_result(component)
        self._process_implies()
        return self.results

    def start(self):
        self._multi_check_matches()
        self._process_implies()
        return self.results
