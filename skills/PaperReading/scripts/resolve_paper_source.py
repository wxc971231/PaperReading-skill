#!/usr/bin/env python3
"""Resolve basic paper metadata and source links.

This is a lightweight helper, not a replacement for Codex's web research.
It is useful as a first pass for arXiv papers and for producing a structured
metadata artifact that Codex can compare with conference, OpenReview, project,
and author pages.

Examples:
  python resolve_paper_source.py "Attention is all you need"
  python resolve_paper_source.py 1706.03762
  python resolve_paper_source.py https://arxiv.org/abs/2502.11102 --out paper_source.json
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path


ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
ARXIV_ID_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf)/)?(?P<id>\d{4}\.\d{4,5})(?:v\d+)?", re.I)


@dataclass
class PaperSource:
    query: str
    title: str | None = None
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    published: str | None = None
    updated: str | None = None
    venue: str | None = None
    arxiv_id: str | None = None
    arxiv_abs_url: str | None = None
    pdf_url: str | None = None
    version_note: str | None = None
    source: str | None = None
    code_hints: list[str] = field(default_factory=list)
    project_hints: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def fetch_text(url: str, timeout: int = 30) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "PaperReading/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310 - user-requested metadata fetch
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def normalize_query(query: str) -> str:
    query = query.strip()
    match = ARXIV_ID_RE.search(query)
    if match:
        return match.group("id")
    return query


def arxiv_api_url(query: str, max_results: int) -> str:
    normalized = normalize_query(query)
    if ARXIV_ID_RE.fullmatch(normalized):
        params = {"id_list": normalized}
    else:
        params = {
            "search_query": f'ti:"{normalized}" OR all:"{normalized}"',
            "start": "0",
            "max_results": str(max_results),
            "sortBy": "lastUpdatedDate",
            "sortOrder": "descending",
        }
    return "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)


def text_of(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    return " ".join(html.unescape(element.text).split())


def links_from_text(text: str | None) -> tuple[list[str], list[str]]:
    if not text:
        return [], []
    urls = re.findall(r"https?://[^\s)>\]}]+", text)
    code = [url for url in urls if "github.com" in url.lower() or "gitlab.com" in url.lower()]
    project = [url for url in urls if url not in code]
    return sorted(set(code)), sorted(set(project))


def parse_arxiv_entry(entry: ET.Element, query: str) -> PaperSource:
    title = text_of(entry.find("atom:title", ARXIV_NS))
    abstract = text_of(entry.find("atom:summary", ARXIV_NS))
    authors = [
        text_of(author.find("atom:name", ARXIV_NS)) or ""
        for author in entry.findall("atom:author", ARXIV_NS)
    ]
    authors = [author for author in authors if author]
    published = text_of(entry.find("atom:published", ARXIV_NS))
    updated = text_of(entry.find("atom:updated", ARXIV_NS))

    arxiv_id = None
    abs_url = None
    pdf_url = None
    entry_id = text_of(entry.find("atom:id", ARXIV_NS))
    if entry_id:
        abs_url = entry_id
        match = ARXIV_ID_RE.search(entry_id)
        if match:
            arxiv_id = match.group("id")

    for link in entry.findall("atom:link", ARXIV_NS):
        if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
            pdf_url = link.attrib.get("href")
            break
    if not pdf_url and arxiv_id:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"

    code_hints, project_hints = links_from_text(abstract)
    return PaperSource(
        query=query,
        title=title,
        authors=authors,
        abstract=abstract,
        published=published,
        updated=updated,
        arxiv_id=arxiv_id,
        arxiv_abs_url=abs_url,
        pdf_url=pdf_url,
        version_note="arXiv API result sorted by lastUpdatedDate; compare with conference/OpenReview/project pages before final use.",
        source="arxiv",
        code_hints=code_hints,
        project_hints=project_hints,
    )


def resolve_arxiv(query: str, max_results: int) -> list[PaperSource]:
    payload = fetch_text(arxiv_api_url(query, max_results=max_results))
    root = ET.fromstring(payload)
    return [parse_arxiv_entry(entry, query) for entry in root.findall("atom:entry", ARXIV_NS)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Paper title, arXiv id, or arXiv URL")
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    result = {
        "query": args.query,
        "sources": [],
        "notes": [
            "Use this JSON as a first-pass metadata hint.",
            "Codex must still compare arXiv with conference/proceedings/OpenReview/project/author pages and document the version used.",
        ],
    }
    try:
        result["sources"] = [asdict(source) for source in resolve_arxiv(args.query, args.max_results)]
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 0 if result.get("sources") else 1


if __name__ == "__main__":
    raise SystemExit(main())
