# PaddleOCR-VL-1.5 部署记录与 PP-StructureV3 Lite 对比

这篇文章分两部分：

- 一部分是基于飞桨官方文档，对 `PaddleOCR-VL-1.5` 和 `PP-StructureV3` 的定位、调用方式做一个简明梳理。
- 另一部分是基于我在本机完成的 `lite benchmark` 实测，对两者的效果、速度、适用场景做一个落地对比。

## 1. 先看飞桨官方怎么定义这两个方案

### 1.1 PaddleOCR-VL-1.5

根据飞桨官方 `PaddleOCR-VL` 使用文档，`PaddleOCR-VL` 的命令行入口就是：

```bash
paddleocr doc_parser -i ./demo.png
```

官方文档同时说明：

- `doc_parser` 支持直接输入图片或 PDF。
- `pipeline_version` 当前可选 `v1` 和 `v1.5`，默认就是 `v1.5`。
- 结果可以保存为 Markdown。
- `max_new_tokens`、`max_pixels`、`use_layout_detection` 等参数可以控制文档解析行为。

这意味着 `PaddleOCR-VL-1.5` 更像一条偏 VLM 的通用文档解析产线，不只是传统 OCR。

官方资料：

- PaddleOCR-VL 使用教程: <https://www.paddleocr.ai/main/version3.x/pipeline_usage/PaddleOCR-VL.html>

### 1.2 PP-StructureV3

根据飞桨官方 `PP-StructureV3` 说明和使用文档，它是一条通用文档解析产线，重点增强了：

- 版面检测
- 表格识别
- 公式识别
- 图表理解
- 阅读顺序恢复
- Markdown 转换

官方命令行入口是：

```bash
paddleocr pp_structurev3 -i ./demo.png
```

官方文档还明确说明：

- 支持输出 `json`、可视化图片和 `markdown`
- 支持 `save_to_markdown()`
- 支持 `default / full / lightweight` 等不同配置形态
- 支持按场景替换模块配置，做更轻量或更高精度的部署

这说明 `PP-StructureV3` 更像一条工程化的文档解析 pipeline。

官方资料：

- PP-StructureV3 使用教程: <https://www.paddleocr.ai/latest/version3.x/pipeline_usage/PP-StructureV3.html>
- PP-StructureV3 简介: <https://www.paddleocr.ai/main/version3.x/algorithm/PP-StructureV3/PP-StructureV3.html>

## 2. 我在本机是怎么部署 PaddleOCR-VL-1.5 的

这次本地环境是 Windows，机器里用户名路径带中文。为了避免模型缓存落进中文目录导致下载或推理异常，我先把缓存路径统一改到纯英文目录。

### 2.1 统一缓存目录

我使用的环境脚本会把以下目录全部固定到 `D:\OCR\cache\...`：

- `HF_HOME`
- `HUGGINGFACE_HUB_CACHE`
- `TRANSFORMERS_CACHE`
- `PADDLE_HOME`
- `PADDLE_PDX_CACHE_HOME`
- `TMP`
- `TEMP`

同时额外设置：

```powershell
$env:HF_HUB_DISABLE_XET = "1"
```

这样做的原因是，前面下载 `PaddleOCR-VL-1.5` 时，Hugging Face 的 Xet 分片下载在本机上出现过异常，禁用后更稳。

### 2.2 独立虚拟环境

我给 `PaddleOCR-VL-1.5` 单独放了一个环境：

```powershell
& D:\OCR\venvs\paddlevl\Scripts\Activate.ps1
```

### 2.3 实际 smoke test 命令

