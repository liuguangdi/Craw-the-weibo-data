#! python3
# -*- coding: utf-8 -*-

import os, codecs
from datetime import datetime, timedelta

from os.path import join

import jieba
from collections import Counter

import pandas as pd
import pymongo
import xlwt

DATE_LIMIT = '2020-02-03'

def anaFlow(collectionTweet, collectionComment):
    '''链接数据库'''
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client["weibo"]
    collectionTweet = db[collectionTweet]
    collectionComment = db[collectionComment]
    '''excel记录'''
    book = xlwt.Workbook(encoding="utf-8", style_compression=0)
    # 创建一个sheet对象，一个sheet对象对应Excel文件中的一张表格。
    sheet = book.add_sheet('Tweet' + DATE_LIMIT, cell_overwrite_ok=True)
    sheet1 = book.add_sheet('Commont' + DATE_LIMIT, cell_overwrite_ok=True)
    sheet2 = book.add_sheet('Emotion1' + DATE_LIMIT, cell_overwrite_ok=True)
    # sheet3 = book.add_sheet('Emotion2_0203', cell_overwrite_ok=True)
    # 其中的test是这张表的名字,cell_overwrite_ok，表示是否可以覆盖单元格，其实是Worksheet实例化的一个参数，默认值是False

    sheet.write(0, 0, '区间')
    sheet.write(0, 1, '微博数')
    sheet.write(0, 2, '点赞数')
    sheet.write(0, 3, '转发数')
    sheet.write(0, 4, '评论数')

    sheet1.write(0, 0, '区间')
    for j in range(1, 21):
        sheet1.write(0, j, '第' + str(j) + '位词')

    col = 0 #写表情表，列号
    for i in range(0,24):
        dateStart = (datetime.fromisoformat(DATE_LIMIT + 'T00:00') + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
        dateEnd = (datetime.fromisoformat(DATE_LIMIT + 'T00:59') + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M")
        # print(dateStart + '----' + dateEnd)
        datas = collectionTweet.find({ "$and" : [{"created_at" : { "$gte" : dateStart }}, {"created_at" : { "$lte" : dateEnd }}] })

        str_sum = ''
        like_sum = 0
        repost_sum = 0
        comment_sum = 0
        tweet_num = datas.count()

        #用于判定评论是否属于该段微博
        TweetList = []
        for data in list(datas):
            #1 统计微博
            str_sum = str_sum + ';' + data['content']
            like_sum = like_sum + data['like_num']
            repost_sum = repost_sum + data['repost_num']
            comment_sum = comment_sum + data['comment_num']
            # print("当前文字获取长度:"+ str(len(str_sum)))
            # print(str(tweet_num) + ',' + str(like_sum) + ',' + str(repost_sum) + ',' + str(comment_sum))

            TweetList.append(str(data['id']).split('_')[1])

        '''记录'''
        sheet.write(i + 1, 0, dateStart.split(' ')[1] + '-' + dateEnd.split(' ')[1])
        sheet.write(i + 1, 1, tweet_num)
        sheet.write(i + 1, 2, like_sum)
        sheet.write(i + 1, 3, repost_sum)
        sheet.write(i + 1, 4, comment_sum)

        # 2 统计微博主题
        print("当前文字获取长度:"+ str(len(str_sum)))
        '''去除一些没用的字符串'''
        str_sum = str_sum.replace('人民日报','').replace('关注','').replace('微博','').replace('视频','').replace('转发','').replace('组图','') \
            .replace('收藏', '').replace('举报','').replace('今日','').replace('我们','').replace('一起','').replace('近日','').replace('今天','') \
            .replace('一个', '').replace('网友','').replace('自己','').replace('发现','').replace('问题','').replace('操作','').replace('表示','') \
            .replace('他们', '').replace('发布','').replace('工作','').replace('什么','').replace('生活','').replace('目前','').replace('发布','') \
            .replace('进行', '')

        wordList = get_words(str_sum)
        sheet1.write(i + 1, 0, dateStart.split(' ')[1] + '-' + dateEnd.split(' ')[1])
        for j in range(0, len(wordList)):
            sheet1.write(i + 1, j + 1, wordList[j])

        # 3 罗列评论
        emotionNameY1 = [] #记录表情
        likeNumY2 = []  #记录点赞量
        CommWithEmotion = collectionComment.find({"emotion": {"$ne": ""}})
        for comment in list(CommWithEmotion):
            if comment['tweet_id'] in TweetList:#判断是不是相关的微博
                updateY(comment, emotionNameY1, likeNumY2)

        df1 = pd.DataFrame({'emotion': emotionNameY1, 'like_num': likeNumY2})
        df1 = df1.groupby(['emotion']).agg({'like_num':sum}).reset_index().sort_values(by='like_num', ascending=False)
        # print(df1)
        #表情写进excel
        sheet2.write(0, col, dateStart.split(' ')[1] + '-' + dateEnd.split(' ')[1])
        sheet2.write(1, col, '表情')
        sheet2.write(1, col + 1, '点赞和')
        for x in range(0, len(df1)):
            emotionTmp = df1.iloc[x].values[0]
            likeNumTmp = df1.iloc[x].values[1]
            sheet2.write(x+2, col, str(emotionTmp))
            sheet2.write(x+2, col+1, str(likeNumTmp))
        #按时间隔开
        col = col + 4

        # sheet2
        # 4 统计评论
        # sheet3.

    book.save('Baogao' + DATE_LIMIT.replace('-','') + '.xls')
    return

def updateY(comment, emotionNameY1, likeNumY2):
    likeNum = comment['like_num']
    emotions = sorted(set(comment['emotion'].split(',')))[1:]
    for emotionOne in emotions:
        emotionNameY1.append(emotionOne)
        likeNumY2.append(likeNum)


    return

def gettxt(collection):
    '''链接数据库'''
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client["weibo"]
    collectionCurr = db[collection]
    # count = collectionCurr.find({"created_at" : ["2020-01-01" , "2020-01-07"] }).count()
    data = collectionCurr.find({ "$and" : [{"created_at" : { "$gte" : "2020-02-03 00:00" }}, {"created_at" : { "$lte" : "2020-02-03 23:59 " }}] })
    str_sum = ''
    like_sum = 0
    repost_sum = 0
    comment_sum = 0
    tweet_num = data.count()
    for i in list(data):
        str_sum = str_sum + ';' + i['content']
        like_sum = like_sum + i['like_num']
        repost_sum = repost_sum + i['repost_num']
        comment_sum = comment_sum + i['comment_num']
    print("当前文字获取长度:"+ str(len(str_sum)))
    print(str(tweet_num) + ',' + str(like_sum) + ',' + str(repost_sum) + ',' + str(comment_sum))
    '''去除一些没用的字符串'''
    str_sum = str_sum.replace('人民日报','').replace('关注','').replace('微博','').replace('视频','').replace('转发','').replace('组图','') \
        .replace('收藏', '').replace('举报','').replace('今日','').replace('我们','').replace('一起','').replace('近日','').replace('今天','') \
        .replace('一个', '').replace('网友','').replace('自己','').replace('发现','').replace('问题','').replace('操作','').replace('表示','') \
        .replace('他们', '').replace('发布','').replace('工作','').replace('什么','').replace('生活','').replace('目前','').replace('发布','') \
        .replace('进行', '').replace('其中','').replace('累计','').replace('可以','').replace('明天','').replace('可能','').replace('没有','')
    get_words(str_sum)
    return

def get_words(txt):
    seg_list = jieba.cut(txt)
    c = Counter()
    wordList = []
    for x in seg_list:
        if len(x) > 1 and x != '\r\n':
            c[x] += 1
    print('常用词频度统计结果')
    for (k, v) in c.most_common(20):
        # print('%s%s%d' % (k, ',' , v))
        wordList.append(k + '/' +str(v))
    return wordList

def anaEmotion(db):
    collection = db["emotion0129done"]
    # count = collectionCurr.find({"created_at" : ["2020-01-01" , "2020-01-07"] }).count()
    data = collection.find()
    strTmp = ''
    like_num = 0
    tweet_num = data.count()
    print(tweet_num)
    # 创建一个Workbook对象，相当于创建了一个Excel文件
    book = xlwt.Workbook(encoding="utf-8", style_compression=0)

    # 创建一个sheet对象，一个sheet对象对应Excel文件中的一张表格。
    sheet = book.add_sheet('emotion0129', cell_overwrite_ok=True)
    # 其中的test是这张表的名字,cell_overwrite_ok，表示是否可以覆盖单元格，其实是Worksheet实例化的一个参数，默认值是False
    dataList = list(data)
    for i in range(0,len(dataList)):
        strTmp = dataList[i]['_id']['emotion'].replace(',','')
        like_num = dataList[i]['like_num']
        occur_num = dataList[i]['num']
    # print("当前文字获取长度:"+ str(len(str_sum)))
        sheet.write(i, 0, strTmp)
        sheet.write(i, 1, like_num)
        sheet.write(i, 2, int(occur_num))
        print(strTmp + ',' + str(like_num) + ',' + str(occur_num))

    book.save('emotion1.xls')
    return

if __name__ == '__main__':
    # with codecs.open('19d.txt', 'r', 'utf8') as f:
    #     txt = f.read()
    '''链接数据库'''
    client = pymongo.MongoClient(host='localhost', port=27017)
    db = client["weibo"]
    # get_words(txt)
    # gettxt("Tweets")
    # anaCommont("emotion0129done")
    # anaEmotion(db)
    anaFlow("TweetsKey0203_0206_ALL", "Comment_RMRB0131_ex0206_ALL_copy1")