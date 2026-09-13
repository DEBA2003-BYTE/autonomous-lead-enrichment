import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from app.llm.evidence import build_evidence
from app.llm.extractor import LLMExtractor
from app.scraper.browser import BrowserManager
from app.scraper.crawler import WebsiteCrawler
from app.scraper.content import ContentProcessor
from app.scoring.scorer import LeadScorer
from app.outreach.generator import OutreachGenerator
from app.metrics.cost import CostTracker
from app.utils.logger import setup_logger


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

logger = setup_logger()

OUTPUT_FILE = Path("output.json")


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> str:
    """
    Return the current UTC timestamp in ISO-8601 format.
    """

    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def serialize_model(value):
    """
    Safely serialize Pydantic models or normal Python objects.
    """

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if isinstance(value, dict):
        return value

    return value


def is_http_failure(page: dict) -> bool:
    """
    Determine whether a fetched page represents an HTTP failure.
    """

    status_code = page.get("status_code")

    return (
        status_code is not None
        and status_code >= 400
    )


# ============================================================
# DOMAIN PROCESSING
# ============================================================

async def process_domain(
    domain: str,
    context,
    extractor: LLMExtractor,
    scorer: LeadScorer,
    outreach_generator: OutreachGenerator,
    cost_tracker: CostTracker,
):
    """
    Run the complete enrichment pipeline for one domain.

    Pipeline:

        1. Homepage
        2. Internal page discovery
        3. Selected page crawling
        4. Evidence construction
        5. LLM intelligence extraction
        6. Lead scoring
        7. Outreach generation
    """

    crawler = WebsiteCrawler(
        context=context,
        max_pages=8,
    )

    processor = ContentProcessor()

    normalized_domain = crawler.normalize_domain(
        domain
    )

    print()
    print("=" * 70)
    print(
        "PROCESSING: {}".format(
            normalized_domain
        )
    )
    print("=" * 70)

    result = {
        "domain": normalized_domain,
        "success": False,
        "error": None,
        "processed_at": utc_now(),
        "pages": [],
        "intelligence": None,
        "lead_score": None,
        "outreach": None,
        "cost": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_input_cost_usd": 0,
            "estimated_output_cost_usd": 0,
            "estimated_cost_usd": 0,
        },
    }

    # ========================================================
    # 1. HOMEPAGE
    # ========================================================

    print("[1/7] Fetching homepage...")

    homepage = await crawler.fetch_page(
        normalized_domain
    )

    if homepage.get("error"):

        error = homepage["error"]

        logger.error(
            "Homepage failed for %s: %s",
            domain,
            error,
        )

        result["error"] = (
            "Homepage fetch failed: {}".format(
                error
            )
        )

        return result

    if is_http_failure(homepage):

        error = (
            "Homepage returned HTTP {}".format(
                homepage["status_code"]
            )
        )

        logger.error(
            "%s: %s",
            normalized_domain,
            error,
        )

        result["error"] = error

        return result

    # ========================================================
    # 2. DISCOVER INTERNAL PAGES
    # ========================================================

    print("[2/7] Discovering internal pages...")

    internal_links = (
        crawler.extract_internal_links(
            normalized_domain,
            homepage.get(
                "links",
                [],
            ),
        )
    )

    prioritized_links = (
        crawler.prioritize_links(
            internal_links,
            max_pages=8,
        )
    )

    print(
        "Discovered {} candidate pages.".format(
            len(prioritized_links)
        )
    )

    # ========================================================
    # 3. FETCH SELECTED PAGES
    # ========================================================

    print("[3/7] Fetching selected pages...")

    pages = [
        processor.process(homepage)
    ]

    for index, link in enumerate(
        prioritized_links,
        start=1,
    ):

        print(
            "  Fetching page {}/{}: {}".format(
                index,
                len(prioritized_links),
                link["url"],
            )
        )

        try:

            page = await crawler.fetch_page(
                link["url"]
            )

        except Exception as exc:

            logger.warning(
                "Failed to fetch %s: %s",
                link["url"],
                exc,
            )

            continue

        if page.get("error"):

            logger.warning(
                "Skipping page %s: %s",
                link["url"],
                page["error"],
            )

            continue

        if is_http_failure(page):

            logger.warning(
                "Skipping page %s: HTTP %s",
                link["url"],
                page["status_code"],
            )

            continue

        try:

            processed_page = processor.process(
                page
            )

            pages.append(
                processed_page
            )

        except Exception as exc:

            logger.warning(
                "Content processing failed for %s: %s",
                link["url"],
                exc,
            )

    print(
        "Successfully processed {} page(s).".format(
            len(pages)
        )
    )

    # ========================================================
    # 4. BUILD EVIDENCE
    # ========================================================

    print("[4/7] Building evidence...")

    evidence = build_evidence(
        normalized_domain,
        pages,
        max_tokens=10000,
    )

    total_clean_tokens = sum(
        page.token_count
        for page in pages
    )

    print(
        "Clean tokens: {}".format(
            total_clean_tokens
        )
    )

    result["pages"] = [
        {
            "url": page.url,
            "title": page.title,
            "emails": page.emails,
            "linkedin_urls": page.linkedin_urls,
            "token_count": page.token_count,
        }
        for page in pages
    ]

    result["clean_tokens"] = (
        total_clean_tokens
    )

    # ========================================================
    # 5. LLM EXTRACTION
    # ========================================================

    print(
        "[5/7] Extracting company intelligence..."
    )

    try:

        intelligence = await extractor.extract(
            company_domain=normalized_domain,
            evidence=evidence,
        )

    except Exception as exc:

        usage = extractor.get_usage()

        result["cost"] = (
            cost_tracker.calculate(
                usage
            )
        )

        error_text = str(exc)

        logger.error(
            "LLM extraction failed for %s: %s",
            domain,
            error_text,
        )

        # ----------------------------------------------------
        # Give a useful error classification.
        # ----------------------------------------------------

        lowered_error = error_text.lower()

        if (
            "rate limit" in lowered_error
            or "429" in lowered_error
            or "quota" in lowered_error
        ):

            result["error"] = (
                "LLM API rate limit or quota exceeded: "
                + error_text
            )

        elif (
            "authentication" in lowered_error
            or "api key" in lowered_error
            or "401" in lowered_error
        ):

            result["error"] = (
                "LLM API authentication failed: "
                + error_text
            )

        else:

            result["error"] = (
                "LLM extraction failed: "
                + error_text
            )

        return result

    # ========================================================
    # LLM COST
    # ========================================================

    usage = extractor.get_usage()

    llm_cost = cost_tracker.calculate(
        usage
    )

    result["cost"] = llm_cost

    print(
        "Input tokens: {}".format(
            llm_cost["input_tokens"]
        )
    )

    print(
        "Output tokens: {}".format(
            llm_cost["output_tokens"]
        )
    )

    print(
        "Total LLM tokens: {}".format(
            llm_cost["total_tokens"]
        )
    )

    print(
        "Estimated LLM cost: ${:.8f}".format(
            llm_cost["estimated_cost_usd"]
        )
    )

    # ========================================================
    # 6. LEAD SCORING
    # ========================================================

    print("[6/7] Scoring lead...")

    try:

        lead_score = scorer.score(
            intelligence
        )

    except Exception as exc:

        logger.error(
            "Lead scoring failed for %s: %s",
            domain,
            exc,
        )

        result["error"] = (
            "Lead scoring failed: {}".format(
                str(exc)
            )
        )

        result["intelligence"] = (
            serialize_model(
                intelligence
            )
        )

        return result

    # ========================================================
    # 7. OUTREACH GENERATION
    # ========================================================

    print("[7/7] Generating outreach...")

    try:

        outreach = outreach_generator.generate(
            intelligence=intelligence,
            company_domain=normalized_domain,
        )

    except Exception as exc:

        logger.warning(
            "Outreach generation failed for %s: %s",
            domain,
            exc,
        )

        # Outreach failure should not destroy the
        # successfully extracted lead.

        outreach = {
            "error": str(exc)
        }

    # ========================================================
    # FINAL RESULT
    # ========================================================

    result["success"] = True

    result["intelligence"] = (
        serialize_model(
            intelligence
        )
    )

    result["lead_score"] = (
        serialize_model(
            lead_score
        )
    )

    result["outreach"] = (
        serialize_model(
            outreach
        )
    )

    return result


