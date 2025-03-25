import time
import pandas as pd
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import requests
from appium.options.android import UiAutomator2Options


class NoonScraper:
    def __init__(self, version, adb_name, target_url):
        self.version = '15'
        self.adb_name = 'emulator-5554'
        self.target_url = 'https://www.noon.com/saudi-en/noon/'
        self.product_names = []
        self.product_prices = []
        self.driver = self.initialize_driver()

    def initialize_driver(self):
        options = UiAutomator2Options().load_capabilities({
        'platformName': 'Android',
        'deviceName': 'emulator-5554',
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

        product_cards = soup.select('[data-qa="product-name"]') or \
                        soup.select('div.productContainer') or \
                        soup.select('div.product-card') or \
                        soup.select('span.name')

        for card in product_cards:
            try:
                product_name = card.get_text(strip=True) if card else None
                price_elem = card.find_next('strong', class_='amount')
                product_price = price_elem.get_text(strip=True) if price_elem else None
                
                self.product_names.append(product_name)
                self.product_prices.append(product_price)
            except:
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

        # Save results
        data = pd.DataFrame({
            'Product Name': self.product_names,
            'Price': self.product_prices
        })
        data.to_excel('noon_products.xlsx', index=False)

        print("Scraping completed successfully!")

# Usage
scraper = NoonScraper(version='12', adb_name='emulator-5554', target_url='https://www.noon.com/saudi-en/noon/')
scraper.scrape()
