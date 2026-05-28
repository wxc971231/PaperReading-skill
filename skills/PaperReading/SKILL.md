---
name: PaperReading
description: Create Chinese paper-interpretation blog drafts from a paper link, arXiv/OpenReview page, DOI, or PDF. Use when Codex needs to read a research paper and produce a Typora-friendly Markdown/PDF article folder containing the article .md file, a same-content rendered article PDF, the original paper PDF, and an img/ directory of extracted or generated figures in the user's established "论文理解" style.
---

# Paper Blog Writer

## Overview

Use this skill to turn a research paper into a self-contained Markdown reading-note folder plus a matching rendered article PDF. The Markdown remains the source of truth and must be Typora-friendly; the article PDF is generated from that Markdown after drafting so the user can read/share a figure-rich PDF without running a separate converter. Do not create Hexo scaffolding, HTML posts, front matter metadata, or "首发链接".

Read `references/style-guide.md`, `references/local-density-prompts.md`, and `references/output-contract.md` before writing the article. Use `scripts/resolve_paper_source.py` as a first-pass metadata helper when the input is a title, arXiv id, or arXiv URL, then still compare against conference/OpenReview/project/author pages. Use `scripts/fetch_openreview_notes.py` whenever an OpenReview forum URL/id is found; static OpenReview HTML can omit dynamically loaded reviews. Use `scripts/detect_pdf_visuals.py` first when a PDF is available and figures/tables are needed. Use `scripts/extract_pdf_figures.py` for embedded-image/page-render fallback. Use `scripts/crop_pdf_regions.py` for Codex-driven high-DPI correction when automatic candidates are incomplete. After the Markdown is final, use `scripts/render_markdown_pdf.py` to generate the same-basename article PDF. Use `scripts/verify_article_folder.py` before finalizing.
Read `references/depth-rubric.md` before drafting; the article must satisfy that depth bar unless the paper is genuinely short.
When working inside the user's blog/source workspace, inspect the closest existing `论文理解` posts on the same topic before drafting and compare the generated article against them before finishing.

## Output Contract

Create one folder per paper under the repository/workspace root's `output/` directory:

```text
output/
  <paper-note-folder>/
    <paper-note-folder>.md
    <paper-note-folder>.pdf
    paper.pdf
    img/
      img_001.png
      img_002.png
      ...
      audit.md
    code/                 # only when an official/open-source repository exists
```

Create paper-note folders in `<project-root>/output/`, not directly in the root and not inside this skill directory. For this workspace, the default output root is `C:\Users\wwxc9\Desktop\git\PaperReading\output`; if the user is running from another checkout, use the nearest project root that contains `skills/PaperReading/`, then create/use its `output/` subfolder. The skill folder must stay clean and contain only reusable skill files such as `SKILL.md`, `references/`, `scripts/`, and `agents/`.

Name the paper-note folder after the paper title, not after a Chinese topic category. Use the official paper title from the latest available version, then make it filesystem-safe by removing characters invalid on Windows (`<>:"/\|?*`), collapsing whitespace, and trimming trailing dots/spaces. Keep the title readable; only shorten it when it would become impractically long.

```text
OptMATH Benchmarking Mathematical Reasoning with Optimization Modeling/
```

The Markdown file must be directly openable in Typora. The rendered article PDF must be generated from this Markdown and should contain the same text, headings, code snippets, tables, formulas as text, and all referenced images. Use relative image paths:

```markdown
![在这里插入图片描述](img/img_001.png)
```

Do not use `/MyBlog/...`, Hexo tags, `index_img`, YAML front matter, or HTML `<img>` blocks.

## Workflow

