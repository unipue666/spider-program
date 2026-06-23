## 中国观鸟中心 爬虫逆向思路

这个网站的数据来自 `https://www.birdreport.cn/`，前端会请求 `https://api.birdreport.cn/front/activity/search` 这个接口获取观鸟活动记录。

接口的 Content-Type 是 `application/x-www-form-urlencoded`，用 POST 方式提交。

## 请求怎么加密的

发请求的时候，需要在 headers 里带上三个东西：`requestId`、`timestamp` 和 `sign`。

`requestId` 是一个 32 位的随机字符串，用了一个自定义的函数生成的，看起来像是 uuid 的格式。`timestamp` 就是当前时间的毫秒时间戳。`sign` 是把要提交的数据原文和 requestId、timestamp 拼在一起，再取 MD5 算出来的，32 位小写。

请求体是一个叫 `data` 的字段，里面放的是一段加密后的密文。明文本身很简单，就是一个 JSON 字符串 `{"limit":"20","page":"第几页"}`。加密用的是 RSA，公钥是写死在 JS 文件里的，很长一串。前端的 JS 代码用了 `jsencrypt` 这个库来做的 RSA 加密。

## 响应怎么解密的

接口返回的 JSON 里，`data` 字段是加密的。解密用的是 AES，模式是 CBC，填充方式是 Pkcs7。密钥是一串 32 位的字符串 `C8EB5514AF5ADDB94B2207B08C66601C`，偏移量是 `55DD79C6F04E1A67`。解密之后得到的就是真正的数据 JSON，里面有报告编号、观测时间、地点、用户名这些字段。

## 整个流程大概是这样

先准备好页码，拼成 JSON 明文。然后用 RSA 加密得到 data，同时用 MD5 算出 sign，连同 requestId 和 timestamp 塞进 headers。POST 出去之后，拿到的响应里 data 字段用 AES 解密，就能拿到最终的数据了。

## 环境配置

需要 Python 和 Node.js 两个环境配合运行。Python 负责发请求和存数据，Node.js 负责加密解密的部分，通过 PyExecJS 来调用。

## 需要的 Python 包

```
pip install requests pymongo redis PyExecJS
```

## 需要的 Node.js 包

在 `bird-watching-crypto.js` 同目录下执行：

```
npm install crypto-js jsencrypt
```

## 需要启动的服务

爬虫用到了 MongoDB 来存数据，Redis 来做去重，所以本地要先跑起来这两个服务：

- MongoDB 默认端口 27017
- Redis 默认端口 6379

如果不想用数据库，把 `main.py` 里保存数据那块改一下就行。
