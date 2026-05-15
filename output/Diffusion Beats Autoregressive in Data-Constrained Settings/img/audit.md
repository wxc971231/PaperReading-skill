# 图表抽取审核记录

论文：Diffusion Beats Autoregressive in Data-Constrained Settings

审核时间：2026-05-15

## 抽取流程

1. 使用 PDFFigures2 抽取论文图表，得到 Figure 1、3、4、5、7、9 与 Table 1、2、5 等候选。
2. 使用 `detect_pdf_visuals.py` 结合 PDF caption、图形区域、表格区域与 PDFFigures2 metadata 生成 13 个候选图表，并输出 contact sheet。
3. 人工目视审核 contact sheet，检查是否存在缺轴标签、图例、表头、关键行列、多面板内容缺失或误裁。
4. 对不完整图表重新从 PDF 页面裁剪，并覆盖为最终文章使用图。

## 最终采用图表

| 文件 | 来源 | 审核结论 |
| --- | --- | --- |
| `img_001.png` | Figure 1 | 完整。左右两个 Pareto frontier 子图、坐标轴、图例、临界计算点和 Chinchilla-optimal 标注均保留。 |
| `img_002.png` | Figure 2 重裁 | 完整。原候选只裁到右侧 diffusion contour，已从第 6 页重裁，保留 AR 与 diffusion 两个 contour、坐标轴、星标和图例。 |
| `img_003.png` | Figure 3 | 完整。三联图均保留，可读性足够支撑“重复数据价值衰减”分析。 |
| `img_004.png` | Figure 6 重裁 | 完整。原候选只包含左侧 heatmap，已从第 9 页重裁，保留 heatmap 与右侧 critical compute curve。 |
| `img_005.png` | Figure 5 | 完整。左右两个预测曲线子图、虚线、坐标轴和图例均保留。 |
| `img_006.png` | Table 2 | 完整。表头、所有 benchmark 行、AR / flop-matched AR / Diffusion 三列和加粗结果均保留。 |
| `img_007.png` | Figure 7 | 完整。不同 token ordering 数量的 AR 曲线和 diffusion best loss 虚线均保留。 |

## 候选图表处理说明

- `candidate_002.png`：只包含 Figure 2 右半边，判定不完整，已重裁为 `img_002.png`。
- `candidate_007.png`：只包含 Figure 6 左侧 heatmap，判定不完整，已重裁为 `img_004.png`。
- `candidate_009.png`：是 Table 2 下方正文说明，不作为表格图使用。
- `candidate_013.png`：Table 5 模型结构表很长，虽然 PDFFigures2 抽取完整，但文章主线不依赖该表，未纳入正文。
- `page6_full.png` 与 `page9_full.png`：用于审核和定位重裁区域，不作为最终正文图片。

## 结论

最终正文使用的 7 张图表均已通过完整性审核。对自动抽取不完整的多面板图，已完成自主重裁与复核，最终版本未发现缺少关键轴标签、图例、表头、关键行列或多面板内容的问题。
