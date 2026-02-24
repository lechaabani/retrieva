"""URL crawler connector for fetching web pages."""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError

logger = logging.getLogger(__name__)


class URLCrawlerConnector(BaseConnector):
    """Crawls web pages and returns their content as Documents.

    Uses httpx for HTTP requests and BeautifulSoup or trafilatura for
    content extraction. Respects robots.txt when configured.
    """

    name = "url_crawler"

    def __init__(
        self,
        url: str,
        max_depth: int = 1,
        max_pages: int = 50,
        respect_robots: bool = True,
        timeout: float = 30.0,
        allowed_domains: Optional[list[str]] = None,
    ) -> None:
        """
        Args:
            url: Starting URL to crawl.
            max_depth: Maximum link-following depth (0 = single page).
            max_pages: Maximum number of pages to crawl.
            respect_robots: Whether to check robots.txt.
            timeout: HTTP request timeout in seconds.
            allowed_domains: Restrict crawling to these domains. Defaults to
                             the domain of the starting URL.
        """
        self.start_url = url
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.respect_robots = respect_robots
        self.timeout = timeout

        parsed = urlparse(url)
        self.allowed_domains = set(allowed_domains or [parsed.netloc])

    async def pull(self) -> list[Document]:
        """Crawl the configured URL and return extracted pages.

        Returns:
            List of Document instances, one per crawled page.

        Raises:
            ConnectorError: On network or parsing failure.
        """
        try:
            import httpx
        except ImportError:
            raise ConnectorError("httpx is required for URLCrawlerConnector: pip install httpx")

        visited: set[str] = set()
        documents: list[Document] = []
        queue: list[tuple[str, int]] = [(self.start_url, 0)]

        async with httpx.AsyncClient(
            follow_redirects=True, timeout=self.timeout
        ) as client:
            while queue and len(documents) < self.max_pages:
                url, depth = queue.pop(0)

                if url in visited:
                    continue
                visited.add(url)

                # Domain check
                parsed = urlparse(url)
                if parsed.netloc not in self.allowed_domains:
                    continue

                # Robots.txt check
                if self.respect_robots and not await self._check_robots(client, url):
                    logger.debug("Blocked by robots.txt: %s", url)
                    continue

                try:
                    response = await client.get(url)
                    response.raise_for_status()
                except Exception as exc:
                    logger.warning("Failed to fetch %s: %s", url, exc)
                    continue

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    continue

                html = response.text
                title, text, links = self._parse_html(html, url)

                if text.strip():
                    documents.append(
                        Document(
                            content=text,
                            title=title or url,
                            source=url,
                            metadata={
                                "connector": self.name,
                                "source_type": "url",
                                "url": url,
                                "depth": depth,
                            },
                        )
                    )

                # Enqueue child links
                if depth < self.max_depth:
                    for link in links:
                        absolute = urljoin(url, link)
                        if absolute not in visited:
                            queue.append((absolute, depth + 1))

        logger.info("Crawled %d pages from %s", len(documents), self.start_url)
        return documents

    async def test_connection(self) -> bool:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.head(self.start_url, follow_redirects=True)
                return response.status_code < 400
        except Exception:
            return False

    @staticmethod
    def _parse_html(html: str, base_url: str) -> tuple[str, str, list[str]]:
        """Parse HTML and return (title, text, links)."""
        try:
            # Try trafilatura first for better content extraction
            import trafilatura

            text = trafilatura.extract(html) or ""
        except ImportError:
            text = ""

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        # Fallback to BS4 if trafilatura unavailable or returned nothing
        if not text.strip():
            for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        links: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href and not href.startswith(("#", "mailto:", "javascript:", "tel:")):
                links.append(href)

        return title, text, links

    async def _check_robots(self, client, url: str) -> bool:
        """Check if the URL is allowed by robots.txt."""
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            from urllib.robotparser import RobotFileParser

            response = await client.get(robots_url)
            if response.status_code != 200:
                return True  # No robots.txt means allowed

            rp = RobotFileParser()
            rp.parse(response.text.splitlines())
            return rp.can_fetch("*", url)
        except Exception:
            return True  # Allow on failure
