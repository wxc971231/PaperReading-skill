# Style Guide

## Writing Positioning

Write as a Chinese research reading note, not a literal translation. The goal is to help the reader understand:

1. What problem the paper tries to solve.
2. Why previous methods are insufficient.
3. What core idea the paper contributes.
4. How the method works.
5. What the experiments prove.
6. What the paper's strengths and limitations are.

## Article Opening

Do not include Hexo front matter or "首发链接".

Use this exact opening block. Keep every metadata key in this order; if a field is genuinely unavailable, write a concise placeholder such as `无公开代码`, `无独立项目页`, or `未找到公开 OpenReview`, rather than deleting the line.

```markdown
- 文章链接：[Paper Title](...)
- 作者：Author A, Author B, ...
- 机构：University / Lab / Company
- 代码：[owner/repo](...)
- 项目页：[Project Name](...)
- OpenReview：[Paper Title](...)
- 发表：ICML 2025
- 领域：LLM 数值回归
- 一句话总结：...
-------
- 摘要：...
```

Always search OpenReview. Do not put an OpenReview URL in `项目页`; `项目页` is reserved for an official project/demo page.

For authors and institutions:

- Prefer the latest-version PDF title page and official paper page.
- Keep names concise; use "等" when there are many authors.
- For institutions, group repeated affiliations and keep the line readable.

## Default Structure

Use this for most papers:

```markdown
# 1. 背景
## 1.1 ...
## 1.2 ...

# 2. 本文方法
## 2.1 ...
## 2.2 ...

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

Only include `# 4. 代码分析` when an official or clearly associated code repository exists. If no repository exists, use `# 4. 总结` and renumber the summary subsections as `4.1 创新思想来源`, optional `4.2 Review意见`, `4.3 未来展望`, and `4.4 Q&A`.

Do not replace the default structure with shorter free-form headings. For short or classic architecture papers, keep the same top-level skeleton but make the subsections more compact. For analysis-heavy papers, add extra `##` / `###` subsections inside the mandatory skeleton rather than renaming the top-level sections.

Before choosing the final outline, identify the paper type: classic method/architecture, dataset/benchmark, system/agent/tool-use, theory, survey, or other. Let the paper type control emphasis. For example, a classic architecture paper can spend more space on formulas and mechanism reconstruction, while a benchmark paper should spend more space on data construction and evaluation reliability.

## Feature-Specific Depth

Choose depth rules by the paper's method features, not by a fixed research area.

For papers with multiple prior method families:

- Background should distinguish the major families, explain how they work at a high level, then state the exact weakness the paper targets.
- Use the paper's own taxonomy when it is clearer than a generic one, for example prompt-based vs learning-based, retrieval vs fine-tuning, supervised vs reinforcement learning, discriminative vs generative, or model-based vs model-free.

For papers with a central representation or decomposition:

- Explain what the representation is, what information it preserves, and why it makes the original task easier.
- Treat intermediate objects such as graphs, trees, formal languages, latent variables, tool calls, memory states, generated programs, model files, or structured labels as first-class method components.
- If the paper motivates the representation with diagnostic observations, failure statistics, case studies, or small pilot experiments, give those observations their own background subsection such as `动机性观察`. Do not bury them in one sentence before the method.
- When the method has a reusable intermediate structure, explain both its stored fields and its relation semantics, for example what a node/edge/state/example contains and what parent-child, transition, retrieval, or update means.

For papers with data construction, annotation, filtering, or benchmark cleaning:

- Separately explain data sources, generation/annotation rules, filtering criteria, quality checks, and known failure modes.
- Treat dataset reliability as part of the method interpretation when the paper or OpenReview discusses label errors, ambiguity, leakage, corrected test sets, or annotation burden.

For papers with post-training, alignment, search, correction, or reinforcement learning:

- Separate data/reward construction, training objective, regularization, sampling/search, correction, and inference-time procedure. Do not compress these into one "training" paragraph.
- If the paper uses SFT, preference learning, DPO/KTO/PPO/RL, self-correction, verifier feedback, or tool feedback, include the core formula or workflow and explain it intuitively.
- Include reward formulas, surrogate losses, advantage estimates, KL/regularization terms, or curriculum stages when they are central to the contribution.

For papers with external verifiers, executable evaluation, simulators, tools, or generated artifacts:

