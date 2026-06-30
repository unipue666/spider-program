from DrissionPage import ChromiumPage, ChromiumOptions
from DrissionPage.common import By
import pymysql
import hashlib
import redis


class StructerSpider:

    def __init__(self):
        browser_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        co = ChromiumOptions()
        co.set_browser_path(browser_path)
        self.page = ChromiumPage(co)
        self.mysql_client = None
        self.cursor = None
        self.redis_client = redis.Redis()

    def init_db(self):
        conn = pymysql.connect(host="localhost", port=3306, user="root", password="123456")
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS StructerServer")
        cursor.execute("USE StructerServer")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS StructerServer_INFO(
                id INT PRIMARY KEY AUTO_INCREMENT,
                `统一信用社代码` VARCHAR(255) NOT NULL,
                `企业名称` VARCHAR(255) NOT NULL,
                `企业法定代表人` VARCHAR(255) NOT NULL,
                `企业注册属地` VARCHAR(255) NOT NULL
            )

        """)
        conn.commit()
        self.mysql_client = conn
        self.cursor = cursor

    @staticmethod
    def get_hash(value):
        md5_hash = hashlib.md5(str(value).encode("utf-8")).hexdigest()
        return md5_hash

    def open_url(self, url):
        self.page.get(url)
        self.page.set.window.max()

    def get_data(self, page):
        for i in range(page):
            self.page.wait.eles_loaded((By.XPATH, '//tbody'), timeout=10)
            my_datas = []
            page_information = self.page.eles((By.XPATH, "//tr[@class='el-table__row']"))
            for items in page_information:
                unified_code = items.ele((By.XPATH, "./td[2]/div"), timeout=0)
                company_name = items.ele((By.XPATH, "./td[3]//span"), timeout=0)
                legal_representative = items.ele((By.XPATH, "./td[4]/div"), timeout=0)
                registered_location = items.ele((By.XPATH, "./td[5]/div"), timeout=0)
                print(unified_code.text, company_name.text, legal_representative.text, registered_location.text)
                my_datas.append({
                    "统一信用社代码": unified_code.text if unified_code else '暂无数据',
                    "企业名称": company_name.text if company_name else '暂无数据',
                    "企业法定代表人": legal_representative.text if legal_representative else '暂无数据',
                    "企业注册属地": registered_location.text if registered_location else '暂无数据'
                })
            self.save_data(my_datas)
            print(f"{i + 1}页数据采集完成！")
            self.page.ele((By.XPATH, "//button[@class='btn-next']")).click()
            self.page.wait(5)

    def save_data(self, datas):
        for data in datas:
            result = self.redis_client.sadd("structer_hash1", self.get_hash(data))
            if result:
                sql = "insert into StructerServer_INFO(`统一信用社代码`, `企业名称`, `企业法定代表人`, `企业注册属地`) values(%s, %s, %s, %s)"
                self.cursor.execute(sql, (
                data['统一信用社代码'], data['企业名称'], data['企业法定代表人'], data['企业注册属地']))
                self.mysql_client.commit()
                print("数据保存成功")
            else:
                print("数据重复")

    def close_client(self):
        self.mysql_client.close()
        self.redis_client.close()

    def main(self):
        self.init_db()
        url = "https://jzsc.mohurd.gov.cn/data/company"
        self.open_url(url)
        page = int(input("请输入你要爬的页数："))
        self.get_data(page)
        self.close_client()


if __name__ == '__main__':
    StructerServer = StructerSpider()
    StructerServer.main()