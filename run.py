import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.llm.evidence import build_evidence
from app.llm.extractor import LLMExtractor
from app.scraper.browser import BrowserManager
from app.scraper.crawler import WebsiteCrawler
from app.scraper.content import ContentProcessor
from app.utils.logger import setup_logger

from app.scoring.scorer import LeadScorer
from app.outreach.generator import OutreachGenerator


OUTPUT_FILE = Path("output.json")


async def process_domain(
    domain: str,
    browser: BrowserManager,
    logger,
    extractor: LLMExtractor,
    scorer: LeadScorer,
    outreach_generator: OutreachGenerator,
):
    """
    Complete lead-enrichment pipeline for one domain.

    Pipeline:

    1. Fetch homepage
    2. Discover internal links
    3. Rank relevant pages
    4. Process webpage content
    5. Build LLM evidence
    6. Extract structured company intelligence
    7. Score the lead
    8. Generate personalized outreach
    9. Return complete result
    """

    result = {
        "domain": domain,
        "status": "failed",
        "error": None,
        "intelligence": None,
        "lead_scoring": None,
        "outreach": None,
        "metadata": {},
    }

    crawler = WebsiteCrawler(
        browser.context,
        max_pages=8,
    )

    processor = ContentProcessor(
        max_tokens=6000,
    )

    base_url = crawler.normalize_domain(domain)

    print("\n" + "=" * 70)
    print(f"PROCESSING: {base_url}")
    print("=" * 70)

    # =========================================================
    # 1. Fetch homepage
    # =========================================================

    print("\n[1/9] FETCHING HOMEPAGE")

    homepage = await crawler.fetch_page(
        base_url
    )

    if homepage["error"]:
        error_message = homepage["error"]

        logger.error(
            "Homepage failed for %s: %s",
            domain,
            error_message,
        )

        result["error"] = (
            f"Homepage fetch failed: {error_message}"
        )

        return result

    print(
        f"URL:          {homepage['url']}"
    )

    print(
        f"Status:       {homepage['status_code']}"
    )

    print(
        f"Title:        {homepage['title']}"
    )

    print(
        f"Links found:  {len(homepage['links'])}"
    )

    # =========================================================
    # 2. Discover internal links
    # =========================================================

    print("\n[2/9] DISCOVERING INTERNAL LINKS")

    internal_links = crawler.extract_internal_links(
        homepage["url"],
        homepage["links"],
    )

    print(
        f"Internal links discovered: "
        f"{len(internal_links)}"
    )

    # =========================================================
    # 3. Rank relevant pages
    # =========================================================

    print("\n[3/9] RANKING RELEVANT PAGES")

    relevant_pages = crawler.prioritize_links(
        internal_links,
        max_pages=8,
    )

    if not relevant_pages:
        print(
            "No relevant subpages discovered."
        )

    else:
        for index, link in enumerate(
            relevant_pages,
            start=1,
        ):
            print(
                f"{index}. "
                f"[score={link['score']}] "
                f"{link['url']}"
            )

            if link.get("anchor_text"):
                print(
                    f"   Anchor: "
                    f"{link['anchor_text']}"
                )

    # =========================================================
    # 4. Process homepage
    # =========================================================

    print("\n[4/9] PROCESSING CONTENT")

    processed_pages = []

    homepage_content = processor.process(
        url=homepage["url"],
        title=homepage["title"],
        html=homepage["html"],
    )

    processed_pages.append(
        homepage_content
    )

    # =========================================================
    # 5. Fetch and process subpages
    # =========================================================

    for link in relevant_pages:

        try:

            page_result = await crawler.fetch_page(
                link["url"]
            )

            if page_result["error"]:

                logger.warning(
                    "Skipping %s: %s",
                    link["url"],
                    page_result["error"],
                )

                continue

            if not page_result["html"]:

                logger.warning(
                    "No HTML content: %s",
                    link["url"],
                )

                continue

            processed = processor.process(
                url=page_result["url"],
                title=page_result["title"],
                html=page_result["html"],
            )

            processed_pages.append(
                processed
            )

        except Exception as exc:

            logger.exception(
                "Failed processing subpage %s",
                link["url"],
            )

            continue

    # =========================================================
    # 6. Content statistics
    # =========================================================

    total_tokens = 0

    all_emails = set()
    all_linkedin = set()

    for page in processed_pages:

        total_tokens += page.token_count

        all_emails.update(
            page.emails
        )

        all_linkedin.update(
            page.linkedin_urls
        )

    print(
        f"Pages processed: "
        f"{len(processed_pages)}"
    )

    print(
        f"Clean tokens: "
        f"{total_tokens}"
    )

    print(
        f"Emails found: "
        f"{sorted(all_emails)}"
    )

    print(
        f"LinkedIn URLs found: "
        f"{sorted(all_linkedin)}"
    )

    # =========================================================
    # 7. Build LLM evidence
    # =========================================================

    print("\n[5/9] BUILDING LLM EVIDENCE")

    evidence = build_evidence(
        domain=domain,
        pages=processed_pages,
    )

    print(
        f"Evidence characters: "
        f"{len(evidence):,}"
    )

    # =========================================================
    # 8. LLM structured extraction
    # =========================================================

    print("\n[6/9] LLM EXTRACTION")

    try:

        intelligence = await extractor.extract(
            company_domain=domain,
            evidence=evidence,
        )

        intelligence_dict = (
            intelligence.model_dump()
        )

        result["intelligence"] = (
            intelligence_dict
        )

        print(
            "\nStructured LLM result:"
        )

        print(
            json.dumps(
                intelligence_dict,
                indent=2,
            )
        )

    except Exception as exc:

        logger.exception(
            "LLM extraction failed for %s",
            domain,
        )

        result["error"] = (
            f"LLM extraction failed: {str(exc)}"
        )

        result["metadata"] = {
            "pages_processed": len(
                processed_pages
            ),
            "emails_found": sorted(
                all_emails
            ),
            "linkedin_urls_found": sorted(
                all_linkedin
            ),
            "clean_tokens": total_tokens,
            "evidence_characters": len(
                evidence
            ),
        }

        return result

    # =========================================================
    # 9. Lead scoring
    # =========================================================

    print("\n[7/9] LEAD QUALIFICATION")

    try:

        lead_score = scorer.score(
            intelligence_dict
        )

        if hasattr(
            lead_score,
            "model_dump",
        ):
            lead_score_dict = (
                lead_score.model_dump()
            )

        elif isinstance(
            lead_score,
            dict,
        ):
            lead_score_dict = lead_score

        else:
            lead_score_dict = {
                "score": getattr(
                    lead_score,
                    "score",
                    0,
                ),
                "priority": getattr(
                    lead_score,
                    "priority",
                    "C",
                ),
                "reasons": getattr(
                    lead_score,
                    "reasons",
                    [],
                ),
            }

        result["lead_scoring"] = (
            lead_score_dict
        )

        print(
            f"Lead Score: "
            f"{lead_score_dict.get('score', 0)}/100"
        )

        print(
            f"Priority: "
            f"{lead_score_dict.get('priority', 'C')}"
        )

        print("\nReasons:")

        for reason in lead_score_dict.get(
            "reasons",
            [],
        ):
            print(
                f"- {reason}"
            )

    except Exception as exc:

        logger.exception(
            "Lead scoring failed for %s",
            domain,
        )

        result["lead_scoring"] = {
            "score": 0,
            "priority": "C",
            "reasons": [
                f"Scoring failed: {str(exc)}"
            ],
        }

    # =========================================================
    # 10. Outreach generation
    # =========================================================

    print("\n[8/9] GENERATING OUTREACH")

    try:

        outreach = (
            outreach_generator.generate(
                domain=domain,
                intelligence=intelligence_dict,
                lead_scoring=result[
                    "lead_scoring"
                ] or {},
            )
        )

        result["outreach"] = outreach

        print(
            f"Subject: "
            f"{outreach.get('subject', '')}"
        )

        print(
            f"Priority: "
            f"{outreach.get('priority', '')}"
        )

        print(
            f"Lead Score: "
            f"{outreach.get('lead_score', '')}"
        )

        print("\nMessage:")

        print(
            outreach.get(
                "body",
                "",
            )
        )

    except Exception as exc:

        logger.exception(
            "Outreach generation failed for %s",
            domain,
        )

        result["outreach"] = {
            "subject": "",
            "body": "",
            "priority": "C",
            "lead_score": "0",
        }

    # =========================================================
    # 11. Final metadata
    # =========================================================

    result["metadata"] = {
        "pages_processed": len(
            processed_pages
        ),
        "emails_found": sorted(
            all_emails
        ),
        "linkedin_urls_found": sorted(
            all_linkedin
        ),
        "clean_tokens": total_tokens,
        "evidence_characters": len(
            evidence
        ),
    }

    result["status"] = "success"

    print("\n[9/9] DOMAIN COMPLETE")

    print(
        f"Successfully enriched: "
        f"{domain}"
    )

    return result


