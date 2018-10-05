from io import BytesIO
from urllib.parse import urlencode
import requests
import re
import json
import execjs
from bs4 import BeautifulSoup
from PIL import Image
from pymongo import MongoClient

conn = MongoClient('localhost',27017)
db = conn['comics']

def get_comic(comic_name):
    param = {'s':comic_name}

    url = 'https://sacg.dmzj.com/comicsum/search.php?' + urlencode(param)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Referer': 'https://manhua.dmzj.com/tags/search.shtml?s=%E5%9B%9B%E6%9C%88%E6%98%AF%E4%BD%A0%E7%9A%84%E8%B0%8E%E8%A8%80',
        'Host': 'sacg.dmzj.com',
    }
    response = requests.get(url ,headers=headers)
    str = re.search("\[(.*?)\];",response.text).group(1)
    comic_url = 'https:' + json.loads(str)['comic_url_raw']
    return comic_url

def get_chapter(comic_url):
    response = requests.get(comic_url)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    srcs = soup.find('div',class_="cartoon_online_border").find_all('a')
    chapters_url = []
    for a in srcs:
        chapters_url.append(a.get('href'))
    return chapters_url

def get_chapter_imgs_url(chapter_url):
    response = requests.get(chapter_url)
    js_str = re.search('eval\((.*?)\)\n', response.text).group(1)
    js_str = js_str.replace('function(p,a,c,k,e,d)', 'function fun(p, a, c, k, e, d)')

    fun = """
             function run(){
                    var result = %s;
                    return result;
                }
        """ % js_str
    pages = execjs.compile(fun).call('run')
    data = pages.split('=')[2][1:-2]
    url_list = json.JSONDecoder().decode(data)
    for i in range(0, len(url_list)):
        url_list[i] = 'https://images.dmzj.com/' + url_list[i]
    # url_list = dict(zip(range(1,len(url_list)+1),url_list))
    return url_list

def download_imgs(src_list, comic_name):
    for src in src_list:
        response = requests.get(src)
        image = Image.open(BytesIO(response.content))
        image.save('D:/')

def save_to_mongo(comic_name,list):
    if(db[comic_name].insert(list)):
        print('存入Mongo成功')
        return True
    return  False


def main():
    comic_name = '四月是你的谎言'
    comic_url = get_comic(comic_name)
    chapters_url = get_chapter(comic_url)
    list = {}
    for i in range(0, len(chapters_url)):
        chapters_url[i] = 'https://manhua.dmzj.com' + chapters_url[i]
        list['_id'] = i + 1
        list['chapter'] = (i + 1)
        list['img'] = (get_chapter_imgs_url(chapters_url[i]))
        save_to_mongo(comic_name,list)
    #download_imgs(list,comic_name)


if __name__ == '__main__':
    main()