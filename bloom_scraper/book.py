import re
import urllib.parse
from pathlib import Path

import PyPDF2
from selenium.webdriver.common.by import By

from bloom_scraper.errors import ScraperError
from bloom_scraper.util import random_sleep
from bloom_scraper.web import Session, translate


class Book:
    def __init__(self, driver, category, language, book_url):
        self.category = category
        self.language = language
        self.book_url = book_url
        self.type_ = "PDF"

        level_match = re.search(r"\bLevel\s+(\d+)\b", self.category)
        if level_match is None:
            self.level = "Unknown"
        else:
            self.level = level_match.group(1)

        driver.get(self.book_url)
        random_sleep()

        self.title = driver.find_element(By.XPATH, "//div[@role='main']//h1").text

    def download_book(self, driver):
        driver.get(self.book_url)
        random_sleep()
        pdf_download_button = driver.find_element(By.XPATH, "//div[@role='main']//button[contains(@aria-label, 'Download PDF')]")
        if self.is_button_enabled(pdf_download_button):
            pdf_download_button.click()
            random_sleep()
            self.url = driver.current_url
            driver.back()

        filename = self.safe_path(Path(urllib.parse.unquote(self.url)).name)
        self.local_path = Path("books") / self.language / self.level / filename

        Session().download_file(self.url, self.local_path, self.book_url)
        self.english_title = translate(self.title)

        try:
            self.pages = self.get_book_length(self.local_path)
        except PyPDF2.errors.PdfReadError as e:
            raise ScraperError(self.title, f"Corrupt PDF: {self.local_path}") from e

    def is_button_enabled(self, element):
        svg = element.find_element(By.XPATH, ".//*[name()='svg']")
        return svg.get_attribute("fill") != "#DDD"

    def get_book_length(self, path):
        reader = PyPDF2.PdfReader(path)
        return len(reader.pages)

    def safe_path(self, name):
        return re.sub(r"[\>\<\"\:\/\\\*\?\|]", "", name)

    def __repr__(self):
        class_name = type(self).__name__
        return f"{class_name}(title={self.title!r}"