本机验证时，实际使用的命令如下：

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
. D:\OCR\scripts\Set-OcrEnv.ps1
& D:\OCR\venvs\paddlevl\Scripts\Activate.ps1
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'
paddleocr doc_parser -i D:\OCR\samples\smoke_input.png --save_path D:\OCR\logs\paddlevl_smoke --pipeline_version v1.5 --device gpu:0 --max_new_tokens 256
```

这里有两个关键点：

- `--pipeline_version v1.5` 明确指定 `PaddleOCR-VL-1.5`
- `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` 能减少本机环境下的兼容问题

### 2.4 为什么这套部署方式靠谱

因为它不是“装成功就算完成”，而是已经在本机做过真实 smoke test，且后续 benchmark 里也沿用了同一条官方 CLI 调用链路。

一句话概括，这次 `PaddleOCR-VL-1.5` 的部署逻辑就是：

1. 用英文缓存目录避开中文路径问题
2. 用独立虚拟环境隔离依赖
3. 用官方 `paddleocr doc_parser` 入口跑通
4. 再接进统一 benchmark pipeline

## 3. 这次 lite benchmark 是怎么跑的

这次对比不是全量长跑，而是本地 `lite benchmark`：

- `OmniDocBench Lite`: 80 页
- `MDPBench Lite`: 24 页

硬件环境是：

- GPU: `GTX 1080 Ti 11GB`
- OS: Windows

需要注意的是，这里的 `rank_score` 不是官方单一指标，而是本地为了便于排序做的聚合分数：

```text
((1 - text_block) + (1 - reading_order) + table_teds + (1 - formula)) / 4
```

其中：

- `rank_score` 越高越好，理论满分 `1.0`
- `text_block` 越低越好，理想值 `0.0`
- `reading_order` 越低越好，理想值 `0.0`
- `table_teds` 越高越好，理想值 `1.0`
- `formula` 越低越好，理想值 `0.0`

所以这组表更适合回答“哪一个在本机这套 lite benchmark 里更强”，而不是替代官方完整 benchmark 论文结论。

## 4. Lite 数据集实测对比

### 4.1 OmniDocBench Lite

| 模型 | Rank Score | Text Block | Reading Order | Table TEDS | Formula | 成功率 | 平均单页耗时 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| PaddleOCR-VL-1.5 | 0.9274 | 0.0416 | 0.0361 | 0.9027 | 0.1155 | 80/80 | 73.11s |
| PP-StructureV3 | 0.8610 | 0.1111 | 0.0696 | 0.8234 | 0.1988 | 80/80 | 40.17s |

### 4.2 MDPBench Lite

| 模型 | Rank Score | Text Block | Reading Order | Table TEDS | Formula | 成功率 | 平均单页耗时 |
| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| PaddleOCR-VL-1.5 | 0.7690 | 0.2248 | 0.1604 | 0.7988 | 0.3375 | 24/24 | 35.39s |
| PP-StructureV3 | 0.6734 | 0.3278 | 0.1538 | 0.5142 | 0.3391 | 23/24 | 37.04s |

### 4.3 直接结论

从这次本机 `lite benchmark` 看：

- `PaddleOCR-VL-1.5` 在两个数据集上都赢了
- `PP-StructureV3` 在 `OmniDocBench Lite` 上速度明显更快
- `PP-StructureV3` 在 `MDPBench Lite` 上阅读顺序略优一点，但表格能力差距比较明显
- `PaddleOCR-VL-1.5` 的综合精度和跨场景稳定性更好

补充一句很重要：

- 以上表格是这两条路线的正面对比，数值本身没有变化
- 但在包含全部模型的最新 `lite leaderboard` 里，随着 `MonkeyOCR` 改成完整 parse 接入后重新计分，`PP-StructureV3` 在 `OmniDocBench Lite` 的总榜位置已经从原先的第 `4` 变成了第 `5`
- 在 `MDPBench Lite` 里，`PP-StructureV3` 仍然是第 `2`

也就是说：

- 如果只比较 `PaddleOCR-VL-1.5 vs PP-StructureV3`，这篇里的主结论不变
- 如果放回五模型总榜里看，`PP-StructureV3` 在 `OmniDocBench Lite` 的相对位置已经被修正后的 `MonkeyOCR` 反超

## 5. 这两个方案分别有什么优缺点

### 5.1 PaddleOCR-VL-1.5 的优点

- 综合效果更强，这次两个 lite 数据集都领先
- 文本块恢复最好，复杂页面内容还原更稳
- 表格结构恢复明显更强
- 公式恢复整体更稳
- 在跨场景文档上泛化更好

### 5.2 PaddleOCR-VL-1.5 的缺点

- 更吃资源
- 在这台 `1080 Ti 11GB` 上明显更慢
- 更像一条偏 VLM 的文档解析路线，部署和推理成本都更高

### 5.3 PP-StructureV3 的优点

- 更偏工程化 pipeline，结构化思路更清晰
- 官方本身就支持 `default / full / lightweight` 多配置形态
- 更容易根据硬件和场景做轻量化调节
- 在本机 `OmniDocBench Lite` 上速度明显快于 `PaddleOCR-VL-1.5`
- 对只需要文档结构解析、Markdown 导出和工程集成的场景比较友好

### 5.4 PP-StructureV3 的缺点

- 这次本机 benchmark 中综合精度不如 `PaddleOCR-VL-1.5`
- 表格指标差距较明显，尤其在 `MDPBench Lite`
- 跨复杂场景时整体恢复质量仍弱一档
- 这次 `MDPBench Lite` 有 `1` 页失败，不如 `PaddleOCR-VL-1.5` 全成功稳定

## 6. 更适合什么场景

### 6.1 更适合选 PaddleOCR-VL-1.5 的场景

- 你最关心最终解析质量
- 文档里表格、公式、复杂版面较多
- 你想做更高质量的 PDF 转 Markdown
- 你需要跨场景稳定性，而不是只在单一版式里表现好
- 你在做 benchmark、评测、研究型项目

一句话概括：`PaddleOCR-VL-1.5` 更适合“效果优先”。

### 6.2 更适合选 PP-StructureV3 的场景

- 你更关注工程落地而不是极限精度
- 你希望用更明确的 pipeline 方式做二次集成
- 你需要可调的轻量化配置
- 你更看重解析速度和部署灵活性
- 你的任务重点是版面解析、结构提取、Markdown 导出，而不是追求最强的表格和公式恢复

一句话概括：`PP-StructureV3` 更适合“工程优先”。

## 7. 最后怎么选

如果只给一个简单建议：

- 要综合效果，优先选 `PaddleOCR-VL-1.5`
- 要工程可控性、轻量化和更快的本地 pipeline，优先看 `PP-StructureV3`

如果你的任务是复杂文档高质量转写，我会更推荐 `PaddleOCR-VL-1.5`。  
如果你的任务是生产环境里的结构化解析和工程接入，`PP-StructureV3` 往往更顺手。

## 8. 参考资料

- 飞桨官方 PaddleOCR-VL 使用教程: <https://www.paddleocr.ai/main/version3.x/pipeline_usage/PaddleOCR-VL.html>
- 飞桨官方 PP-StructureV3 使用教程: <https://www.paddleocr.ai/latest/version3.x/pipeline_usage/PP-StructureV3.html>
- 飞桨官方 PP-StructureV3 简介: <https://www.paddleocr.ai/main/version3.x/algorithm/PP-StructureV3/PP-StructureV3.html>

## 9. 附注

本文中的部署命令和 benchmark 结果，来自同一台本地机器的实际运行记录，不是只根据官方文档推测。  
其中 `lite benchmark` 的样本量为 `OmniDocBench 80 页 + MDPBench 24 页`，因此它适合做快速对比，不适合替代完整全量 benchmark 结论。
