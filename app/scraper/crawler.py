from urllib.parse import urlparse

from playwright.async_api import (
    BrowserContext,
    TimeoutError as PlaywrightTimeoutError,
)

class WebsiteCrawler:
    PAGE_KEYWORDS = {
        "about": 20,
        "company": 20,
        "team": 20,
        "leadership": 20,
        "contact": 18,
        "contact-us": 18,
        "pricing": 16,
        "product": 10,
        "products": 10,
        "solutions": 9,
        "customers": 9,
        "industries": 8,
        "security": 7,
        "careers": 5,
        "investors": 5,
    }

    EXCLUDED_KEYWORDS = {
        "blog",
        "docs",
        "documentation",
        "changelog",
        "login",
        "signin",
        "signup",
        "register",
        "download",
        "status",
        "community",
        "forum",
        "terms",
        "privacy",
        "cookie",
    }

    def __init__(
        self,
        context: BrowserContext,
        max_pages: int = 8,
    ):
        self.context = context
        self.max_pages = max_pages


    @staticmethod
    def normalize_domain(domain: str) -> str:
        domain = domain.strip()

        if not domain:
            raise ValueError("Domain cannot be empty.")

        if not domain.startswith(("http://", "https://")):
            domain = "https://" + domain

        return domain.rstrip("/")

    @staticmethod
    def normalize_hostname(hostname: str) -> str:

        hostname = hostname.lower().strip()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    async def fetch_page(self, url: str) -> dict:
        page = await self.context.new_page()

        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=30_000,
            )

            try:
                await page.wait_for_load_state(
                    "networkidle",
                    timeout=10_000,
                )
            except PlaywrightTimeoutError:
                pass

            status_code = (
                response.status
                if response
                else None
            )

            title = await page.title()

            html = await page.content()

            text = await page.locator("body").inner_text(
                timeout=10_000,
            )

            links = await page.locator(
                "a[href]"
            ).evaluate_all(
                """
                elements => elements.map(a => ({
                    text: (a.innerText || "").trim(),
                    href: a.href || ""
                }))
                """
            )

            return {
                "url": url,
                "status_code": status_code,
                "title": title,
                "html": html,
                "text": text,
                "links": links,
                "error": None,
            }

        except PlaywrightTimeoutError:
            return {
                "url": url,
                "status_code": None,
                "title": "",
                "html": "",
                "text": "",
                "links": [],
                "error": "timeout",
            }

        except Exception as exc:
            return {
                "url": url,
                "status_code": None,
                "title": "",
                "html": "",
                "text": "",
                "links": [],
                "error": str(exc),
            }

        finally:
            await page.close()


    @classmethod
    def extract_internal_links(
        cls,
        base_url: str,
        links: list[dict],
    ) -> list[dict]:

        base_domain = cls.normalize_hostname(
            urlparse(base_url).hostname or ""
        )

        internal_links = []
        seen = set()

        ignored_extensions = (
            ".pdf",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".webp",
            ".ico",
            ".zip",
            ".css",
            ".js",
            ".xml",
            ".mp4",
            ".mp3",
            ".wav",
        )

        for link in links:
            href = link.get("href", "").strip()
            text = link.get("text", "").strip()

            if not href:
                continue

            parsed = urlparse(href)

            if parsed.scheme not in ("http", "https"):
                continue

            hostname = cls.normalize_hostname(
                parsed.hostname or ""
            )

            if hostname != base_domain:
                continue

            path = parsed.path.lower()

            if path.endswith(ignored_extensions):
                continue

            clean_url = (
                f"{parsed.scheme}://"
                f"{parsed.netloc}"
                f"{parsed.path}"
            ).rstrip("/")

            if not clean_url:
                continue

            if clean_url in seen:
                continue

            seen.add(clean_url)

            internal_links.append(
                {
                    "url": clean_url,
                    "anchor_text": text,
                }
            )

        return internal_links

    @classmethod
    def score_link(
        cls,
        url: str,
        anchor_text: str = "",
    ) -> int:

        parsed = urlparse(url)

        path = parsed.path.lower().strip("/")
        anchor = anchor_text.lower().strip()

        segments = [
            segment
            for segment in path.split("/")
            if segment
        ]

        score = 0


        for segment in segments:
            if segment in cls.PAGE_KEYWORDS:
                score += cls.PAGE_KEYWORDS[segment]

        anchor_keywords = {
            "about us": 12,
            "about": 8,
            "company": 8,
            "our team": 12,
            "team": 8,
            "leadership": 10,
            "contact us": 10,
            "contact": 7,
            "sales": 7,
            "pricing": 7,
            "customers": 6,
            "security": 5,
        }

        for keyword, points in anchor_keywords.items():
            if keyword in anchor:
                score += points

        for keyword in cls.EXCLUDED_KEYWORDS:
            if keyword in segments:
                score -= 12

            if keyword in anchor:
                score -= 8

        if not segments:
            score -= 100

        return score


    @classmethod
    def prioritize_links(
        cls,
        links: list[dict],
        max_pages: int = 8,
    ) -> list[dict]:

        scored_links = []

        for link in links:
            url = link.get("url", "")

            if not url:
                continue

            score = cls.score_link(
                url,
                link.get("anchor_text", ""),
            )

            if score <= 0:
                continue

            scored_links.append(
                {
                    **link,
                    "score": score,
                }
            )

        scored_links.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        return scored_links[:max_pages]