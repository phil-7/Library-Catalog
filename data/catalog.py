"""
libraryhub/catalog.py

Orchestrates discovery across configured sources and returns a unified list
of CatalogItem objects.

Responsibilities:
- instantiate concrete Source implementations (or accept them from caller)
- call is_available() and discover() on each source, handling transient errors
- normalize and deduplicate results (by open_url when available)
- return a stable list[CatalogItem] suitable for writing to the DB or serving

This module intentionally keeps orchestration logic simple and testable.
"""
from __future__ import annotations

import logging
from typing import List, Optional, Iterable, Set, Tuple

from libraryhub.models import CatalogItem
from libraryhub.sources.base import Source, FakeSource

logger = logging.getLogger(__name__)


def _import_default_sources() -> List[Source]:
    """
    Try to import and instantiate default concrete sources.

    If a source module is missing or fails to initialize, log and continue.
    This keeps the catalog builder resilient during development.
    """
    sources: List[Source] = []

    # Attempt to load KiwixSource if available
    try:
        from libraryhub.sources.kiwix import KiwixSource  # type: ignore
    except Exception as exc:
        logger.debug("KiwixSource not available: %s", exc)
    else:
        try:
            sources.append(KiwixSource())
        except Exception as exc:
            logger.warning("Failed to instantiate KiwixSource: %s", exc)

    # Attempt to load KolibriSource if available
    try:
        from libraryhub.sources.kolibri import KolibriSource  # type: ignore
    except Exception as exc:
        logger.debug("KolibriSource not available: %s", exc)
    else:
        try:
            sources.append(KolibriSource())
        except Exception as exc:
            logger.warning("Failed to instantiate KolibriSource: %s", exc)

    # If no real sources were found, provide a tiny FakeSource so the app can run.
    if not sources:
        logger.info("No concrete sources found; using FakeSource for local development.")
        sample = [
            CatalogItem(
                source="fake",
                title="Sample One",
                description="A sample item",
                language="en",
                kind="pdf",
                open_url="file:///data/sample1.pdf",
                extra={"size": 1234},
            ),
            CatalogItem(
                source="fake",
                title="Sample Two",
                description="Another sample",
                language="es",
                kind="zim",
                open_url="file:///data/sample2.zim",
                extra={"article_count": 42},
            ),
        ]
        sources.append(FakeSource(sample))

    return sources


def _dedupe_items(items: Iterable[CatalogItem]) -> List[CatalogItem]:
    """
    Deduplicate items while preserving order.

    Deduplication key preference:
      1. open_url (if present and non-empty)
      2. (source, title) tuple fallback

    Returns a list with the first occurrence kept.
    """
    seen_urls: Set[str] = set()
    seen_pairs: Set[Tuple[str, str]] = set()
    out: List[CatalogItem] = []

    for it in items:
        key_url = (it.open_url or "").strip()
        if key_url:
            if key_url in seen_urls:
                continue
            seen_urls.add(key_url)
            out.append(it)
            continue

        pair = (it.source or "", (it.title or "").strip())
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        out.append(it)

    return out


def build_catalog(sources: Optional[Iterable[Source]] = None) -> List[CatalogItem]:
    """
    Build the catalog by querying each provided source (or default sources).

    - Calls is_available() first; if False, skips the source.
    - Calls discover() and collects CatalogItem objects.
    - Logs errors but continues with other sources.
    - Deduplicates results before returning.

    Returns a list[CatalogItem].
    """
    if sources is None:
        sources = _import_default_sources()

    items: List[CatalogItem] = []
    for src in sources:
        try:
            if not src.is_available():
                logger.info("Source %s not available; skipping.", repr(src))
                continue
        except Exception as exc:
            logger.warning("is_available() failed for %s: %s", repr(src), exc)
            # Treat as unavailable and continue
            continue

        try:
            discovered = src.discover() or []
            logger.info("Source %s discovered %d items", repr(src), len(discovered))
            items.extend(discovered)
        except Exception as exc:
            logger.exception("discover() failed for %s: %s", repr(src), exc)
            # Continue with other sources

    deduped = _dedupe_items(items)
    logger.info("Catalog built: %d items (deduped from %d)", len(deduped), len(items))
    return deduped


if __name__ == "__main__":
    # Quick manual smoke test when running this module directly.
    logging.basicConfig(level=logging.INFO)
    catalog = build_catalog()
    for i, item in enumerate(catalog, start=1):
        print(f"{i}. {item.source} - {item.title} ({item.language}) -> {item.open_url}")
