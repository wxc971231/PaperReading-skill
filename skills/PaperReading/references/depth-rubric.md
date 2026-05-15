# Depth Rubric

Use this rubric to avoid producing an outline-level article. The target style is the user's existing `论文理解` posts: dense but readable Chinese learning notes with enough detail that the reader can reconstruct the paper's logic.

## Minimum Bar for a Normal ML Paper

A normal full paper should usually include:

- 180-320 lines of Markdown before code-analysis additions, unless the paper is genuinely short.
- 8-15 final figures when the PDF contains enough useful figures.
- Comparable figure coverage to the user's closest same-topic post when such a post exists. For figure-rich papers, 15-25 figures can be appropriate when method diagrams, prompts/templates, appendix result tables, dataset-distribution plots, or failure-analysis examples carry important meaning.
- Multiple `##` and `###` subsections under method and experiments.
- Important formulas or algorithmic definitions when the paper has them.
- At least one paragraph of interpretation after each important figure/table.
- Explicit comparison with related method families or baselines.
- Experiment discussion organized by research questions, not just a single result paragraph.
- Abstract translated faithfully from the original paper abstract, with interpretation moved out of the opening metadata block.

## Local Information Density

Match the information density of the user's established paper-reading style. Do not rely on a machine-specific path being available; use the reusable pattern below:

- Begin by defining the task in concrete input-output terms.
- Name the existing method families before the new method, and explain the typical workflow of each family.
- State the paper's critique of those families as concrete failure modes, such as accumulated error, privacy risk, data scarcity, weak variable identification, tool dependence, overfitting, or poor ranking.
- Use figures as evidence: each important figure/table should be followed by 2-4 numbered or bulleted observations with concrete numbers, metrics, baselines, or failure types.
- Prefer dense bullet learning notes over broad essay paragraphs. A paragraph should usually contain a mechanism, setting, metric, formula, data statistic, or caveat.
- When the workspace or local blog contains related posts, briefly locate the new paper relative to them.

Do not treat these as exact quotas, but if the draft is much shorter, contains only 1-3 figures, or reads like a paper abstract expanded into headings, revise before finishing.

## Paper-Type Calibration

Classify the paper before applying depth requirements:

- **Classic method / architecture papers**: prioritize mechanism clarity, notation, formula derivation, historical context, and why the design became influential. These papers may have fewer figures; do not pad the article with weak visuals just to meet a quota.
- **Dataset / benchmark papers**: prioritize data sources, annotation/generation rules, filtering, leakage checks, metrics, split design, baselines, and benchmark limitations.
- **System / agent / tool-use papers**: prioritize module boundaries, call timing, intermediate artifacts, feedback channels, error handling, and engineering tradeoffs.
- **Theory papers**: prioritize assumptions, definitions, theorem statements, proof intuition, counterexamples, and what the result does or does not guarantee.
- **Survey papers**: prioritize the taxonomy, comparison axes, coverage limits, and how the survey reframes the field.

Adjust figure count and code-analysis expectations to the paper type. A classic method paper with no official code should still be deep if the article reconstructs the algorithm and formulas carefully.

## Background Depth

The background should do more than say "this problem matters".

Include:

1. The task definition in concrete terms.
2. Existing method families and how they work at a high level.
3. The author's critique of existing methods.
4. Why the proposed idea is a plausible response to those limitations.
5. Related links or local prior articles if the user has existing related posts.
6. The paper's own motivating evidence, when it exists: diagnostic statistics, pilot experiments, failure examples, or observations that justify the method design.

When the paper sits between multiple method families, distinguish the relevant families using the paper's own taxonomy. Common examples include:

- prompt/program/tool-based systems: prompt engineering, decomposition, agents, search, self-correction, tool calls, or generated code;
- learning-based systems: synthetic data, supervised fine-tuning, preference learning, RL/post-training, representation learning, or domain-specific models;
- retrieval/data-centric systems: retrieval, reranking, data filtering, annotation, benchmark cleaning, or memory construction;
- verifier/tool/simulator-based systems: external execution, tests, simulators, judges, domain tools, humans, or other feedback sources;
- the specific failure mode the current paper targets, such as poor generalization, missing implicit constraints, hallucinated executable-but-wrong outputs, poor transfer, data noise, weak grounding, or high inference cost.

## Method Depth

Each major method component should be explained with this pattern:

```text
What it is -> why it is needed -> formalization / workflow -> intuitive explanation -> relation to prior work -> figure or example
```

When the paper contains formulas, include the important ones and explain the symbols. Do not skip formal material solely to keep the article short.

All formulas should be written in LaTeX form. Do not put mathematical expressions in Markdown code spans or code blocks. Use `\( ... \)` for inline math and `$$ ... $$` for display math.

For multi-module papers, do not compress all components into one section. Create subsections such as:

- data representation / problem definition
- data construction or annotation
- training objective
- alignment or preference learning
- inference / search / correction
- evaluation pipeline
- stage/call timing summary, when the method depends on repeated LLM/tool/verifier/retriever calls or separates offline construction from online inference

