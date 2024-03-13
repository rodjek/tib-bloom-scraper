import httpx
import requests

import googletrans
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from bloom_scraper.errors import DownloadError


class Session:
    _ua = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self._ua})

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3),
           retry=retry_if_exception_type((
               httpx.ConnectError,
               httpx.ReadTimeout,
               TimeoutError)),
           reraise=True)
    def download_file(self, remote, local, referer):
        download_dir = local.parent
        if not download_dir.is_dir():
            download_dir.mkdir(parents=True)

        response = self.session.get(remote, headers={"referer": referer})

        if not response.ok:
            raise DownloadError(remote, f"Unable to download {remote}: "
                                        f"error {response.status_code}")

        with local.open("wb") as local_file:
            local_file.write(response.content)


@retry(wait=wait_exponential(multiplier=1, min=2, max=10),
       stop=stop_after_attempt(3),
       retry=retry_if_exception_type((
           httpx.ConnectError,
           httpx.ReadTimeout,
           TimeoutError)),
       reraise=True)
def translate(text):
    translator = googletrans.Translator()
    return translator.translate(text, dest="en").text
