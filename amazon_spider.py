import scrapy
import json
from datetime import datetime

class AmazonSpider(scrapy.Spider):
    name = "amazon_sa"
    allowed_domains = ["amazon.sa"]

    def __init__(self, urls=None, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls.split(",")  
        else:
            self.start_urls = [
                "https://www.amazon.sa/s?k=foundation&crid=1VFWJ49DC409R&sprefix=foundation%2Caps%2C325&ref=nb_sb_noss_1"
            ]
        
        self.output_files = {}

    def start_requests(self):
        for url in self.start_urls:
            
            category = url.split("k=")[1].split("&")[0] if "k=" in url else "default"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_name = f'{category}.json'

            
            self.output_files[url] = open(output_file_name, 'w', encoding='utf-8')
            self.output_files[url].write('[')  

            yield scrapy.Request(url=url, callback=self.parse, meta={'url': url})

    def parse(self, response):
        url = response.meta['url']
        file_handle = self.output_files[url]
        products = response.xpath('//div[contains(@class, "s-main-slot")]//div[@data-component-type="s-search-result"]')

        
        for idx, product in enumerate(products):
            item = {
                'title': product.xpath('.//h2[contains(@class, "a-size-base-plus")]/span/text()').get(),
                'price': product.xpath('.//span[@class="a-offscreen"]/text()').get(),
                'rating': product.xpath('.//span[@class="a-icon-alt"]/text()').get(),
                'link': response.urljoin(product.xpath('//a[@class="a-link-normal s-line-clamp-4 s-link-style a-text-normal"]/@href').get()),
                
            }
            
          
            
            json.dump(item, file_handle, ensure_ascii=False, indent=4)
            if idx < len(products) - 1:
                file_handle.write(',')

    
        next_page = response.xpath('//a[contains(@class, "s-pagination-next")]/@href').get()
        if next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(url=next_page_url, callback=self.parse, meta={'url': url})
        else:
            file_handle.write(']')
            file_handle.close()
            del self.output_files[url]  


    def closed(self, reason):
        for file_handle in self.output_files.values():
            file_handle.write(']')
            file_handle.close()