1. **Ingest the paper**
   - If the user gives a PDF path, copy it into the output folder as `paper.pdf`.
   - If the user gives a paper link, download or fetch the latest available PDF when network/tools allow. If downloading is blocked, ask the user for the PDF.
   - When the input is a title, arXiv id, or arXiv URL, run `scripts/resolve_paper_source.py` and save its output as `output/<paper-note-folder>/paper_source.json` when useful. Treat this JSON as a first-pass hint, not as the final authority.
   - Search for the latest version before naming the folder or writing:
     - For arXiv, prefer the `abs` page's latest version and download the latest `pdf` URL, not a stale `v1` link unless the user explicitly asks for that version.
     - If the title appears on OpenReview, a conference page, publisher page, project page, or authors' homepage, compare dates/version labels and use the newest public paper PDF.
     - If multiple versions disagree, record which version was used in the article's `文章链接`/`发表` information or in a short note near the opening block.
   - Collect paper title, authors, institutions, venue/date if available, code/project links if available, latest-version source, and the main PDF text.
   - Search OpenReview by exact title and common title variants. If a match exists, record the OpenReview URL and run `scripts/fetch_openreview_notes.py <openreview-url-or-id> --out output/<paper-note-folder>/openreview_notes.json`. Read the API artifact for decision, official reviews, reviewer scores, rebuttals, and follow-up comments when accessible. Do not conclude that reviews are unavailable only because the browser/text view shows the paper metadata plus `Loading`.
   - Search the paper, arXiv page, official project page, Papers with Code, OpenReview, and PDF footnotes for code links.
   - If an official or clearly associated open-source repository exists, clone or download it into `output/<paper-note-folder>/code/` and analyze it while writing.
   - Distinguish an official project/demo page from a code repository. Do not duplicate the GitHub URL in both `代码` and `项目页`; omit `项目页` when no separate project page exists.
   - Do not reuse images from existing blog posts. Final figures must come from the current paper PDF extraction/cropping or from newly created explanatory visuals.

2. **Extract and prepare figures**
   - Run `scripts/detect_pdf_visuals.py` on `paper.pdf` to produce high-DPI figure/table candidates, `manifest.csv`, and `contact_sheet.png`.
   - Codex must autonomously inspect the contact sheet, manifest, and relevant rendered PDF pages. Select complete, sharp candidates for final article images, then copy/rename the selected files to `img/img_001.png`, `img/img_002.png`, etc. Do not ask the user to choose or approve routine figure crops.
   - Codex must audit every final figure/table against the source PDF page before writing around it. Check that the crop is not cut off, duplicated, overly small, blurred, missing legends/axis labels/table headers, missing rows/columns, or mixed with unrelated prose. Re-crop with `scripts/crop_pdf_regions.py` whenever a final image fails this audit, then re-audit the replacement.
   - Iterate extraction -> visual audit -> re-crop -> re-audit until every referenced `img/img_*` file is complete enough for the article. If the crop cannot be made complete from the PDF, omit that image or replace it with a better source page/candidate; do not leave a known-bad crop in the final Markdown.
   - Write an audit log at `img/audit.md` before finalizing. For every final `img/img_*` referenced by the article, record: image filename, source PDF page, figure/table number or role, crop source/coordinates when known, audit status, and any repair performed. This log is for traceability; do not reference it from the article body unless the user asks.
   - For main-result tables, ablation tables, and comparison tables, verify that the crop includes all rows discussed in the article, especially the proposed method row and the strongest baselines. If a candidate contains only the upper part of a table or includes unrelated prose below it, re-crop the table with `scripts/crop_pdf_regions.py` and re-audit it.
   - If PDFFigures2 output is available, pass it via `--pdffigures-json`; use it as a bounding-box source, then still render final crops directly from the PDF with PyMuPDF.
   - Prefer automatically detected high-DPI crops for framework diagrams, method figures, data-construction figures, training/alignment figures, result tables, ablation charts, analysis plots, and qualitative examples.
   - If automatic detection is poor or yields too few usable figures, run `scripts/extract_pdf_figures.py` for embedded images/page renders, then crop the relevant figure/table areas directly from the PDF with `scripts/crop_pdf_regions.py`. This is high-DPI PDF-region rendering, not a low-resolution screenshot workflow.
   - Many ML papers store diagrams and tables as vector PDF content rather than embedded images. Treat "0 embedded figures but many rendered page visuals" as normal; crop high-DPI PDF regions instead of giving up.
   - For final figures/tables, prefer tight crops without captions or surrounding paper prose. Use `--caption auto --trim --dpi 360` when cropping from vector PDF pages, and adjust the crop region if a figure/table is incomplete.
   - If PyMuPDF is missing, install it after approval or use an approved local target install, then retry extraction. Do not silently proceed with a one-figure or no-figure article.
   - Rename final article figures sequentially as `img_001.png`, `img_002.png`, etc.
   - Use 8-15 figures for a normal systems/ML paper when the PDF provides them; fewer is acceptable only for short or figure-light papers. For papers with many method and experiment figures, include enough figures to support each major method and experiment subsection.
   - If the user's closest existing post for the same paper/topic uses many figures, treat that as evidence that the paper is figure-rich. Revisit appendices and rendered pages until the new draft has comparable visual coverage, unless the user explicitly requests a shorter version.
   - If the paper lacks usable figures, create simple explanatory diagrams or tables as images only when they materially improve understanding.

