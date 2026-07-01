import requests
import execjs
import pymongo
import redis
import hashlib
import re

class PropertyTransactionSpider:

    def __init__(self):
        self.headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "text/xml;charset=UTF-8",
    "Origin": "https://www.ccprec.com",
    "Pragma": "no-cache",
    "Referer": "https://www.ccprec.com/projectSecPage/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
        self.url = "https://www.ccprec.com/honsanCloudAct"
        self.mongo_client = pymongo.MongoClient(host="localhost", port=27017)
        self.conn = self.mongo_client["property_transaction"]["information"]
        self.redis_client = redis.Redis()

    @staticmethod
    def get_hash(value):
        md5_hash = hashlib.md5(str(value).encode("utf-8")).hexdigest()
        return md5_hash

    def get_encrypt_params(self, page):
        params = {
            "id": "ru6ek7z7u34478dx",
            "projectKey": "honsan_cloud_ccprec",
            "clientKey": "ru6ek7qoi1c3i9m9",
            "token": None,
            "clientDailyData": {},
            "acts": [
                {
                    "id": "ru6ek7uiwaoosbru",
                    "fullPath": "/ccprec.com.cn.web/client/info/cqweb_nonphy_cqzr",
                    "args": [
                        page,
                        20,
                        None
                    ]
                }
            ]
        }
        with open("params_and_response.js", "r", encoding="utf-8") as f:
            js_code = f.read()
        ctx = execjs.compile(js_code)
        result = ctx.call("get_encrypt_data", params)
        data = result["encrypt_data"].encode('unicode_escape')
        return data

    def get_data(self, encrypt_params):
        response = requests.post(self.url, headers=self.headers, data=encrypt_params).text
        with open("JiLin-crypto.js", "r", encoding="utf-8") as f:
            js_code = f.read()
        ctx = execjs.compile(js_code)
        my_datas = []
        results = ctx.call("get_decrypt_response", response)
        for result in results:
            s1 = result["publish_optime"]
            s2 = result["publish_edtime"]
            d1 = re.search(r"(.*?) ", s1).group(1) if (s1 and re.search(r"(.*?) ", s1)) else ""
            d2 = re.search(r"(.*?) ", s2).group(1) if (s2 and re.search(r"(.*?) ", s2)) else ""
            my_datas.append({
                "唯一编号": result["id"],
                "标题": result["object_name"],
                "披露起止时间": d1 + "__" + d2
            })
        self.save_data(my_datas)
        print("-" * 10)

    def save_data(self, datas):
        for data in datas:
            result_hash = self.redis_client.sadd("transaction_hash2", self.get_hash(data["唯一编号"]))
            if result_hash:
                self.conn.insert_one(data)
                print("数据保存成功")
            else:
                print("数据重复")

    def close(self):
        self.redis_client.close()
        self.mongo_client.close()

    def main(self):
        page = int(input("请输入你要爬取的数据页数:"))
        for i in range(1, page+1):
            data = self.get_encrypt_params(i)
            self.get_data(data)

if __name__ == '__main__':
    PropertyTransaction = PropertyTransactionSpider()
    PropertyTransaction.main()