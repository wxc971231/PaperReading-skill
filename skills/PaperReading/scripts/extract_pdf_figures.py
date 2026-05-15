#!/usr/bin/env python3
"""Extract embedded PDF images and/or render PDF pages for paper-note figures.

Requires PyMuPDF:
    pip install pymupdf
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def parse_pages(spec: str | None, page_count: int) -> set[int] | None:
    if not spec:
        return None
    selected: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = int(start_s)
            end = int(end_s)
            if start > end:
                start, end = end, start
            selected.update(range(start, end + 1))
        else:
            selected.add(int(part))
    return {p - 1 for p in selected if 1 <= p <= page_count}


def safe_ext(ext: str) -> str:
    ext = (ext or "png").lower().lstrip(".")
    if ext in {"jpeg", "jpe"}:
        return "jpg"
    if ext not in {"png", "jpg", "webp", "jp2", "bmp"}:
        return "png"
    return ext


def extract_images(doc, out_dir: Path, prefix: str, min_width: int, min_height: int) -> int:
    seen: set[str] = set()
    count = 0

    for page_index in range(len(doc)):
        page = doc[page_index]
        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = image_info[0]
            try:
                base = doc.extract_image(xref)
            except Exception as exc:  # pragma: no cover - depends on source PDF
                print(f"skip page {page_index + 1} image {image_index}: {exc}", file=sys.stderr)
                continue

            width = int(base.get("width", 0))
            height = int(base.get("height", 0))
            if width < min_width or height < min_height:
                continue

            image_bytes = base["image"]
            digest = hashlib.sha1(image_bytes).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)

            count += 1
            ext = safe_ext(base.get("ext", "png"))
            target = out_dir / f"{prefix}_{count:03d}.{ext}"
            target.write_bytes(image_bytes)
            print(f"image {count:03d}: page={page_index + 1} size={width}x{height} -> {target}")

    return count


def render_pages(doc, out_dir: Path, prefix: str, dpi: int, pages: set[int] | None) -> int:
    zoom = dpi / 72.0
    matrix = None
    try:
        import fitz

        matrix = fitz.Matrix(zoom, zoom)
    except Exception:
        matrix = None

    count = 0
    for page_index in range(len(doc)):
        if pages is not None and page_index not in pages:
            continue
        page = doc[page_index]
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        count += 1
        target = out_dir / f"{prefix}_{page_index + 1:03d}.png"
        pix.save(target)
        print(f"page {page_index + 1}: dpi={dpi} -> {target}")
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Input PDF path")
    parser.add_argument("--out", type=Path, default=Path("img/raw"), help="Output directory")
    parser.add_argument("--mode", choices=["images", "pages", "both"], default="images")
    parser.add_argument("--pages", help="1-based page list, e.g. 1,3,7-9. Only used for page rendering.")
    parser.add_argument("--dpi", type=int, default=180, help="DPI for rendered pages")
    parser.add_argument("--min-width", type=int, default=180, help="Minimum embedded image width")
    parser.add_argument("--min-height", type=int, default=120, help="Minimum embedded image height")
    parser.add_argument("--image-prefix", default="extracted", help="Prefix for embedded images")
    parser.add_argument("--page-prefix", default="page", help="Prefix for rendered pages")
    args = parser.parse_args()

    if not args.pdf.exists():
        print(f"PDF not found: {args.pdf}", file=sys.stderr)
        return 2

    try:
        import fitz
    except ImportError:
        print("Missing dependency: PyMuPDF. Install with: pip install pymupdf", file=sys.stderr)
        return 3

    args.out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(args.pdf)
    try:
        total = 0
        if args.mode in {"images", "both"}:
            total += extract_images(doc, args.out, args.image_prefix, args.min_width, args.min_height)
        if args.mode in {"pages", "both"}:
            selected = parse_pages(args.pages, len(doc))
            total += render_pages(doc, args.out, args.page_prefix, args.dpi, selected)
        print(f"done: wrote {total} file(s) to {args.out}")
    finally:
        doc.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
