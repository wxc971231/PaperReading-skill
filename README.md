# PaperReading

这个仓库用于存放我的 Codex 论文阅读工作流 skill：`PaperReading`。给定论文标题、链接、arXiv/OpenReview 页面、DOI 或本地 PDF，让 Codex 自动完成论文检索、PDF 下载、图表抽取、代码仓库分析，并生成一份适合 Typora 阅读和后续整理的中文论文解读 Markdown。

## 目录结构

```text
skills/
  PaperReading/
    SKILL.md                 # skill 主说明
    references/              # 写作风格、输出规范、深度要求
    scripts/                 # PDF 图表检测、抽取、裁剪脚本
    agents/                  # 可选 agent 配置
```

## PaperReading 能做什么

- 搜索论文的最新公开版本，优先使用 arXiv 最新版本、PMLR/会议正式版、OpenReview 或作者主页中更新的 PDF。
- 在项目根目录的 `output/` 下创建以论文标题命名的输出文件夹。
- 保存原始论文为 `paper.pdf`。
- 自动抽取论文中的图、表，并由 Codex 自主完成完整性审核与迭代重裁，保证最终使用的图片不缺轴标签、图例、表头、关键行列或多面板内容。
- 搜索 OpenReview，若有公开评审，则在文章中总结 reviewer 关注点和作者 rebuttal；若没有公开记录，也会在固定信息块中标明未找到。
- 搜索官方代码仓库，若存在则克隆到输出文件夹的 `code/` 目录，并在文章中写代码分析。
- 按固定格式生成高信息密度中文论文解读：摘要严格翻译原文，方法部分拆清机制和公式，实验部分按设定与逐实验分析展开。

## 工作流程

1. **输入论文信息**

   用户给 Codex 一个论文标题、链接、arXiv ID、OpenReview 页面、DOI 或 PDF 路径。

2. **确认最新版本**

   Codex 会搜索论文来源，比较 arXiv、会议页面、OpenReview、项目页和作者主页，尽量使用最新公开版本。若版本不一致，会在文章开头注明使用的版本。

3. **创建文章目录**

   在项目根目录的 `output/` 下创建一个以论文标题命名的文件夹，例如：

   ```text
   output/
     OptMATH A Scalable Bidirectional Data Synthesis Framework for Optimization Modeling/
       paper.pdf
       img/
       code/
       OptMATH A Scalable Bidirectional Data Synthesis Framework for Optimization Modeling.md
   ```

4. **抽取和审核图表**

   skill 会先运行自动检测脚本生成候选图表和 contact sheet，再由 Codex 对照论文页面逐张审核。自动抽取不完整时，Codex 会自行用高 DPI PDF 区域裁剪重新生成最终图片，并再次审核，直到最终 Markdown 引用的图表足够完整。

5. **阅读论文和附录**

   Codex 会读取正文、实验、附录、prompt template、算法框和表格，避免只写摘要级总结。

6. **分析代码仓库**

   如果找到官方代码，Codex 会克隆仓库并阅读 README、目录结构、核心 pipeline、评测脚本、数据处理逻辑等，再写代码分析。`4.1 伪代码` 和 `4.2 工程技巧` 的代码块都需要相对详细的中文注释；`4.2` 每个工程技巧都必须配一个来自源码仓库的精简代码片段。

7. **生成 Markdown**

   最终输出是 Typora 友好的中文 Markdown，使用相对图片路径：

   ```markdown
   ![图片说明](img/img_001.png)
   ```

   不包含 Hexo front matter、HTML 图片标签或绝对博客路径。

8. **最终检查**

   Codex 会检查输出目录、PDF、图片引用、代码目录、OpenReview 搜索结果、Markdown 格式和最终图表完整性。

## 生成文章格式

每篇论文会生成一个独立文件夹，文件夹名称使用论文最新版本的正式标题，并移除 Windows 文件名不支持的字符：

```text
output/
  <论文标题>/
    <论文标题>.md
    paper.pdf
    img/
      img_001.png
      img_002.png
      ...
      audit.md
    code/                 # 仅当找到官方或明确关联的开源仓库时创建
```

Markdown 文件直接面向 Typora 阅读，不包含 Hexo、Jekyll、YAML front matter 或 HTML 图片标签。文章开头使用论文信息块：

```markdown
- 文章链接：[Paper Title](...)
- 作者：Author A, Author B, ...
- 机构：University / Lab / Company
- 代码：[owner/repo](...)
- 项目页：[Project Name](...)
- OpenReview：[Paper Title](...)
- 发表：ICML 2025
- 领域：...
- 一句话总结：...
-------
- 摘要：...
```