- Explain why the task is verifiable and what feedback channels exist, such as unit tests, compiler/runtime status, external-tool status, objective values, simulator scores, retrieval hits, human labels, structure checks, or output-file statistics.
- If the paper parses generated artifacts, explain what information is extracted and why final-answer-only evaluation is insufficient.
- For multi-stage systems, add a compact "调用时机/流程小结" subsection when it improves understanding. Split the method into stages, triggers, inputs, outputs, and whether each stage happens offline/training-time or online/inference-time.
- If a system repeatedly calls an LLM, tool, simulator, verifier, retriever, parser, or solver, state what each call is doing: classification, retrieval, generation, verification, correction, scoring, or update.

For experiment-heavy papers:

- Experiments should follow the paper's research questions when available, for example `Q1/Q2/Q3/Q4`, rather than merging all results into one paragraph.
- Appendix tables can be important: include data statistics, training/sampling parameters, robustness checks, ablations, baseline variants, error-type breakdowns, and failure cases when they affect the paper's claims.
- Discussion should include the paper's relevant costs and tradeoffs, such as compute, data quality, annotation burden, tool dependence, robustness, scalability, interpretability, and general-task ability.
- If the appendix contains code pass/execution rates, robustness to data/model choices, partial-credit metrics, error-type analysis, failure cases, or prompt templates that explain the method's behavior, add an experiment or discussion subsection for them rather than limiting the article to main-paper results.

## Code Analysis Style

When a code repository exists, download it into the article folder and inspect it before writing the code-analysis section.

Before writing, map the repository to the paper pipeline:

- entry points for building/training/updating;
- entry points for inference/evaluation;
- modules that implement retrieval/search/matching/generation/verification;
- files that store learned artifacts, prompts, templates, trees, indices, checkpoints, or benchmark outputs;
- utilities that parse generated outputs, execute tools, compare metrics, or log failures.

In `## 4.1 伪代码`:

- Use concise Python-style pseudocode, not copied repository code.
- Express the method's algorithmic skeleton: inputs, model/loss construction, forward pass, training or inference loop, and output.
- Keep it short enough to read as an explanation.
- Add relatively detailed Chinese comments inside the pseudocode. The comments should explain why each major step exists, not merely restate the code. A normal pseudocode block should include comments for input preparation, core objective/decision, and output/update.
- Mention that it is a simplified reconstruction based on the repository.
- If the repository is release/inference/evaluation only and does not contain the training implementation, say this explicitly. In that case, build the pseudocode from the paper's algorithm plus the repository's prompt, inference, parsing, and evaluation utilities; do not pretend the missing training code was inspected.

Example shape:

```python
def train_step(batch):
    # 准备输入与监督信号：这里对应论文中的一个训练样本或 mini-batch。
    x, y = batch
    # 前向计算得到模型输出；真实文章里应替换成论文方法的核心模块。
    pred = model(x)
    # 主损失负责论文任务目标，辅助损失负责额外约束或正则项。
    loss = main_loss(pred, y) + lambda_aux * aux_loss(pred, y)
    # 更新模型参数；若论文是推理算法，则这里应改成搜索/验证/选择步骤。
    loss.backward()
    optimizer.step()
    return loss
```

In `## 4.2 工程技巧`:

- Focus on reusable ideas, not every file.
- Prefer points like config organization, dataset preprocessing, loss implementation, evaluation protocol, caching, distributed training, logging, numerical stability, and reproducibility.
- Reference concrete modules or filenames in prose when useful.
- Keep each point tied to "为什么值得学习".
- Every bullet must include a concise code snippet extracted or distilled from the source repository. Use `...` to omit unrelated middle lines when needed.
- Every snippet must include Chinese comments that explain the transferable engineering idea, for example why this branch exists, what variable controls, how the mask/loss/evaluation works, or what reproducibility assumption the code encodes. Comments should be explanatory, not decorative.
- When the repository lacks full reproducibility, include that as a concrete engineering limitation rather than only praising the repo.
- If the repository is a research prototype, it is fine to note practical issues such as external API dependence, solver/tool licensing, concurrent file writes, fragile JSON parsing, missing data, or environment assumptions.

Do not paste long source code. Quote only tiny fragments if essential.

## Voice and Formatting

