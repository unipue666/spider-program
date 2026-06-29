## 福建公共资源电子平台 爬虫逆向思路

这个网站的数据来自 `https://ggzyfw.fj.gov.cn/`，前端会请求 `FwPortalApi/Article/PageList` 这个接口获取公告列表数据。

接口的 Content-Type 是 `application/json`，用 POST 方式提交。

## 请求怎么加密的

请求 headers 需要带上一个 `portal-sign` 字段，它是把所有请求参数（ts、pageNo、pageSize、total、type、timeType）的 key 按字典序排序后拼接成 key+value 的字符串，前面加上固定密钥 `B3978D054A72A7002063637CCDF6B2E5`，然后对整个字符串做 MD5 得到的。

ts 是当前时间戳，也需要同时放在请求参数和 headers 里。

## 响应怎么解密的

接口返回的 JSON 里，`Data` 字段是一段 AES/CBC/Pkcs7 加密的密文，需要解密后 JSON.parse 才能拿到真正的公告列表，包含 ID、标题、发布时间等字段。

AES 的 key 是 `EB444973714E4A40876CE66BE45D5930`，IV 是 `B5A8904209931867`，都是固定的。

## 怎么找到加密位置的

站点逻辑相对简单。直接打开浏览器 DevTools 的 Sources 面板，通过 xhr 断点方式定位。

## 整个流程大概是这样

先准备好页码，调 `get_encrypt_header(page)` 拿到 portal-sign 和 ts，构造完整参数 POST 出去，拿到响应后调 `get_decrypt_response(data)` 解密，就能拿到最终的公告列表了。

## 数据存储

爬虫直接写到 CSV 文件。