信息块的 key 和顺序固定。缺失的信息不删除行，而是写清楚状态，例如 `代码：无公开代码`、`项目页：无独立项目页`、`OpenReview：未找到公开记录`。如果版本来源需要说明，写在 `文章链接`、`发表` 或正文开头的短说明里，不额外增加 `版本` key。

正文默认采用下面的结构：

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

其中：

- 如果没有官方代码仓库，会省略 `代码分析`，并把 `总结` 调整为第 4 节。
- 如果没有公开 OpenReview，会省略 `Review意见`，不编造 reviewer 观点。
- 摘要必须严格按论文 abstract 做中文翻译，不把个人理解、代码信息或 reviewer 观点混进去。
- `# 2. 本文方法` 是解释密度最高的部分：按问题定义、核心机制、公式、训练/推理流程、与旧方法差异拆成多个小节；论文中有助于理解的公式都用 LaTeX 写入正文，禁止把公式放进 Markdown 代码片。
- `# 3. 实验` 固定拆为 `3.1 实验设定` 和 `3.2 实验结果与分析`。`3.1` 说明数据集、baseline、指标、模型规模、训练/评测协议和公平性控制；`3.2` 每个主要实验单独起 `3.2.x` 小节，并先用一句话说明实验设定，再解释图表和结论。
- `# 4. 代码分析` 仅在存在官方或明确关联的代码仓库时出现。`4.1 伪代码` 用中文注释解释主要算法步骤；`4.2 工程技巧` 每条都要附一个从源码仓库提炼或截取的精简代码片段，并在代码块内加入中文注释说明工程意图。
- 文章会尽量包含公式、图表解释、实验解读、局限分析和 Q&A，而不是只写摘要级概括。

图片统一使用相对路径，并放在解释它的段落附近：

```markdown
![图示说明](img/img_001.png)
```

如果图片、公式、表格、引用或代码块属于某个列表项，需要整体缩进 4 个空格，让 Typora 把它们渲染为该列表项的从属内容。

最终 `img/` 下的 `img_*.png` 是文章实际引用的图片；候选图、原始页面渲染和工具输出会放在 `img/candidates/`、`img/raw/` 或其他子目录中，不直接作为正文图片引用。

`img/audit.md` 是图表审核记录，用于说明每张最终图片来自 PDF 第几页、对应哪张图/表、是否经过重裁、审核是否通过。它不一定会在正文中引用，但用于保证 example 和最终文章可追溯。

生成完成后，Codex 会运行文章目录验证脚本：

```bash
python skills/PaperReading/scripts/verify_article_folder.py output/<论文标题>
```

## 部署方式

直接让 Codex 根据 skill 自动安装所需依赖，例如：

```text
把 skills/PaperReading 这个 skill 提到的工具都安装到 conda base 环境里。
```

Codex 会读取 `skills/PaperReading/SKILL.md` 和相关脚本，识别需要的工具，并按当前机器环境安装。常用依赖包括：

- Python 包：`pymupdf`、`pillow`、`pdfplumber`、`camelot-py`、`tabula-py`
- Java 环境：OpenJDK
- PDF 图表工具：PDFFigures2
- 可选工具：Ghostscript、Marker、Docling

在 Windows + Conda 环境中，推荐让 Codex 自己完成安装和验证，因为不同工具对 Python 版本、Java、Ghostscript、OpenCV 的要求不完全一致。安装后可以让 Codex 运行一次导入检查和 PDFFigures2 命令检查，确认图表抽取链路可用。

仓库内提供的辅助脚本包括：

- `resolve_paper_source.py`：根据论文标题或 arXiv ID 生成第一轮论文来源 JSON。
- `detect_pdf_visuals.py`：检测 PDF 中的图表候选并生成 contact sheet。
- `crop_pdf_regions.py`：从 PDF 页面中高 DPI 裁剪最终图表。
- `extract_pdf_figures.py`：抽取嵌入图像或渲染页面作为 fallback。
- `verify_article_folder.py`：检查最终文章目录结构、图片引用和常见格式问题。

## 使用示例

```text
现在用 PaperReading skill 处理一下 OptMATH: A Scalable Bidirectional Data Synthesis Framework for Optimization Modeling 这篇文章。
```

Codex 会自动完成检索、下载、抽图、读论文、读代码、写文章和检查产物。
