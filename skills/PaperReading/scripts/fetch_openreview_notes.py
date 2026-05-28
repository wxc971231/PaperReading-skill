#!/usr/bin/env python3
"""Fetch public OpenReview notes for a paper forum.

OpenReview forum pages are rendered by a client-side app, so plain HTML/text
fetches often show the submission metadata but not reviews or rebuttals. This
helper queries the public notes API directly and classifies the returned notes.

Examples:
  python fetch_openreview_notes.py https://openreview.net/forum?id=9P5e6iE4WK --out openreview_notes.json
  python fetch_openreview_notes.py 9P5e6iE4WK --markdown --out openreview_notes.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API_BASES = (
    "https://api2.openreview.net/notes",
    "https://api.openreview.net/notes",
)


def forum_id_from(value: str) -> str:
    """Extract an OpenReview forum id from a URL or raw id."""
    value = value.strip()
    parsed = urllib.parse.urlparse(value)
    if parsed.netloc and "openreview.net" in parsed.netloc:
        query = urllib.parse.parse_qs(parsed.query)
        if query.get("id"):
            return query["id"][0]
    match = re.search(r"(?:id=)?([A-Za-z0-9_-]{6,})", value)
    if match:
        return match.group(1)
    raise ValueError(f"Could not parse OpenReview forum id from: {value}")


def fetch_notes(forum_id: str, timeout: float = 30.0) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for base in API_BASES:
        url = f"{base}?{urllib.parse.urlencode({'forum': forum_id})}"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload.get("notes", [])
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
    raise RuntimeError(f"Failed to fetch OpenReview notes for {forum_id}: {last_error}")


def content_value(content: dict[str, Any], key: str) -> Any:
    raw = content.get(key)
    if isinstance(raw, dict) and "value" in raw:
        return raw["value"]
    return raw


def flatten_content(content: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for key in sorted(content):
        value = content_value(content, key)
        flattened[key] = value
    return flattened


def note_kind(note: dict[str, Any], forum_id: str) -> str:
    invitations = " ".join(note.get("invitations") or [])
    content = flatten_content(note.get("content") or {})
    title = str(content.get("title") or "")
    replyto = note.get("replyto")

    if note.get("id") == forum_id or not replyto:
        return "submission"
    if "Decision" in invitations or title.lower() == "paper decision":
        return "decision"
    if "Official_Review" in invitations and "Rebuttal" not in invitations:
        return "official_review"
    if "Rebuttal" in invitations and "Comment" not in invitations:
        return "author_rebuttal"
    if "Rebuttal_Comment" in invitations:
        return "rebuttal_comment"
    if "Comment" in invitations:
        return "comment"
    return "other"


def normalize_note(note: dict[str, Any], forum_id: str) -> dict[str, Any]:
    content = flatten_content(note.get("content") or {})
    return {
        "id": note.get("id"),
        "forum": note.get("forum"),
        "replyto": note.get("replyto"),
        "number": note.get("number"),
        "kind": note_kind(note, forum_id),
        "signatures": note.get("signatures") or [],
        "readers": note.get("readers") or [],
        "invitations": note.get("invitations") or [],
        "tcdate": note.get("tcdate"),
        "cdate": note.get("cdate"),
        "mdate": note.get("mdate"),
        "content": content,
    }


def classify(notes: list[dict[str, Any]], forum_id: str) -> dict[str, Any]:
    normalized = [normalize_note(note, forum_id) for note in notes]
    order = {
        "submission": 0,
        "decision": 1,
        "official_review": 2,
        "author_rebuttal": 3,
        "rebuttal_comment": 4,
        "comment": 5,
        "other": 6,
    }
    normalized.sort(key=lambda item: (order.get(item["kind"], 99), item.get("number") or 0, item.get("tcdate") or 0))
    counts: dict[str, int] = {}
    for item in normalized:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    return {
        "forum_id": forum_id,
        "source": f"https://openreview.net/forum?id={forum_id}",
        "counts": counts,
        "has_public_reviews": counts.get("official_review", 0) > 0,
        "has_public_rebuttals": counts.get("author_rebuttal", 0) > 0,
        "notes": normalized,
    }


def text_excerpt(value: Any, limit: int = 1200) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def primary_text(content: dict[str, Any], keys: tuple[str, ...]) -> str:
    parts: list[str] = []
    for key in keys:
        if key in content and content[key] not in (None, "", []):
            parts.append(f"**{key}**: {text_excerpt(content[key])}")
    return "\n\n".join(parts)


def to_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# OpenReview Notes",
        "",
        f"- Forum: https://openreview.net/forum?id={payload['forum_id']}",
        f"- Counts: {json.dumps(payload['counts'], ensure_ascii=False, sort_keys=True)}",
        f"- Public reviews: {'yes' if payload['has_public_reviews'] else 'no'}",
        f"- Public rebuttals: {'yes' if payload['has_public_rebuttals'] else 'no'}",
        "",
    ]
    wanted_keys = {
        "decision": ("decision", "comment"),
        "official_review": (
            "summary",
            "claims_and_evidence",
            "methods_and_evaluation_criteria",
            "experimental_designs_or_analyses",
            "other_strengths_and_weaknesses",
            "questions_for_authors",
            "overall_recommendation",
        ),
        "author_rebuttal": ("rebuttal",),
        "rebuttal_comment": ("comment",),
        "comment": ("comment",),
    }
    for note in payload["notes"]:
        kind = note["kind"]
        if kind == "submission":
            continue
        lines.append(f"## {kind}: {note.get('id')}")
        if note.get("signatures"):
            lines.append(f"- Signatures: {', '.join(note['signatures'])}")
        if note.get("number") is not None:
            lines.append(f"- Number: {note['number']}")
        body = primary_text(note["content"], wanted_keys.get(kind, tuple(note["content"].keys())))
        if body:
            lines.extend(["", body])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("forum", help="OpenReview forum URL or id")
    parser.add_argument("--out", type=Path, help="Output path. Defaults to stdout.")
    parser.add_argument("--markdown", action="store_true", help="Write a Markdown extraction instead of JSON.")
    args = parser.parse_args()

    try:
        forum_id = forum_id_from(args.forum)
        payload = classify(fetch_notes(forum_id), forum_id)
        text = to_markdown(payload) if args.markdown else json.dumps(payload, ensure_ascii=False, indent=2)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
