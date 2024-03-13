import csv


class FailureList:
    _csv_fields = [
        "Title",
        "Failure",
    ]

    def __init__(self, path):
        self.path = path
        self.failures = {}

    def load(self):
        if not self.path.is_file():
            return

        with self.path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.failures[row["Title"]] = row["Failure"]

    def save(self):
        if not self.failures:
            if self.path.is_file():
                self.path.unlink()
            return

        with self.path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self._csv_fields)
            writer.writeheader()
            for title in self.failures:
                row = dict(zip(self._csv_fields,
                               [title, self.failures[title]]))
                writer.writerow(row)

    def add(self, key, value):
        self.failures[key] = value

    def remove(self, key):
        del self.failures[key]

    def exists(self, key):
        return key in self.failures

    def isempty(self):
        return not self.failures
