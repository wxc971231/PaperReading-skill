#!/usr/bin/env python3
"""Verify a generated paper-reading article folder.

The checks here intentionally cover mechanical correctness only. Codex still
needs to read the paper, audit figure completeness, and judge explanation depth.

Example:
  python verify_article_folder.py output/"Attention Is All You Need"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


IMAGE_RE = re.compile(r"!\[[^\]]*\]\((img/[^)]+)\)")
CJK_COMMENT_RE = re.compile(r"(?m)^\s*(?:#|//|/\*|\*|--)\s*.*[\u4e00-\u9fff]")
METADATA_LINES = [
    "- 文章链接：",
    "- 作者：",
    "- 机构：",
    "- 代码：",
    "- 项目页：",
    "- OpenReview：",
    "- 发表：",
    "- 领域：",
    "- 一句话总结：",
    "-------",
    "- 摘要：",
]
FORBIDDEN_PATTERNS = {
    "yaml_front_matter": re.compile(r"\A---\s*\n"),
    "myblog_path": re.compile(r"/MyBlog/"),
    "html_img": re.compile(r"<img\b", re.I),
    "hexo_index_img": re.compile(r"\bindex_img\b"),
    "first_publish_link": re.compile(r"首发链接"),
}
OPENREVIEW_ABSENT_RE = re.compile(
    r"- OpenReview：\s*(?:无|暂无|未找到|没有|无公开|未检索到|N/A|None)",
    re.I,
)
OPENREVIEW_UNREAD_REVIEWS_RE = re.compile(
    r"(?:OpenReview|公开页面).{0,80}(?:未展示|没有展示|看不到|不可见).{0,80}(?:reviewer|review|审稿|rebuttal|打分|意见)"
    r"|不推断具体审稿人观点",
    re.I | re.S,
)


@dataclass
class CheckReport:
    folder: str
    markdown: str | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    image_refs: list[str] = field(default_factory=list)
    final_images: list[str] = field(default_factory=list)
    has_pdf: bool = False
    has_article_pdf: bool = False
    has_code_dir: bool = False
    has_audit: bool = False

    @property
    def ok(self) -> bool:
        return not self.errors


def expected_markdown(folder: Path) -> Path:
    return folder / f"{folder.name}.md"


def resolve_article_folder(folder: Path) -> Path:
    """Accept either output/<title> or a bare title that exists under output/."""
    if folder.exists():
        return folder
    if not folder.is_absolute():
        output_candidate = Path("output") / folder
        if output_candidate.exists():
            return output_candidate
    return folder


def sequential_image_errors(files: list[Path]) -> list[str]:
    errors: list[str] = []
    expected = [f"img_{idx:03d}.png" for idx in range(1, len(files) + 1)]
    actual = [path.name for path in files]
    if actual != expected:
        errors.append(f"Final images are not sequential: expected {expected}, got {actual}")
    return errors


def missing_metadata_lines(text: str) -> list[str]:
    opening = text[:1800]
    return [line for line in METADATA_LINES if line not in opening]


def ordered_section_errors(text: str, has_code: bool, has_openreview: bool) -> list[str]:
    sections = ["# 1. 背景", "# 2. 本文方法", "# 3. 实验", "## 3.1 实验设定", "## 3.2 实验结果与分析"]
    if has_code:
        sections.extend(["# 4. 代码分析", "## 4.1 伪代码", "## 4.2 工程技巧", "# 5. 总结", "## 5.1 创新思想来源"])
        if has_openreview:
            sections.append("## 5.2 Review意见")
            sections.extend(["## 5.3 未来展望", "## 5.4 Q&A"])
        else:
            sections.extend(["## 5.2 未来展望", "## 5.3 Q&A"])
    else:
        sections.extend(["# 4. 总结", "## 4.1 创新思想来源"])
        if has_openreview:
            sections.append("## 4.2 Review意见")
            sections.extend(["## 4.3 未来展望", "## 4.4 Q&A"])
        else:
            sections.extend(["## 4.2 未来展望", "## 4.3 Q&A"])

    errors: list[str] = []
    positions: list[int] = []
    for section in sections:
        pos = text.find(section)
        if pos < 0:
            errors.append(f"Missing required section heading: {section}")
        positions.append(pos)
    existing = [pos for pos in positions if pos >= 0]
    if existing != sorted(existing):
        errors.append("Required section headings are not in the expected order")
    return errors


def experiment_structure_errors(text: str) -> list[str]:
    errors: list[str] = []
    if not re.search(r"^### 3\.2\.\d+\s+\S+", text, re.M):
        errors.append("Missing per-experiment subsection under ## 3.2, expected headings like ### 3.2.1 ...")
    return errors


def abstract_warnings(text: str) -> list[str]:
    match = re.search(r"- 摘要：(.*?)(?:\n# 1\. 背景|\Z)", text, re.S)
    if not match:
        return []
    abstract = match.group(1).strip()
    warnings: list[str] = []
    if "这篇论文" in abstract or "本文重新审视" in abstract or "作者改为" in abstract:
        warnings.append("摘要 may be rewritten commentary; it should be a faithful Chinese translation of the original abstract")
    if len(abstract) < 180:
        warnings.append("摘要 looks too short for a full-paper abstract translation")
    return warnings


def openreview_warnings(text: str, has_openreview: bool) -> list[str]:
    if has_openreview and OPENREVIEW_UNREAD_REVIEWS_RE.search(text):
        return [
            "Article says OpenReview reviews/rebuttals are not visible; verify with scripts/fetch_openreview_notes.py before making this claim"
        ]
    return []


def formula_format_errors(text: str) -> list[str]:
    errors: list[str] = []
    for match in re.finditer(r"^```(?:text|math)?[ \t]*\n(.*?)^```", text, re.S | re.M):
        body = match.group(1)
        if re.search(r"(\\sum|\\prod|\\frac|p\(|L\(|D\s*=|U\s*=|x_\{|x_1|theta|alpha|beta)", body):
            errors.append("Formula-like content appears inside a code block; use LaTeX math blocks instead")
            break
    if re.search(r"`[^`\n]*(?:\\sum|\\prod|\\frac|p\(|L\(|D\s*=|U\s*=|x_1|theta|alpha|beta)[^`\n]*`", text):
        errors.append("Formula-like content appears inside inline code; use inline LaTeX instead")
    return errors


def engineering_snippet_errors(text: str) -> list[str]:
    match = re.search(r"## 4\.2 工程技巧(.*?)(?:\n# \d+\. |\Z)", text, re.S)
    if not match:
        return []
    section = match.group(1)
    bullets = len(re.findall(r"(?m)^- \*\*", section))
    code_blocks = len(re.findall(r"```(?:python|[A-Za-z0-9_-]+)?\s*\n", section))
    if bullets and code_blocks < bullets:
        return ["Every ## 4.2 工程技巧 bullet must include a source-derived code snippet"]
    return []


def code_analysis_comment_errors(text: str) -> list[str]:
    """Check that code-analysis snippets carry Chinese explanatory comments."""
    errors: list[str] = []
    pseudo = re.search(r"## 4\.1 伪代码(.*?)(?:\n## 4\.2 工程技巧|\n# \d+\. |\Z)", text, re.S)
    if pseudo:
        pseudo_blocks = re.findall(r"```[A-Za-z0-9_-]*\s*\n(.*?)^```", pseudo.group(1), re.S | re.M)
        comment_count = sum(len(CJK_COMMENT_RE.findall(block)) for block in pseudo_blocks)
        if pseudo_blocks and comment_count < 3:
            errors.append("## 4.1 伪代码 should include relatively detailed Chinese comments for the main steps")

    engineering = re.search(r"## 4\.2 工程技巧(.*?)(?:\n# \d+\. |\Z)", text, re.S)
    if engineering:
        blocks = re.findall(r"```[A-Za-z0-9_-]*\s*\n(.*?)^```", engineering.group(1), re.S | re.M)
        for index, block in enumerate(blocks, start=1):
            if not CJK_COMMENT_RE.search(block):
                errors.append(f"## 4.2 工程技巧 code snippet {index} lacks a Chinese explanatory comment")
                break
    return errors


def verify(folder: Path) -> CheckReport:
    folder = resolve_article_folder(folder)
    report = CheckReport(folder=str(folder))
    if not folder.exists() or not folder.is_dir():
        report.errors.append(f"Folder does not exist: {folder}")
        return report
    if folder.parent.name != "output":
        report.errors.append("Article folder should live under output/<paper-title>/")

    md = expected_markdown(folder)
    if not md.exists():
        candidates = sorted(folder.glob("*.md"))
        if candidates:
            report.markdown = str(candidates[0])
            report.errors.append(f"Markdown filename should match folder name: expected {md.name}, found {candidates[0].name}")
            md = candidates[0]
        else:
            report.errors.append(f"Missing Markdown file: {md.name}")
            return report
    else:
        report.markdown = str(md)

    report.has_pdf = (folder / "paper.pdf").exists()
    if not report.has_pdf:
        report.errors.append("Missing paper.pdf")
    article_pdf = folder / f"{folder.name}.pdf"
    report.has_article_pdf = article_pdf.exists()
    if not report.has_article_pdf:
        report.errors.append(f"Missing rendered article PDF: {article_pdf.name}")

    img_dir = folder / "img"
    if not img_dir.exists():
        report.errors.append("Missing img/ directory")
    else:
        final_images = sorted(img_dir.glob("img_*.png"))
        report.final_images = [path.name for path in final_images]
        report.errors.extend(sequential_image_errors(final_images))
        report.has_audit = (img_dir / "audit.md").exists() or (img_dir / "audit.csv").exists()

    report.has_code_dir = (folder / "code").exists()

    text = md.read_text(encoding="utf-8")
    if report.has_article_pdf:
        try:
            if article_pdf.stat().st_mtime < md.stat().st_mtime:
                report.warnings.append("Rendered article PDF is older than the Markdown file; regenerate it")
        except OSError:
            pass
    for line in missing_metadata_lines(text):
        report.errors.append(f"Missing required opening metadata line: {line}")

    has_openreview = "- OpenReview：" in text and not OPENREVIEW_ABSENT_RE.search(text)
    report.errors.extend(ordered_section_errors(text, report.has_code_dir, has_openreview))
    report.errors.extend(experiment_structure_errors(text))
    report.errors.extend(formula_format_errors(text))
    report.errors.extend(engineering_snippet_errors(text))
    report.errors.extend(code_analysis_comment_errors(text))
    report.warnings.extend(abstract_warnings(text))
    report.warnings.extend(openreview_warnings(text, has_openreview))

    for name, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(text):
            report.errors.append(f"Forbidden Markdown pattern found: {name}")

    image_refs = IMAGE_RE.findall(text)
    report.image_refs = image_refs
    for ref in image_refs:
        if not (folder / ref).exists():
            report.errors.append(f"Missing referenced image: {ref}")

    if image_refs and not report.has_audit:
        report.warnings.append("Final images are referenced but img/audit.md or img/audit.csv is missing")
    if "OpenReview" in text and "项目页：[OpenReview" in text:
        report.errors.append("OpenReview appears to be used as 项目页")
    if "# 4. 代码分析" in text and not report.has_code_dir:
        report.errors.append("Article has code analysis section but code/ directory is missing")
    if report.has_code_dir and "# 4. 代码分析" not in text:
        report.warnings.append("code/ directory exists but article has no # 4. 代码分析 section")
    if len(image_refs) <= 3 and len(report.final_images) > 3:
        report.warnings.append("Many final images exist but only a few are referenced in Markdown")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--json", action="store_true", help="Print JSON report")
    args = parser.parse_args()

    report = verify(args.folder)
    if args.json:
        payload = asdict(report)
        payload["ok"] = report.ok
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        status = "OK" if report.ok else "FAILED"
        print(f"{status}: {report.folder}")
        for error in report.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        for warning in report.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        print(f"markdown: {report.markdown}")
        print(f"paper.pdf: {report.has_pdf}")
        print(f"article pdf: {report.has_article_pdf}")
        print(f"image refs: {len(report.image_refs)}")
        print(f"final images: {len(report.final_images)}")
        print(f"image audit: {report.has_audit}")
        print(f"code dir: {report.has_code_dir}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
