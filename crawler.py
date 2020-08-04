#!/usr/bin/python3
# -*- coding: utf-8 -*-
import requests
import json
from bs4 import BeautifulSoup
import time
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs
import abc
from config import DOMAIN_TZ_DIC
import asyncio
import aiohttp


class Crawler(metaclass=abc.ABCMeta):
    @staticmethod
    def get_domain_path_query(url):
        o = urlparse(url)
        return o.netloc, o.path, o.query

    def __init__(self, url, sz=10):
        self.domain, self.path, self.query = Crawler.get_domain_path_query(url)
        self._get_domain_tz()
        self.list_sz = sz
        self.loop = asyncio.get_event_loop()
        # print("__init__", "domain",self.domain, "path",self.path, self.query, self.TZ, self.list_sz)

    def _get_response(self, url):
        response = requests.get(url)
        if not response.ok:
            response.raise_for_status()
        return response

    async def _get_content(self, url):
        content = ""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                content = await res.text()
        return content


    def _get_domain_tz(self):
        self.TZ = DOMAIN_TZ_DIC.get(self.domain)

    @abc.abstractmethod
    def get_list(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_articles(self):
        raise NotImplementedError

class BinanceCrawler(Crawler):
    def __init__(self, url):
        Crawler.__init__(self, url)
        # self.TZ = "+0900"

    def get_list(self):
        list_url = "https://www.binance.com/kr/support/announcement"
        contents = self.loop.run_until_complete(asyncio.gather(self._get_content(list_url)))
        content = contents[0]
        dom = BeautifulSoup(content, 'html.parser')
        app_data = dom.select_one("#__APP_DATA")
        app_dic = json.loads(app_data.text)

        catalogs = app_dic['routeProps']['fca4']['catalogs']
        post_list = []
        for catalog in catalogs:
            for article in catalog['articles']:
                post_dic = {
                    "url": "https://www.binance.com/kr/support/articles/%s" % article['code'],
                    "title": article['title']
                }
                post_list.append(post_dic)
        return post_list[:self.list_sz]


    def get_articles(self):
        articles = []
        post_list = self.get_list()
        for post_dic in post_list:
            url = post_dic["url"]
            title = post_dic["title"]
            contents = self.loop.run_until_complete(asyncio.gather(self._get_content(url)))
            content = contents[0]
            dom = BeautifulSoup(content, 'html.parser')
            article_data = dom.select_one("#__APP_DATA")
            article = dom.select_one("#__APP")
            body = ""
            pub_date = ""
            for t in article.select("div, p"):
                if t.get('data-bn-type','') and t.text.count("-") == 2:
                    pub_date += t.text
                    pub_date += ":00 " + self.TZ
                    ps = pub_date.split()
                    pub_date = ps[0] + "T" + ps[1] + ps[2]
                    #2020-02-05T17:07:41+0900
                elif t.name == "p":
                    body += t.text
            articles.append({
                "url": url,
                "title": title,
                "body": body,
                "published_datetime": pub_date,
                "attachment_list": []
            })
        return articles

class UpbitCrawler(Crawler):
    def __init__(self, url):
        Crawler.__init__(self, url)
        # self.TZ = "+0900"

    def get_list(self):
        list_tmpl = "https://api-manager.upbit.com/api/v1/notices?page=1&per_page={}"
        list_url = list_tmpl.format(self.list_sz)
        response = self._get_response(list_url)
        post_list = response.json()["data"]["list"]
        print(post_list)
        return post_list

    def get_articles(self):
        articles = []
        post_list = self.get_list()
        for post_dic in post_list:
            url = "https://api-manager.upbit.com/api/v1/notices/%s" % post_dic["id"]
            title = post_dic["title"]
            pub_date = post_dic["created_at"]
            response = self._get_response(url)
            body = response.json()["data"]["body"]
            body = body.replace("\r\n","\n")
            articles.append({
                "url": url,
                "title": title,
                "body": body,
                "published_datetime": pub_date,
                "attachment_list": []
            })
        return articles

if __name__ == '__main__':
    url = input("크롤링할 홈페이지를 입력하세요? ")
    start = time.time()
    from creator import Creator
    creator = Creator()
    articles = creator.get_articles(url)
    print(json.dumps(articles, sort_keys=True, indent=4, ensure_ascii=False))
    end = time.time()
    print("Elapsed time:", end-start)
