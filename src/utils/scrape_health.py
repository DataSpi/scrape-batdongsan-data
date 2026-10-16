"""
Page-level health of one scrape step, and the exit-code contract with the orchestrator.

fetch_and_parse() returns None for a page it could not fetch (after retries), and the scrapers
used to drop those silently, so a step could finish "Done" with most of its data missing. A
ScrapeHealth counts them instead, and turns the result into an exit code that
src/orchestrator/run_pipeline.py understands:

    0  EXIT_OK       every page fetched
    2  EXIT_PARTIAL  some pages/districts failed, but at least MIN_PAGE_SUCCESS_RATIO of the pages
                     came through; what was scraped is loaded and the pipeline carries on
    1  EXIT_FAILED   below the threshold, or nothing scraped (what was scraped is still loaded)
"""

import os

from src.utils.common_tools import setup_logging

logger = setup_logging()

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_PARTIAL = 2

MIN_PAGE_SUCCESS_RATIO = float(os.getenv("SCRAPE_MIN_PAGE_SUCCESS_RATIO", "0.5"))


class ScrapeHealth:
    def __init__(self):
        self.pages_total = 0
        self.pages_failed = 0
        self.districts_skipped = []

    def record_pages(self, total, failed):
        """Count one crawl's pages. The first page is fetched separately and has to succeed for
        the crawl to start at all, so callers pass `failed` for the remaining pages only."""
        self.pages_total += total
        self.pages_failed += failed

    def record_skipped_district(self, name):
        """A district whose first page could not be fetched (or whose URL did not resolve) never
        gets its page count, so it counts as one failed page."""
        self.districts_skipped.append(name)
        self.pages_total += 1
        self.pages_failed += 1

    @property
    def success_ratio(self):
        return 1.0 if self.pages_total == 0 else (self.pages_total - self.pages_failed) / self.pages_total

    def finish(self, df):
        """Log the summary, print the machine-readable metric line, and return the exit code."""
        pages_ok = self.pages_total - self.pages_failed
        print(f"PIPELINE_METRIC pages_ok={pages_ok} pages_total={self.pages_total}", flush=True)
        if self.districts_skipped:
            logger.warning(f"Skipped districts: {', '.join(self.districts_skipped)}")
        logger.info(f"Scrape health: {pages_ok}/{self.pages_total} pages ({self.success_ratio:.0%}), {len(df)} rows")

        if df.empty or self.success_ratio < MIN_PAGE_SUCCESS_RATIO:
            return EXIT_FAILED
        return EXIT_OK if self.pages_failed == 0 else EXIT_PARTIAL
