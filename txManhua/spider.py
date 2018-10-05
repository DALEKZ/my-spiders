import json
import base64
import urllib
from urllib.parse import urlencode, quote
import requests
import re
import time
from pymongo import MongoClient

conn = MongoClient('localhost', 27017)
db = conn['comics']
proxy_pool_url  = 'http://localhost:5555/random'
proxy = None

def get_proxy():
    try:
        response = requests.get(proxy_pool_url)
        if response.status_code == 200:
            return response.text
    except ConnectionError:
        return None


def get_comic_id(commic_name):
    commic_urlcode = quote(commic_name)
    url = 'http://ac.qq.com/Comic/search/word/' + commic_urlcode
    response = requests.get(url)
    commic_id = response.text.split("|")[0]
    return commic_id

def get_comic_chapter(comic_id,cid):
    global proxy
    url = 'http://ac.qq.com/ComicView/index/id/' + comic_id + '/cid/' + str(cid)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Upgrade - Insecure - Requests': '1'
    }
    response = requests.get(url, headers=headers)
    html = response.text
    base64_str = re.search(' var DATA        = \'(.*?)\',',html).group(1)[1:]
    info = base64.b64decode(base64_str).decode('utf-8')
    pics = json.loads(info)['picture']
    for pic in pics:
        pic['chap'] = cid
        pic.pop('width')
        pic.pop('height')
    return pics

def save_to_mongo(commic_name,chap):
    if db[commic_name].insert_many(chap):
        print('chapter'+str(chap[0]['chap'])+'存入Mongo成功')
        return True
    return  False


def main():
    commic_name = '四月是你的谎言'
    comic_id  = get_comic_id(commic_name)
    for i in range(1,44):
        chap = get_comic_chapter(comic_id, i)
        save_to_mongo(commic_name,chap)

if __name__=='__main__':
    main()