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

        return max(1, len(text) // 4)

    @staticmethod
    def page_priority(page: ProcessedContent) -> int:

        url = page.url.lower()
        title = page.title.lower()

        priority = 0

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

        for keyword, score in keywords.items():

            if keyword in url:
                priority += score

            if keyword in title:
                priority += score

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

        if not pages:
            return (
                f"COMPANY DOMAIN: {domain}\n\n"
                "PUBLIC WEBSITE EVIDENCE\n"
                "No website evidence available."
            )

        # -----------------------------------------------------
        # Sort pages by usefulness
        # -----------------------------------------------------

        ranked_pages = sorted(
            pages,
            key=self.page_priority,
            reverse=True,
        )

        sections = [
            f"COMPANY DOMAIN: {domain}",
            "",
            "PUBLIC WEBSITE EVIDENCE",
            "=" * 70,
            "",
            "Use only the evidence below when extracting company intelligence.",
            "Do not invent names, roles, emails, LinkedIn URLs, or company facts.",
            "",
        ]
        used_tokens = self.estimate_tokens(
            "\n".join(sections)
        )

        source_index = 1

        for page in ranked_pages:

            if used_tokens >= self.max_tokens:
                break

            # -------------------------------------------------
            # Build page metadata
            # -------------------------------------------------

            page_header = [
                f"SOURCE {source_index}",
                f"URL: {page.url}",
                f"TITLE: {page.title}",
                f"TOKEN COUNT: {page.token_count}",
            ]

            if page.emails:
                page_header.append(
                    "EMAILS FOUND: "
                    + ", ".join(page.emails)
                )

            if page.linkedin_urls:
                page_header.append(
                    "LINKEDIN URLS FOUND: "
                    + ", ".join(page.linkedin_urls)
                )

            page_header.extend(
                [
                    "",
                    "CONTENT:",
                    "-" * 70,
                ]
            )

            header_text = "\n".join(page_header)

            header_tokens = self.estimate_tokens(
                header_text
            )

            remaining_tokens = (
                self.max_tokens
                - used_tokens
                - header_tokens
            )

            if remaining_tokens <= 100:
                break

            # -------------------------------------------------
            # Limit page content to remaining global budget
            # -------------------------------------------------

            content = page.text or (
                "[No meaningful text extracted from this page]"
            )

            content_tokens = self.estimate_tokens(
                content
            )

            if content_tokens > remaining_tokens:

                # Approximate character limit.
                max_chars = remaining_tokens * 4

                content = content[:max_chars]

                content += (
                    "\n\n[Content truncated due to "
                    "global evidence token budget]"
                )

            page_section = (
                header_text
                + "\n"
                + content
                + "\n\n"
                + "=" * 70
                + "\n"
            )

            section_tokens = self.estimate_tokens(
                page_section
            )

            if (
                used_tokens + section_tokens
                > self.max_tokens
            ):
                break

            sections.append(page_section)

            used_tokens += section_tokens
            source_index += 1

        return "\n".join(sections)


def build_evidence(
    domain: str,
    pages: List[ProcessedContent],
    max_tokens: int = 10000,
) -> str:

    builder = EvidenceBuilder(
        max_tokens=max_tokens
    )

    return builder.build(
        domain=domain,
        pages=pages,
    )