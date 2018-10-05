from multiprocessing.dummy import Pool

import requests
import json
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import re
import pymongo
from config import *
import os
from multiprocessing import pool

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def get_page_index(offset, keyword):
    data={
        'offset': offset,
        'format': 'json',
        'keyword' : keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab' : '3',
        'from':'gallery'
    }
    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    response = requests.get(url)
    try:
        if response.status_code == 200:
            return response.text
        return None
    except:
        print('请求索引页出错')
        return None

def parse_page_index(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('article_url')

def get_page_detail(url):
    headers = {
        'referer'  : 'https://www.toutiao.com/search/?keyword=%E7%BE%BD%E7%94%9F%E7%BB%93%E5%BC%A6',
        'upgrade-insecure-requests' : '1',
        'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
    }

    try:
        response = requests.get(url,headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except:
        print('请求索引页出错')
        return None

def parse_page_detail(html,url):
    soup = BeautifulSoup(html,'lxml')
    title = soup.select('title')[0].get_text()
    #("")json.load（）参数应该是个字符串来着...
    images_pattern = re.compile('gallery: JSON.parse\((".*?")\)', re.S)
    result = re.search(images_pattern,html)

    if result:
        # load一次，type是str
        data = json.loads(json.loads(result.group(1)))

        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images = [item.get('url') for item in sub_images]
            for image in images: download_images(image)
            return {
                'title' : title,
                'url' :url,
                'images': images
            }

def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print("存入Mongo成功")
        return True
    return False

def download_images(url):
    headers = {
        'Host': 'p1.pstatp.com',
        'Upgrade - Insecure - Requests': '1',
        'User - Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'If - Modified - Since': 'Wed, 19 Sep 2018 06:15: 35GMT'
    }
    print("当前正在下载", url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            save_image(response.content)
        return None
    except:
        print('请求图片出错', url)
        return None
def save_image(content):
    from _md5 import md5
    path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(path):
        with open(path, 'wb') as f:
            f.write(content)
            f.close()

def main(offset):
    html = get_page_index(offset, KEY_WORD)
    for url in parse_page_index(html):
        html = get_page_detail(url)
        if html:
            result =parse_page_detail(html, url)

            try:
               # save_to_mongo(result)
               pass
            except:
                print('请求索引页出错')

if __name__ == '__main__':
    groups = [x*20 for x in range(GROUP_START, GROUP_END+1)]
    pool = Pool()
    pool.map(main, groups)