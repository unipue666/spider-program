import execjs
import requests
import pymysql
import redis
import hashlib
import json
import time
import random


class SichuanSpider:

    def __init__(self):
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "http://202.61.89.161:12021",
            "Pragma": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
            "sign": "5d08965477a10399a5acd514e0b9e16f3be18fda8a5f5604bd30ebcf958ae12e9e29bfd43b97b4f08a19058df30499234a19af7d6062d43de17aae6994021c13ba532c7c82c95484140e5a9ffbe7ae48",
            "source": "ZRCSL7V0JIRK1PHY",
            "timestamp": "db8a0b708a4f0f56002b128c8cf38d5b",
            "urlprefix;": ""
        }
        self.url = "http://202.61.89.161:12021/api/api/loginSidePageEDE/getPurchaseOfAgriculturalMachinery"
        self.mysql_client = None
        self.cursor = None
        self.redis_client = redis.Redis()

    def init_db(self):
        conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456")
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS sichuan")
        cursor.execute("USE sichuan")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sichuan_info(
                id INT PRIMARY KEY AUTO_INCREMENT,
                `县` VARCHAR(255) NOT NULL,
                `所在乡（镇）` VARCHAR(255) NOT NULL,
                `购机者名字` VARCHAR(255) NOT NULL,
                `机具品目` VARCHAR(255) NOT NULL,
                `生产厂家` VARCHAR(255) NOT NULL,
                `产品名称` VARCHAR(255) NOT NULL,
                `购买机型` VARCHAR(255) NOT NULL,
                `购买数量` VARCHAR(255) NOT NULL,
                `经销商` VARCHAR(255) NOT NULL,
                `购买日期` VARCHAR(255) NOT NULL,
                `单台销售价格` VARCHAR(255) NOT NULL,
                `单台中央补贴` VARCHAR(255) NOT NULL,
                `出厂编号` VARCHAR(255) NOT NULL
            )
        """)
        conn.commit()
        self.mysql_client = conn
        self.cursor = cursor

    @staticmethod
    def get_hash(value):
        md5_hash = hashlib.md5(str(value).encode("utf-8")).hexdigest()
        return md5_hash

    def get_ctx(self):
        with open("sichuan-crypto.js", "r", encoding="utf-8") as f:
            js_code = f.read()
        ctx = execjs.compile(js_code)
        return ctx

    def get_data(self, page, ctx):
        result_encrypt = ctx.call("get_encrypt", page)
        self.headers["sign"] = result_encrypt["encrypt_headers"]["sign"]
        self.headers["timestamp"] = result_encrypt["encrypt_headers"]["timestamp"]
        self.headers["source"] = result_encrypt["encrypt_headers"]["source"]
        data = {
            "parameter": result_encrypt["encrypt_parma"]
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(url=self.url, headers=self.headers, data=data).json()
        encrypt_data = response["data"]
        result_decrypt = ctx.call("decrypt_res", encrypt_data)
        my_datas = []
        for items in result_decrypt:
            my_datas.append({
                "county": items["county"],
                "town": items["town"],
                "buyName": items["buyName"],
                "itemName": items["itemName"],
                "factoryName": items["factoryName"],
                "productName": items["productName"],
                "machineCode": items["machineCode"],
                "equipmentNo": items["equipmentNo"],
                "agentName": items["agentName"],
                "purchaseDate": items["purchaseDate"],
                "everySalePrice": items["everySalePrice"],
                "everySubsidy": items["everySubsidy"],
                "factoryNumber": items["factoryNumber"]
            })
        self.sava_data(my_datas)
        print(f"第{page}页数据采集完成！")

    def sava_data(self, datas):
        for data in datas:
            result_hash = self.redis_client.sadd("sichuan_hash2", self.get_hash(data["factoryNumber"]))
            if result_hash:
                sql = "insert into sichuan_info(`县`, `所在乡（镇）`, `购机者名字`, `机具品目`, `生产厂家`, `产品名称`, `购买机型`, `购买数量`, `经销商`, `购买日期`, `单台销售价格`, `单台中央补贴`, `出厂编号`) values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                self.cursor.execute(sql, (data["county"], data["town"], data["buyName"], data["itemName"], data["factoryName"], data["productName"], data["machineCode"], data["equipmentNo"], data["agentName"], data["purchaseDate"], data["everySalePrice"], data["everySubsidy"], data["factoryNumber"]))
                self.mysql_client.commit()
                print("数据保存成功")
            else:
                print("数据重复")

    def close_client(self):
        self.mysql_client.close()
        self.redis_client.close()

    def main(self):
        self.init_db()
        ctx = self.get_ctx()
        page = int(input("请输入采集的页数："))
        for i in range(1, page + 1):
            self.get_data(i, ctx)
            time.sleep(random.uniform(0, 2))
        self.close_client()

if __name__ == '__main__':
    spider = SichuanSpider()
    spider.main()