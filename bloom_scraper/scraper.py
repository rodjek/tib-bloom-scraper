import logging
import time

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bloom_scraper.book import Book
from bloom_scraper.book_list import BookList
from bloom_scraper.errors import DownloadError, ScraperError
from bloom_scraper.failure_list import FailureList
from bloom_scraper.util import random_sleep


class Scraper:
    LEVELS = ["all"] + [str(i) for i in range(1, 5)]

    def __init__(self, language, book_list_file, failure_list_file,
                 show_browser, level):
        self.book_list = BookList(book_list_file)
        self.failure_list = FailureList(failure_list_file)
        self.language = language
        self.show_browser = show_browser

        if level is None:
            self.levels = self.LEVELS[1:]
        else:
            if "all" in level:
                self.levels = self.LEVELS[1:]
            else:
                self.levels = level

        self.levels = [f"Level {r}" for r in self.levels]

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type(NoSuchElementException),
           reraise=True)
    def find_categories(self, driver):
        return driver.find_elements(
            By.XPATH, "//div[@role='main']//ul/li[@role='region']")

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type(NoSuchElementException),
           reraise=True)
    def find_next_link(self, category):
        return category.find_element(
            By.XPATH, "./div/div[contains(@class, 'swiper-button-next')]")

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type(NoSuchElementException),
           reraise=True)
    def find_books(self, category):
        return category.find_elements(
            By.XPATH, ".//a[contains(@class, 'cheapCard')]")

    def is_not_clickable(self, link):
        return (link.get_attribute("aria-disabled") == "true"
                or not link.is_displayed())

    def find_books_in_page(self, driver, url, index=False):
        driver.get(url)
        random_sleep()
        categories = self.find_categories(driver)
        subcategories = []
        book_links = []

        for category in categories:
            category_text = category.get_attribute("aria-label")
            if index and category_text not in self.levels:
                continue
            logging.info("Searching %s for books...", category_text)

            try:
                while True:
                    next_link = self.find_next_link(category)
                    if self.is_not_clickable(next_link):
                        break
                    next_link.click()
            except NoSuchElementException:
                pass

            time.sleep(5)
            books = self.find_books(category)

            if (books and books[-1].text == "See more of these books."
                    and books[-1].is_displayed()):
                subcategories.append(books[-1].get_attribute("href"))
            else:
                for book in books:
                    if book.is_displayed():
                        book_links.append(
                            [category_text, book.get_attribute("href")])

        for subcategory in subcategories:
            book_links.extend(self.find_books_in_page(driver, subcategory))

        return book_links

    def run(self):
        self.book_list.load()

        options = webdriver.ChromeOptions()
        if not self.show_browser:
            options.add_argument("--headless")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options)
        driver.get("https://bloomlibrary.org")
        random_sleep()

        language_finder = driver.find_element(
            By.XPATH, "//li[@aria-labelledby='findBooksByLanguage']")
        language_search = language_finder.find_element(By.XPATH, ".//input")
        language_search.send_keys(self.language)

        try:
            language_url = language_finder.find_element(
                By.XPATH,
                f".//a[h2/span[text()='{self.language}']]"
            ).get_attribute("href")
        except NoSuchElementException:
            logging.error("Unable to find language '%s', check the spelling",
                          self.language)
            return

        books = self.find_books_in_page(driver, language_url, True)

        for category, url in books:
            book = Book(driver, category, self.language, url)
            if not self.book_list.exists(book):
                logging.info("Downloading %s...", book.title)
                try:
                    book.download_book(driver)
                    self.book_list.add(book)
                    self.book_list.save()
                    if self.failure_list.exists(book.title):
                        self.failure_list.remove(book.title)
                        self.failure_list.save()
                except (ScraperError, DownloadError) as e:
                    logging.warning(e.message)
                    self.failure_list.add(book.title, e.message)
                    self.failure_list.save()
