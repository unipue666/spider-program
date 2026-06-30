## 行行查 爬虫逆向思路

这个网站的数据来自 `https://www.hanghangcha.com/hhcreport`，前端请求 `https://api.hanghangcha.com/hhc/member/industry/getReportList` 获取行业研究报告列表。

## 请求怎么构造的

GET 请求，参数是 `filter` 字段，内容是一个 JSON 字符串，包含 reportType、limit、skip 参数。headers 需要带上 `Client-Encrypt: v1.1` 标记。

## 响应怎么解密的

接口返回的 JSON 里，`data` 字段是一整段 SM4-CBC 加密的密文（base64 编码），需要解密后才能拿到真正的列表数据。

SM4 的 key 是 `MbzgvXzBWynQrtpy`，IV 是 `kDrvPQfPIuArAzkF`，都是固定的。加密模式是 CBC，输出格式是 base64。

## 怎么找到加密位置的

返回数据全是密文，通过 xhr 断点定位到解密函数。行行查用的是国密 SM4 算法，加密逻辑打包在 webpack 的 `1e8b` 模块里，通过 `window.loader` 加载。

## 怎么还原加密的

把 webpack 的 runtime 代码（`hhc-webpack.js`）和调用层（`hhc-decrypt.js`）一起拿出来，`hhc-decrypt.js` 里 `require("./hhc-webpack")` 加载 webpack 模块，然后用 `window.loader("1e8b")` 加载 SM4 模块，实例化后调用 `decrypt` 方法。Python 端用 execjs 编译这个 JS，直接调 `get_decrypt_response` 函数就能解密。

## 整个流程大概是这样

构造好评分页参数 GET 请求，拿到加密的 `data` 字段后，调 execjs 执行 SM4 解密得到明文 JSON，遍历 `data` 数组提取报告 ID、标题、页数、摘要、点赞数、发布时间、查看次数等字段。

## 数据存储

爬虫写到 MongoDB 的 HangHangCha 数据库下的 report_info 集合中，用 Redis 对报告 ID 做哈希去重。