For papers with external verifiers, executable evaluation, tool feedback, simulators, or RL from verifiable rewards, method depth should additionally cover:

- verifier/tool feedback channels;
- reward components and their values/conditions;
- KL, clipping, advantage, or policy-gradient objective if central;
- curriculum stages or training phases;
- generated artifacts such as logs, code, structured files, simulator traces, predictions, retrieval outputs, or model states and how they are parsed.

Use blockquotes for your own explanatory detours, for example "可以这样理解..." or "这里和传统做法的差异在于...".

For staged agentic or tool-using systems, include an explicit input-output view. A strong method section should make clear:

- what is stored in each intermediate artifact;
- when each model/tool/verifier call happens;
- what information is passed to the next stage;
- which steps are one-time/offline and which steps are per-example/online;
- what happens when verification fails or no suitable candidate is found.

## Experiment Depth

Organize experiments around the questions they answer.

Use this section structure by default:

```markdown
# 3. 实验
## 3.1 实验设定
## 3.2 实验结果与分析
### 3.2.1 Main result / question title
### 3.2.2 Ablation / analysis title
```

`## 3.1 实验设定` should name datasets, baselines, metrics, model sizes/backbones, training budget, evaluation protocol, and fairness controls. `## 3.2 实验结果与分析` should split each major experiment into its own `### 3.2.x` subsection. Each `3.2.x` subsection must begin with one sentence describing the experiment setting before interpreting the figure/table.

For each major experiment:

1. State the question.
2. Describe data, metric, and baselines.
3. Insert the relevant figure or table.
4. Explain the observed result.
5. Add a short caveat or interpretation when useful.

For papers with ablations, include the ablations. For papers with discussion sections, include the most important discussion points if they affect the method's interpretation.

For papers with substantial appendices, do one pass over appendix headings before finalizing. Include appendix material when it changes interpretation of the paper's claims, especially:

- executable/code-pass rates versus final-task accuracy;
- robustness to model/data choices;
- partial-credit or alternative metrics;
- error-type breakdowns and failure cases;
- algorithm boxes or prompt templates that clarify the implementation;
- sensitivity analysis around central assumptions.

Avoid vague lines such as "results show the method is better" without naming the metric, baseline, and reason.

If the paper states explicit research questions such as Q1/Q2/Q3/Q4, mirror them in the article. Do not merge Q1 and Q2, or Q3 and Q4, when the user's local style anchor separates them.

## Figure Depth

Figures are part of the explanation, not decoration.

Prioritize:

- Overall framework figure.
- Core representation or algorithm figure.
- Data construction or prompt/template figure.
- Training/alignment objective figure.
- Inference/self-correction workflow figure.
- Main comparison table.
- Generalization or per-dataset result table.
- Ablation figures/tables.
- Discussion or failure-analysis figures.
- For papers whose claims depend on data quality, post-training, tools, or robustness, also consider appendix tables for benchmark cleaning, training parameters, sampling parameters, tool-free comparisons, supervised-vs-RL comparisons, ablations, and error-type distributions.

If embedded extraction only gives one image, render PDF pages to locate useful visuals, then crop high-DPI PDF regions with `scripts/crop_pdf_regions.py`. A normal paper with many figures should not end with only one image.

If only rendered pages are available, crop the relevant regions tightly. Final figures should not be uncropped full-page screenshots except for rare cases where the whole page is being discussed. Spot-check crops so they are complete and do not include captions or surrounding prose unless that text is intentionally needed.

## Code Analysis Depth

The code-analysis section should be anchored in real repository files. Before writing it:

- Inspect README and directory structure.
- Find training entry points.
- Find inference/evaluation entry points.
- Find prompt/data processing utilities.
- Find loss/alignment/model code when relevant.
- Find stored artifacts such as templates, trees, indices, checkpoints, configs, and benchmark result files when the method relies on them.
- Trace the paper's algorithm through the repository: which file builds/updates artifacts, which file consumes them, and which utility verifies outputs.

The pseudocode should reflect the repository workflow, but stay concise. It must include relatively detailed Chinese comments for the main steps so the reader can understand the intent without reading the source file line by line.

Every bullet in `## 4.2 工程技巧` must include a compact source-derived code snippet from the repository. The snippet may be shortened with `...`, but it should preserve the relevant lines and include Chinese comments explaining the engineering idea, not just the syntax.

If the official repository is only a release or inference/evaluation repo, do not fabricate a full training-code analysis. State what is present, what is missing, and reconstruct the method logic from paper formulas plus concrete repo utilities.

## Summary Depth

The summary should not only restate the contribution.

Include:

- A judgement of what is actually new.
- A judgement of what is useful but may be costly or fragile.
- A plausible source of the core idea.
- Review opinions only if OpenReview exists.
- Future directions based on method limits and experiment gaps.
- 3-5 Q&A items that resolve real conceptual confusion.

For empirical OpenReview papers, the summary should surface reviewer concerns about benchmark integrity, data leakage, novelty relative to adjacent methods, tool/dataset dependence, open-source completeness, missing ablations, compute cost, and statistical significance when those concerns appear.

For inferred opinions, mark them as inference.
