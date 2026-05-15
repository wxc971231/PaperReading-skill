#!/usr/bin/env python3
"""Crop regions from PDF pages into standalone article figures.

Coordinates are normalized page fractions: x0,y0,x1,y1 in [0, 1].
This is intended for vector PDF figures/tables that cannot be extracted as
embedded bitmap images. Rendering a tight PDF clip at high DPI preserves LaTeX
text and vector lines much better than cropping from a low-resolution screenshot.

Example:
  python crop_pdf_regions.py paper.pdf --out img \
    --crop img_001.png:2:0.16,0.10,0.86,0.48 \
    --crop img_002.png:4:0.15,0.13,0.86,0.42

Drop captions and trim whitespace:
  python crop_pdf_regions.py paper.pdf --out img --dpi 360 --trim \
    --caption auto \
    --crop img_001.png:2:0.16,0.10,0.86,0.48

Export a vector SVG region when the downstream renderer supports SVG:
  python crop_pdf_regions.py paper.pdf --out img --format svg \
    --caption auto \
    --crop img_001.svg:2:0.16,0.10,0.86,0.48
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    print("Missing dependency: PyMuPDF. Install with: pip install pymupdf", file=sys.stderr)
    raise SystemExit(2)


def parse_crop(value: str) -> tuple[str, int, tuple[float, float, float, float]]:
    try:
        name, page_text, coords_text = value.split(":", 2)
        page = int(page_text)
        coords = tuple(float(part) for part in coords_text.split(","))
    except Exception as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError(
            "crop must be output.png:page:x0,y0,x1,y1"
        ) from exc

    if page < 1:
        raise argparse.ArgumentTypeError("page numbers are 1-based")
    if len(coords) != 4:
        raise argparse.ArgumentTypeError("crop must contain four coordinates")
    x0, y0, x1, y1 = coords
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise argparse.ArgumentTypeError("coordinates must satisfy 0 <= x0 < x1 <= 1")
    return name, page, coords


def find_caption_bounds(page, clip: "fitz.Rect") -> list["fitz.Rect"]:
    captions: list[fitz.Rect] = []
    for block in page.get_text("blocks", clip=clip):
        text = " ".join(str(block[4]).split())
        if text.startswith(("Figure ", "Fig. ", "Table ")):
            captions.append(fitz.Rect(block[:4]))
    return captions


def without_caption(
    page,
    clip: "fitz.Rect",
    mode: str,
    padding_points: float,
) -> "fitz.Rect":
    if mode == "keep":
        return clip

    captions = find_caption_bounds(page, clip)
    if not captions:
        return clip

    height = clip.height
    top_band = clip.y0 + height * 0.45
    bottom_band = clip.y0 + height * 0.55

    def drop_bottom() -> fitz.Rect:
        lower = [cap for cap in captions if cap.y0 >= bottom_band]
        if not lower:
            return clip
        first = min(lower, key=lambda cap: cap.y0)
        return fitz.Rect(clip.x0, clip.y0, clip.x1, max(clip.y0, first.y0 - padding_points))

    def drop_top() -> fitz.Rect:
        upper = [cap for cap in captions if cap.y1 <= top_band]
        if not upper:
            return clip
        last = max(upper, key=lambda cap: cap.y1)
        return fitz.Rect(clip.x0, min(clip.y1, last.y1 + padding_points), clip.x1, clip.y1)

    if mode == "drop-bottom":
        return drop_bottom()
    if mode == "drop-top":
        return drop_top()

    bottom_clip = drop_bottom()
    top_clip = drop_top()
    if bottom_clip != clip:
        return bottom_clip
    if top_clip != clip:
        return top_clip
    return clip


def trim_png(path: Path, tolerance: int) -> bool:
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("skip --trim: Pillow is not installed", file=sys.stderr)
        return False

    image = Image.open(path).convert("RGB")
    background = Image.new("RGB", image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background)
    if tolerance > 0:
        diff = diff.point(lambda value: 0 if value <= tolerance else 255)
    bbox = diff.getbbox()
    if not bbox:
        return False
    image.crop(bbox).save(path)
    return True


def render_png(page, clip: "fitz.Rect", output: Path, dpi: int) -> None:
    pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False)
    pix.save(output)


def render_svg(doc, page_number: int, clip: "fitz.Rect", output: Path) -> None:
    page_doc = fitz.open()
    try:
        target_page = page_doc.new_page(width=clip.width, height=clip.height)
        target_page.show_pdf_page(target_page.rect, doc, page_number - 1, clip=clip)
        svg = target_page.get_svg_image(text_as_path=1)
        output.write_text(svg, encoding="utf-8")
    finally:
        page_doc.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--format", choices=["png", "svg"], default="png")
    parser.add_argument("--dpi", type=int, default=360)
    parser.add_argument(
        "--caption",
        choices=["keep", "drop-bottom", "drop-top", "auto"],
        default="keep",
        help="Remove captions inside the selected clip before rendering.",
    )
    parser.add_argument(
        "--caption-padding",
        type=float,
        default=4.0,
        help="Padding in PDF points between visual content and removed caption.",
    )
    parser.add_argument("--trim", action="store_true", help="Trim white margins after rendering.")
    parser.add_argument("--trim-tolerance", type=int, default=8)
    parser.add_argument("--crop", action="append", type=parse_crop, required=True)
    args = parser.parse_args()

    if not args.pdf.exists():
        parser.error(f"PDF not found: {args.pdf}")
    args.out.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(args.pdf)
    for output_name, page_number, coords in args.crop:
        if page_number > len(doc):
            parser.error(f"page {page_number} exceeds PDF length {len(doc)}")
        page = doc[page_number - 1]
        rect = page.rect
        x0, y0, x1, y1 = coords
        clip = fitz.Rect(
            rect.x0 + rect.width * x0,
            rect.y0 + rect.height * y0,
            rect.x0 + rect.width * x1,
            rect.y0 + rect.height * y1,
        )
        clip = without_caption(page, clip, args.caption, args.caption_padding)
        output = args.out / output_name
        if args.format == "svg":
            if output.suffix.lower() != ".svg":
                output = output.with_suffix(".svg")
            render_svg(doc, page_number, clip, output)
        else:
            if output.suffix.lower() != ".png":
                output = output.with_suffix(".png")
            render_png(page, clip, output, args.dpi)
        if args.trim and output.suffix.lower() == ".png":
            trim_png(output, args.trim_tolerance)
        print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
