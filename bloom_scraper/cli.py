import argparse
import logging
from pathlib import Path

from bloom_scraper.scraper import Scraper


def main():
    parser = argparse.ArgumentParser(
        prog="bloom_scraper",
        description="Scrape books from the bloom library.")
    parser.add_argument("-l", "--language", dest="language", type=str,
                        help="The language of books to scrape",
                        required=True)
    parser.add_argument("--debug", action="store_true", dest="debug",
                        help="Enable debug logging")
    parser.add_argument("--show-browser", action="store_true",
                        dest="show_browser",
                        help="Show the web browser when scraping")
    parser.add_argument("-e", "--level", dest="level", choices=Scraper.LEVELS,
                        nargs="+", type=str,
                        help="The level of books to scrape")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s",
                            level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    book_list = Path("bloom_book_list.csv")
    failure_list = Path("bloom_failures.csv")

    Scraper(args.language, book_list, failure_list, args.show_browser,
            args.level).run()
