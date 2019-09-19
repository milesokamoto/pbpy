import scrapy
class LinkSpider(scrapy.Spider):
    name = 'linkspider'

    start_urls = [input("start_url: ")]
    allowed_domains = [input("allowed_domain: ")]

    def __init__(self):
        self.links=[]

    def parse(self, response):
        if not response.url in self.links:
            self.links.append(response.url)
            link = response.url
            out = open("links.txt", "a")
            string = str(link)
            out.write(string + '\n')
            out.close
        for href in response.css('a::attr(href)'):
            yield response.follow(href, self.parse)
