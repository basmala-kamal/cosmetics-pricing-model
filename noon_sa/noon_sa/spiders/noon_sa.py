import scrapy
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time
import requests


class NoonSpider(scrapy.Spider):
    name = "noon_sa"
    allowed_domains = ["noon.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS": 1,
        "RETRY_TIMES": 3,
        "DOWNLOAD_TIMEOUT": 300,
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/98.0.4758.102 Safari/537.36"
        ),
    }

    SCRAPINGANT_API_URL = "https://api.scrapingant.com/v2/general"

    def __init__(self, urls=None, *args, **kwargs):
        super(NoonSpider, self).__init__(*args, **kwargs)
        self.api_key = '85e9f47391244a40b2bb88ed74e364ca'
        self.start_url = urls or "https://www.noon.com/saudi-en/search/?q=body+splash&page=1"
        self.output_file_name = f"noon_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.output_file = open(self.output_file_name, 'w', encoding='utf-8')
        self.output_file.write('[')
        self.first_item_written = False
        self.max_pages = 10  # avoid infinite loops

    def start_requests(self):
        for page in range(1, self.max_pages + 1):
            paginated_url = re.sub(r"page=\d+", f"page={page}", self.start_url)
            yield scrapy.Request(
                url="https://example.com",  # Dummy request to hand off to our API call
                callback=self.fetch_from_scrapingant,
                meta={"page": page, "target_url": paginated_url},
                dont_filter=True
            )

    def fetch_from_scrapingant(self, response):
        page_number = response.meta["page"]
        target_url = response.meta["target_url"]

        self.logger.info(f"Fetching Noon page {page_number} via ScrapingAnt: {target_url}")

        params = {
            "url": target_url,
            "x-api-key": self.api_key,
            "browser": True,
            "proxy_type": "residential"
        }

        try:
            api_response = requests.get(self.SCRAPINGANT_API_URL, params=params, timeout=120)

            if api_response.status_code == 200:
                soup = BeautifulSoup(api_response.content, 'lxml')

                product_cards = soup.select('h2.ProductDetailsSection_title__JorAV')

                products_found = 0
                for card in product_cards:
                    product_name = card.get_text(strip=True)

                    parent = card.find_parent()
                    price_elem = parent.find('strong', class_='Price_amount__2sXa7')
                    product_price = price_elem.get_text(strip=True) if price_elem else None

                    if product_name and product_price:
                        products_found += 1
                        item = {
                            'name': product_name,
                            'price': product_price,
                            'page': page_number,
                            'url': target_url
                        }

                        if self.first_item_written:
                            self.output_file.write(',\n')
                        else:
                            self.first_item_written = True

                        json.dump(item, self.output_file, ensure_ascii=False, indent=4)

                self.logger.info(f"Page {page_number}: Found {products_found} products.")

                if products_found == 0:
                    self.logger.info(f"Stopping at page {page_number} - no products found.")

            else:
                self.logger.error(f"ScrapingAnt request failed [{api_response.status_code}]: {api_response.text}")

        except Exception as e:
            self.logger.error(f"Error scraping page {page_number}: {e}")

    def closed(self, reason):
        self.logger.info(f"Spider closed. Reason: {reason}")
        self.output_file.write(']')
        self.output_file.close()

