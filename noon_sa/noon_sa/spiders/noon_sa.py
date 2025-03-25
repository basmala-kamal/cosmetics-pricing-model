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
        self.start_url = urls if urls else "https://www.noon.com/saudi-en/search/?q=face%20serums&page=1"
        self.output_file_name = f"noon_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.output_file = open(self.output_file_name, 'w', encoding='utf-8')
        self.output_file.write('[')
        self.first_item_written = False
        self.max_pages = 10  # Set a reasonable limit to avoid infinite loops

    def start_requests(self):
        self.logger.info(f"Starting request for URL: {self.start_url}")
        # Create a simple dummy request to start the process
        yield scrapy.Request(
            url="https://example.com",  # Dummy URL
            callback=self.initialize_scraping,
            dont_filter=True
        )

    def initialize_scraping(self, response):
        """Initialize the scraping process with page 1"""
        # Make a direct API call to ScrapingAnt for the first page
        self.process_page(1)
        
    def process_page(self, page_number, retry_attempts=0):
        """Process a single page using URL-based pagination"""
        if page_number > self.max_pages:
            self.logger.info(f"Reached maximum page limit ({self.max_pages})")
            return
            
        # Create the paginated URL
        base_url = self.start_url
        if "page=" in base_url:
            paginated_url = re.sub(r"page=\d+", f"page={page_number}", base_url)
        else:
            # If no page parameter exists, add it
            if "?" in base_url:
                paginated_url = f"{base_url}&page={page_number}"
            else:
                paginated_url = f"{base_url}?page={page_number}"
                
        self.logger.info(f"Fetching URL with ScrapingAnt API: {paginated_url}")

        params = {
            "url": paginated_url,
            "x-api-key": self.api_key,
            "wait_for": 5,
            "browser": True,
            "proxy_country": 'sa',  # Use Saudi Arabia proxies
            "browser_timeout": 60000,  # 60 seconds timeout
            "cookies": [{"name": "country", "value": "sa"}],  # Ensure Saudi Arabia localization
            "screenshot": True
        }

        try:
            api_response = requests.get(self.SCRAPINGANT_API_URL, params=params, timeout=300)
            
            if api_response.status_code == 200:
                soup = BeautifulSoup(api_response.content, 'lxml')
                
                # Try different selectors for product cards
                product_cards = soup.select('[data-qa="product-name"]') or \
                               soup.select('div.productContainer') or \
                               soup.select('div.product-card') or \
                               soup.select('span.name')
                
                products_found = 0
                for card in product_cards:
                    product_name = card.get_text(strip=True) if card else None
                    price_elem = card.find_next('strong', class_='amount')
                    product_price = price_elem.get_text(strip=True) if price_elem else None

                    if product_name and product_price:
                        products_found += 1
                        item = {
                            'name': product_name,
                            'price': product_price,
                            'page': page_number,
                            'url': paginated_url
                        }

                        if self.first_item_written:
                            self.output_file.write(',')
                        else:
                            self.first_item_written = True

                        json.dump(item, self.output_file, ensure_ascii=False, indent=4)
                
                self.logger.info(f"Found {products_found} products on page {page_number}")
                
                # If products were found, continue to the next page
                if products_found > 0:
                    self.logger.info(f"Moving to page {page_number + 1}")
                    # Process the next page non-recursively
                    self.process_page(page_number + 1)
                else:
                    self.logger.info(f"No more products found after page {page_number}")

            else:
                self.logger.error(f"Failed to fetch {paginated_url}: {api_response.status_code}")
                self.logger.error(f"Response content: {api_response.text}")

                # Retry on error
                if retry_attempts < 3:
                    delay = 2 ** retry_attempts
                    self.logger.warning(f"Retrying page {page_number} after {delay}s...")
                    time.sleep(delay)
                    self.process_page(page_number, retry_attempts + 1)

        except Exception as e:
            self.logger.error(f"Error fetching {paginated_url}: {e}")

            # Exponential Backoff for Stability
            if retry_attempts < 3:
                delay = 2 ** retry_attempts
                self.logger.warning(f"Retrying page {page_number} after {delay}s...")
                time.sleep(delay)
                self.process_page(page_number, retry_attempts + 1)
            else:
                self.logger.error(f"Failed after multiple retries: {paginated_url}")

    def closed(self, reason):
        """Close JSON file on completion."""
        self.logger.info(f"Spider closed. Reason: {reason}")
        self.output_file.write(']')
        self.output_file.close()
