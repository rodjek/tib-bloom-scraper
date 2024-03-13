class DownloadError(Exception):
    def __init__(self, url, message):
        self.url = url
        self.message = message
        super().__init__(self.message)


class ScraperError(Exception):
    def __init__(self, title, message):
        self.title = title,
        self.message = message
        super().__init__(self.message)