3. **Plan the article**
   - Classify the paper type before drafting and adapt the emphasis:
     - `classic method / architecture`: prioritize core idea, notation, algorithm, historical context, and mechanism-level explanation; do not force 8-15 figures when the original paper is figure-light.
     - `dataset / benchmark`: prioritize data construction, annotation/filtering, leakage/quality checks, metrics, and benchmark limitations.
     - `system / agent / tool-use`: prioritize modules, call timing, artifacts, feedback channels, failure modes, and engineering tradeoffs.
     - `theory`: prioritize assumptions, theorem statements, proof intuition, and what the result does or does not imply.
     - `survey`: prioritize taxonomy, comparison dimensions, missing coverage, and how the survey organizes the field.
   - Identify the paper's core problem, motivation, method, experiments, conclusion, source of the core idea, strengths, weaknesses, and future directions.
   - If OpenReview exists, extract reviewer praise, main concerns, requested experiments/clarifications, and the authors' rebuttal from `openreview_notes.json` or the OpenReview API response. If the API returns no public `official_review` notes, state only that no public reviews were returned by the API.
   - If a code repository exists, locate the files that implement the central method, training loop, loss, model architecture, inference/evaluation, and data processing.
- Reconstruct the paper as a learning note rather than translating section-by-section.
- Calibrate information density using the portable style rules in `references/local-density-prompts.md`; do not depend on any machine-specific blog path being present.
  - Open with a concrete task definition, not only a generic motivation.
  - Name the main existing method families and explain how each works at a high level.
  - State the exact weakness the paper targets, preferably with the paper's own motivating evidence or failure observation.
  - Use dense bullet-style exposition: a normal paragraph should carry a concrete mechanism, setting, metric, number, failure mode, or interpretation.
  - After every important figure/table, add 2-4 concrete takeaways rather than one vague sentence.
  - Preserve local cross-paper context when the topic matches the user's previous posts, e.g. "这类方法和 ORLM / OptiMUS / OptiTree 的差异在于...".
   - Build a section outline from all major paper contributions. Do not collapse distinct contributions such as data construction, model training, alignment, inference, automatic testing, and ablation into one short paragraph.
   - For each method component, plan: motivation, formal definition or algorithm, why it is needed, how it differs from prior work, and a figure/table if available.
   - For each experiment group, plan: question being answered, setting/metric/baseline, figure/table, result interpretation, and caveat.
   - For papers with external verifiers, executable evaluation, tool feedback, or reinforcement learning from verifiable rewards, explicitly plan feedback channels, reward components, regularization/objective design, curriculum/training phases, data-quality checks, and appendix diagnostics when present.
   - If the paper relies on staged LLM/tool/retriever/verifier calls, plan a compact stage-timing summary: trigger, input, output, and whether each stage is offline/training-time or online/inference-time.
   - Scan appendix headings before drafting. Include appendix algorithms, robustness tables, code-pass/execution rates, partial-credit metrics, prompt templates, and failure/error analyses when they clarify the method's behavior or limitations.
   - Choose a structure from the style guide. Default:

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
# 4. 代码分析   # only when code exists
## 4.1 伪代码
## 4.2 工程技巧
# 5. 总结
## 5.1 创新思想来源
## 5.2 Review意见   # only when OpenReview exists
## 5.3 未来展望
## 5.4 Q&A
```

This skeleton is mandatory. Keep the exact opening metadata keys and numbered top-level headings. Do not replace them with free-form sections such as `基本信息`, `关键实验发现`, `我的理解`, or `参考链接`. When code is absent, omit `# 4. 代码分析` and renumber the summary to `# 4. 总结`; when OpenReview is absent, omit only the `Review意见` subsection and renumber following summary subsections if needed.

