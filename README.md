# WebHunt

![image](https://user-images.githubusercontent.com/26270009/87249915-737d0b00-c494-11ea-9c9a-1b63d1da843a.png)

> A command line tool for analyzing web components for security testing. 𒈯

对 https://github.com/webanalyzer/rules 组件规则的实现，修改部分规则，新增了支持多线程，支持管理组件更新、同步等功能。

## Installation

```bash
git clone https://github.com/WebHunt-Kits/WebHunt.git
pip3 install -r requirements.txt
```

## Usage

- man

```bash
./webhunt --help
./webhunt manage --help
./webhunt scan --help
```

- 从 [rules](https://github.com/webanalyzer/rules) 更新组件

```bash
./webhunt manage --pull_webanalyzer
```

- scan

```bash
./webhunt scan -u http://www.baidu.com
./webhunt scan -u http://www.baidu.com -a
```

## Thx

- https://github.com/webanalyzer/rules
- https://github.com/webanalyzer/webanalyzer.py
