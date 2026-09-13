from typing import List

from app.scraper.content import ProcessedContent


class EvidenceBuilder:

    def __init__(
        self,
        max_tokens: int = 10000,
    ):
        self.max_tokens = max_tokens

    @staticmethod
    def estimate_tokens(text: str) -> int:

        if not text:
            return 0

        return max(
            1,
            len(text) // 4,
        )

    @staticmethod
    def page_priority(
        page: ProcessedContent,
    ) -> int:

        url = page.url.lower()
        title = page.title.lower()

        keywords = {
            "about": 30,
            "company": 30,
            "team": 30,
            "leadership": 30,
            "contact": 25,
            "pricing": 20,
            "product": 15,
            "products": 15,
            "solutions": 15,
            "customers": 15,
            "security": 10,
            "careers": 10,
        }

        priority = 0

        for keyword, points in keywords.items():

            if keyword in url:
                priority += points

            if keyword in title:
                priority += points

        if page.emails:
            priority += 20

        if page.linkedin_urls:
            priority += 20

        priority += min(
            page.token_count // 500,
            10,
        )

        return priority

    def build(
        self,
        domain: str,
        pages: List[ProcessedContent],
    ) -> str:

        sections = [
            "COMPANY DOMAIN: " + domain,
            "",
            "PUBLIC WEBSITE EVIDENCE",
            "=" * 70,
            "",
            "Use only the evidence below.",
            "Do not invent information.",
            "",
        ]

        if not pages:

            sections.append(
                "No website evidence available."
            )

            return "\n".join(sections)

        ranked_pages = sorted(
            pages,
            key=self.page_priority,
            reverse=True,
        )

        used_tokens = self.estimate_tokens(
            "\n".join(sections)
        )

        source_index = 1

        for page in ranked_pages:

            if used_tokens >= self.max_tokens:
                break

            header = [
                "SOURCE {}".format(source_index),
                "URL: {}".format(page.url),
                "TITLE: {}".format(page.title),
                "TOKEN COUNT: {}".format(page.token_count),
            ]

            if page.emails:
                header.append(
                    "EMAILS FOUND: "
                    + ", ".join(page.emails)
                )

            if page.linkedin_urls:
                header.append(
                    "LINKEDIN URLS FOUND: "
                    + ", ".join(page.linkedin_urls)
                )

            header.extend(
                [
                    "",
                    "CONTENT:",
                    "-" * 70,
                ]
            )

            header_text = "\n".join(header)

            header_tokens = self.estimate_tokens(
                header_text
            )

            remaining = (
                self.max_tokens
                - used_tokens
                - header_tokens
            )

            if remaining <= 100:
                break

            content = page.text or (
                "[No meaningful text extracted]"
            )

            if self.estimate_tokens(content) > remaining:

                max_chars = remaining * 4

                content = content[:max_chars]

                content += (
                    "\n\n[Content truncated]"
                )

            section = (
                header_text
                + "\n"
                + content
                + "\n\n"
                + "=" * 70
            )

            section_tokens = self.estimate_tokens(
                section
            )

            if (
                used_tokens + section_tokens
                > self.max_tokens
            ):
                break

            sections.append(section)

            used_tokens += section_tokens
            source_index += 1

        return "\n".join(sections)


def build_evidence(
    domain: str,
    pages: List[ProcessedContent],
    max_tokens: int = 10000,
) -> str:

    return EvidenceBuilder(
        max_tokens=max_tokens
    ).build(
        domain=domain,
        pages=pages,
    )