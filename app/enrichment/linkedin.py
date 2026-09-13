import re
from typing import Dict, List, Optional
from urllib.parse import quote

from playwright.async_api import BrowserContext


class LinkedInFinder:
    """
    Finds publicly indexed LinkedIn profiles
    using search engine result pages.
    """

    def __init__(
        self,
        context: BrowserContext,
    ):
        self.context = context

    @staticmethod
    def normalize_linkedin_url(
        url: str,
    ) -> Optional[str]:

        if not url:
            return None

        match = re.search(
            r"https?://(?:www\.)?linkedin\.com/"
            r"(?:in|pub)/[^?\s\"'<>]+",
            url,
            re.IGNORECASE,
        )

        if not match:
            return None

        result = match.group(0)

        return result.rstrip(
            "/.,;:!?)]}"
        )

    @staticmethod
    def build_query(
        name: str,
        company: str,
    ) -> str:

        return (
            '"{}" "{}" site:linkedin.com/in'
            .format(
                name,
                company,
            )
        )

    async def search_profile(
        self,
        name: str,
        company: str,
    ) -> Optional[str]:

        if not name or not company:
            return None

        query = self.build_query(
            name,
            company,
        )

        search_url = (
            "https://www.google.com/search?q="
            + quote(query)
        )

        page = await self.context.new_page()

        try:

            await page.goto(
                search_url,
                wait_until="domcontentloaded",
                timeout=20000,
            )

            links = await page.locator(
                "a[href]"
            ).evaluate_all(
                """
                elements => elements.map(a => ({
                    href: a.href || "",
                    text: (a.innerText || "").trim()
                }))
                """
            )

            seen = set()

            for link in links:

                linkedin_url = (
                    self.normalize_linkedin_url(
                        link.get(
                            "href",
                            "",
                        )
                    )
                )

                if not linkedin_url:
                    continue

                if linkedin_url in seen:
                    continue

                seen.add(linkedin_url)

                return linkedin_url

            return None

        except Exception:

            return None

        finally:

            await page.close()

    async def find_for_leadership(
        self,
        leadership: List[Dict],
        company: str,
    ) -> List[Dict]:

        if not leadership:
            return leadership

        updated = []

        for member in leadership:

            member_copy = dict(member)

            if member_copy.get(
                "linkedin_url"
            ):
                updated.append(member_copy)
                continue

            name = member_copy.get(
                "name"
            )

            if not name:
                updated.append(member_copy)
                continue

            linkedin_url = await self.search_profile(
                name=name,
                company=company,
            )

            if linkedin_url:

                member_copy[
                    "linkedin_url"
                ] = linkedin_url

            updated.append(member_copy)

        return updated