import os
import sys
import requests
import json
import subprocess
import pymongo
import redis
import hashlib


class JianYuSpider:

    def __init__(self):
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "origin": "https://www.jianyu360.cn",
            "pragma": "no-cache",
            "referer": "https://www.jianyu360.cn/jylab/supsearch/index.html?searchGroup=1",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
        }
        self.cookies = {
            "SESSIONID": "bc9ac8706717c346aeca7bfbe8303b428a9c8797",
            "JYGuestUID": "2069216487628865536",
            "fid": "7c69b68dde7efd88bec1892f3dc8ac89",
            "JYTrustedId": "QwxGVwdCClRVUEMKFgpdTFBVUgRMVkIIVhBRCFBWTFZaRE9GAgYIB0VZRFZSQgAICQNBWkNY",
            "limitSearchTextFlag": "aaImQ1782174630997345456",
            "eid": "Z5UZV2y5nycJt5+SR8l9CtJQCooGkyqTpidc+V1RvKBprcEhuHU8N58SGIOGws9jbPXEZr/B/MDAMqlUrihAJ6vOJEp9Xi+OtzMQVtPfZ8fT3JlUH9dPBzb2pkNb0jEvlyaq2yrhuwzKkKe70d8iiGsbPugp14WRYYODkRn2cP4="
        }
        self.url = "https://www.jianyu360.cn/jyapi/jybx/core/fType/searchList"
        self.mongo_client = pymongo.MongoClient(host="localhost", port=27017)
        self.redis_client = redis.Redis()

    @staticmethod
    def get_hash(value):
        md5_hash = hashlib.md5(str(value).encode("utf-8")).hexdigest()
        return md5_hash

    def node_decrypt(self, encrypt_text, secret_key):
        proc = subprocess.run(
            ["node", "decrypt_wrapper.js"],
            input=json.dumps({"encrypt_text": encrypt_text, "secret_key": secret_key}),
            capture_output=True, text=True, encoding="utf-8", timeout=30,
            cwd=os.path.dirname(__file__)
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Node.js 解密失败: {proc.stderr}")
        return json.loads(proc.stdout)

    def get_data(self, page):
        data = {
            "searchGroup": 1,
            "reqType": "lastNews",
            "pageNum": page,
            "pageSize": 50,
            "keyWords": "",
            "searchMode": 0,
            "bidField": "",
            "publishTime": "1750823045-1782359045",
            "selectType": "title,content",
            "subtype": "",
            "exclusionWords": "",
            "buyer": "",
            "winner": "",
            "agency": "",
            "industry": "",
            "province": "",
            "city": "",
            "district": "",
            "buyerClass": "",
            "fileExists": "",
            "price": "",
            "buyerTel": "",
            "winnerTel": "",
            "basicClass": "",
            "deadlineType": ""
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(self.url, headers=self.headers, cookies=self.cookies, data=data).json()
        encrypt_text = response["data"]
        secret_key = response["secretKey"]
        result = self.node_decrypt(encrypt_text, secret_key)
        decrypt_data = json.loads(result["value"]) if isinstance(result.get("value"), str) else result
        my_datas = []
        for item in decrypt_data.get("data", {}).get("list", []):
            my_datas.append({
                "title": item.get("title", ""),
                "publishTime": item.get("publishTime", ""),
                "area": item.get("area", ""),
                "city": item.get("city", ""),
                "district": item.get("district", ""),
                "industry": item.get("industry", ""),
                "subtype": item.get("subtype", ""),
                "site": item.get("site", ""),
                "noticeId": item.get("id", ""),
            })
        self.save_data(my_datas)
        print(f"第{page}页数据采集完成！")

    def save_data(self, datas):
        for data in datas:
            try:
                result_hash = self.redis_client.sadd("JianYu_hash1", self.get_hash(data.get("noticeId")))
                if result_hash:
                    self.mongo_client["JianYu"]["bidding_info"].insert_one(data)
                    print("数据保存成功")
                else:
                    print("数据重复")
            except Exception as e:
                print("存储失败:", e)

    def close_client(self):
        self.mongo_client.close()
        self.redis_client.close()

    def main(self):
        if len(sys.argv) > 1:
            page = int(sys.argv[1])
        else:
            page = int(input("请输入您要采集的页数: "))
        for i in range(1, page + 1):
            self.get_data(i)
        self.close_client()


if __name__ == '__main__':
    JianYu = JianYuSpider()
    JianYu.main()
