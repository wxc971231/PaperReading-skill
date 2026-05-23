#!/usr/bin/env python3
"""Render a PaperReading Markdown article to a self-contained PDF.

The preferred renderer is Pandoc + Typst, followed by Pandoc + XeLaTeX.
Those engines handle Markdown structure, figures, and LaTeX math much better
than PyMuPDF's lightweight HTML renderer. The PyMuPDF renderer remains as a
last-resort fallback for environments without Pandoc.

- Preferred: ``pandoc --pdf-engine=typst``.
- Fallback: ``pandoc --pdf-engine=xelatex``.
- Last resort: ``markdown_it`` + PyMuPDF's HTML Story renderer.
- Local tools are discovered from ``.tools/md-pdf/bin`` and local fonts from
  ``.tools/md-pdf/fonts``.
- Relative image paths such as ``img/img_001.png`` are resolved from the
  Markdown file's parent directory.

Example:
  python render_markdown_pdf.py output/"Paper Title"/"Paper Title.md"
  python render_markdown_pdf.py output/"Paper Title"/"Paper Title.md" --out article.pdf
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import fitz
except ImportError:  # pragma: no cover
    print("Missing dependency: PyMuPDF. Install with: pip install pymupdf", file=sys.stderr)
    raise SystemExit(2)

try:
    from markdown_it import MarkdownIt
except ImportError:  # pragma: no cover
    print("Missing dependency: markdown-it-py. Install with: pip install markdown-it-py", file=sys.stderr)
    raise SystemExit(2)


DISPLAY_MATH_RE = re.compile(r"(?<!\\)\$\$(.*?)(?<!\\)\$\$", re.S)
INLINE_MATH_RE = re.compile(r"(?<!\\)\\\((.*?)(?<!\\)\\\)", re.S)
DISPLAY_MATH_FENCE_RE = re.compile(r"^([ \t]*)\$\$\s*$")


DEFAULT_CSS = """
body {
  font-family: "Noto Sans CJK SC", "Source Han Sans SC", "Microsoft YaHei",
    "PingFang SC", "WenQuanYi Micro Hei", sans-serif;
  font-size: 11pt;
  line-height: 1.55;
  color: #222;
}
h1 {
  font-size: 22pt;
  margin: 22pt 0 10pt;
  padding-bottom: 4pt;
  border-bottom: 1px solid #cccccc;
}
h2 {
  font-size: 16pt;
  margin: 16pt 0 8pt;
}
h3 {
  font-size: 13pt;
  margin: 12pt 0 6pt;
}
p, ul, ol, blockquote, pre, table {
  margin-top: 0;
  margin-bottom: 8pt;
}
li {
  margin-bottom: 4pt;
}
img {
  max-width: 100%;
  height: auto;
  margin: 6pt 0 8pt;
}
blockquote {
  border-left: 3pt solid #d0d7de;
  color: #4b5563;
  padding: 4pt 8pt;
  background: #f7f7f7;
}
code {
  font-family: "Noto Sans Mono CJK SC", "Source Code Pro", "Consolas", monospace;
  font-size: 9.5pt;
  background: #f3f4f6;
}
pre {
  font-family: "Noto Sans Mono CJK SC", "Source Code Pro", "Consolas", monospace;
  font-size: 8.5pt;
  white-space: pre-wrap;
  background: #f6f8fa;
  border: 1px solid #e5e7eb;
  padding: 7pt;
}
table {
  border-collapse: collapse;
  width: 100%;
  font-size: 9pt;
}
th, td {
  border: 1px solid #d0d7de;
  padding: 4pt 5pt;
  vertical-align: top;
}
th {
  background: #f3f4f6;
}
.math-block {
  font-family: "Noto Sans Mono CJK SC", "Source Code Pro", "Consolas", monospace;
  font-size: 10pt;
  white-space: pre-wrap;
  text-align: center;
  background: #fafafa;
  border: 1px solid #eeeeee;
  padding: 7pt;
  margin: 8pt 0;
}
.math-inline {
  font-family: "Noto Sans Mono CJK SC", "Source Code Pro", "Consolas", monospace;
  background: #f7f7f7;
}
hr {
  border: 0;
  border-top: 1px solid #cccccc;
  margin: 12pt 0;
}
"""


PAGE_SIZES = {
    "a4": fitz.paper_rect("a4"),
    "letter": fitz.paper_rect("letter"),
}

PANDOC_INPUT_FORMAT = "markdown-implicit_figures+tex_math_dollars+tex_math_single_backslash+pipe_tables+task_lists"
TYPST_STYLE_HEADER = r"""
#let paperreading-main-fonts = (
  "Times New Roman",
  "Microsoft YaHei",
  "Noto Sans CJK SC",
  "New Computer Modern",
)

