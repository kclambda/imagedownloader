import os
import json
import re
import sys
import time

import requests
import urllib3
from concurrent.futures import ThreadPoolExecutor

from util import image_name, headers, SECONDS
# 禁用HTTPS安全请求警告
urllib3.disable_warnings()


class ImageURL(object):
    def __init__(self):
        self.url = "https://{}/search/index?ct=201326592&tn=baiduimage&word={}&pn={}"
        self.re_image = re.compile(r"app\.setData\('imgData', (.*?)\);", re.S)  # Image information
        self.re_name_suffix = re.compile(r".*?\//.*\/.*?(\.\w+)")  # File name suffix
        self.domain_names = ['180.149.131.70', '182.61.62.30', '119.75.222.23', '112.34.112.11',
                             '14.215.177.185', '112.80.248.122', '180.97.33.134', '115.239.210.36',
                             '163.177.151.139']

    def parse_url(self):
        """
        访问不同地区的服务器，得到图片下载URL连接
        :return:
        """
        page = 0
        content = ""
        print("正在搜索图片，请稍等....")
        for domain_name in self.domain_names:
            while True:
                url = self.url.format(domain_name, sys.argv[1], page)
                # print(url)
                try:
                    response = requests.get(url, headers=headers(), verify=False)
                    # print(response.status_code)
                    if response.status_code == 200:
                        content = response.content.decode("utf-8")
                    if response.status_code == 403 or response.status_code == 302:
                        break
                except Exception as e:
                    print("当前服务器不存在您要搜索的图片，正在切换服务器...")
                    break
                content = self.re_image.findall(content)
                if len(content) == 0:
                    break
                content = content[0].replace("'", "\"")
                try:
                    image_info = json.loads(content)["data"]
                except Exception:
                    page += 30
                    # print("Json 字符串解析失败")
                    continue
                for image_url in image_info:
                    objurl = image_url.get("objURL")
                    image_url = image_url.get("thumbURL")
                    if image_url is None:
                        continue
                    url = f"https://{domain_name}/search/down?tn=download&word=download&ie=utf8&fr=detail&url={objurl}&thumburl={image_url}"
                    yield url
                # print(f"第{int((page+30)/30)}页加载完成，等待下载...")
                if int((page+30)/30) == 60:
                    break
                page += 30
                time.sleep(SECONDS*2)
            if domain_name == self.domain_names[-1] or int((page+30)/30) == 60:
                break
            continue

    def save_image(self, url):
        """
        保存图片，并且实现去重
        :param url: Image url
        :return:
        """
        local_path = f"./images/{sys.argv[1]}/"
        os.makedirs(local_path, exist_ok=True)
        content = ""
        try:
            response = requests.get(url, headers=headers(), verify=False)
            if response.status_code == 200:
                # print(f"{'---'*20} Image url request success {response.status_code}{'---'*40}")
                content = response.content
        except Exception as e:
            # print(f"----Request image url failure----")
            return
        if len(content) == 0:
            return
        name = image_name(content)
        image_url = re.findall(r"thumburl=(.*)", url)[0]
        name_suffix = self.re_name_suffix.findall(image_url)
        if len(name_suffix) == 1:
            suffix = name_suffix[0]
        if os.path.exists(local_path + f"{name}{suffix}"):
            print(f"图片 {name}{suffix} 已经存在")
            # time.sleep(SECONDS)
            return
        with open(local_path + f"{name}{suffix}", "ab") as f:
            f.write(content)
            f.flush()
        print(f"下载 {name}.jpg 成功")
        # time.sleep(SECONDS)

    def run(self):
        p = ThreadPoolExecutor(max_workers=16)
        for url in self.parse_url():
            p.submit(self.save_image, url)
        p.shutdown()


if __name__ == '__main__':
    image = ImageURL()
    while True:
        del sys.argv[1:]
        print("请输入要进行的操作，输入下载图片名称(例如：4k超高清壁纸)\n或者按回车（Enter键）直接退出应用")
        search_content = input(">>>:")
        if len(search_content) == 0:
            break
        try:
            input_content = search_content.split(",")
            sys.argv.append(input_content[0])
        except Exception:
            print("输入有误，请重新输入")
            continue
        image.run()
        DIR = f"./images/{input_content[0]}/"
        image_num = len([name for name in os.listdir(DIR) if os.path.isfile(os.path.join(DIR, name))])
        print(f"此次共下载了{image_num}张图片")