def save_output(results):
    """
    Save all domain results to output.json.
    """

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"\nOutput saved to: "
        f"{OUTPUT_FILE.resolve()}"
    )


async def main():

    # =========================================================
    # Environment
    # =========================================================

    load_dotenv()

    logger = setup_logger()

    # =========================================================
    # Validate command line
    # =========================================================

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            "python run.py postman.com"
        )

        print(
            "python run.py "
            "postman.com supabase.com vapi.ai"
        )

        return

    domains = sys.argv[1:]

    # =========================================================
    # Initialize components
    # =========================================================

    try:

        extractor = LLMExtractor()

        scorer = LeadScorer()

        outreach_generator = (
            OutreachGenerator()
        )

    except Exception as exc:

        logger.exception(
            "Failed initializing application"
        )

        print(
            f"Initialization failed: {exc}"
        )

        return

    # =========================================================
    # Start browser
    # =========================================================

    browser = BrowserManager(
        headless=True
    )

    results = []

    try:

        print(
            "[Browser] Starting Chromium..."
        )

        await browser.start()

        # =====================================================
        # Process domains one by one
        # =====================================================

        for domain in domains:

            try:

                result = await process_domain(
                    domain=domain,
                    browser=browser,
                    logger=logger,
                    extractor=extractor,
                    scorer=scorer,
                    outreach_generator=(
                        outreach_generator
                    ),
                )

                results.append(
                    result
                )

                # Save after every domain.
                #
                # This is important because if a later
                # domain fails, previously processed
                # companies are still stored.
                save_output(
                    results
                )

            except Exception as exc:

                logger.exception(
                    "Domain failed unexpectedly: %s",
                    domain,
                )

                failed_result = {
                    "domain": domain,
                    "status": "failed",
                    "error": str(exc),
                    "intelligence": None,
                    "lead_scoring": None,
                    "outreach": None,
                    "metadata": {},
                }

                results.append(
                    failed_result
                )

                save_output(
                    results
                )

    finally:

        await browser.close()

    # =========================================================
    # Final summary
    # =========================================================

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    successful = sum(
        1
        for result in results
        if result["status"] == "success"
    )

    failed = len(results) - successful

    print(
        f"Domains processed: {len(results)}"
    )

    print(
        f"Successful: {successful}"
    )

    print(
        f"Failed: {failed}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    asyncio.run(main())