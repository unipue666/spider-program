## 四川省农机购置与应用补贴信息 爬虫逆向思路

这个网站的数据来自 `http://202.61.89.161:12021/`，前端会请求 `api/loginSidePageEDE/getPurchaseOfAgriculturalMachinery` 这个接口获取农机购置补贴数据。

接口的 Content-Type 是 `application/json`，用 POST 方式提交。

## 请求怎么加密的

请求参数用 SM4 加密后放在 `parameter` 字段里，同时 headers 需要带上 `sign`、`timestamp`、`source` 三个字段用于服务器校验。其中 `sign` 是将请求参数（含时间戳）拼接后加上固定 key 做 SM3 哈希再转大写，最后用 SM4 加密得到的。

## 响应怎么解密的

接口返回的 JSON 里，`data` 字段是一段 SM4 加密的密文，需要解密后 JSON.parse 才能拿到真正的数据列表，包含县、乡镇、购机者名字、机具品目、生产厂家等字段。

## 怎么找到加密位置的

加密逻辑全在 webpack 里。在浏览器 DevTools 的 Sources 面板搜索 `sm4`、`sm3`、`encrypt` 这些关键字，定位到 webpack 打包后的 JS，找到对应的模块。关键加密模块的 ID 是 `8060`，里面导出了 sm4 和 sm3 方法。


## 怎么收集 webpack 模块的

先把整个 webpack bundle 抠下来，在文件开头补一行 `window = global;` 让它在 Node.js 里能跑。

然后在模块加载器的内部加一行日志 `console.log("调用模块e: ", e)`，每次加载模块时把模块 ID 打印出来。接着在加载器定义完之后加一行 `window.loader = d`，把模块加载器挂到全局。

但光加日志还不够——因为 webpack 的模块是动态加载的，很多模块在初始化时并不会被执行到。所以需要用条件断点把模块从缓存池里捞出来。

做法是：在模块加载器里找到缓存对象 `u`，在 `u[e]` 判断的地方打条件断点，形如 `new_obj[e] = c[e], 0`。先把 `u` 置空（`u = {}`），创建一个新对象 `new_obj`，然后触发页面操作让 webpack 去加载模块。每次命中断点时，`c[e]` 就是当前加载的模块定义，把它存到 `new_obj` 里。最后在控制台用下面这段代码把收集到的模块拼成字符串：

```
result = ""; for(let x of Object.keys(new_obj)){result = result + "'" + x + "':" + new_obj[x] + ",";}
```

把这段字符串贴回 webpack 文件的模块定义对象 `{}` 里，就完成了模块收集。

## 怎么封装成可调用的接口

新建了 `sichuan-crypto.js`，require 这个 webpack 文件之后通过 `window.loader("8060")` 拿到 sm4/sm3 模块，再通过 `window.loader` 加载其他辅助模块拿到 sm4 的密钥（是一个被二次加密的 base64 字符串，需要先解密一次才能得到真正的 sm4 key）。对外暴露两个函数：`get_encrypt(page)` 用来构造加密后的请求参数和 headers，`decrypt_res(encrypt_data)` 用来解密响应数据。

## 这个 key 是怎么处理的

`四川_encrypt.js` 里有一个硬编码的 s：
```
s = "e3xFjZ4ezDBUbyMbdwwTH+GzxbOe7kHsn4YNMr1j4KerhffMsEXu5GEVad4hpIj2XRQkBRAfKFhk1u5IlLdKLw=="
```
这个 s 是加密过的，需要通某个 webpack 模块的 decrypt 方法解密一次才能得到真正的 sm4 密钥，之后的加密解密都用这个 key。

## 整个流程大概是这样

先准备好页码和查询参数，调 `get_encrypt(page)` 拿到加密后的 parameter 和 headers（sign、timestamp、source），POST 出去之后，拿到响应调 `decrypt_res(data)` 解密，就能拿到最终的数据了。

## 环境配置

需要 Python 和 Node.js 两个环境配合运行。Python 负责发请求和存数据，Node.js 负责加密解密的部分，通过 PyExecJS 来调用。

## 需要的 Python 包

```
pip install requests pymysql redis PyExecJS
```


## 需要启动的服务

爬虫用到了 MySQL 来存数据，Redis 来做去重，所以本地要先跑起来这两个服务：

- MySQL 默认端口 3306
- Redis 默认端口 6379

如果不想用数据库，把 `main.py` 里保存数据那块改一下就行。
