import datetime
import re
import time


def parse_time(date):
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
        # return '2020-02-04'
        date = re.match('今天(.*)', date).group(1).strip()
        date = time.strftime('%Y-%m-%d', time.localtime(time.time())) + ' ' + date
    return date