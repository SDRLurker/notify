#!/usr/bin/python3
# -*- coding: utf-8 -*-
from crawler import Crawler
from crawler import BinanceCrawler
from crawler import UpbitCrawler

class Creator:
    def __init__(self):
        pass

    def create_crawler(self, url):
        domain, path, query = Crawler.get_domain_path_query(url)
        DOMAIN_CLASS_DIC = {
            "www.binance.com": BinanceCrawler(url),
            "upbit.com": UpbitCrawler(url)
        }
        # print(domain, DOMAIN_CLASS_DIC.get(domain))
        if DOMAIN_CLASS_DIC.get(domain):
            crawler = DOMAIN_CLASS_DIC.get(domain)
            return crawler
        else:
            raise TypeError('domain %s is not supported' % domain)

    def get_articles(self, url):
        crawler = self.create_crawler(url)
        return crawler.get_articles()
