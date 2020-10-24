通用的组件识别规则

## 组件编写

### 基础信息

例子:

```Json
{
  "name": "wordpress",
  "type": "cms",
  "author": "someone",
  "version": "0.1.0",
  "desc": "wordpress 是世界上最为广泛使用的博客系统",
  "website": "http://www.wordpress.org/",
  "producer": "wordpress.org",
  "properties": {
    "deploy_path": {
      "type": "string",
      "default": "/"
    }
  },
  "matches": [],
  "condition": "0 and (1 and not 2)",
  "implies": "PHP",
  "excludes": "Apache"
}
```

描述:

| FIELD            | TYPE         | DESCRIPTION          | EXAMPLE                                               | REQUIRED |
|------------------|--------------|----------------------|-------------------------------------------------------|----------|
| name             | string       | 组件名称             | `wordpress`                                           | true     |
| type             | string       | 组件类型             | `cms`                                                 | true     |
| author           | string       | 作者名               | `fate0`                                               | false    |
| version          | string       | 插件版本             | `0.1.0`                                               | false    |
| description/desc | string       | 组件描述             | `wordpress 是世界上最为广泛使用的博客系统`            | false    |
| website          | string       | 组件网站             | `http://www.wordpress.org/`                           | false    |
| producer         | string       | 组件厂商             | `wordpress.org`                                       | false    |
| properties       | object       | 组件属性参数         | `{"deploy_path": {"type": "string","default": "/"} }` | false    |
| matches          | array        | 规则                 | `[{"regexp": "wordpress"}]`                           | true     |
| condition        | string       | 规则组合条件         | `0 and (1 and not 2)`                                 | false    |
| implies          | string/array | 依赖的其他组件       | `PHP`                                                 | false    |
| excludes         | string/array | 肯定不依赖的其他组件 | `Apache`                                              | false    |

### 规则信息

例子:

```Json
[
    {
        "search": "headers",
        "text": "Nginx",
    }
]

```

描述:

| FIELD   | TYPE   | DESCRIPTION                                                                                                              | EXAMPLE                            |
|---------|--------|--------------------------------------------------------------------------------------------------------------------------|------------------------------------|
| search  | string | 搜索的位置，可选值为 `all`, `headers`, `title`, `body`, `script`, `cookies`, `headers[key]`, `meta[key]`, `cookies[key]` | `body`                             |
| regexp  | string | 正则表达式                                                                                                               | `wordpress.*`                      |
| text    | string | 明文搜索                                                                                                                 | `wordpress`                        |
| version | string | 匹配的版本号                                                                                                             | `0.1`                              |
| offset  | int    | regexp 中版本搜索的偏移                                                                                                  | `1`                                |
| md5     | string | 目标文件的 md5 hash 值                                                                                                   | `beb816a701a4cee3c2f586171458ceec` |
| url     | string | 需要请求的 url                                                                                                           | `/properties/aboutprinter.html`    |
| status  | int    | 请求 url 的返回状态码，默认是 200                                                                                        | `400`                              |

## 返回信息

例子:

```Json
[
    {
        "name": "4images",
        "version": "1.1"
    }
]
```

描述:

| FIELD   | TYPE   | DESCRIPTION | EXAMPLE     | REQUIRED |
|---------|--------|-------------|-------------|----------|
| name    | string | 组件名称    | `wordpress` | true     |
| version | string | 插件版本    | `0.1.0`     | false    |

## 检测逻辑

- 如果 match 中存在 url 字段，`aggression` 开启，则请求 url 获取相关信息
- 根据 search 字段选取搜索位置
- 根据 regexp/text 进行文本匹配，或者 status 匹配状态码，或者 md5 匹配 body 的 hash 值
- 如果 match 中存在 version 就表明规则直接出对应版本，如果存在 offset 就表明需要从 regexp 中匹配出版本
- 如果 matches 中存在 condition，则根据 condition 判断规则是否匹配，默认每个 match 之间的关系为 `or`

## 来源

> https://github.com/webanalyzer/rules#%E8%A7%84%E5%88%99%E7%BC%96%E5%86%99
