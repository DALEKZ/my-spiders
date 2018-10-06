from urllib.parse import urlencode
import requests
import re
import json
import execjs
from bs4 import BeautifulSoup
from pymongo import MongoClient
import os

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
    # 提取存有图片url信息的js代码
    response = requests.get(url ,headers=headers)
    str = re.search("\[(.*?)\];",response.text).group(1)
    str = re.search("({.*?})",str).group(1)
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

# 运行存有图片url的js代码
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



def save_to_mongo(comic_name,list):
    if(db[comic_name].insert(list)):
        print('存入Mongo成功')
        return True
    return  False

def save_images(content, comic_name, chap, imgNum):
    root_path = 'D:\\comic\\' + comic_name
    if not os.path.exists(root_path):
        os.mkdir(root_path)
    chapter_path = root_path + '\第' + str(chap) + '话\\'
    if not os.path.exists(chapter_path):
        os.mkdir(chapter_path)
    path = chapter_path + str(imgNum) + '.jpg'
    if not os.path.exists(path):
        with open(path, 'wb') as f:
            f.write(content)
            f.close()
            print(path + '下载完成')

def download_images(comic_name):
    table = db[comic_name]
    # 破解图片防盗链（低级版），加referer即可
    headers = {
        'User - Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Upgrade - Insecure - Requests': '1',
        'Referer': 'https://www.baidu.com/link?url=g3QbzSNbZietJQ_Rf4wcjn8RDipbM5wWtRYwvndTU64RtUj0yIVYBz75dHfoLnu9&wd=&eqid=ca0acac40002851a000000065bb84b15'
    }
    for src in table.find({}, {"_id": 0}):
        i = 0
        for url in src['img']:
            i+=1
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    save_images(response.content, comic_name, src['chapter'], i)
                elif response.status_code == 403:
                    print('403 Forbidden ')
            except Exception as e:
                print('请求图片出错', url)
                print('error ', e)


def main():
    comic_name = '四月是你的谎言'
    # comic_url = get_comic(comic_name)
    # chapters_url = get_chapter(comic_url)
    list = {}
    # for i in range(0, len(chapters_url)):
    #     chapters_url[i] = 'https://manhua.dmzj.com' + chapters_url[i]
    #     list['_id'] = i + 1
    #     list['chapter'] = (i + 1)
    #     list['img'] = (get_chapter_imgs_url(chapters_url[i]))
    #     save_to_mongo(comic_name,list)
    download_images(comic_name)


if __name__ == '__main__':
    main()

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