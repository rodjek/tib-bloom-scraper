import csv
import datetime
import logging


class BookList:
    _csv_fields = [
        "Title",
        "Language",
        "Level",
        "Category",
        "Pages",
        "File Name",
        "English Title",
        "Date Downloaded",
        "Type",
    ]

    def __init__(self, path):
        self.path = path.resolve()
        self.books = []

    def load(self):
        if not self.path.is_file():
            return

        logging.debug("Loading %s", self.path)

        with self.path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.books.append(row)

    def save(self):
        logging.debug("Saving %s", self.path)

        parent = self.path.parent
        if not parent.is_dir():
            parent.mkdir(parents=True)

        with self.path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self._csv_fields)
            writer.writeheader()
            for book in self.books:
                writer.writerow(book)

    def exists(self, book):
        return any(filter(
            lambda r: (r["Title"] == book.title and
                       r["Language"] == book.language),
            self.books))

    def add(self, book):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = [
            book.title,
            book.language,
            book.level,
            book.category,
            book.pages,
            book.local_path.name,
            book.english_title,
            now,
            book.type_,
        ]

        book = dict(zip(self._csv_fields, values))
        self.books.append(book)
