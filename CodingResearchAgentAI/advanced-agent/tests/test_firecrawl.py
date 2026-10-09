from types import SimpleNamespace

from src.firecrawl import FirecrawlService


class FakeApp:
    def __init__(self, search_result=None, error=False):
        self.search_result = search_result
        self.error = error
        self.scraped = []

    def search(self, **kwargs):
        if self.error:
            raise RuntimeError("provider down")
        return self.search_result

    def scrape_url(self, url, **kwargs):
        self.scraped.append(url)
        return SimpleNamespace(markdown="page")


def test_search_returns_consistent_empty_list_after_provider_error():
    service = FirecrawlService(app=FakeApp(error=True))
    assert service.search_companies("frameworks") == []


def test_search_normalizes_result_data():
    service = FirecrawlService(app=FakeApp(search_result=SimpleNamespace(data=[{"url": "https://example.com"}])))
    assert service.search_companies("frameworks") == [{"url": "https://example.com"}]


def test_scrape_rejects_local_and_non_http_targets():
    app = FakeApp()
    service = FirecrawlService(app=app)

    assert service.scrape_company_pages("http://127.0.0.1/admin") is None
    assert service.scrape_company_pages("http://localhost:8000/") is None
    assert service.scrape_company_pages("file:///etc/passwd") is None
    assert app.scraped == []


def test_scrape_accepts_public_https_url():
    app = FakeApp()
    service = FirecrawlService(app=app)

    assert service.scrape_company_pages("https://example.com/docs").markdown == "page"
    assert app.scraped == ["https://example.com/docs"]
