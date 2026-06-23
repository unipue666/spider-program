import redis
import requests
import execjs
import time
import pymongo
import hashlib
import random


class YiBaoSpider:

    def __init__(self):
        self.headers = {
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Origin": "https://fuwu.nhsa.gov.cn",
            "Pragma": "no-cache",
            "Referer": "https://fuwu.nhsa.gov.cn/nationalHallSt/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
            "X-Tingyun": "c=B|4Nl_NnGbjwY;x=da81e6c3d25b4487",
            "channel": "web",
            "contentType": "application/x-www-form-urlencoded",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "x-tif-nonce": "g5pBPE0T",
            "x-tif-paasid": "undefined",
            "x-tif-signature": "16193054b93e9ff0e039967a29fa9c00131d0157271cbe485ba6c317738aa072",
            "x-tif-timestamp": "1781587893"
        }
        self.cookies = {
            "amap_local": "410400",
            "yb_header_active": "-1",
            "acw_tc": "276082b217815878870114561ee8992ff5355d625aa06b89ab4908706db244"
        }
        self.url = "https://fuwu.nhsa.gov.cn/ebus/fuwu/api/nthl/api/CommQuery/queryFixedHospital"
        self.mongo_client = pymongo.MongoClient(host="localhost", port=27017)
        self.conn = self.mongo_client["YiBao"]["information_info"]
        self.redis_client = redis.Redis()

    @staticmethod
    def get_hash(value):
        md5_hash = hashlib.md5(str(value).encode("utf-8")).hexdigest()
        return md5_hash

    @staticmethod
    def open_js(js_file):
        with open(js_file, "r", encoding="utf-8")as f:
            js_code = f.read()
        ctx = execjs.compile(js_code)
        return ctx

    def get_request_encrypt(self, page, ctx):
        result = ctx.call("get_encrypt", page)
        self.headers["x-tif-nonce"] = result["headers"]["x-tif-nonce"]
        self.headers["x-tif-signature"] = result["headers"]["x-tif-signature"]
        self.headers["x-tif-timestamp"] = str(result["headers"]["x-tif-timestamp"])
        data = result["data"]
        return data

    def get_decrypt_data(self, ctx, data):
        response = requests.post(self.url, headers=self.headers, cookies=self.cookies, data=data).json()
        result = ctx.call("get_decrypt", response)
        my_datas = []
        page_infos = result["list"]
        for items in page_infos:
            addr = items.get("addr", '')
            my_datas.append({
                "唯一编号": items["medinsCode"],
                "医疗机构名称": items["medinsName"],
                "医疗机构类型": items["medinsTypeName"],
                "医疗机构等级": items["medinsLvName"],
                "详细地址": addr if addr else "暂无数据"
            })
        self.save_data(my_datas)
        print("-" * 20)

    def save_data(self, datas):
        for data in datas:
            result_hash = self.redis_client.sadd("YiBao_hash2", self.get_hash(data["唯一编号"]))
            if result_hash:
                self.conn.insert_one(data)
                print("数据采集完成！")
            else:
                print("数据重复！")

    def close_client(self):
        self.mongo_client.close()
        self.redis_client.close()

    def main(self):
        # ctx = input("请输入js文件：")
        ctx = self.open_js("nhsa-crypto.js")
        page = int(input("请输入您要采集的页数: "))
        for i in range(1, page+1):
            data = self.get_request_encrypt(i, ctx)
            self.get_decrypt_data(ctx, data)
            time.sleep(random.uniform(1, 3))
        self.close_client()


if __name__ == '__main__':
    YiBao = YiBaoSpider()
    YiBao.main()