4. **Write the Markdown**
   - Write in Chinese.
   - The `摘要` line must be a faithful Chinese translation of the paper abstract, not a rewritten summary, commentary, or merged conclusion. Preserve the abstract's claim order and key qualifiers. Do not add extra background, reviewer information, code information, or your own judgement inside `摘要`; put interpretation in later sections.
   - Keep the user's explanatory style: motivation first, concept unpacking, formulas when useful, method comparison, experiment interpretation, then concise judgement.
   - Write a full interpretation, not an abstract-level summary. A normal ML paper should usually produce a substantial article with multiple `##`/`###` subsections, formulas, figures, and experiment-by-experiment analysis.
   - Keep the information density close to the user's established paper-reading style: define tasks precisely, spell out method families and failure modes, include key numbers/settings, and avoid one-sentence sections. If a section feels like a high-level news summary, revise it into a learning note.
   - In `# 2. 本文方法`, explain the method clearly enough that the reader can reconstruct the paper's mechanism. Split into multiple `## 2.x` / `### 2.x.x` subsections when the paper has distinct components such as problem formulation, objective, data construction, training, inference, scaling law, verifier, or ablation mechanism.
   - If the paper gives formulas, include them in LaTeX unless the formula is incidental or not useful for understanding. Use display math `$$...$$` or inline math `\(...\)`; do not write formulas inside Markdown code spans or plain code blocks.
   - Preserve the paper's best explanatory shape when it is useful: motivated observations, mechanism definitions, stage/call timing summaries, appendix diagnostics, and failure cases should be kept as general writing patterns rather than tied to one domain.
   - Use bold text for key claims and important takeaways.
   - Use blockquotes for supplemental explanations, intuition, related concepts, or caveats.
   - Use Markdown tables for compact comparisons.
   - Insert figures near the paragraph that explains them; every figure should have surrounding explanation.
   - Follow the list-nesting rules in `references/style-guide.md`: when images, display formulas, blockquotes, tables, or code blocks explain the nearest `-` list item, indent them by 4 spaces so they render as part of that item in Typora.
     - If a code repository exists, add a `代码分析` section between `实验` and `总结`:
     - `## 4.1 伪代码`: write concise inline Python-style pseudocode that captures the paper method's main logic, based on the repository rather than paper prose alone. Add relatively detailed Chinese comments for the major steps, especially input preparation, core objective/decision, training or inference update, and output.
     - `## 4.2 工程技巧`: explain reusable implementation details, such as data organization, config design, loss implementation, evaluation scripts, efficient batching, logging, or numerical-stability tricks. Every bullet in this subsection must include a concise source-derived code snippet from the cloned repository. Snippets may omit irrelevant middle lines with `...`, but must include enough context and Chinese comments to show the engineering idea.
     - If the repository only contains release, inference, evaluation, or prompt utilities, state that limitation and write pseudocode from the paper algorithm plus the actual repository utilities that were inspected. Do not imply missing training code was present.
   - Keep the code-analysis section concise; it should help understand the method and transferable engineering choices, not become a full code walkthrough.
   - Use numbered subsections in the final summary. If code exists, use `# 5. 总结` with `## 5.1 创新思想来源`, optional `## 5.2 Review意见`, `## 5.3 未来展望`, and `## 5.4 Q&A`.
   - If code does not exist, use `# 4. 总结` with `## 4.1 创新思想来源`, optional `## 4.2 Review意见`, `## 4.3 未来展望`, and `## 4.4 Q&A`.
   - Include `Review意见` only when a public OpenReview record is found. If OpenReview is unavailable, do not add the Review subsection and do not speculate about reviewer claims.
   - In `# 3. 实验`, always split:
     - `## 3.1 实验设定`: datasets, unique train/test splits, baselines, model sizes, metrics, training/evaluation protocol, and any fairness controls.
     - `## 3.2 实验结果与分析`: create one `### 3.2.x` subsection per major experiment/result. Each experiment subsection must start with a short statement of the experiment setting (data/model/baseline/metric as relevant), then explain the result and its implication.

5. **Render the article PDF**
   - After the Markdown and final images are complete, render a same-basename PDF next to the Markdown:

