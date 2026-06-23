import requests
import pymongo
import redis
import hashlib
import execjs
import json


class BirdWatchingSpider:

    def __init__(self):
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.birdreport.cn",
            "Pragma": "no-cache",
            "Referer": "https://www.birdreport.cn/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
            "requestId": "9dd76142f1907f4463fb1a4f1a82adc8",
            "sec-ch-ua": "\"Chromium\";v=\"148\", \"Microsoft Edge\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sign": "6a8f8b8070faae518859f34fa7de843b",
            "timestamp": "1780400997000"
        }
        self.api_url = "https://api.birdreport.cn/front/activity/search"
        self.mongo_client = pymongo.MongoClient(host="localhost", port=27017)
        self.conn = self.mongo_client["bird_watching"]["information_info"]
        self.redis_client = redis.Redis()

    @staticmethod
    def get_hash(value):
        md5_hash = hashlib.md5(str(value).encode("utf-8")).hexdigest()
        return md5_hash

    def get_encrypt_headers_data(self, page):
        with open("bird-watching-crypto.js", "r", encoding="utf-8")as f:
            js_code = f.read()
        ctx = execjs.compile(js_code)
        result = ctx.call("get_encrypt", page)
        self.headers["requestId"] = result["requestId"]
        self.headers["sign"] = result["sign"]
        self.headers["timestamp"] = str(result["timestamp"])
        return result["data"]

    def decrypt_response(self, encrypt_data):
        with open("bird-watching-crypto.js", "r", encoding="utf-8")as f:
            js_code = f.read()
        ctx = execjs.compile(js_code)
        result = ctx.call("get_decrypt_data", encrypt_data)
        return result

    def get_data(self, data, page):
        response_data = requests.post(self.api_url, headers=self.headers, data=data).json()["data"]
        decrypt_datas = json.loads(self.decrypt_response(response_data))
        my_datas = []
        for items in decrypt_datas:
            my_datas.append({
                "报告编号": items["serialId"],
                "观测时间": items["startTime"] + "至" + items["endTime"],
                "观测地点": items["address"],
                "记录用户": items["username"],
                "鸟种数量": items["taxonCount"],
                "浏览数": items["visitsCount"]
            })
        self.save_data(my_datas)
        print(f"第{page}页数据采集完成")

    def save_data(self, datas):
        for data in datas:
            result_hash = self.redis_client.sadd("BirdWatching_hash1", self.get_hash(data["报告编号"]))
            if result_hash:
                self.conn.insert_one(data)
                print("数据保存成功")
            else:
                print("数据重复")

    def main(self):
        page = int(input("请输入采集页数："))
        for i in range(1, page+1):
            data = self.get_encrypt_headers_data(i)
            self.get_data(data, i)

if __name__ == '__main__':
    BWS = BirdWatchingSpider()
    BWS.main()

