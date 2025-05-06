import time
import pandas as pd
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from appium.options.android import UiAutomator2Options
from datetime import datetime
import json

timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

class AlnahdiScraper:
    def __init__(self, version, adb_name, target_url):
        self.version = "15"
        self.adb_name = 'emulator-5554'
        self.target_url = target_url
        self.product_names = []
        self.product_prices = []
        self.driver = self.initialize_driver()

    def initialize_driver(self):
        options = UiAutomator2Options().load_capabilities({
            'platformName': 'Android',
            'deviceName': self.adb_name,
            'browserName': 'Chrome',
            'automationName': 'UiAutomator2',
            'chromedriverExecutable': r"C:\Users\Basmala Kamal\chrome\win64-124.0.6367.219\chrome-win64\chromedriver.exe",
            'newCommandTimeout': 300
        })

        return webdriver.Remote('http://127.0.0.1:4723', options=options)

    def load_page(self):
        self.driver.get(self.target_url)
        time.sleep(5)

    def extract_data(self):
        soup = BeautifulSoup(self.driver.page_source, 'lxml')

        product_cards = soup.select('a.flex.h-full.flex-col')

        for card in product_cards:
            try:
                product_name_tag = card.select_one('span.line-clamp-3')
                price_tag = card.select_one('span.text-custom-sm')

                product_name = product_name_tag.get_text(strip=True) if product_name_tag else None
                product_price = price_tag.get_text(strip=True) if price_tag else None

                if product_name and product_price:
                    self.product_names.append(product_name)
                    self.product_prices.append(product_price)
            except Exception as e:
                print(f"Error extracting product: {e}")
                continue

    def scroll_down(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    def scrape(self, max_scrolls=10):
        self.load_page()

        for _ in range(max_scrolls):
            self.extract_data()
            self.scroll_down()

        self.driver.quit()

        # Save results as JSON
        data = [
            {'Product Name': name, 'Price': price}
            for name, price in zip(self.product_names, self.product_prices)
        ]
        output_file = f'alnahdi_products_{timestamp}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Scraping completed successfully! Results saved to {output_file}")

# === USAGE ===
if __name__ == "__main__":
    scraper = AlnahdiScraper(
        version='15',
        adb_name='emulator-5554',
        target_url='https://www.nahdionline.com/en-sa/search?query=styling+gel'
    )
    scraper.scrape()