```bash
python <skill-dir>/scripts/render_markdown_pdf.py output/<paper-note-folder>/<paper-note-folder>.md
```

   - The expected output is `output/<paper-note-folder>/<paper-note-folder>.pdf`, distinct from the original paper stored as `paper.pdf`.
   - The renderer prefers Pandoc + Typst, discovers local binaries from `.tools/md-pdf/bin`, and discovers local CJK fonts from `.tools/md-pdf/fonts`. This is the expected path for readable Chinese, proper image sizing, tables, and rendered LaTeX math.
   - The rendered PDF must be图文并茂 and content-equivalent to the Markdown: all Markdown image references should appear in the PDF, headings and tables should be readable, and formulas should render as math. The PyMuPDF fallback is only acceptable when Pandoc/Typst is unavailable; if it leaves raw LaTeX text or tiny images, install or use the local Pandoc/Typst toolchain and rerender.
   - Spot-check at least the first page and one image-heavy page of the rendered PDF when possible. If images are missing, broken, oversized, or compressed into unreadable thumbnails, fix the Markdown image paths or rerender.
   - If PDF rendering fails because `pandoc`, `typst`, `font-ttf-noto-cjk`, `markdown_it`, or PyMuPDF is missing, install the missing package after approval when network access is needed, or place the missing executable/font under `.tools/md-pdf/`, then rerender. Do not finalize without the article PDF unless the user explicitly waives it.

6. **Verify**
   - Confirm the paper-note folder is directly under `<project-root>/output/` and its folder name is the sanitized latest-version paper title.
   - Confirm the PDF and metadata come from the latest public paper version found during search, or explicitly document why a non-latest/user-provided version was used.
   - Confirm the folder has exactly the expected shape.
   - Confirm the same-basename rendered article PDF exists beside the Markdown and is newer than or as new as the Markdown.
   - Confirm every image reference in the Markdown resolves to an existing file under `img/`.
   - Confirm `img/audit.md` exists when the article references final images, and that every referenced `img/img_*` appears in the audit log.
   - Confirm no Hexo YAML front matter, `/MyBlog/`, raw HTML image tags, or "首发链接" remains.
   - Confirm images, formulas, blockquotes, tables, and code fences are nested under the relevant list item when they are subordinate to a `-` bullet.
   - If code exists, confirm `output/<paper-note-folder>/code/` exists and the article references concrete repository files or modules in prose.
   - Confirm OpenReview was searched and either included or explicitly marked unavailable. If an OpenReview URL/id was found, confirm `openreview_notes.json` (or an equivalent saved API response) was inspected before claiming reviews are absent.
   - Compare the draft against `references/depth-rubric.md`; revise if it reads like a high-level outline, has too few figures, omits formulas/algorithm details, or fails to interpret experiments.
   - Perform a final Codex-owned visual audit: open/check all final `img/img_*` files against their PDF pages or candidate manifest entries. Tables must include all relevant headers, columns, and rows; figures must include all panels, legends, axes, labels, and visual elements needed by the article. Re-crop incomplete images and re-run this audit before finalizing.
   - Run `scripts/verify_article_folder.py output/<paper-note-folder>` and fix reported errors before finalizing. Treat warnings as prompts for judgment; resolve or explicitly mention any residual warning in the final response.
   - If a same-paper or close-topic local `论文理解` post exists, compare behavior rather than copying text:
     - section granularity: method components and experiment questions should be split at a similar level;
     - figure density: major diagrams, tables, ablations, appendices, and prompt templates should not disappear;
     - explanatory density: formulas should be unpacked with intuition, not merely listed;
     - writer stance: include concise personal judgement such as "我觉得..." or "这里可以理解为..." when the user's style uses it;
     - code and summary additions should match the body style, not read like appended generic reports.
     - for same-paper comparisons, new sections may be structurally different, but the main method/experiment coverage should preserve the local article's named mechanisms, formulas, figures, and concrete reviewer controversies.
   - Revise once before finalizing if the comparison shows the generated article is more survey-like, less concrete, or less visually grounded than the local style anchor.
   - If possible, open or render the Markdown preview enough to catch broken paths and obvious formatting issues.
   - If possible, inspect the rendered article PDF enough to catch missing images, severe pagination problems, unreadable text, or a PDF that does not reflect the latest Markdown.

## Figure Extraction Script

Resolve arXiv metadata as an optional first pass:

