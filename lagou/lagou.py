import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import uuid

def get_uuid():
    return str(uuid.uuid4())
def crawl_detail(id):
    cookie = "JSESSIONID=" + get_uuid() + ";" \
                                          "user_trace_token=" + get_uuid() + "; LGUID=" + get_uuid() + "; index_location_city=%E6%88%90%E9%83%BD; " \
                                                                                                       "SEARCH_ID=" + get_uuid() + '; _gid=GA1.2.717841549.1514043316; ' \
                                                                                                                                   '_ga=GA1.2.952298646.1514043316; ' \
                                                                                                                                   'LGSID=' + get_uuid() + "; " \
                                                                                                                                                           "LGRID=" + get_uuid() + "; "
    url = 'https://www.lagou.com/jobs/%s.html' %id
    headers = {
        'Host' : 'www.lagou.com',
        'Origin' : 'https://www.lagou.com',
        'Referer' : 'https://www.lagou.com/jobs/list_python?city=%E6%9D%AD%E5%B7%9E&cl=false&fromSearch=true&labelWords=&suginput=',
        'Upgrade-Insecure-Requests' : '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Cookie' : cookie
    }

    result = requests.get(url, headers=headers)
    soup = BeautifulSoup(result.text,'lxml')
    job_bt = soup.find('dd', attrs={'class': 'job_bt'})
    try:
        return job_bt.text
    except Exception :
        print('职位详情请求失败，正在重新请求...')
        time.sleep(25)
        crawl_detail(id)

def get_info(i,headers,x):
    positions = []
    data = {
        'first': 'false',
        'pn': i,
        'kd': 'java'
    }
    result = requests.post('https://www.lagou.com/jobs/positionAjax.json?city='
                           '%E6%9D%AD%E5%B7%9E&needAddtionalResult=false', headers=headers, data=data)
    result = result.json()
    if (result['success']):
        page_positions = result['content']['positionResult']['result']
        df = pd.DataFrame(page_positions)

        # 页详情
        for position in page_positions:
            dict = {
                'position_name': position['positionName'],
                'salary': position['salary'],
                'workYear': position['workYear'],
                'companyFullName': position['companyFullName'],
                'positionAdvantage': position['positionAdvantage'],
                'financeStage': position['financeStage'],
                'companySize': position['companySize'],
                'district': position['district']

            }
            position_id = position['positionId']
            position_detail = crawl_detail(position_id)
            dict['position_detail'] = position_detail
            positions.append(dict)
            x = x + 1
            print("-----------------------------------------------------------", x)
    else:
        print('页详情请求失败，重新请求中...')
        time.sleep(10)
        get_info(i, headers, x)

    return positions

def main():
    cookie = "JSESSIONID=" + get_uuid() + ";" \
                    "user_trace_token=" + get_uuid() + "; LGUID=" + get_uuid() + "; index_location_city=%E6%88%90%E9%83%BD; " \
                            "SEARCH_ID=" + get_uuid() + '; _gid=GA1.2.717841549.1514043316; ' \
                          '_ga=GA1.2.952298646.1514043316; ' \
                        'LGSID=' + get_uuid() + "; " \
                          "LGRID=" + get_uuid() + "; "

    headers = {
        'Accept': 'application / json, text / javascript, * / *; q = 0.01',
        'Accept - Encoding': 'gzip, deflate, br',
        'Accept - Language': 'zh - CN, zh; q = 0.8',
        'Connection': 'keep - alive',
        'Content - Length': '41',
        'Content - Type':'application / x - www - form - urlencoded; charset = UTF - 8',
        'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
        'Host': 'www.lagou.com',
        'Referer' : 'https://www.lagou.com/jobs/list_java%E5%AE%9E%E4%B9%A0?city=%E6%9D%AD%E5%B7%9E&cl=false&fromSearch=true&labelWords=&suginput=',
        'X - Anit - Forge - Code': '0',
        'X - Anit - Forge - Token': None,
        'X - Requested - With': 'XMLHttpReques',
        'Cookie' : cookie
    }

    x = 0
    total = []
    for i in range(1,30):
        list = get_info(i, headers, x)
        for position in list:
            total.append(position)
    df = pd.DataFrame(total)
    df.to_csv("java_bigSet.csv")
if __name__ == "__main__":
    main()
