import scrapy
import json
from datetime import datetime

class DawaaSpider(scrapy.Spider):
    name = "shopify"
    allowed_domains = ["hajarafa.com", "sourcebeauty.com"]

    def __init__(self, urls=None, *args, **kwargs):
        super(DawaaSpider, self).__init__(*args, **kwargs)
        if urls:
            self.start_urls = urls.split(",")
        else:
            self.start_urls = [
                "https://sourcebeauty.com/collections/fragrance?tab=products"
            ]

        self.output_files = {}

    def start_requests(self):
        for url in self.start_urls:
            category = "sourcebeauty"  # Default category
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_name = f'{category}_{timestamp}.json'

            self.output_files[url] = open(output_file_name, 'w', encoding='utf-8')
            self.output_files[url].write('[')
            yield scrapy.Request(url=url, callback=self.parse, meta={'url': url})

    def parse(self, response):
        url = response.meta['url']
        file_handle = self.output_files[url]
        products = response.css('h3.card__heading.h5')
        # Update this to Dawaa's correct product structure
        for idx, product in enumerate(products):
            title = product.css('a::text').get()
            link = response.urljoin(product.css('a::attr(href)').get())
            # Search price in parent container
            parent = product.xpath('ancestor::div[contains(@class, "card-information")][1]')
            price = product.xpath('ancestor::div[contains(@class, "card-wrapper")][1]').css('span.price-item.price-item--regular::text').get()


            item = {
                'title': title,
                'price': price,
                'link': link,
            }

            json.dump(item, file_handle, ensure_ascii=False, indent=4)
            if idx < len(products) - 1:
                file_handle.write(',')

        # Handle pagination
        next_page = response.css('a[aria-label="Next page"]::attr(href)').get()
        if next_page:
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse, meta={'url': url})
        else:
            file_handle.write(']')
            file_handle.close()
            del self.output_files[url]

    def closed(self, reason):
        for file_handle in self.output_files.values():
            file_handle.write(']')
            file_handle.close()
