import requests
import execjs
import pymongo
import redis
import hashlib
import time
import random
import json


class HangHangChaSpider:

    def __init__(self):
        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Client-Encrypt": "v1.1",
            "Connection": "keep-alive",
            "Origin": "https://www.hanghangcha.com",
            "Pragma": "no-cache",
            "Referer": "https://www.hanghangcha.com/hhcreport",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
            "X-Requested-With": "XMLHttpRequest",
            "clientInfo": "web",
            "clientVersion": "1.0.7",
            "currentHref": "https://www.hanghangcha.com/hhcreport",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
        self.cookies = {
            "JSESSIONID": "248E50D97C9E577CE9F2F6164606EEB3",
            "_ACCOUNT_": "MDI3NTc4ODcxZGYzNGM1NGJhMmY1OWVlYTY0NDk4M2MlNDAlNDBtb2JpbGU6MTc4NDAzMDMxMzMxMDplZGFlOWQ2ZTM3MmFjYzQ3NTQ3YjdhOTFjM2ZlYmQ4ZA"
        }
        self.url = "https://api.hanghangcha.com/hhc/member/industry/getReportList"
        self.mongo_client = pymongo.MongoClient(host="localhost", port=27017)
        self.redis_client = redis.Redis()

    @staticmethod
    def get_hash(value):
        md5_hash = hashlib.md5(str(value).encode("utf-8")).hexdigest()
        return md5_hash

    @staticmethod
    def open_js(js_file):
        with open(js_file, "r", encoding="utf-8") as f:
            js_code = f.read()
        ctx = execjs.compile(js_code)
        return ctx

    def get_data(self, page, ctx):
        params = {
            "filter": '{"reportType":null,"limit":10,"skip":%d}' % ((page - 1) * 10)
        }
        response = requests.get(self.url, headers=self.headers, cookies=self.cookies, params=params).json()
        my_datas = []
        result_data = ctx.call("get_decrypt_response", response["data"])
        result_json = json.loads(result_data)
        for items in result_json["data"]["data"]:
            my_datas.append({
                "报告ID": items.get("reportId", ""),
                "标题": items.get("title", ""),
                "页数": items.get("page", ""),
                "内容": items.get("desc", ""),
                "点赞": items.get("thumbsUpCount", ""),
                "创建时间": items.get("publish_date", ""),
                "查看次数": items.get("readCount", "")
            })
        self.save_data(my_datas)
        print(f"第{page}页数据采集完成！")

    def save_data(self, datas):
        for data in datas:
            result_hash = self.redis_client.sadd("HangHangCha_hash1", self.get_hash(data["报告ID"]))
            if result_hash:
                self.mongo_client["HangHangCha"]["report_info"].insert_one(data)
                print("数据采集完成！")
            else:
                print("数据重复！")

    def close_client(self):
        self.mongo_client.close()
        self.redis_client.close()

    def main(self):
        ctx = self.open_js("hhc-decrypt.js")
        page = int(input("请输入您要采集的页数: "))
        for i in range(1, page + 1):
            self.get_data(i, ctx)
            time.sleep(random.uniform(1, 3))
        self.close_client()


if __name__ == '__main__':
    HangHangCha = HangHangChaSpider()
    HangHangCha.main()