```bash
python <skill-dir>/scripts/resolve_paper_source.py "Attention is all you need" --out paper_source.json
```

Start with automatic visual detection:

```bash
python <skill-dir>/scripts/detect_pdf_visuals.py paper.pdf --out img/candidates --dpi 360
```

This writes `candidate_*.png`, `manifest.csv`, and `contact_sheet.png`. Inspect the contact sheet, then copy selected candidates into final sequential names under `img/`.

For final-image traceability, create `img/audit.md` with this shape:

```markdown
# Figure Audit

| Final image | PDF page | Source visual | Crop/source | Audit result | Repair notes |
| --- | ---: | --- | --- | --- | --- |
| img_001.png | 3 | Figure 1 | candidate_001 / recrop coords | PASS | Re-cropped to include all labels |
```

If PDFFigures2 metadata is available:

```bash
python <skill-dir>/scripts/detect_pdf_visuals.py paper.pdf --out img/candidates --dpi 360 \
  --pdffigures-json pdffigures.json
```

Use embedded-image/page rendering as a fallback or debugging aid:

```bash
python <skill-dir>/scripts/extract_pdf_figures.py paper.pdf --out img/raw --mode both
```

Common options:

```bash
python <skill-dir>/scripts/extract_pdf_figures.py paper.pdf --out img/raw --mode images
python <skill-dir>/scripts/extract_pdf_figures.py paper.pdf --out img/raw --mode pages --pages 1,3,7-9 --dpi 180
python <skill-dir>/scripts/extract_pdf_figures.py paper.pdf --out img/raw --mode both --min-width 240 --min-height 160
```

The script requires PyMuPDF (`fitz`). If missing, install `pymupdf` only after user approval when network access is needed.

For vector PDF figures or tables, first render pages, then crop normalized page regions:

```bash
python <skill-dir>/scripts/crop_pdf_regions.py paper.pdf --out img \
  --crop img_001.png:2:0.16,0.10,0.86,0.48 \
  --crop img_002.png:4:0.15,0.13,0.86,0.42
```

For publication-quality vector figures/tables, use:

```bash
python <skill-dir>/scripts/crop_pdf_regions.py paper.pdf --out img --dpi 360 --caption auto --trim \
  --crop img_001.png:2:0.16,0.10,0.86,0.48
```

If the downstream Markdown/blog converter supports SVG and the figure is mostly vector content, export SVG instead:

```bash
python <skill-dir>/scripts/crop_pdf_regions.py paper.pdf --out img --format svg --caption auto \
  --crop img_001.svg:2:0.16,0.10,0.86,0.48
```

Coordinates are `output.png:page:x0,y0,x1,y1`, where the page number is 1-based and coordinates are fractions of the PDF page. Use cropped figures/tables as final article images, not the raw rendered full pages. If `--caption auto` removes the wrong text or leaves a caption/prose line, tighten the coordinates and rerun. Prefer PNG for maximum blog compatibility; use SVG only when the user's conversion/rendering pipeline handles it reliably.

Before finalizing, run the folder verifier:

```bash
python <skill-dir>/scripts/verify_article_folder.py output/<paper-note-folder>
```

Render the article PDF from the final Markdown:

```bash
python <skill-dir>/scripts/render_markdown_pdf.py output/<paper-note-folder>/<paper-note-folder>.md
```

Common options:

```bash
python <skill-dir>/scripts/render_markdown_pdf.py output/<paper-note-folder>/<paper-note-folder>.md \
  --out output/<paper-note-folder>/<paper-note-folder>.pdf
python <skill-dir>/scripts/render_markdown_pdf.py output/<paper-note-folder>/<paper-note-folder>.md \
  --page-size letter --margin 48
```

## Quality Bar

The article should read like the user's existing "论文理解" posts:

- It should explain why the problem matters before describing the method.
- It should name the paper's central insight in one or two sentences early.
- It should not merely summarize figures; interpret what each figure proves.
- It should separate paper claims from the writer's own understanding when adding judgement.
- It should connect paper ideas to their likely inspirations, reviewer feedback when available, practical limitations, future improvements, and a few deep self-asked Q&A items.
- It should be closer to a careful paper-reading note than a concise survey blurb; when the paper has several method modules and many experiments, mirror that richness.
