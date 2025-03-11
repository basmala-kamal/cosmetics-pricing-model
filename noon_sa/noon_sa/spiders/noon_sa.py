import scrapy
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re

class NoonSpider(scrapy.Spider):
    name = "noon_sa"
    allowed_domains = ["noon.com"]
    
    # Custom settings to prevent timeouts and avoid getting blocked
    custom_settings = {
        "DOWNLOAD_DELAY": 2,  # Delay between requests
        "CONCURRENT_REQUESTS": 2,  # Limit simultaneous requests
        "RETRY_TIMES": 5,          # Retry failed requests
        "DOWNLOAD_TIMEOUT": 20,    # Increase timeout duration
        "ROBOTSTXT_OBEY": False,   # Ignore robots.txt
        "USER_AGENT": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/98.0.4758.102 Safari/537.36"
        ),
    }

    def __init__(self, urls=None, *args, **kwargs):
        super(NoonSpider, self).__init__(*args, **kwargs)

        if urls:
            self.logger.info(f"Received URLs: {urls}")
            self.start_urls = urls.split(",")
        else:
            default_url = "https://www.noon.com/saudi-en/search/?isCarouselView=false&limit=100&originalQuery=face%20serums&page=1"
            self.logger.info(f"No URLs provided. Using default: {default_url}")
            self.start_urls = [default_url]

        # Dictionary to keep track of open files for each URL
        self.output_files = {}
        
        # Dictionary to track if the first item for a given URL has been written
        # to handle JSON commas properly.
        self.first_item_written = {}

    def start_requests(self):
        self.logger.info("Starting requests ...")
        
        for url in self.start_urls:
            # Determine a 'category' from the URL if possible
            category = "default"
            if "originalQuery=" in url:
                category = url.split("originalQuery=")[1].split("&")[0] or "default"

            # Generate a unique timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_name = f"{category}_{timestamp}.json"

            # Open the file and write the opening bracket
            self.logger.info(f"Opening file: {output_file_name} for URL: {url}")
            f = open(output_file_name, 'w', encoding='utf-8')
            f.write('[')
            self.output_files[url] = f

            # Initialize the comma-control flag to False
            self.first_item_written[url] = False

            # Generate up to 15 page requests
            for page_number in range(1, 16):
                # Replace or append `page=page_number` in the URL
                paginated_url = re.sub(r"page=\d+", f"page={page_number}", url)
                
                # If, for any reason, the base URL doesn't contain page=, 
                # you might need to append it differently. Just an example below:
                if "page=" not in paginated_url:
                    paginated_url += f"&page={page_number}"

                self.logger.info(f"Scheduling request for: {paginated_url}")
                
                yield scrapy.Request(
                    url=paginated_url,
                    headers={"User-Agent": self.custom_settings["USER_AGENT"]},
                    callback=self.parse,
                    errback=self.handle_error,
                    meta={'url': url, 'page': page_number},
                )

    def parse(self, response):
        """Parse a single page of product results."""
        url = response.meta['url']
        current_page = response.meta['page']
        self.logger.info(f"Parsing page {current_page} for URL: {url}")

        file_handle = self.output_files.get(url)
        if not file_handle:
            self.logger.warning(f"No file handle found for URL: {url}. This is unexpected.")
            return

        soup = BeautifulSoup(response.text, 'lxml')
        
        # Noon might change their selectors, so adjust as necessary
        product_cards = soup.select('[data-qa="product-name"]')
        self.logger.info(f"Found {len(product_cards)} product cards on page {current_page} for URL: {url}")

        for card in product_cards:
            product_name = card.get_text(strip=True) if card else None
            price_elem = card.find_next('strong', class_='amount')
            product_price = price_elem.get_text(strip=True) if price_elem else None

            # If there's valid data, write it to JSON
            if product_name and product_price:
                item = {
                    'name': product_name,
                    'price': product_price,
                    'page': current_page
                }

                # Write comma if this isn't the first item in the file
                if self.first_item_written[url]:
                    file_handle.write(',')
                else:
                    self.first_item_written[url] = True

                # Dump the actual JSON
                json.dump(item, file_handle, ensure_ascii=False, indent=4)
            else:
                self.logger.debug("Skipped product with missing name or price.")

    def handle_error(self, failure):
        """Handle request failures to retry or log them."""
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")

    def closed(self, reason):
        """When the spider closes, finalize each JSON file."""
        self.logger.info(f"Spider closed. Reason: {reason}")
        
        for url, file_handle in list(self.output_files.items()):
            self.logger.info(f"Closing file for URL: {url}")
            file_handle.write(']')
            file_handle.close()
            del self.output_files[url]
