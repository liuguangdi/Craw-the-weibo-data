# -*- coding: utf-8 -*-
import queue

import pymongo
import scrapy
from scrapy import Request
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import TCPTimedOutError, DNSLookupError

from .urlList import *
from ..items import *
import datetime
import re
import time


class WeiboCommentSpider(scrapy.Spider):

    name = 'comment_spider'
    allowed_domains = ['weibo.cn']
    # start_urls = ['http://weibo.cn/']
    base_url = "https://weibo.cn"
    tweetIdTmp = ''
    repeatChkQue = queue.Queue(20)  # 重复检查队列

    def start_requests(self):
        '''
        https://weibo.cn/comment/hot/IrjSQbO1T?rl=100&page=2
        "https://weibo.cn/comment/hot/IrRSAktpZ?",
        "https://weibo.com/2803301701/Is5xeqvl1"
        '''

        '''链接数据库'''
        client = pymongo.MongoClient(host='localhost', port=27017)
        db = client["weibo"]
        collection = db["TweetsKey_0210_ALL"]
        dataList = list(collection.find())
        print(len(dataList))
        # dataList = URL_COMMENT_LIST

        '''创建urllist'''
        urlList = []
        for data in dataList:
            #组成评论的url格式
            if isinstance(data, str):
                # urlTmp = data.replace('weibo.com', 'weibo.cn').replace(ID_RMRB, 'comment/hot') + '?'
                urlTmp = re.sub("\d{10}", 'comment/hot', (data.replace('weibo.com', 'weibo.cn') + '?'))
                re.sub()
            else:
                # urlTmp = data['weibo_url'].replace('weibo.com', 'weibo.cn').replace(ID_RMRB, 'comment/hot') + '?'
                urlTmp = re.sub("\d{10}", 'comment/hot', (data['weibo_url'].replace('weibo.com', 'weibo.cn') + '?'))
            urlList.append(urlTmp)

        count = 0
        for url in urlList:
            self.tweetIdTmp = re.findall(r"\/hot\/(.+)\?", url)[0]
            print('!!!Start:' + '[' + str(count) + ']:' + url)
            count = count + 1
            #清空重复检查队列
            while(self.repeatChkQue.qsize()):
                self.repeatChkQue.get()
            yield Request(url, callback=self.parse_comment, dont_filter=True, errback=self.Errshow)

    def parse_comment(self, response):
        """
        解析本页的数据
        """
        comment_nodes = response.xpath('//div[@class="c" and @id]')  # class=c 代表一个微博
        if(len(comment_nodes) == 0):
            return
        for comment_node in comment_nodes:
            try:
                comment_item = CommentItem()
                '''id = Field()  # 评论id
                user_id = Field()  # 用户id
                contant = Field()  # 评论内容
                date = Field()  # 评论日期
                emotion = Field()  # 评论内的表情
                like_num = Field()  # 点赞数
                hate_num = Field()  # 举报数'''

                # 微博id
                tweet_id = self.tweetIdTmp
                comment_item['tweet_id'] = tweet_id
                # 点赞数
                like_num = comment_node.xpath('.//a[contains(text(),"赞[")]/text()').extract()
                comment_item['like_num'] = int(re.search('\d+', like_num[0]).group()) \
                    if len(like_num) else 0
                # 暂时不要没有赞的
                if(not comment_item['like_num']):
                    return

                # 举报数
                hate_num = comment_node.xpath('.//a[contains(text(),"举报[")]/text()').extract()
                comment_item['hate_num'] = int(re.search('\d+', hate_num[0]).group()) \
                    if len(hate_num) else 0

                # 评论用户id
                user_id = comment_node.xpath('.//a/@href').extract()[0]
                comment_item['user_id'] = user_id
                # if('6480381648' not in comment_item['user_id']):
                #     continue
                # 评论id
                comment_item['id'] = comment_node.attrib['id']
                # 查重，遇到重复直接返回
                if (self.repeatChk(comment_item['id'])):
                    comment_item['id'] = comment_node.attrib['id']
                    return

                # 评论内容
                contant = comment_node.xpath('.//text()').extract()
                comment_item['contant'] = ''  # 要先赋值
                for i in range(2, len(contant) - 7):
                    comment_item['contant'] = str(comment_item['contant']) + contant[i]

                # 日期
                create_time_info = ''.join(comment_node.xpath('.//span[@class="ct"]').xpath('string(.)').extract())
                # comment_item['date'] = re.findall(r'(.*) ', create_time_info.split('来自')[0].strip())[0]
                if "来自" in create_time_info:
                    comment_item['date'] = self.parse_time(create_time_info.split('来自')[0].strip())
                else:
                    comment_item['date'] = self.parse_time(create_time_info.strip())

                # 表情和表情链接
                emotion = comment_node.xpath('.//img/@alt').extract()
                emotion_src = comment_node.xpath('.//img[@alt]/@src').extract()
                comment_item['emotion'] = ''
                comment_item['emotion_src'] = ''
                j = 0
                for i in emotion:
                    if re.match(r'\[.+\]', i):
                        comment_item['emotion'] = comment_item['emotion'] + ',' + i
                        if emotion_src[j] not in comment_item['emotion_src']:
                            comment_item['emotion_src'] = comment_item['emotion_src'] + '$$$' + emotion_src[0]
                    j = j + 1

                yield comment_item

            except Exception as e:
                self.logger.error(e)

        next_page = response.xpath('//div[@id="pagelist"]//a[contains(text(),"下页")]/@href')
        if next_page:
            url = self.base_url + next_page[0].extract()
            yield Request(url, callback=self.parse_comment, dont_filter=True)

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

    def parse_time(self, date):
        if re.match('刚刚', date):
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        if re.match('\d+分钟前', date):
            minute = re.match('(\d+)', date).group(1)
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() - float(minute) * 60))
        if re.match('\d+小时前', date):
            hour = re.match('(\d+)', date).group(1)
            date = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time() - float(hour) * 60 * 60))
        if re.match('昨天.*', date):
            date = re.match('昨天(.*)', date).group(1).strip()
            date = time.strftime('%Y-%m-%d', time.localtime(time.time() - 24 * 60 * 60)) + ' ' + date
        if re.match('\d{2}月\d{2}日', date):
            now_time = datetime.datetime.now()
            date = date.replace('月', '-').replace('日', '')
            date = str(now_time.year) + '-' + date
        if re.match('今天.*', date):
            date = re.match('今天(.*)', date).group(1).strip()
            date = time.strftime('%Y-%m-%d', time.localtime(time.time())) + ' ' + date
        return date

    def repeatChk(self, id):
        '''查看当前评论是否是重复的'''
        if (id in self.repeatChkQue.queue):
            return True
        else:
            if(self.repeatChkQue.full()):
                self.repeatChkQue.get()
            self.repeatChkQue.put(id)
            return False

