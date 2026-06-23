## 国家医保局服务平台 爬虫逆向思路

这个网站的数据来自 `https://fuwu.nhsa.gov.cn/`，前端会请求 `https://fuwu.nhsa.gov.cn/ebus/fuwu/api/nthl/api/CommQuery/queryFixedHospital` 这个接口获取定点医疗机构信息。

接口的 Content-Type 是 `application/json`，用 POST 方式提交。

## 请求怎么加密的

整个网站的请求走了一套完整的加密流程，拦截器在 axios 层面把每个请求的 data 加密、headers 注入签名再发出去。发请求的时候，headers 里会带上 `x-tif-nonce`、`x-tif-signature` 和 `x-tif-timestamp` 三个字段，这是网站自研的反篡改签名机制。请求体里的 data 是一段加密后的密文。

## 响应怎么解密的

接口返回的 JSON 里，`data` 字段包含 `signData`、`encType`、`data.encData` 等字段，需要解密后才能拿到真正的数据列表，包含医疗机构编码、名称、类型、等级、地址等字段。

## 怎么找到加密位置的

这个站的加密逻辑全在 webpack 里。在浏览器 DevTools 的 Sources 面板搜索关键字像是 `encrypt`、`sign`、`SM4`、`x-tif` 这些，定位到一段 webpack 打包后的 JS，里面的 axios 拦截器（在模块 `0d5e` 里）会在请求发出去之前调一个加密方法，把 data 加密并往 headers 写签名参数。跟踪那个加密方法发现它在一个 webpack 模块里，模块 ID 是 `7d92`。

## 这个 webpack 有什么特征

这个 webpack 打包了网站的几乎所有前端代码，包括 polyfill、Vue 组件、axios、国密算法这些混在一起。模块 ID 都是短 hex 字符串，像 `7d92`、`0d5e`、`56d7` 这种。webpack 内部有一个模块加载函数，它负责按模块 ID 去加载和执行对应模块。

## 怎么把这个 webpack 弄到 Node 里跑的

把整个 webpack bundle 抠下来存成 `nhsa-webpack.js`，然后在文件开头补一行 `window = global;` 让它在 Node.js 环境里不报错。

但光这样还不够，webpack 的模块加载器是内部函数，从外面调不到具体模块。我的做法是在那个模块加载函数里加了两行自己的代码：

一是在加载器内部加了一行 `console.log("模块调度t: ", t)`，这样每次 webpack 加载模块的时候就会把模块 ID 打印出来。拿着这个日志去跑一遍页面操作，就能看到实际走了哪些模块，比如看到 `7d92` 被调用了就知道它是加密相关的模块。

二是在加载器定义完之后加了一行 `window.loader = o;`，把模块加载器挂到全局上，这样在外部就能通过 `window.loader("7d92")` 手动加载任意模块，拿到模块导出的东西来用。

## 怎么封装成可调用的接口

新建了一个 `nhsa-crypto.js`，require 这个 webpack 文件之后通过 `window.loader("7d92")` 拿到加密模块，对外暴露两个函数：`get_encrypt(page)` 用来构造加密后的请求参数和 headers，`get_decrypt(data)` 用来解密响应数据。

## 整个流程大概是这样

先准备好页码和查询参数，调 `get_encrypt(page)` 拿到加密后的 data 和 headers，POST 出去之后，拿到响应调 `get_decrypt(data)` 解密，就能拿到最终的数据了。

## 环境配置

需要 Python 和 Node.js 两个环境配合运行。Python 负责发请求和存数据，Node.js 负责加密解密的部分，通过 PyExecJS 来调用。

## 需要的 Python 包

```
pip install requests pymongo redis PyExecJS
```

## 需要的 Node.js 包

无需额外安装 npm 包，加密解密完全依赖 `nhsa-webpack.js` 中打包好的 webpack 模块，`nhsa-crypto.js` 直接引用该文件即可。

## 需要启动的服务

爬虫用到了 MongoDB 来存数据，Redis 来做去重，所以本地要先跑起来这两个服务：

- MongoDB 默认端口 27017
- Redis 默认端口 6379

如果不想用数据库，把 `main.py` 里保存数据那块改一下就行。