- Use bullet points heavily, especially for concepts, method steps, and experiment observations.
- Prefer `-` unordered list items as the main body narration unit, matching the user's existing posts.
- Use numbered lists for ordered mechanisms, algorithm stages, and conclusions.
- Use **bold** for the main claim in a paragraph.
- Use inline code for method names, losses, modules, datasets, and important notation when helpful.
- Use LaTeX for all formulas, and explain each important formula in plain Chinese. Do not put mathematical expressions in Markdown code spans or code blocks.
- Use blockquotes for background knowledge, intuitive interpretations, caveats, and related blog-style notes.
- Prefer concrete causal language: "作者认为这是因为...", "这说明...", "核心问题在于...".
- Avoid empty academic filler. Every paragraph should advance understanding.

## Markdown Nesting

When the article uses `-` list items as正文 narration, keep related visual and formal material attached to the nearest relevant list item:

- Indent images, display formulas, blockquotes, Markdown tables, and code fences by 4 spaces when they explain or belong to the preceding `-` item.
- Preserve a blank line before and after the indented block so Typora renders it as part of the list item.
- Keep headings at top level. Start a new top-level `-` only when the thought is independent, not when it is merely explaining the previous bullet.
- If a figure/table introduces several following observations, write an introductory bullet, nest the figure/table under it, then put the observations as an indented numbered list or indented sub-bullets.
- If a formula is the main object of a paragraph, put the sentence introducing it in a `-` bullet and nest the `$$...$$` block under that bullet.
- If a blockquote is a personal explanation of the previous bullet, nest it under that bullet; use top-level blockquotes only for section-level asides.

Example:

```markdown
- 作者将训练目标写成如下形式：

    $$
    \mathcal{L} = \mathcal{L}_{main} + \lambda \mathcal{L}_{aux}
    $$

    > 这里可以理解为：主损失负责任务目标，辅助损失负责约束中间表示。

- 实验结果如下图所示：

    ![在这里插入图片描述](img/img_001.png)

    1. 第一组结果说明...
    2. 第二组结果说明...
```

## Figure Style

Use Markdown image syntax only:

```markdown
![在这里插入图片描述](img/img_001.png)
```

Place figures immediately after the paragraph that introduces them, then add interpretation after the image. Do not leave unexplained image dumps.

If a full paper has many useful figures but the draft has only 1-3 images, the figure extraction failed as a workflow matter. Render relevant PDF pages and select more figures before finalizing.

Default extraction workflow:

1. Run `scripts/detect_pdf_visuals.py` to generate high-DPI figure/table candidates plus `contact_sheet.png` and `manifest.csv`.
2. Select candidates that are complete, sharp, and relevant to the article.
3. Rename selected candidates as final `img_001.png`, `img_002.png`, ...
4. Use `scripts/crop_pdf_regions.py` for Codex-driven repair when a candidate is clipped, includes captions/prose, or merges multiple unrelated visuals.

After selection, Codex must audit every final `img/img_*` file against the original PDF page before writing or finalizing. The audit should check completeness, not only visual cleanliness: multi-panel figures need all referenced panels, legends, axes, and labels; tables need all headers, relevant columns, proposed-method rows, and key baseline rows. Re-crop any incomplete figure/table before using it in the article, then re-audit the replacement. Do not rely on the user to perform this routine completeness check.

Write the final audit record to `img/audit.md`. The audit record should be compact but complete enough to trace each final image back to its PDF page and to explain any re-cropping decision.

If the paper contains vector figures/tables, use `scripts/crop_pdf_regions.py` to render tight high-DPI PDF regions. This preserves LaTeX text and vector lines better than cropping a low-resolution page screenshot. Use `--dpi 360 --caption auto --trim` for final PNG figures/tables unless the caption itself is being discussed. When the downstream Markdown/blog converter supports SVG and the figure is mostly vector content, `--format svg` is also acceptable. Do not use old blog images as shortcuts when validating or generating a new article.

Final article images should usually exclude captions and surrounding paper prose, because the Markdown article provides its own explanation. Include a caption only when it contains information that is not otherwise visible in the figure/table.

For tables:

- Prefer high-DPI PDF crops when the article needs the original LaTeX/table visual.
- Use Camelot, pdfplumber, Tabula, PyMuPDF `find_tables()`, Marker, or Docling only as optional structure aids when the table should be rewritten as Markdown or when visual detection needs help.
- Do not trust a structured table extractor blindly; merged cells, multi-level headers, and mathematical notation often require manual checking against the PDF crop.

