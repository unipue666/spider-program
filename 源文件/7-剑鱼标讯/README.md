## 剑鱼标讯 爬虫逆向思路

这个网站的数据来自 `https://www.jianyu360.cn/jylab/supsearch/index.html`，前端 POST 请求 `https://www.jianyu360.cn/jyapi/jybx/core/fType/searchList` 获取招标公告列表。

## 请求怎么构造的

请求体是 JSON 格式，包含搜索关键词、页码、发布时间范围等参数，直接 POST 提交即可，没有额外的签名参数。

## 响应怎么解密的

接口返回的 JSON 里有 `data`（加密的公告列表密文）和 `secretKey`（加密的 AES 密钥）两个字段。解密分两步。

先用硬编码在 JS 里的 RSA 私钥对 `secretKey` 做 RSA 解密，拿到真正的 AES key。再用这个 key 对 `data` 做 AES-CBC 解密，IV 取密文的前 16 个字节，剩下的是真正的密文内容，解密后得到公告列表数据。

RSA 私钥和 AES 算法参数都写在 `JianYv-decrypt.js` 里。

## 怎么找到加密位置的

请求返回的数据是密文，在 Sources 面板搜索 `secretKey` 或者 `data` 定位到解密函数 `get_decrypt_res`，然后在调用栈往上翻就能看到完整的解密流程。

## 有趣的地方 Promise 怎么解决的

`JianYv-decrypt.js` 里的 `AESDecrypt` 函数用到了 Web Crypto API 的 `crypto.subtle.decrypt`，它返回的是一个 Promise，所以上层的 `get_decrypt_res` 也返回 Promise。

用 `execjs` 调用这种异步函数比较麻烦（execjs 默认不支持 Promise），所以换了个方式：写了一个 `decrypt_wrapper.js` 作为中间层，通过 Node.js 子进程的标准输入传入密文和密钥，在 JS 里 `.then` 拿到结果后从 stdout 输出。Python 这边用 `subprocess.run` 调用 Node.js 进程完成解密，完美绕过了 Promise 的同步调用问题。

## 整个流程大概是这样

构造好搜索参数 POST 出去，拿到加密的响应后，用 `subprocess` 调 Node.js 执行 `decrypt_wrapper.js` 完成 RSA + AES 解密，解析出明文中的公告列表，提取标题、发布时间、地区、行业、公告 ID 等字段。

## 数据存储

爬虫写到 MongoDB 的 JianYu 数据库下的 bidding_info 集合中，用 Redis 对 noticeId 做哈希去重。
