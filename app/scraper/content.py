import re
from dataclasses import dataclass
from typing import List

from bs4 import BeautifulSoup


@dataclass
class ProcessedContent:
    url: str
    title: str
    text: str
    emails: List[str]
    linkedin_urls: List[str]
    token_count: int


class ContentProcessor:

    EMAIL_PATTERN = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    LINKEDIN_PATTERN = re.compile(
        r"https?://(?:www\.)?linkedin\.com/"
        r"(?:in|pub)/[A-Za-z0-9._%\-]+",
        re.IGNORECASE,
    )

    @staticmethod
    def estimate_tokens(
        text: str,
    ) -> int:

        if not text:
            return 0

        return max(
            1,
            len(text) // 4,
        )

    @classmethod
    def process(
        cls,
        page: dict,
    ) -> ProcessedContent:

        html = page.get(
            "html",
            "",
        )

        title = page.get(
            "title",
            "",
        )

        url = page.get(
            "url",
            "",
        )

        raw_text = page.get(
            "text",
            "",
        )

        if html:

            soup = BeautifulSoup(
                html,
                "html.parser",
            )

            for element in soup(
                [
                    "script",
                    "style",
                    "noscript",
                    "svg",
                ]
            ):
                element.decompose()

            text = soup.get_text(
                " ",
                strip=True,
            )

        else:
            text = raw_text

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        emails = sorted(
            set(
                cls.EMAIL_PATTERN.findall(
                    html + " " + text
                )
            )
        )

        linkedin_urls = sorted(
            set(
                cls.LINKEDIN_PATTERN.findall(
                    html
                )
            )
        )

        return ProcessedContent(
            url=url,
            title=title,
            text=text,
            emails=emails,
            linkedin_urls=linkedin_urls,
            token_count=cls.estimate_tokens(
                text
            ),
        )