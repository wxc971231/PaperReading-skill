#!/usr/bin/env python3
"""Detect and crop figure/table candidates from scholarly PDFs.

This script is a higher-level companion to crop_pdf_regions.py. It tries to
find visual regions automatically by combining:

- caption text blocks such as "Figure 2:" and "Table 1:";
- PDF vector drawing objects and embedded image blocks;
- PyMuPDF table detection when available;
- optional PDFFigures2 JSON metadata when supplied.

The final crop is rendered directly from the PDF page at high DPI. This keeps
vector figures and LaTeX tables sharper than cropping from rendered screenshots.

Example:
  python detect_pdf_visuals.py paper.pdf --out img/candidates --dpi 360

Optional PDFFigures2 metadata:
  python detect_pdf_visuals.py paper.pdf --out img/candidates \
    --pdffigures-json pdffigures.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    print("Missing dependency: PyMuPDF. Install with: pip install pymupdf", file=sys.stderr)
    raise SystemExit(2)


CAPTION_RE = re.compile(
    r"^\s*(figure|fig\.?|table|algorithm|alg\.?)\s*[\w.\-]+[:.]\s+",
    re.IGNORECASE,
)


@dataclass
class TextBlock:
    rect: "fitz.Rect"
    text: str


@dataclass
class Candidate:
    kind: str
    page: int
    rect: "fitz.Rect"
    caption: str = ""
    source: str = "auto"
    score: float = 0.0


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\u00ad", "").split())


def caption_kind(text: str) -> str | None:
    match = CAPTION_RE.match(text)
    if not match:
        return None
    word = match.group(1).lower()
    if word.startswith("fig"):
        return "figure"
    if word.startswith("tab"):
        return "table"
    if word.startswith("alg"):
        return "algorithm"
    return None


def rect_area(rect: "fitz.Rect") -> float:
    return max(0.0, rect.width) * max(0.0, rect.height)


def overlap_ratio(a: "fitz.Rect", b: "fitz.Rect") -> float:
    inter = a & b
    if inter.is_empty:
        return 0.0
    return rect_area(inter) / max(1.0, min(rect_area(a), rect_area(b)))


def h_overlap_ratio(a: "fitz.Rect", b: "fitz.Rect") -> float:
    left = max(a.x0, b.x0)
    right = min(a.x1, b.x1)
    return max(0.0, right - left) / max(1.0, min(a.width, b.width))


def union_rects(rects: Iterable["fitz.Rect"]) -> "fitz.Rect | None":
    iterator = iter(rects)
    try:
        result = fitz.Rect(next(iterator))
    except StopIteration:
        return None
    for rect in iterator:
        result |= rect
    return result


def inflate(rect: "fitz.Rect", amount: float, page_rect: "fitz.Rect") -> "fitz.Rect":
    inflated = fitz.Rect(rect.x0 - amount, rect.y0 - amount, rect.x1 + amount, rect.y1 + amount)
    return inflated & page_rect


def extract_text_blocks(page) -> list[TextBlock]:
    blocks: list[TextBlock] = []
    for block in page.get_text("blocks"):
        if len(block) < 5:
            continue
        text = normalize_text(str(block[4]))
        if text:
            blocks.append(TextBlock(fitz.Rect(block[:4]), text))
    return blocks


def drawing_rects(page, min_side: float = 1.0) -> list["fitz.Rect"]:
    rects: list[fitz.Rect] = []
    try:
        drawings = page.get_drawings()
    except Exception:  # noqa: BLE001
        return rects
    for item in drawings:
        rect = item.get("rect")
        if not rect:
            continue
        rect = fitz.Rect(rect)
        if rect.width >= min_side and rect.height >= min_side:
            rects.append(rect)
    return rects


def image_rects(page) -> list["fitz.Rect"]:
    rects: list[fitz.Rect] = []
    for block in page.get_text("dict").get("blocks", []):
        if block.get("type") == 1 and "bbox" in block:
            rects.append(fitz.Rect(block["bbox"]))
    return rects


def table_rects(page) -> list["fitz.Rect"]:
    rects: list[fitz.Rect] = []
    finder = getattr(page, "find_tables", None)
    if finder is None:
        return rects
    try:
        tables = finder()
    except Exception:  # noqa: BLE001
        return rects
    for table in getattr(tables, "tables", []):
        bbox = getattr(table, "bbox", None)
        if bbox:
            rects.append(fitz.Rect(bbox))
    return rects


def cluster_rects(rects: list["fitz.Rect"], page_rect: "fitz.Rect") -> list["fitz.Rect"]:
    useful = [
        rect & page_rect
        for rect in rects
        if rect_area(rect) >= 20 and rect.width >= 2 and rect.height >= 2
    ]
    clusters: list[fitz.Rect] = []
    x_gap = page_rect.width * 0.025
    y_gap = page_rect.height * 0.02

    for rect in useful:
        merged = False
        probe = fitz.Rect(rect.x0 - x_gap, rect.y0 - y_gap, rect.x1 + x_gap, rect.y1 + y_gap)
        for idx, existing in enumerate(clusters):
            if not (probe & existing).is_empty:
                clusters[idx] = existing | rect
                merged = True
                break
        if not merged:
            clusters.append(fitz.Rect(rect))

    changed = True
    while changed:
        changed = False
        output: list[fitz.Rect] = []
        for rect in clusters:
            probe = fitz.Rect(rect.x0 - x_gap, rect.y0 - y_gap, rect.x1 + x_gap, rect.y1 + y_gap)
            for idx, existing in enumerate(output):
                if not (probe & existing).is_empty:
                    output[idx] = existing | rect
                    changed = True
                    break
            else:
                output.append(rect)
        clusters = output

    min_area = rect_area(page_rect) * 0.0025
    return [rect for rect in clusters if rect_area(rect) >= min_area]


def include_text_inside(rect: "fitz.Rect", text_blocks: list[TextBlock], page_rect: "fitz.Rect") -> "fitz.Rect":
    expanded = fitz.Rect(rect)
    search = inflate(rect, 3, page_rect)
    for block in text_blocks:
        if overlap_ratio(search, block.rect) > 0.15 and not CAPTION_RE.match(block.text):
            expanded |= block.rect
    return expanded & page_rect


def choose_component_for_caption(
    caption: TextBlock,
    kind: str,
    components: list["fitz.Rect"],
    page_rect: "fitz.Rect",
) -> tuple["fitz.Rect | None", float]:
    best: tuple[fitz.Rect | None, float] = (None, -math.inf)
    for comp in components:
        horizontal = h_overlap_ratio(caption.rect, comp)
        if horizontal < 0.18:
            continue
        if comp.y1 <= caption.rect.y0:
            distance = caption.rect.y0 - comp.y1
            direction_bonus = 1.0 if kind in {"figure", "algorithm"} else 0.35
        elif comp.y0 >= caption.rect.y1:
            distance = comp.y0 - caption.rect.y1
            direction_bonus = 1.0 if kind in {"table", "algorithm"} else 0.45
        else:
            distance = 0
            direction_bonus = 0.5
        if distance > page_rect.height * 0.45:
            continue
        size_bonus = min(rect_area(comp) / max(1.0, rect_area(page_rect) * 0.10), 1.5)
        score = horizontal * 4.0 + direction_bonus * 2.0 + size_bonus - distance / page_rect.height
        if score > best[1]:
            best = (comp, score)
    return best


def fallback_region_from_caption(
    caption: TextBlock,
    kind: str,
    page_rect: "fitz.Rect",
    text_blocks: list[TextBlock],
) -> "fitz.Rect":
    margin_x = page_rect.width * 0.12
    if kind == "table":
        next_text = [
            b.rect.y0 for b in text_blocks
            if b.rect.y0 > caption.rect.y1 + 8 and b.rect.height > 8 and not CAPTION_RE.match(b.text)
        ]
        y1 = min(next_text) - 2 if next_text else min(page_rect.y1, caption.rect.y1 + page_rect.height * 0.24)
        return fitz.Rect(margin_x, caption.rect.y1 + 2, page_rect.width - margin_x, y1)
    previous_text = [
        b.rect.y1 for b in text_blocks
        if b.rect.y1 < caption.rect.y0 - 8 and b.rect.height > 8 and not CAPTION_RE.match(b.text)
    ]
    y0 = max(previous_text) + 2 if previous_text else max(page_rect.y0, caption.rect.y0 - page_rect.height * 0.24)
    return fitz.Rect(margin_x, y0, page_rect.width - margin_x, caption.rect.y0 - 2)


def looks_like_section_heading(text: str) -> bool:
    stripped = text.strip()
    if re.match(r"^\s*(\d+|[A-Z])(\.\d+)?\s+[A-Z][A-Za-z ]{2,80}$", stripped):
        return True
    # PDF extraction may split "5 Experiments" into separate nearby blocks.
    if re.match(r"^\d+(\.\d+)?$", stripped):
        return True
    common_titles = {
        "experiments",
        "conclusion",
        "references",
        "acknowledgments",
        "acknowledgements",
        "appendix",
        "limitations",
        "case analysis",
    }
    return stripped.lower() in common_titles


def table_region_from_caption(
    caption: TextBlock,
    components: list["fitz.Rect"],
    text_blocks: list[TextBlock],
    page_rect: "fitz.Rect",
) -> "fitz.Rect":
    """Build a table crop from caption down to the next logical boundary.

    LaTeX tables are often mostly text with only a few vector rules. A raw
    drawing bbox may only cover one horizontal rule or shaded band, so tables
    need a text-aware vertical span rather than a pure graphics component.
    """

    y0 = caption.rect.y1 + 2
    below_captions = [
        b.rect.y0
        for b in text_blocks
        if b.rect.y0 > y0 + 8 and CAPTION_RE.match(b.text)
    ]
    below_headings = [
        b.rect.y0
        for b in text_blocks
        if b.rect.y0 > y0 + 18 and looks_like_section_heading(b.text)
    ]
    related: list[fitz.Rect] = []
    for comp in components:
        if (
            comp.y1 >= y0
            and comp.y0 <= y0 + page_rect.height * 0.50
            and h_overlap_ratio(comp, fitz.Rect(page_rect.x0, y0, page_rect.x1, page_rect.y1)) > 0.12
        ):
            related.append(comp)

    boundary_options = below_captions + below_headings
    boundary_y = min(boundary_options) - 4 if boundary_options else None
    component_y = max((rect.y1 for rect in related), default=None)
    if component_y is not None:
        y1 = min(boundary_y, component_y + 8) if boundary_y is not None else component_y + 8
    else:
        y1 = boundary_y if boundary_y is not None else min(page_rect.y1, y0 + page_rect.height * 0.30)
    y1 = min(page_rect.y1, max(y0 + 10, y1))

    for block in text_blocks:
        if block.rect.y1 >= y0 and block.rect.y0 <= y1 and not CAPTION_RE.match(block.text):
            # Keep only central text/table material, not marginal page numbers.
            if block.rect.x1 > page_rect.width * 0.12 and block.rect.x0 < page_rect.width * 0.88:
                related.append(block.rect)

    if related:
        rect = union_rects(related)
        assert rect is not None
        return inflate(rect, 4, page_rect)
    return fitz.Rect(page_rect.width * 0.12, y0, page_rect.width * 0.88, y1)


def candidates_from_page(page, page_number: int) -> list[Candidate]:
    page_rect = page.rect
    text_blocks = extract_text_blocks(page)
    captions = [(block, caption_kind(block.text)) for block in text_blocks]
    captions = [(block, kind) for block, kind in captions if kind]

    visual_rects = drawing_rects(page) + image_rects(page) + table_rects(page)
    components = cluster_rects(visual_rects, page_rect)

    candidates: list[Candidate] = []
    for caption, kind in captions:
        if kind == "table":
            rect = table_region_from_caption(caption, components, text_blocks, page_rect)
            score = 5.0
            source = "caption+table-span"
        else:
            component, score = choose_component_for_caption(caption, kind, components, page_rect)
            source = "caption+graphics"
            if component is None:
                component = fallback_region_from_caption(caption, kind, page_rect, text_blocks)
                score = 0.1
                source = "caption+fallback"
            rect = include_text_inside(inflate(component, 4, page_rect), text_blocks, page_rect)
        # Keep the caption out of final crops; the Markdown article explains figures.
        if rect.intersects(caption.rect):
            if caption.rect.y0 >= rect.y0 + rect.height * 0.45:
                rect = fitz.Rect(rect.x0, rect.y0, rect.x1, max(rect.y0, caption.rect.y0 - 3))
            elif caption.rect.y1 <= rect.y0 + rect.height * 0.55:
                rect = fitz.Rect(rect.x0, min(rect.y1, caption.rect.y1 + 3), rect.x1, rect.y1)
        if rect.width > 20 and rect.height > 20:
            candidates.append(Candidate(kind or "visual", page_number, rect, caption.text, source, score))

    if not candidates:
        # Some pages have standalone graphics without recognizable captions.
        for comp in sorted(components, key=rect_area, reverse=True)[:3]:
            rect = include_text_inside(inflate(comp, 4, page_rect), text_blocks, page_rect)
            if rect_area(rect) >= rect_area(page_rect) * 0.025:
                candidates.append(Candidate("visual", page_number, rect, "", "graphics-only", 0.0))
    return candidates


def candidates_from_pdffigures_json(json_path: Path) -> list[Candidate]:
    raw = json_path.read_bytes()
    text = None
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("utf-8", errors="replace")
    data = json.loads(text)
    if isinstance(data, dict):
        items = data.get("figures") or data.get("items") or []
    else:
        items = data
    candidates: list[Candidate] = []
    for item in items:
        page = int(item.get("page", item.get("pageNumber", 0))) + 1
        region = item.get("regionBoundary") or item.get("renderDpiRegion") or item.get("figBoundary")
        if not region:
            continue
        x1 = float(region.get("x1", region.get("x", 0)))
        y1 = float(region.get("y1", region.get("y", 0)))
        x2 = float(region.get("x2", x1 + region.get("w", 0)))
        y2 = float(region.get("y2", y1 + region.get("h", 0)))
        caption = normalize_text(str(item.get("caption", "")))
        kind = str(item.get("figType", item.get("type", "visual"))).lower()
        candidates.append(Candidate(kind, page, fitz.Rect(x1, y1, x2, y2), caption, "pdffigures2", 10.0))
    return candidates


def dedupe_candidates(candidates: list[Candidate]) -> list[Candidate]:
    result: list[Candidate] = []
    for cand in sorted(candidates, key=lambda c: (c.page, -c.score, c.rect.y0)):
        duplicate = False
        for existing in result:
            if existing.page == cand.page and overlap_ratio(existing.rect, cand.rect) > 0.82:
                duplicate = True
                break
        if not duplicate:
            result.append(cand)
    return sorted(result, key=lambda c: (c.page, c.rect.y0, c.rect.x0))


def trim_png(path: Path, tolerance: int) -> None:
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return
    image = Image.open(path).convert("RGB")
    background = Image.new("RGB", image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background)
    if tolerance > 0:
        diff = diff.point(lambda value: 0 if value <= tolerance else 255)
    bbox = diff.getbbox()
    if bbox:
        image.crop(bbox).save(path)


def render_candidate(doc, cand: Candidate, output: Path, dpi: int, trim: bool) -> None:
    page = doc[cand.page - 1]
    clip = cand.rect & page.rect
    pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False)
    pix.save(output)
    if trim:
        trim_png(output, tolerance=8)


def write_manifest(path: Path, candidates: list[Candidate], doc) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "page", "kind", "source", "score", "x0", "y0", "x1", "y1", "caption"])
        for idx, cand in enumerate(candidates, start=1):
            page = doc[cand.page - 1]
            rect = page.rect
            writer.writerow([
                f"candidate_{idx:03d}.png",
                cand.page,
                cand.kind,
                cand.source,
                f"{cand.score:.3f}",
                f"{cand.rect.x0 / rect.width:.4f}",
                f"{cand.rect.y0 / rect.height:.4f}",
                f"{cand.rect.x1 / rect.width:.4f}",
                f"{cand.rect.y1 / rect.height:.4f}",
                cand.caption,
            ])


def make_contact_sheet(out_dir: Path, count: int, columns: int = 3) -> None:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    images: list[tuple[str, Image.Image]] = []
    for path in sorted(out_dir.glob("candidate_*.png")):
        image = Image.open(path).convert("RGB")
        image.thumbnail((360, 260))
        images.append((path.name, image.copy()))
    if not images:
        return
    rows = math.ceil(len(images) / columns)
    cell_w, cell_h = 390, 310
    sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (name, image) in enumerate(images):
        x = (idx % columns) * cell_w
        y = (idx // columns) * cell_h
        draw.text((x + 10, y + 8), name, fill="black")
        sheet.paste(image, (x + 10, y + 34))
        draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), outline="#cccccc")
    sheet.save(out_dir / "contact_sheet.png")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dpi", type=int, default=360)
    parser.add_argument("--trim", action="store_true", default=True)
    parser.add_argument("--no-trim", dest="trim", action="store_false")
    parser.add_argument("--max-candidates", type=int, default=40)
    parser.add_argument("--pdffigures-json", type=Path)
    parser.add_argument("--contact-sheet", action="store_true", default=True)
    args = parser.parse_args()

    if not args.pdf.exists():
        parser.error(f"PDF not found: {args.pdf}")
    args.out.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(args.pdf)
    candidates: list[Candidate] = []
    if args.pdffigures_json and args.pdffigures_json.exists():
        candidates.extend(candidates_from_pdffigures_json(args.pdffigures_json))
    for page_number in range(1, len(doc) + 1):
        candidates.extend(candidates_from_page(doc[page_number - 1], page_number))
    candidates = dedupe_candidates(candidates)[: args.max_candidates]

    for idx, cand in enumerate(candidates, start=1):
        target = args.out / f"candidate_{idx:03d}.png"
        render_candidate(doc, cand, target, args.dpi, args.trim)
        print(f"candidate_{idx:03d}.png page={cand.page} kind={cand.kind} source={cand.source}")
    write_manifest(args.out / "manifest.csv", candidates, doc)
    if args.contact_sheet:
        make_contact_sheet(args.out, len(candidates))
    print(f"done: wrote {len(candidates)} candidate(s) to {args.out}")
    doc.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
