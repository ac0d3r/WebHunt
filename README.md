# WebHunt

![image](https://user-images.githubusercontent.com/26270009/87249915-737d0b00-c494-11ea-9c9a-1b63d1da843a.png)

> A command line tool for analyzing web components for security testing. 𒈯

对 https://github.com/webanalyzer/rules 组件规则的实现，修改部分规则，新增了支持多线程，支持管理组件更新、同步等功能。

## Installation

```bash
git clone https://github.com/./webhunt-Kits/./webhunt.git
pip3 install -r requirements.txt
```

## Usage

```bash
# all commands help
$ ./webhunt --help

## Scan
$ ./webhunt scan --help
# 扫描 http://www.example.com
$ ./webhunt scan -u http://www.example.com
# 开启侵略模式
$ ./webhunt scan -a -u http://www.example.com
# 指定组件（多个）
$ ./webhunt scan -a -u http://www.example.com -c Nginx -c WordPress


## Manage
$ ./webhunt manage --help
# 从远程数据库拉取组件到本地
$ ./webhunt manage --pull --db Database --user root --passwd "hello"
# 同步组件到远程数据库
$ ./webhunt manage --sync --db Database --user root --passwd "hello"
# 同步并更新已存在的组件到远程数据库
$ ./webhunt manage --sync --sync-updating --db Database --user root --passwd "hello"
```

## Result Demo:
```Json
[{"name": "title", "title": "Hyuga Platform🌀"}, {"name": "ip", "ips": ["39.107.117.128"]}, {"name": "Apache-Tomcat"}, {"name": "Plesk"}, {"name": "JBoss"}, {"name": "Nginx", "version": "1.8.0"}, {"name": "ElasticSearch"}, {"name": "Atlassian-Confluence"}, {"name": "Drupal"}, {"name": "MikroTik"}, {"name": "NVRmini2", "version": "2013"}, {"name": "Microsoft-Windows-Business-Server", "version": 2003}]
```

# Components

插件脚本编放在 `./components` 目录下或者指定其目录，在运行时使用`./webhunt ... -d [指定组件目录]`

## 组件编写规范 <div id="templates"></div>

如下：[templates.md](./templates/templates.md)


## Dev
```shell
$ pipenv install -dev
```

## Thx

- https://github.com/webanalyzer/rules
- https://github.com/webanalyzer/webanalyzer.py
