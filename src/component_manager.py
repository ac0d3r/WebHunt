# -*- coding: utf-8 -*-
import json
import os
import shutil
from collections import OrderedDict
from typing import Dict, Tuple

from src import echo
from src.core import ComponentGeneratorMixin, RemoteComponentMixin
from src.utils import get_pinyin_first_letter, get_uuid


class ComponentManager(ComponentGeneratorMixin, RemoteComponentMixin):
    def __init__(self, directory: str):
        self.directory = directory

    def lists(self):
        count = {}
        for c in self.iter_components():
            count.setdefault(c.type, 0)
            count[c.type] += 1
            echo.binfo("- %s" % c)
        echo.succ("*Count: %s" % " ".join("%s: %d" % (k, v)
                                          for k, v in count.items()))

    def pull_from_remote_database(self, db, user, password, host="127.0.0.1", port=3306):
        """Pull components from remote database
        """
        self.init_database(db, user, password, host, port)
        for components in self.select_components():
            for c_data in components:
                if not c_data:
                    continue
                path = os.path.join(self.directory, c_data['c_type'])
                self._create_component_file(path, c_data)

    def pull_from_webanalyzer(self):
        """Pull components from 'https://github.com/webanalyzer/rules'
        """
        echo.tips(
            "Start update components from 'https://github.com/webanalyzer/rules' ...")
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
        echo.succ("*Update '%s' Finished" %
                  os.path.join(self.directory, 'thirdparty'),
                  )

    def _create_component_file(self, path: str, component_data: Dict):
        component_file = os.path.join(
            path, component_data['c_name']) + '.json'
        if os.path.exists(component_file):
            echo.warn("Update this component '%s' content " % component_file)
            os.system("rm -f '%s'" % component_file)
        else:
            echo.binfo("Create component '%s'" % component_file)
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
        try:
            with open(component_file, 'w', encoding="utf-8") as f:
                f.write(raw_data)
        except Exception as err:
            echo.fail("component '%s' write to file: '%s' error: %s" %
                      (c_['name'], component_file, err))

    def sync(self, db, user, password, host="127.0.0.1", port=3306, updating=False):
        count = {"new": 0, "updated": 0}
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
                echo.binfo("Add new component: %s" % c)
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
                echo.binfo("Update component: %s" % c)
                flag = self.update_component_with(c.name, **info)
                if flag:
                    count["updated"] += 1
        self.cnx_close()
        echo.succ("*Count: %s" %
                  " ".join("%s: %d" % (k, v) for k, v in count.items()))

    def search(self, components: Tuple[str]):
        count = 0
        for c, c_path in self.iter_components(needpath=True):
            for c_name in components:
                if c.name.lower() in c_name.lower():
                    echo.warn("IN '%s'" % c_path)
                    echo.binfo("- %s" % c)
                    count += 1
        echo.succ("*Count: %s" % count)
