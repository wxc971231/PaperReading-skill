# Output Contract

## Required Files

For each paper, create:

```text
output/
  <article-folder>/
    <article-folder>.md
    paper.pdf
    img/
      img_001.png
      img_002.png
      ...
      audit.md              # required when the article references final images
    code/                   # only when an official/open-source repository exists
```

Create article outputs directly under the repository/workspace root's `output/` directory. In this checkout, that output root is `C:\Users\wwxc9\Desktop\git\PaperReading\output`; in another checkout, use the nearest project root that contains `skills/PaperReading/`, then create/use its `output/` subfolder.

Do not create article outputs directly in the project root or inside the skill folder itself. The skill directory is reusable tooling, not a destination for generated notes.

The `img/` directory must contain only images used by the article or clearly named raw extraction subfolders such as `img/raw/`.

Final article images should be tight cropped figures/tables. Raw full-page renders belong under `img/raw/` and should not be referenced directly unless the whole page is intentionally being discussed. Final figures should normally exclude PDF captions and unrelated surrounding prose; the Markdown article should explain the figure in text.

Automatic visual-detection outputs may live under `img/candidates/` during drafting. Do not reference candidate files directly in the final Markdown unless they have been selected and copied/renamed to final sequential `img_*.png` names.

Every final figure/table must be autonomously audited by Codex against the source PDF page before finishing. A crop is acceptable only if it contains the complete visual content needed by the article: no clipped panels, missing legends, missing axes/labels, missing table headers, missing columns, missing rows, duplicated fragments, or unrelated prose mixed into the image. Codex must iterate by re-cropping and re-auditing failed images; routine crop approval should not be delegated back to the user.

When the article references any final `img/img_*` image, write `img/audit.md`. It must list each referenced final image, source PDF page, source figure/table/candidate, crop source or coordinates when known, audit pass/fail status, and any repair notes. The audit log is a traceability artifact, not article content.

If a code repository exists, clone or download it under `code/`. Preserve the repository contents; do not flatten it into the article folder.

## Markdown Rules

The Markdown is Typora-first:

- No YAML front matter.
- No Hexo metadata.
- No HTML image tags.
- No `/MyBlog/` absolute image paths.
- No "首发链接".
- Use relative images such as `img/img_001.png`.
- When a figure, formula, blockquote, table, or code fence belongs to a preceding `-` list item, indent the whole block by 4 spaces so Typora renders it as subordinate content.
- Write formulas in LaTeX form. Do not put mathematical expressions in Markdown code spans or code blocks.
- If code exists, include `# 4. 代码分析`, `## 4.1 伪代码`, and `## 4.2 工程技巧` before the summary.
- In `## 4.1 伪代码`, include relatively detailed Chinese comments that explain the major algorithmic steps.
- In `## 4.2 工程技巧`, every bullet must include a compact code snippet extracted or distilled from the source repository. Use `...` to omit unrelated middle lines when needed. Every snippet must include Chinese comments explaining the engineering idea.
- If OpenReview exists, include a numbered `Review意见` subsection in the summary. If OpenReview does not exist, omit the subsection.

The article must follow this exact section skeleton. Do not replace it with free-form headings such as `基本信息`, `关键实验发现`, or `我的理解`.

```markdown
- 文章链接：
- 作者：
- 机构：
- 代码：
- 项目页：
- OpenReview：
- 发表：
- 领域：
- 一句话总结：
-------
- 摘要：

# 1. 背景
# 2. 本文方法
# 3. 实验
## 3.1 实验设定
## 3.2 实验结果与分析
### 3.2.1 ...
### 3.2.2 ...
# 4. 代码分析
## 4.1 伪代码
## 4.2 工程技巧
# 5. 总结
## 5.1 创新思想来源
## 5.2 Review意见
## 5.3 未来展望
## 5.4 Q&A
```

When no code repository exists, omit `# 4. 代码分析` and renumber the summary to `# 4. 总结`. When no public OpenReview record exists, omit the `Review意见` subsection and renumber the following summary subsections.

## Naming Rules

Use these defaults:

- Article folder name equals the sanitized official paper title from the latest available paper version. Remove Windows-invalid characters (`<>:"/\|?*`), collapse whitespace, and trim trailing dots/spaces.
- Main Markdown file name equals the folder name plus `.md`.
- Original PDF is `paper.pdf`.
- Article images are sequential, usually `img_001.png`, `img_002.png`, ... Use `.svg` only when the downstream converter/rendering pipeline supports SVG reliably.
- Temporary extracted images may live under `img/raw/`, but final references should use images directly under `img/`.
- Code repositories live under `code/<repo-name>/` or directly under `code/` if only one archive was downloaded and extracted that way.

## Version Rules

Before creating the folder or writing the article:

- Search for the latest public version of the paper.
- For arXiv, use the latest version shown on the `abs` page and avoid stale explicit-version PDFs such as `v1` unless the user asked for that exact version.
- Compare arXiv, OpenReview, publisher/conference pages, project pages, and author pages when more than one source exists.
- Use the newest public PDF found. If the user supplied a local PDF or requested an older version, state that version choice in the article metadata or a short opening note.

## Verification Checklist

Before finishing:

1. Check the generated article folder is directly under `<project-root>/output/`.
2. Check the folder name and Markdown filename use the sanitized latest-version paper title.
3. Check the paper PDF is the latest public version found, or that a user-requested/local non-latest version is explicitly noted.
4. Check all Markdown image references point to existing files.
5. Check all final images are named sequentially.
6. Check `img/audit.md` exists when final images are referenced, and every referenced `img/img_*` appears in the audit log.
7. Check the article begins with the paper information block, not YAML.
8. Check the article contains at least one meaningful figure unless the source paper has no suitable visual material and no diagram is useful.
9. Check the original PDF exists as `paper.pdf`.
10. Check OpenReview was searched; include the link and numbered `Review意见` summary only when found.
11. If code exists, check the repository is present under `code/` and the article includes `代码分析`, `伪代码`, and `工程技巧`.
12. Check `项目页` is not used for OpenReview; OpenReview has its own line.
13. For a normal full paper, check the article is not only an outline: it should satisfy `references/depth-rubric.md` and should not have only 1-3 figures when the PDF contains many useful figures.
14. Check the generated article folder is under `output/` and outside the skill directory.
15. If figure extraction produced only full-page renders, check that `scripts/crop_pdf_regions.py` was used to create final cropped `img_*.png` files.
16. Audit every final image for completeness, resolution, and caption/prose leakage. This audit is Codex's responsibility: inspect the final images against the PDF/source candidates, re-crop with `--dpi 360 --caption auto --trim` when figures are incomplete or captions remain, then re-audit the replacement.
    - For result and ablation tables, the crop must include the rows that support the article's claims, including the proposed method and key baselines. A visually clean but semantically incomplete table is not acceptable.
    - For multi-panel figures, the crop must include every panel referenced in the explanation, plus legends, axes, and labels needed to understand the result.
17. Spot-check Markdown rendering around images, formulas, blockquotes, tables, and code fences; subordinate blocks should be indented under the relevant `-` item.
18. If `scripts/detect_pdf_visuals.py` was used, inspect `img/candidates/contact_sheet.png` and `manifest.csv`; final referenced images should be selected crops, not unreviewed candidates.
19. Run `scripts/verify_article_folder.py output/<article-folder>` and fix errors before finalizing.
