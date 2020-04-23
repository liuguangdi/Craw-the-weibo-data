# -*- coding: utf-8 -*-
import time

import scrapy
from scrapy import Request
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import TCPTimedOutError, DNSLookupError

from .urlList import URL_TWEET_LIST
from ..items import *
import datetime
import re

DATE_START = "2020-01-01"
DATE_END = "2020-01-28"
STANDARD = 50

class WeiboSpiderSpider(scrapy.Spider):

    name = 'weibo_spider'
    allowed_domains = ['weibo.cn']
    # start_urls = ['http://weibo.cn/']
    base_url = "https://weibo.cn"
    url_cur = ''

    def start_requests(self):
        count = 0
        for url in URL_TWEET_LIST:
            print('!!!Start:' + '[' + str(count) + ']:' + url)
            self.url_cur = url.replace('weibo.com','weibo.cn')
            count = count + 1
            yield Request(url, callback=self.parse_tweet, dont_filter=True, errback=self.Errshow)

    # 解析微博
    def parse_tweet(self, response):
        """
                解析本页的数据
                """
        tweet_nodes = response.xpath('//div[@class="c" and @id]')  # class=c 代表一个微博
        for tweet_node in tweet_nodes:
            try:
                tweet_item = TweetsItem()

                tweet_repost_url = tweet_node.xpath('.//a[contains(text(),"转发[")]/@href').extract()[0]
                user_tweet_id = re.search(r'/repost/(.*?)\?uid=(\d+)', tweet_repost_url)

                # 点赞数
                like_num = tweet_node.xpath('.//a[contains(text(),"赞[")]/text()').extract()[0]
                tweet_item['like_num'] = int(re.search('\d+', like_num).group())

                # 转发数
                repost_num = tweet_node.xpath('.//a[contains(text(),"转发[")]/text()').extract()[0]
                tweet_item['repost_num'] = int(re.search('\d+', repost_num).group())

                # 评论数
                comment_num = tweet_node.xpath(
                    './/a[contains(text(),"评论[") and not(contains(text(),"原文"))]/text()').extract()[0]
                tweet_item['comment_num'] = int(re.search('\d+', comment_num).group())

                # 微博URL
                tweet_item['weibo_url'] = 'https://weibo.com/{}/{}'.format(user_tweet_id.group(2),
                                                                           user_tweet_id.group(1))

                # 发表该微博用户id
                tweet_item['user_id'] = user_tweet_id.group(2)

                # 微博id
                tweet_item['id'] = '{}_{}'.format(user_tweet_id.group(2), user_tweet_id.group(1))

                create_time_info = ''.join(tweet_node.xpath('.//span[@class="ct"]').xpath('string(.)').extract())
                if "来自" in create_time_info:
                    # 微博发表时间
                    tweet_item['created_at'] = create_time_info.split('来自')[0].strip()
                    # 发布微博的工具
                    # tweet_item['tool'] = create_time_info.split('来自')[1].strip()
                else:
                    tweet_item['created_at'] = create_time_info.strip()

                # 图片
                images = tweet_node.xpath('.//img[@alt="图片"]/@src')
                if images:
                    tweet_item['image_url'] = images.extract()[0]

                # 视频
                # videos = tweet_node.xpath('.//a[contains(@href,"https://m.weibo.cn/s/video/show?object_id=")]/@href')
                # if videos:
                #     tweet_item['video_url'] = videos.extract()[0]

                # 定位信息
                map_node = tweet_node.xpath('.//a[contains(text(),"显示地图")]')
                if map_node:
                    tweet_item['location'] = True

                # 原始微博，只有转发的微博才有这个字段
                # repost_node = tweet_node.xpath('.//a[contains(text(),"原文评论[")]/@href')
                # if repost_node:
                #     tweet_item['origin_weibo'] = repost_node.extract()[0]

                # 检测有没有阅读全文:
                all_content_link = tweet_node.xpath('.//a[text()="全文" and contains(@href,"ckAll=1")]')
                if all_content_link:
                    all_content_url = self.base_url + all_content_link.xpath('./@href').extract()[0]
                    yield Request(all_content_url, callback=self.parse_all_content, meta={'item': tweet_item},
                                  )
                else:
                    # 微博内容
                    tweet_item['content'] = \
                        ''.join(tweet_node.xpath('./div[1]').xpath('string(.)').extract()
                                ).replace(u'\xa0', '').replace(u'\u3000', '').replace(' ', '').split('赞[', 1)[0]

                    if 'location' in tweet_item:
                        tweet_item['location'] = tweet_node.xpath('.//a[contains(text(),"显示地图")]/@href').extract()[0]
                    yield tweet_item

                # 抓取该微博的用户信息
                # yield Request(url="https://weibo.cn/{}/info".format(tweet_item['user_id']), callback=self.parse_information, priority=2)

            except Exception as e:
                self.logger.error(e)

        next_page = response.xpath('//div[@id="pagelist"]//a[contains(text(),"下页")]/@href')
        if next_page:
            url = self.base_url + next_page[0].extract()
            yield Request(url, callback=self.parse_tweet, dont_filter=True)

    def parse_all_content(self, response):
        # 有阅读全文的情况，获取全文
        tweet_item = response.meta['item']
        tweet_item['content'] = ''.join(response.xpath('//*[@id="M_"]/div[1]').xpath('string(.)').extract()
                                        ).replace(u'\xa0', '').replace(u'\u3000', '').replace(' ', '').split('赞[', 1)[0]
        # if 'location' in tweet_item:
        #     tweet_item['location'] = \
        #     response.xpath('//*[@id="M_"]/div[1]//span[@class="ctt"]/a[last()]/text()').extract()[0]
        yield tweet_item

    def Errshow(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
