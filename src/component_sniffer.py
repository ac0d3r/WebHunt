# -*- coding: utf-8 -*-
import queue
import re
import threading
from typing import Dict, Iterable, List, Optional, Set, Tuple

from src.condition import Condition
from src.core import (Component, ComponentGeneratorMixin, ComposeURLMixin,
                      RequestManagerMixin)
from src.log import logger
from src.plugins import PluginsMixin
from src.utils import fake_user_agent, monkeypatch_proxy, synchronized_property


class ComponentSniffer(ComponentGeneratorMixin, RequestManagerMixin, ComposeURLMixin, PluginsMixin):
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

    @property
    def headers(self):
        return self._headers

    @headers.setter
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

    @property
    def user_agent(self):
        return self._headers["user-agent"]

    @user_agent.setter
    def user_agent(self, value):
        if not isinstance(value, str):
            raise TypeError(
                "'%s' object 'user_agent' type must be str", self.__class__.__name__)
        self._headers["user-agent"] = value

    @synchronized_property
    def results(self) -> List[Dict]:
        return self._results

    @synchronized_property
    def implies(self) -> Set[str]:
        return self._implies

    @synchronized_property
    def excludes(self) -> Set[str]:
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

    def load_plugins(self):
        resp = self.request(self.target)
        if resp:
            self.results.append(self.get_title(resp["body"]))
        else:
            self.results.append(self.get_title(""))
        self.results.append(self.get_ip(self.target_parsed.hostname))

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
        if not resp:
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
                    try:
                        regex = re.compile(match[key], re.I)
                    except Exception as err:
                        logger.error("%s re compile error: %s",
                                     match[key], err)
                        continue
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
        # TODO 优化 O(n(m+z))
        for imply in self.implies:
            _result = {
                'name': imply
            }
            for component in self.iter_components():
                if component.name != imply:
                    continue
                self._update_set_data(self.excludes, component.excludes)
                self._update_result(imply, _result)
                break

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
                    logger.error(
                        "in _worker [%s] %s" % (component.name, err))
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
        self.load_plugins()
        for component in self.iter_components():
            if not component.name in components:
                continue
            logger.debug("test '%s' check matches", component.name)
            self._process_check_matches_result(component)
        self._process_implies()
        return self.results

    def start(self):
        self.load_plugins()
        self._multi_check_matches()
        self._process_implies()
        return self.results
