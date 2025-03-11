import scrapy
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time
import requests  # Direct API calls for better reliability

class NoonSpider(scrapy.Spider):
    name = "noon_sa"
    allowed_domains = ["noon.com"]

    custom_settings = {
        "DOWNLOAD_DELAY": 5,
        "CONCURRENT_REQUESTS": 1,
        "RETRY_TIMES": 5,
        "DOWNLOAD_TIMEOUT": 300,
        "ROBOTSTXT_OBEY": False,
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/98.0.4758.102 Safari/537.36"
        ),
    }

    SCRAPINGANT_API_URL = "https://api.scrapingant.com/v2/general"

    def __init__(self, urls=None, *args, **kwargs):
        super(NoonSpider, self).__init__(*args, **kwargs)
        self.api_key = 'd3f13b11a6dc4c05b170b31655780006'

        self.start_url = urls if urls else "https://www.noon.com/saudi-en/search/?q=face%20serums"

        self.output_file_name = f"noon_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.output_file = open(self.output_file_name, 'w', encoding='utf-8')
        self.output_file.write('[')
        self.first_item_written = False

    def start_requests(self):
        self.logger.info(f"Starting request for URL: {self.start_url}")
        self.scrape_page(self.start_url, 1)

    def scrape_page(self, base_url, page_number, retry_attempts=0):
        """Fetch content using ScrapingAnt's API for maximum stability."""
        paginated_url = re.sub(r"page=\d+", f"page={page_number}", base_url)
        self.logger.info(f"Fetching URL with ScrapingAnt API: {paginated_url}")

        params = {
            "url": paginated_url,
            "x-api-key": self.api_key,
            "wait_for": 5,                   # Wait for dynamic content to load
            "browser": True,                 # Enable JavaScript rendering
            "proxy_country": 'ae',           # Use UAE-based proxies for faster access
            "screenshot": True               # Debugging feature to capture failed pages
        }

        try:
            response = requests.get(self.SCRAPINGANT_API_URL, params=params, timeout=300)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                product_cards = soup.select('[data-qa="product-name"]')

                for card in product_cards:
                    product_name = card.get_text(strip=True) if card else None
                    price_elem = card.find_next('strong', class_='amount')
                    product_price = price_elem.get_text(strip=True) if price_elem else None

                    if product_name and product_price:
                        item = {
                            'name': product_name,
                            'price': product_price,
                            'page': page_number
                        }

                        if self.first_item_written:
                            self.output_file.write(',')
                        else:
                            self.first_item_written = True

                        json.dump(item, self.output_file, ensure_ascii=False, indent=4)

                # Follow pagination link dynamically
                next_page_link = soup.select_one('a[aria-label="Next"]')
                if next_page_link:
                    self.scrape_page(base_url, page_number + 1)
                else:
                    self.logger.info(f"No more pages found after page {page_number}")

            else:
                self.logger.error(f"Failed to fetch {paginated_url}: {response.status_code}")
                self.logger.error(f"Response content: {response.text}")

        except Exception as e:
            self.logger.error(f"Error fetching {paginated_url}: {e}")

            # Exponential Backoff for Stability
            if retry_attempts < 5:
                delay = 2 ** retry_attempts
                self.logger.warning(f"Retrying page {page_number} after {delay}s...")
                time.sleep(delay)
                self.scrape_page(base_url, page_number, retry_attempts + 1)
            else:
                self.logger.error(f"Failed after multiple retries: {paginated_url}")

    def closed(self, reason):
        """Close JSON file on completion."""
        self.logger.info(f"Spider closed. Reason: {reason}")
        self.output_file.write(']')
        self.output_file.close()
