from scrapy.spiders import Spider


class BlogSpider(Spider):
    name = 'woodenrobot'
    url = 'https://s.weibo.com/weibo?q=%E8%82%BA%E7%82%8E&region=custom:42:1&typeall=1&suball=1&timescope=custom:2019-12-20:2019-12-21&Refer=g&page=1'
    start_urls = [url]

    def parse(self, response):
        aaa = response.body
        print(aaa)
        yield
