# Local Density Prompts

Use these prompts to match the user's preferred paper-reading style without
depending on any machine-specific blog path.

## Information Density

- Start from a concrete task definition: input, expected output, and why the task is hard.
- Name existing method families before the proposed method, and explain their workflows briefly.
- State the paper's critique as concrete failure modes, not as generic "limitations".
- Prefer dense bullet-style learning notes. Each paragraph should contain at least one concrete mechanism, setting, metric, number, formula, dataset, baseline, or caveat.
- After important figures/tables, write 2-4 concrete observations. Avoid "结果说明方法有效" without naming the evidence.
- When the topic matches previous local posts, position the paper relative to them, e.g. "与 ORLM / OptiMUS / OptiTree 相比...".

## Method Section

`# 2. 本文方法` should be the densest explanatory section.

- Split it into multiple `## 2.x` subsections when the paper has multiple mechanisms.
- Explain each component with: what it is -> why it is needed -> formal definition / workflow -> intuition -> relation to prior methods.
- Include paper formulas in LaTeX unless they are incidental. Prefer display math for objectives, scaling laws, probability factorizations, rewards, or update rules.
- Do not put formulas in Markdown code spans or code blocks. Use `\( ... \)` for inline math and `$$ ... $$` for display math.
- If a figure, formula, table, blockquote, or code block belongs to a preceding list item, indent it by 4 spaces so Typora treats it as subordinate content.

## Abstract

The `摘要` field is a faithful Chinese translation of the original paper abstract.

- Preserve the original sentence order and claim order.
- Preserve qualifiers such as "may", "can", "under", "up to", "we find", "suggest".
- Do not add code links, reviewer opinions, project status, or personal interpretation.
- Put commentary and judgement in later sections.

## Experiments

`# 3. 实验` must use this structure:

```markdown
## 3.1 实验设定
## 3.2 实验结果与分析
### 3.2.1 ...
### 3.2.2 ...
```

`## 3.1 实验设定` should cover:

- datasets and splits;
- baselines;
- metrics;
- model sizes/backbones;
- training/evaluation protocol;
- compute budget or epoch/token budget;
- fairness controls and caveats.

Each `### 3.2.x` experiment subsection should:

1. start with a one-sentence setting, e.g. "实验设定：在 X 数据集上，以 Y 为 baseline，用 Z 指标比较...";
2. insert the relevant figure/table if useful;
3. explain the result with concrete numbers or trends;
4. state what this experiment proves and what it does not prove.

## Code Analysis

`## 4.1 伪代码` should include Chinese comments for the main algorithmic steps, such as input preparation, objective construction, training/inference update, and output. The comments should explain intent rather than restating syntax.

`## 4.2 工程技巧` should not be a file list. Each bullet should explain one reusable implementation choice and include a short source-derived code snippet. Every snippet should include Chinese comments that explain why the implementation detail matters.
