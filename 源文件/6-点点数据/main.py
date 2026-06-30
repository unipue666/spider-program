import requests
import pymongo
import hashlib
import redis
import execjs
from datetime import datetime

class DianDianSpider:

    def __init__(self):
        self.headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Origin": "https://app.diandian.com",
    "Pragma": "no-cache",
    "Referer": "https://app.diandian.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
    "language": "zh",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
        self.url = "https://api.diandian.com/pc/app/v1/rank"
        self.cookies = {
    "i18n_app_redirected": "zh",
    "deviceid": "f5080ac1698139d75290ede14ae495e",
    "_ga": "GA1.1.675695650.1782720520",
    "token": "029c57e6c8d195f1917cf2ae0d8065be519fa529457a2c1b1bbc1f18772526ded4b2569869d28ea1f52c7b6c673dffbc3180effb8904afba76429700f77cab448b619bdcdd7c2c3f37fa69d26fde7010",
    "_ga_GVCWL6PNZ2": "GS2.1.s1782740125$o2$g1$t1782741505$j60$l0$h0"
}
        self.mongo_client = pymongo.MongoClient(host="localhost", port=27017)
        self.redis_client = redis.Redis()

    @staticmethod
    def get_hash(value):
        md5_hash = hashlib.md5(str(value).encode("utf-8")).hexdigest()
        return md5_hash

    def open_js(self, js_file):
        with open(js_file, "r", encoding="utf-8")as f:
            js_code = f.read()
        ctx = execjs.compile(js_code)
        return ctx

    def get_data(self, ctx, page):
        result_params = ctx.call("get_encrypt_k", page)
        response = requests.get(self.url, headers=self.headers, cookies=self.cookies, params=result_params["params"]).json()
        my_datas = []
        for items in response["data"]["apps"]:
            my_datas.append({
                "app_id": items["app_id"],
                "app_name": items["name"],
                "rating": items["rating"],
                "rating_count": items["rating_count"],
                "last_release_time": datetime.fromtimestamp(items["last_release_time"]).strftime("%Y-%m-%d")
            })
        self.save_data(my_datas)
        print(f"第{page}页数据采集完成！")

    def save_data(self, datas):
        for data in datas:
            result_hash = self.redis_client.sadd("DianDian_hash1", self.get_hash(data["app_id"]))
            if result_hash:
                self.mongo_client["DianDian"]["information_info"].insert_one(data)
                print("数据采集完成！")
            else:
                print("数据重复！")

    def close_client(self):
        self.mongo_client.close()
        self.redis_client.close()

    def main(self):
        ctx = self.open_js("DD-encrypt.js")
        page = int(input("请输入您要采集的页数: "))
        for i in range(1, page+1):
            self.get_data(ctx, i)
        self.close_client()

if __name__ == '__main__':
    DianDian = DianDianSpider()
    DianDian.main()