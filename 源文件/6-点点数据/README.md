## 点点数据 爬虫逆向思路

这个网站的数据来自 `https://app.diandian.com/`，前端请求 `https://api.diandian.com/pc/app/v1/rank` 获取应用排行数据。

## 请求参数怎么加密的

GET 请求需要带上 `k` 参数。它的生成逻辑在 `DD-encrypt.js` 中的 `get_encrypt_k` 函数里。

`k` 的生成分为两步。先把所有请求参数（market_id、genre_id、country_id、device_id、page、time、rank_type、brand_id）的值按字典序排序后拼接，加上时间戳偏移、path 和 sort 值，中间用 `(&&)` 连接。然后用固定的 AES-128-CBC key 和 IV 对这个字符串加密。最后对加密结果做一轮 XOR 变换并转 base64，得到最终的 `k` 值。

AES 的 key 是 `9836828ceb09268d`，IV 是 `8bca24d7845d4a97`，都是固定的。

## 怎么找到加密位置的

请求参数里有 `k` 这个可疑字段，在 Sources 面板中全局搜索 `k` 或 `get_encrypt_k` 可以定位到加密函数，断点调试即可还原逻辑。

## 怎么还原加密的

加密逻辑集中在 `DD-encrypt.js` 里，直接把这个 JS 文件拿下来，用 Python 的 execjs 调用 `get_encrypt_k(page)` 就能拿到带 `k` 的完整参数，不需要用 Python 重写一遍加密。

## 整个流程大概是这样

先打开 JS 文件编译出 execjs 上下文，输入要采集的页数后逐页调用 JS 拿到加密参数，带上固定 headers 和 cookies 发 GET 请求，拿到 JSON 响应后解析 `data.apps` 数组，提取 app_id、name、rating、rating_count、last_release_time 等字段。

## 数据存储

爬虫写到 MongoDB 的 DianDian 数据库下的 information_info 集合中，用 Redis 对 app_id 做哈希去重。