#show text: set text(font: paperreading-main-fonts)

#show quote.where(block: true): it => block(
  fill: rgb("#f7f8fa"),
  stroke: (left: 3pt + rgb("#d0d7de")),
  inset: (left: 10pt, right: 10pt, top: 7pt, bottom: 7pt),
  radius: 2pt,
  breakable: true,
)[
  #set text(size: 9.6pt, fill: rgb("#374151"))
  #it.body
]

#show raw.where(block: true): it => block(
  inset: (left: 1.45em),
  breakable: true,
)[
  #block(
    width: 100%,
    fill: rgb("#f6f8fa"),
    stroke: 0.6pt + rgb("#d0d7de"),
    inset: (left: 10pt, right: 8pt, top: 8pt, bottom: 8pt),
    radius: 3pt,
    breakable: true,
  )[
    #set text(font: ("Noto Sans Mono CJK SC", "New Computer Modern"), size: 7.8pt)
    #it
  ]
]

#show raw.where(block: false): it => box(
  fill: rgb("#f3f4f6"),
  inset: (left: 2pt, right: 2pt, top: 1pt, bottom: 1pt),
  radius: 1pt,
)[
  #set text(font: ("Noto Sans Mono CJK SC", "New Computer Modern"), size: 0.94em)
  #it
]
"""


def default_output_path(markdown_path: Path) -> Path:
    return markdown_path.with_suffix(".pdf")


def optimize_pdf(output_path: Path) -> None:
    temp_path = output_path.with_name(f"{output_path.stem}.optimized{output_path.suffix}")
    doc = fitz.open(output_path)
    try:
        doc.save(temp_path, garbage=4, deflate=True, clean=True)
    finally:
        doc.close()
    temp_path.replace(output_path)


def resource_path(markdown_path: Path) -> str:
    parent = markdown_path.parent.resolve()
    return f"{parent}:{parent / 'img'}:."


def align_multiline_math(math_body: str) -> str:
    lines = [line.strip() for line in math_body.strip().splitlines() if line.strip()]
    if len(lines) < 2 or r"\begin" in math_body or r"\\" in math_body:
        return math_body.strip()

    aligned_lines: list[str] = []
    for index, line in enumerate(lines):
        if index == 0 and "=" in line:
            left, right = line.split("=", 1)
            aligned_lines.append(f"{left}&={right}")
        elif line[:1] in {"+", "-", "="}:
            aligned_lines.append(f"&{line}")
        else:
            aligned_lines.append(line)
    return "\\begin{aligned}\n" + (r" \\" + "\n").join(aligned_lines) + "\n\\end{aligned}"


def preprocess_pandoc_markdown(markdown: str) -> str:
    """Keep source content intact while making long display equations printable."""

    lines = markdown.splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        opener = DISPLAY_MATH_FENCE_RE.match(lines[index])
        if not opener:
            if re.fullmatch(r"-{3,}", lines[index].strip()) and output and output[-1].strip():
                output.append("")
            output.append(lines[index])
            index += 1
            continue

        indent = opener.group(1)
        body_lines: list[str] = []
        closer_index = index + 1
        while closer_index < len(lines):
            closer = DISPLAY_MATH_FENCE_RE.match(lines[closer_index])
            if closer and closer.group(1) == indent:
                break
            line = lines[closer_index]
            body_lines.append(line[len(indent) :] if line.startswith(indent) else line)
            closer_index += 1

        if closer_index >= len(lines):
            output.append(lines[index])
            index += 1
            continue

        body = "\n".join(body_lines).strip()
        processed = align_multiline_math(body) if "\n" in body else body
        output.append(lines[index])
        output.extend(f"{indent}{line}" if line else line for line in processed.splitlines())
        output.append(lines[closer_index])
        index = closer_index + 1

    rendered = "\n".join(output)
    return rendered + ("\n" if markdown.endswith("\n") else "")


def prepare_pandoc_input(markdown_path: Path, temp_dir: Path) -> Path:
    markdown = markdown_path.read_text(encoding="utf-8")
    prepared_path = temp_dir / markdown_path.name
    prepared_path.write_text(preprocess_pandoc_markdown(markdown), encoding="utf-8")
    return prepared_path


def prepare_typst_header(temp_dir: Path) -> Path:
    header_path = temp_dir / "paperreading-style.typ"
    header_path.write_text(TYPST_STYLE_HEADER, encoding="utf-8")
    return header_path


def find_tool(name: str, markdown_path: Path) -> str | None:
    path_tool = shutil.which(name)
    if path_tool:
        return path_tool

    search_roots = [markdown_path.resolve().parent, Path(__file__).resolve().parent]
    for root in list(search_roots):
        search_roots.extend(root.parents)

    seen: set[Path] = set()
    for root in search_roots:
        if root in seen:
            continue
        seen.add(root)
        candidate = root / ".tools" / "md-pdf" / "bin" / name
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return None


def find_local_font_dirs(markdown_path: Path) -> list[Path]:
    search_roots = [markdown_path.resolve().parent, Path(__file__).resolve().parent]
    for root in list(search_roots):
        search_roots.extend(root.parents)

    font_dirs: list[Path] = []
    seen: set[Path] = set()
    for root in search_roots:
        if root in seen:
            continue
        seen.add(root)
        candidate = root / ".tools" / "md-pdf" / "fonts"
        if candidate.exists() and candidate.is_dir():
            font_dirs.append(candidate.resolve())
    return font_dirs


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def render_with_pandoc_typst(
    markdown_path: Path,
    output_path: Path,
    *,
    page_size: str,
    margin: float,
) -> None:
    pandoc = find_tool("pandoc", markdown_path)
    typst = find_tool("typst", markdown_path)
    if not pandoc:
        raise RuntimeError("pandoc is not installed")
    if not typst:
        raise RuntimeError("typst is not installed")

    engine_opts = ["--pdf-engine-opt=--root=/"]
    for font_dir in find_local_font_dirs(markdown_path):
        engine_opts.append(f"--pdf-engine-opt=--font-path={font_dir}")
    margin_cm = max(margin / 28.3465, 0.5)
    typst_margin = f"{margin_cm:.2f}cm"

    with tempfile.TemporaryDirectory(prefix="paperreading-pandoc-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        prepared_path = prepare_pandoc_input(markdown_path, temp_dir)
        header_path = prepare_typst_header(temp_dir)
        command = [
            pandoc,
            str(prepared_path.resolve()),
            "-f",
            PANDOC_INPUT_FORMAT,
            "--resource-path",
            resource_path(markdown_path),
            "--include-before-body",
            str(header_path),
            f"--pdf-engine={typst}",
            *engine_opts,
            "-V",
            f"papersize={page_size}",
            "-V",
            f"margin.top={typst_margin}",
            "-V",
            f"margin.right={typst_margin}",
            "-V",
            f"margin.bottom={typst_margin}",
            "-V",
            f"margin.left={typst_margin}",
            "-V",
            "codefont=Noto Sans Mono CJK SC",
            "-V",
            "fontsize=10.2pt",
            "-V",
            "linestretch=1.28",
            "-o",
            str(output_path.resolve()),
        ]
        result = run_command(command, markdown_path.parent)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pandoc+typst failed")


def render_with_pandoc_xelatex(
    markdown_path: Path,
    output_path: Path,
    *,
    page_size: str,
    margin: float,
) -> None:
    pandoc = find_tool("pandoc", markdown_path)
    xelatex = find_tool("xelatex", markdown_path)
    if not pandoc:
        raise RuntimeError("pandoc is not installed")
    if not xelatex:
        raise RuntimeError("xelatex is not installed")

    margin_cm = max(margin / 28.3465, 0.5)
    with tempfile.TemporaryDirectory(prefix="paperreading-pandoc-") as temp_dir_name:
        prepared_path = prepare_pandoc_input(markdown_path, Path(temp_dir_name))
        command = [
            pandoc,
            str(prepared_path.resolve()),
            "-f",
            PANDOC_INPUT_FORMAT,
            "--resource-path",
            resource_path(markdown_path),
            f"--pdf-engine={xelatex}",
            "-V",
            f"geometry:margin={margin_cm:.2f}cm",
            "-V",
            f"papersize={page_size}",
            "-V",
            "CJKmainfont=Noto Sans CJK SC",
            "-V",
            "mainfont=Noto Serif",
            "-V",
            "monofont=Noto Sans Mono",
            "-o",
            str(output_path.resolve()),
        ]
        result = run_command(command, markdown_path.parent)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pandoc+xelatex failed")


def preprocess_math(markdown: str) -> str:
    """Preserve LaTeX formulas as styled text blocks/spans in the rendered PDF.

    PyMuPDF's HTML renderer does not evaluate TeX. Keeping formulas as escaped
    text is preferable to dropping them or relying on a machine-specific LaTeX
    installation.
    """

    def display(match: re.Match[str]) -> str:
        body = html.escape(match.group(1).strip())
        return f'\n<div class="math-block">{body}</div>\n'

    def inline(match: re.Match[str]) -> str:
        body = html.escape(" ".join(match.group(1).split()))
        return f'<span class="math-inline">{body}</span>'

    markdown = DISPLAY_MATH_RE.sub(display, markdown)
    markdown = INLINE_MATH_RE.sub(inline, markdown)
    return markdown


def markdown_to_html(markdown: str, title: str) -> str:
    parser = MarkdownIt("commonmark", {"html": True}).enable("table")
    body = parser.render(preprocess_math(markdown))
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{safe_title}</title>
</head>
<body>
{body}
</body>
</html>
"""


