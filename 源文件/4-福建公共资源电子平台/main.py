import requests
import execjs
import csv
import json


class FuJianSpider:

    def __init__(self):
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://ggzyfw.fj.gov.cn",
            "Pragma": "no-cache",
            "Referer": "https://ggzyfw.fj.gov.cn/index/newList/?type=11",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0",
            "portal-sign": "596357e51728b3dc2acb2e31cf7fcad1",
            "sec-ch-ua": "\"Microsoft Edge\";v=\"149\", \"Chromium\";v=\"149\", \"Not)A;Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
        self.url = "https://ggzyfw.fj.gov.cn/FwPortalApi/Article/PageList"
        self.js_code = open("福建_crypto.js", "r", encoding="utf-8").read()
        self.ctx = execjs.compile(self.js_code)
        self.headers_written = False

    def get_data(self, page):
        result_encrypt = self.ctx.call("get_encrypt_header", page)
        self.headers["portal-sign"] = result_encrypt["portal-sign"]
        data = {
            "pageNo": page,
            "pageSize": 10,
            "total": 748,
            "type": "11",
            "timeType": "0",
            "ts": result_encrypt["ts"]
        }
        data = json.dumps(data, separators=(',', ':'))
        response = requests.post(self.url, headers=self.headers, data=data).json()
        encrypt_data = response["Data"]
        decrypt_data = self.ctx.call("get_decrypt_response", encrypt_data)
        my_datas = []
        for items in decrypt_data["Table"]:
            my_datas.append({
                "编号": items["ID"],
                "标题": items["TITLE"],
                "时间": items["TM"]
            })
        self.save_data(my_datas)
        print(f"第{page}页数据采集完成")

    def save_data(self, my_datas):
        with open("福建.csv", "a", encoding="utf-8", newline="")as f:
            header = ["编号", "标题", "时间"]
            writer = csv.DictWriter(f, header)
            if not self.headers_written:
                writer.writeheader()
                self.headers_written = True
            writer.writerows(my_datas)

    def main(self):
        page = int(input("请输入你要采集的页数："))
        for i in range(1, page + 1):
            self.get_data(i)

if __name__ == '__main__':
    spider = FuJianSpider()
    spider.main()