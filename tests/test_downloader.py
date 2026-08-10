from services.downloader import Downloader

d = Downloader()

d.download(
    "https://www.atptour.com",
    "homepage.html"
)

d.close()