def render_with_pymupdf(
    markdown_path: Path,
    output_path: Path,
    *,
    page_size: str,
    margin: float,
    css: str,
) -> None:
    markdown = markdown_path.read_text(encoding="utf-8")
    html_text = markdown_to_html(markdown, markdown_path.stem)

    paper = PAGE_SIZES[page_size.lower()]
    content_rect = fitz.Rect(
        paper.x0 + margin,
        paper.y0 + margin,
        paper.x1 - margin,
        paper.y1 - margin,
    )

    archive = fitz.Archive(str(markdown_path.parent))
    story = fitz.Story(html_text, user_css=css, archive=archive)
    writer = fitz.DocumentWriter(str(output_path))

    def rectfn(rect_num, filled):
        # Every call starts a new page with the same content rectangle.
        return paper, content_rect, fitz.Identity

    story.write(writer, rectfn)
    writer.close()


def render_pdf(
    markdown_path: Path,
    output_path: Path,
    *,
    page_size: str,
    margin: float,
    css: str,
    engine: str,
    optimize: bool,
) -> str:
    attempts: list[tuple[str, callable]] = []
    if engine == "auto":
        attempts = [
            ("pandoc-typst", lambda: render_with_pandoc_typst(markdown_path, output_path, page_size=page_size, margin=margin)),
            ("pandoc-xelatex", lambda: render_with_pandoc_xelatex(markdown_path, output_path, page_size=page_size, margin=margin)),
            ("pymupdf", lambda: render_with_pymupdf(markdown_path, output_path, page_size=page_size, margin=margin, css=css)),
        ]
    elif engine == "pandoc-typst":
        attempts = [("pandoc-typst", lambda: render_with_pandoc_typst(markdown_path, output_path, page_size=page_size, margin=margin))]
    elif engine == "pandoc-xelatex":
        attempts = [("pandoc-xelatex", lambda: render_with_pandoc_xelatex(markdown_path, output_path, page_size=page_size, margin=margin))]
    elif engine == "pymupdf":
        attempts = [("pymupdf", lambda: render_with_pymupdf(markdown_path, output_path, page_size=page_size, margin=margin, css=css))]
    else:  # pragma: no cover
        raise ValueError(f"unknown engine: {engine}")

    failures: list[str] = []
    for name, attempt in attempts:
        try:
            attempt()
            if optimize:
                optimize_pdf(output_path)
            return name
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name}: {exc}")
            if engine != "auto":
                break

    raise RuntimeError("PDF rendering failed:\n" + "\n".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path, help="Article Markdown file")
    parser.add_argument("--out", type=Path, help="Output PDF path; defaults to <article>.pdf")
    parser.add_argument("--page-size", choices=sorted(PAGE_SIZES), default="a4")
    parser.add_argument("--margin", type=float, default=54.0, help="Page margin in PDF points")
    parser.add_argument("--css", type=Path, help="Optional CSS file appended after the default CSS")
    parser.add_argument(
        "--engine",
        choices=["auto", "pandoc-typst", "pandoc-xelatex", "pymupdf"],
        default="auto",
        help="PDF renderer. auto tries pandoc-typst, pandoc-xelatex, then pymupdf.",
    )
    parser.add_argument("--no-optimize", action="store_true", help="Skip the post-render PDF optimization pass")
    args = parser.parse_args()

    markdown_path = args.markdown
    if not markdown_path.exists():
        parser.error(f"Markdown file not found: {markdown_path}")
    if markdown_path.suffix.lower() != ".md":
        parser.error("Input file must be a Markdown .md file")

    output_path = args.out or default_output_path(markdown_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    css = DEFAULT_CSS
    if args.css:
        css += "\n" + args.css.read_text(encoding="utf-8")

    used_engine = render_pdf(
        markdown_path,
        output_path,
        page_size=args.page_size,
        margin=args.margin,
        css=css,
        engine=args.engine,
        optimize=not args.no_optimize,
    )
    print(f"wrote {output_path} using {used_engine}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