When `contact_sheet.png` shows repeated, partial, or caption-heavy candidates, keep only the best crop and have Codex repair important figures with high-DPI PDF region crops. The final `img/` directory should contain selected article images, while exploratory candidates should stay under `img/candidates/` or `img/raw/`.

Recommended figure choices:

- First method overview or architecture figure.
- One figure/table showing the main experimental result.
- One ablation or analysis figure.
- One qualitative visualization when the paper has it.
- Additional figures only when they clarify a non-obvious mechanism.

For papers whose claims depend on data pipelines, prompts, training settings, robustness checks, or failure analysis, also consider appendix visuals when they explain:

- data augmentation prompts or rules;
- self-correction templates;
- dataset distributions or filtering statistics;
- extended metric tables;
- model-scale or general-task discussions;
- training parameters, decoding/sampling parameters, benchmark-cleaning statistics, tool-free or ablated baselines, supervised-vs-RL comparisons, and error-type analyses.

## Summary Style

The final section should be stronger than a plain recap. Use this structure when enough information exists:

```markdown
# 5. 总结
- ...

## 5.1 创新思想来源
- ...

## 5.2 Review意见
- ...

## 5.3 未来展望
- ...

## 5.4 Q&A
**Q1：...？**

A：...
```

If there is no code-analysis section, use `# 4. 总结` and renumber the same subsections as `4.1`, `4.2`, `4.3`, `4.4`.

Only include `Review意见` when a public OpenReview record exists. If no OpenReview record is found, omit this subsection entirely and move later subsection numbers forward only if necessary to preserve a clean sequence, for example with code but no OpenReview: `5.1 创新思想来源`, `5.2 未来展望`, `5.3 Q&A`.

### 创新思想来源

Explain where the core idea likely comes from:

- Directly cited prior work or method family.
- Combination of multiple research lines.
- A mismatch or limitation exposed by previous methods.
- A simple re-framing, such as changing the prediction object, training target, search space, or data construction process.

Mark inference clearly when the paper does not state the source explicitly, for example: "从论文叙述看，作者的核心想法大概率来自..."

### Review意见

If OpenReview is found, summarize:

- Reviewer praise.
- Main concerns and requested clarifications.
- Weaknesses around novelty, experiments, theory, reproducibility, or writing.
- Author rebuttal or revision response.
- For empirical papers, specifically check whether reviewers discuss benchmark correctness, data leakage, tool or dataset dependence, open-source completeness, statistical significance, compute cost, missing ablations, or novelty relative to adjacent method families.

Use `scripts/fetch_openreview_notes.py` for OpenReview forum pages before deciding whether reviews are public; the visible webpage can show only metadata while official reviews and rebuttals are loaded through the notes API. Save the JSON/Markdown extraction in the article folder when useful. Keep this section concise and neutral. If OpenReview is not found, or the OpenReview notes API returns no public official reviews, omit this subsection and do not infer reviewer opinions.

### 未来展望

Analyze concrete future directions:

- Method limitations.
- Missing experiments or assumptions.
- Scalability, data, compute, robustness, interpretability, safety, or deployment issues.
- How the idea could combine with newer or adjacent methods.

### Q&A

Write 3-5 self-asked questions about parts that are easy to misunderstand. Good questions usually target:

- Why the method works rather than a baseline.
- Why a design choice is necessary.
- What a formula or loss is really optimizing.
- What the experiments do and do not prove.
- Where the method may fail.

Answers should be short but deep, matching the user's explanatory style.

The final section may also contain:

- One paragraph restating the paper's central contribution.
- "优点" list when the paper has clear advantages.
- "缺点" or "局限性" list when limitations are clear.
- "发展方向" list when future work is obvious.

Keep criticism fair. If a limitation is inferred rather than stated, write it as an inference.

## Local Style Calibration

When the repository contains a close existing `论文理解` article, use it as a style anchor after drafting. Match behavior, not exact wording:

- The article should feel like a learning note written after deeply reading the paper, not like a compressed review.
- Prefer the user's pattern of dense bullets with short interpretive paragraphs.
- Split experiments by the paper's own research questions when the style anchor does so.
- Put personal interpretation in measured language, especially after formulas, ablations, and limitations.
- New sections such as `代码分析` and enhanced `总结` should keep the same density: concrete files, concrete mechanisms, concrete takeaways.
