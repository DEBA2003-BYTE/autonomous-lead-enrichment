import html as html_module
import re

from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse, urlunparse

import tiktoken
from bs4 import BeautifulSoup, Comment


@dataclass
class ProcessedContent:

    url: str
    title: str
    text: str
    emails: List[str]
    linkedin_urls: List[str]
    token_count: int


class ContentProcessor:

    UNWANTED_TAGS = {
        "script",
        "style",
        "noscript",
        "svg",
        "canvas",
        "iframe",
        "template",
        "path",
        "video",
        "audio",
        "source",
        "track",
    }

    STRUCTURAL_BOILERPLATE_TAGS = {
        "nav",
        "footer",
        "aside",
    }

    EMAIL_PATTERN = re.compile(
        r"""
        (?<![A-Za-z0-9._%+-])
        [A-Za-z0-9._%+-]+
        @
        [A-Za-z0-9.-]+\.[A-Za-z]{2,}
        (?![A-Za-z0-9._%+-])
        """,
        re.VERBOSE,
    )

    LINKEDIN_PATTERN = re.compile(
        r"""
        https?://
        (?:www\.)?
        linkedin\.com/
        (?:
            in/
            [A-Za-z0-9._%-]+
            |
            company/
            [A-Za-z0-9._%-]+
        )
        (?:/[A-Za-z0-9._%/?=&-]*)?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    def __init__(
        self,
        max_tokens: int = 6000,
        encoding_name: str = "cl100k_base",
    ):
        self.max_tokens = max_tokens

        try:
            self.encoder = tiktoken.get_encoding(
                encoding_name
            )
        except Exception:
            self.encoder = None

    # =========================================================
    # MAIN PROCESSOR
    # =========================================================

    def process(
        self,
        url: str,
        title: str,
        html: str,
    ) -> ProcessedContent:

        if not html:
            return ProcessedContent(
                url=url,
                title=title or "",
                text="",
                emails=[],
                linkedin_urls=[],
                token_count=0,
            )

        decoded_html = html_module.unescape(html)

        emails = self.extract_emails(
            decoded_html
        )

        linkedin_urls = self.extract_linkedin_urls(
            decoded_html
        )

        soup = BeautifulSoup(
            decoded_html,
            "html.parser",
        )

        self.remove_unwanted_elements(
            soup
        )

        text = self.extract_clean_text(
            soup
        )

        text = self.normalize_text(
            text
        )

        text = self.remove_duplicate_lines(
            text
        )

        text = self.optimize_tokens(
            text
        )

        token_count = self.count_tokens(
            text
        )

        return ProcessedContent(
            url=url,
            title=title or "",
            text=text,
            emails=emails,
            linkedin_urls=linkedin_urls,
            token_count=token_count,
        )

    # =========================================================
    # HTML CLEANING
    # =========================================================

    @classmethod
    def remove_unwanted_elements(
        cls,
        soup: BeautifulSoup,
    ) -> None:
        for tag in soup.find_all(
            cls.UNWANTED_TAGS
        ):
            tag.decompose()
        for tag in soup.find_all(
            cls.STRUCTURAL_BOILERPLATE_TAGS
        ):
            tag.decompose()
        for comment in soup.find_all(
            string=lambda text: isinstance(
                text,
                Comment,
            )
        ):
            comment.extract()
        for tag in soup.find_all(
            style=True
        ):
            style = (
                tag.get(
                    "style",
                    "",
                )
                .lower()
                .replace(" ", "")
            )

            if (
                "display:none" in style
                or "visibility:hidden" in style
            ):
                tag.decompose()

        for tag in soup.find_all(
            attrs={
                "aria-hidden": "true"
            }
        ):
            tag.decompose()

        for tag in soup.find_all(
            attrs={"hidden": True}
        ):
            tag.decompose()

    # =========================================================
    # TEXT EXTRACTION
    # =========================================================

    @staticmethod
    def extract_clean_text(
        soup: BeautifulSoup,
    ) -> str:

        for heading in soup.find_all(
            [
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
            ]
        ):
            heading_text = heading.get_text(
                " ",
                strip=True,
            )

            if heading_text:
                heading.replace_with(
                    f"\n\n## {heading_text}\n\n"
                )

        for tag in soup.find_all(
            [
                "p",
                "li",
                "section",
                "article",
                "blockquote",
            ]
        ):
            tag_text = tag.get_text(
                " ",
                strip=True,
            )

            if tag_text:
                tag.replace_with(
                    f"\n{tag_text}\n"
                )

        text = soup.get_text(
            separator="\n",
            strip=True,
        )

        return text

    # =========================================================
    # TEXT NORMALIZATION
    # =========================================================

    @staticmethod
    def normalize_text(
        text: str,
    ) -> str:

        if not text:
            return ""

        text =html_module.unescape(text)

        text = text.replace(
            "\\u003e",
            ">",
        )

        text = text.replace(
            "\\u003c",
            "<",
        )

        text = text.replace(
            "\\u0026",
            "&",
        )

        text = text.replace(
            "\\u0022",
            '"',
        )

        text = text.replace(
            "\\u0027",
            "'",
        )

        text = text.replace(
            "\xa0",
            " ",
        )
        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r" *\n *",
            "\n",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    # =========================================================
    # DUPLICATE REMOVAL
    # =========================================================

    @staticmethod
    def remove_duplicate_lines(
        text: str,
    ) -> str:

        lines = text.splitlines()

        seen = set()
        cleaned = []

        for line in lines:

            normalized = line.strip()

            if not normalized:

                if (
                    cleaned
                    and cleaned[-1] != ""
                ):
                    cleaned.append("")

                continue

            # Keep short structural lines.
            if len(normalized) <= 3:
                cleaned.append(
                    normalized
                )
                continue

            key = re.sub(
                r"^#+\s*",
                "",
                normalized,
            ).lower()

            key = re.sub(
                r"\s+",
                " ",
                key,
            ).strip()

            if key in seen:
                continue

            seen.add(key)

            cleaned.append(
                normalized
            )

        return "\n".join(
            cleaned
        ).strip()

    # =========================================================
    # EMAIL EXTRACTION
    # =========================================================

    @classmethod
    def extract_emails(
        cls,
        html_content: str,
    ) -> List[str]:

        if not html_content:
            return []

        decoded = html_module.unescape(
            html_content
        )

        decoded = decoded.replace(
            "\\u0040",
            "@",
        )

        decoded = decoded.replace(
            "\\x40",
            "@",
        )

        matches = cls.EMAIL_PATTERN.findall(
            decoded
        )

        emails = []

        for email in matches:

            email = (
                email
                .lower()
                .strip()
                .rstrip(
                    ".,;:!?)]}>"
                )
            )

            if email.endswith(
                (
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".gif",
                    ".svg",
                    ".webp",
                )
            ):
                continue

            if email not in emails:
                emails.append(
                    email
                )

        return sorted(
            emails
        )

    # =========================================================
    # LINKEDIN EXTRACTION
    # =========================================================

    @classmethod
    def extract_linkedin_urls(
        cls,
        html_content: str,
    ) -> List[str]:

        if not html_content:
            return []

        decoded = html_module.unescape(
            html_content
        )

        decoded = decoded.replace(
            "\\/",
            "/",
        )

        decoded = decoded.replace(
            "\\u002F",
            "/",
        )

        matches = cls.LINKEDIN_PATTERN.findall(
            decoded
        )

        urls = []

        for url in matches:

            url = url.rstrip(
                ".,;:!?)]}"
            )

            normalized = cls.normalize_linkedin_url(
                url
            )

            if (
                normalized
                and normalized not in urls
            ):
                urls.append(
                    normalized
                )

        return sorted(
            urls
        )

    @staticmethod
    def normalize_linkedin_url(
        url: str,
    ) -> str:

        try:
            parsed = urlparse(
                url
            )

            hostname = (
                parsed.hostname or ""
            ).lower()

            if hostname not in {
                "linkedin.com",
                "www.linkedin.com",
            }:
                return ""

            path = parsed.path.rstrip(
                "/"
            )

            if not path:
                return ""

            if not (
                path.startswith("/in/")
                or path.startswith(
                    "/company/"
                )
            ):
                return ""

            return urlunparse(
                (
                    "https",
                    "www.linkedin.com",
                    path,
                    "",
                    "",
                    "",
                )
            )

        except Exception:
            return ""

    # =========================================================
    # TOKEN COUNTING
    # =========================================================

    def count_tokens(
        self,
        text: str,
    ) -> int:

        if not text:
            return 0

        if self.encoder is None:

            return max(
                1,
                len(text) // 4,
            )

        return len(
            self.encoder.encode(
                text
            )
        )

    # =========================================================
    # TOKEN OPTIMIZATION
    # =========================================================

    def optimize_tokens(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        if (
            self.count_tokens(text)
            <= self.max_tokens
        ):
            return text

        lines = text.splitlines()

        # -----------------------------------------------------
        # First preserve headings and important sections.
        # -----------------------------------------------------

        selected = []
        current_tokens = 0

        for line in lines:

            stripped = line.strip()

            if not stripped:
                continue

            line_tokens = self.count_tokens(
                line
            )

            if (
                current_tokens
                + line_tokens
                > self.max_tokens
            ):
                break

            selected.append(
                line
            )

            current_tokens += line_tokens

        result = "\n".join(
            selected
        ).strip()

        return result