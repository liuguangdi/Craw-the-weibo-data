import time

from scrapy import cmdline
# cmdline.execute('scrapy crawl weibo_spider'.split())
#cmdline.execute('scrapy crawl woodenrobot'.split())
cmdline.execute('scrapy crawl user_spider'.split())
# time.sleep(30)
# cmdline.execute('scrapy crawl comment_spider'.split())