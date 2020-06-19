# Kuchiyose

![](./docs/banner.jpeg)

just for fun

> 一个 web 组件识别工具。

对 https://github.com/webanalyzer/rules 组件规则的实现，修改部分规则，新增了支持多线程，支持管理组件更新、同步等功能。

## Usage

- 从 [rules](https://github.com/webanalyzer/rules) 更新组件

```bash
kuchiyose toad --pull_webanalyzer
```

- scan

```bash
kuchiyose dog -u http://www.baidu.com
kuchiyose dog -u http://www.baidu.com -a
```

## Thx

- https://github.com/webanalyzer/rules
- https://github.com/webanalyzer/webanalyzer.py