# ============================================================
# MAIN PIPELINE
# ============================================================

async def main():

    domains = sys.argv[1:]

    if not domains:

        print()
        print(
            "Usage:"
        )

        print(
            "  python run.py example.com"
        )

        print(
            "  python run.py postman.com supabase.com vapi.ai"
        )

        print()

        return

    print("=" * 70)
    print("AUTONOMOUS LEAD ENRICHMENT")
    print("=" * 70)

    print(
        "Domains to process: {}".format(
            len(domains)
        )
    )

    browser_manager = BrowserManager()

    extractor = None
    scorer = None
    outreach_generator = None
    cost_tracker = None

    results = []

    # ========================================================
    # INITIALIZE PIPELINE COMPONENTS
    # ========================================================

    try:

        extractor = LLMExtractor()

        scorer = LeadScorer()

        outreach_generator = (
            OutreachGenerator()
        )

        cost_tracker = CostTracker()

    except Exception as exc:

        logger.exception(
            "Pipeline initialization failed."
        )

        print()
        print(
            "ERROR: Pipeline initialization failed."
        )

        print(
            str(exc)
        )

        return

    # ========================================================
    # START BROWSER
    # ========================================================

    context = None

    try:

        print()
        print(
            "[Browser] Starting Chromium..."
        )

        context = (
            await browser_manager.start()
        )

        # ====================================================
        # PROCESS DOMAINS
        # ====================================================

        for domain in domains:

            try:

                result = await process_domain(
                    domain=domain,
                    context=context,
                    extractor=extractor,
                    scorer=scorer,
                    outreach_generator=(
                        outreach_generator
                    ),
                    cost_tracker=cost_tracker,
                )

                results.append(
                    result
                )

            except KeyboardInterrupt:

                raise

            except Exception as exc:

                logger.exception(
                    "Unexpected failure for %s",
                    domain,
                )

                results.append(
                    {
                        "domain": domain,
                        "success": False,
                        "error": (
                            "Unexpected pipeline error: "
                            + str(exc)
                        ),
                        "processed_at": utc_now(),
                    }
                )

    finally:

        print()
        print(
            "[Browser] Closing Chromium..."
        )

        try:

            await browser_manager.close()

        except Exception as exc:

            logger.warning(
                "Browser shutdown error: %s",
                exc,
            )

    # ========================================================
    # AGGREGATE METRICS
    # ========================================================

    successful = sum(
        1
        for result in results
        if result.get("success")
    )

    failed = sum(
        1
        for result in results
        if not result.get("success")
    )

    total_input_tokens = sum(
        result.get(
            "cost",
            {},
        ).get(
            "input_tokens",
            0,
        )
        for result in results
    )

    total_output_tokens = sum(
        result.get(
            "cost",
            {},
        ).get(
            "output_tokens",
            0,
        )
        for result in results
    )

    total_tokens = sum(
        result.get(
            "cost",
            {},
        ).get(
            "total_tokens",
            0,
        )
        for result in results
    )

    total_cost = sum(
        result.get(
            "cost",
            {},
        ).get(
            "estimated_cost_usd",
            0,
        )
        for result in results
    )

    # ========================================================
    # SAVE OUTPUT
    # ========================================================

    output = {
        "generated_at": utc_now(),
        "domains_processed": len(domains),
        "successful": successful,
        "failed": failed,

        "summary": {
            "success_rate": round(
                (
                    successful
                    / len(domains)
                    * 100
                )
                if domains
                else 0,
                2,
            ),
            "total_input_tokens": (
                total_input_tokens
            ),
            "total_output_tokens": (
                total_output_tokens
            ),
            "total_llm_tokens": (
                total_tokens
            ),
            "estimated_total_llm_cost_usd": round(
                total_cost,
                8,
            ),
        },

        "results": results,
    }

    OUTPUT_FILE.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ========================================================
    # FINAL TERMINAL SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    print(
        "Domains processed: {}".format(
            len(domains)
        )
    )

    print(
        "Successful: {}".format(
            successful
        )
    )

    print(
        "Failed: {}".format(
            failed
        )
    )

    print(
        "Total LLM tokens: {}".format(
            total_tokens
        )
    )

    print(
        "Estimated LLM cost: ${:.8f}".format(
            total_cost
        )
    )

    print(
        "Output: {}".format(
            OUTPUT_FILE
        )
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        print()
        print(
            "Pipeline interrupted by user."
        )

        sys.exit(130)