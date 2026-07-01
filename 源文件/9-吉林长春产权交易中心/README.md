## 吉林长春产权交易中心 爬虫逆向思路

这个网站的数据来自 `https://www.ccprec.com`，前端 POST 请求 `https://www.ccprec.com/honsanCloudAct` 获取项目列表信息。

## 请求怎么构造的

POST 请求，body 是一整段自定义算法加密后的字符串，Content-Type 是 `text/xml;charset=UTF-8`。原始参数是一个 JSON 对象，包含 id、projectKey、clientKey、acts 等字段，acts 里指定了分页页码和每页条数。

## 加解密是怎么做的

这套加解密是纯手写的自定义算法，没有用标准加密库，完全靠字符编码运算拼出来的。

加密过程：先把参数对象 JSON.stringify 两遍，然后生成一个随机前缀（长度 16 到 32 位随机），对每个字符的 charCode 加上 `pubPassNum` 数组的对应位（循环）再加上随机前缀对应位的 charCode（循环），和累加超过 65535 就回绕，最后转成 base36 格式，前面再拼上校验和、随机前缀长度、随机前缀本身。

解密过程反过来：从密文头部取出校验和、随机前缀长度、随机前缀本身，然后对剩余每两位 base36 解码减去随机前缀对应位 charCode 再减去 `pubPassNum` 对应位，转回字符拼接。

## 怎么找到加密位置的

搜索 `honsanCloudAct` 接口地址定位到 XHR 调用位置，往上追溯发现请求发送前数据经过了一个 `encryptCode` 函数处理，响应回来后又经过 `decryptCode` 函数还原。

## 怎么还原加解密的

把 `encryptCode` 和 `decryptCode` 两个函数完整抠出来，依赖的 `pubPassNum`、`pubPass` 固定密钥一并拿出来，封装成 `get_encrypt_data` 和 `get_decrypt_response` 两个导出函数。Python 端用 execjs 编译这个 JS 文件，直接调用即可。

## 整个流程大概是这样

构造好分页参数 JSON，调 execjs 执行加密得到密文字符串，POST 提交拿到响应密文，再调 execjs 执行解密得到明文 JSON，从 `results[0].args[0].list` 中提取每条数据的唯一编号、标题、披露起止时间。

## 数据存储

爬虫写到 MongoDB 的 `property_transaction` 数据库下的 `information` 集合中，用 Redis 对唯一编号做哈希去重。
