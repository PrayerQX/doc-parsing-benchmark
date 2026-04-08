# PaddleOCR-VL-1.5 对比 MinerU、HunyuanOCR、MonkeyOCR 等主流工具

这篇文档分成两层来看：

- 第一层看各产品官方怎么定义自己，避免只凭跑分下结论。
- 第二层看我在本机 `lite benchmark` 里的真实结果，看看它们在同一批样本上的表现差异。

这里的本机 benchmark 数据来自我自己的 GitHub benchmark pipeline 产物，属于快速对比版：

- `OmniDocBench Lite`: 80 页
- `MDPBench Lite`: 24 页

硬件环境：

- Windows
- `GTX 1080 Ti 11GB`

所以本文适合回答：

- 这些主流文档解析工具各自擅长什么
- 在我的这套本机 benchmark 里，`PaddleOCR-VL-1.5` 处在什么位置
- 不同场景下该优先选谁

不适合回答：

- 全量 benchmark 的最终论文结论
- 所有硬件和所有部署方式下的绝对排名

## 1. 官方定位先看一遍

### 1.1 PaddleOCR-VL-1.5

飞桨官方把 `PaddleOCR-VL` 定位为一条先进的文档解析产线。官方文档明确写到：

- `PaddleOCR-VL-1.5` 在 `OmniDocBench v1.5` 上达到 `94.5%`
- 支持异形框定位
- 在扫描、倾斜、弯折、屏幕拍摄和复杂光照场景下表现更好
- 统一入口是 `paddleocr doc_parser`
- CLI 和 Python API 都支持，生产环境还支持接推理服务

官方链接：

- <https://www.paddleocr.ai/main/version3.x/pipeline_usage/PaddleOCR-VL.html>

一句话概括：`PaddleOCR-VL-1.5` 是飞桨当前偏“高质量通用文档解析”的主力方案。

### 1.2 MinerU

MinerU 官方 GitHub README 把它定位为：

- 高精度文档解析引擎
- 面向 `LLM / RAG / Agent workflows`
- 可把 PDF、Word、PPT、图片、网页转成 `Markdown / JSON`
- 支持 `公式 -> LaTeX`、`表格 -> HTML`
- 支持扫描文档、手写、多栏、跨页表格合并
- 自带 `CLI / REST API / Docker`
- 官方还强调它的 `pipeline backend` 可以跑在 `CPU or GPU`

官方链接：

- <https://github.com/opendatalab/MinerU>
- <https://opendatalab.github.io/MinerU/>

一句话概括：`MinerU` 更像一条工程味很强、部署形态丰富的文档解析系统。

### 1.3 HunyuanOCR

腾讯官方 README 把 `HunyuanOCR` 定位为：

- 端到端 OCR 专家型 VLM
- `1B` 参数
- 支持 `100+` 语言
- 单指令、单次推理完成复杂 OCR 与文档解析
- 覆盖文本检测识别、复杂文档解析、开放域抽取、字幕提取、拍照翻译等

但官方也明确写了部署要求：

- 操作系统：`Linux`
- Python：`3.12+`
- CUDA：`12.9`
- 推荐 `vLLM`
- 显存：`20GB (for vLLM)`

官方链接：

- <https://github.com/Tencent-Hunyuan/HunyuanOCR>
- <https://hunyuan.tencent.com/>

一句话概括：`HunyuanOCR` 很像一条“单模型端到端”的 VLM 路线，能力强，但官方推荐部署门槛也更高。

### 1.4 MonkeyOCR

MonkeyOCR 官方 README 把它定位为：

- `A lightweight LMM-based Document Parsing Model`
- 支持中英文文档解析
- 本地端到端调用是 `python parse.py input_path`
- 支持输出 Markdown、布局 PDF 和中间 JSON
- 单任务模式可以单独跑 `text / formula / table`

官方 README 同时给了一个重要限制：

- 目前还不完全支持拍照文本
- 不完全支持手写内容
- 不完全支持繁体中文
- 不完全支持多语言文本

官方链接：

- <https://github.com/Yuliang-Liu/MonkeyOCR>

一句话概括：`MonkeyOCR` 更偏研究型、轻量级 LMM 文档解析路线，官方自己也明确写了当前适用范围和限制。

## 2. 从部署角度看，谁更好上手

| 工具 | 官方入口 | 官方部署特点 | 我对部署门槛的判断 |
| --- | --- | --- | --- |
| PaddleOCR-VL-1.5 | `paddleocr doc_parser` | CLI、Python API、推理服务都支持 | 最均衡，官方文档最完整，落地路径最清楚 |
| MinerU | `mineru` / `mineru-api` | CLI、REST API、Docker、CPU/GPU、多后端 | 工程集成能力最强，但系统更重 |
| HunyuanOCR | `vllm serve tencent/HunyuanOCR` | 官方推荐 Linux + CUDA 12.9 + 20GB vLLM | 本地门槛最高，不适合老显卡和 Windows 轻量部署 |
| MonkeyOCR | `python parse.py input_path` | 本地脚本、Docker、FastAPI、Windows guide | 研究体验不错，但生产一致性要自己多验证 |

如果只从“最快落地”看：

1. `PaddleOCR-VL-1.5`
2. `MinerU`
3. `MonkeyOCR`
4. `HunyuanOCR`

## 3. 我这套 lite benchmark 怎么算分

本文里用到的排序分 `rank_score` 不是官方单一指标，而是本地为了方便排序做的聚合分：

```text
((1 - text_block) + (1 - reading_order) + table_teds + (1 - formula)) / 4
```

其中：

- `rank_score` 越高越好，理论满分 `1.0`
- `text_block` 越低越好
- `reading_order` 越低越好
- `table_teds` 越高越好
- `formula` 越低越好

所以它适合做“同机、同脚本、同样本”的快速排序，不适合作为官方唯一结论。

## 4. 本机 lite benchmark 结果

### 4.1 OmniDocBench Lite

| 排名 | 模型 | Rank Score | Text Block | Reading Order | Table TEDS | Formula |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | HunyuanOCR | 0.9537 | 0.0534 | 0.0000 | 0.9869 | 0.1186 |
| 2 | PaddleOCR-VL-1.5 | 0.9274 | 0.0416 | 0.0361 | 0.9027 | 0.1155 |
| 3 | MinerU | 0.8967 | 0.0700 | 0.0581 | 0.9189 | 0.2042 |
| 4 | MonkeyOCR | 0.8818 | 0.0738 | 0.0803 | 0.8996 | 0.2183 |
| 5 | PP-StructureV3 | 0.8610 | 0.1111 | 0.0696 | 0.8234 | 0.1988 |

### 4.2 MDPBench Lite

| 排名 | 模型 | Rank Score | Text Block | Reading Order | Table TEDS | Formula |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | PaddleOCR-VL-1.5 | 0.7690 | 0.2248 | 0.1604 | 0.7988 | 0.3375 |
| 2 | PP-StructureV3 | 0.6734 | 0.3278 | 0.1538 | 0.5142 | 0.3391 |
| 3 | MinerU | 0.6279 | 0.3214 | 0.2697 | 0.6563 | 0.5536 |
| 4 | HunyuanOCR | 0.5390 | 0.3581 | 0.3648 | 0.3797 | 0.5006 |
| 5 | MonkeyOCR | 0.4869 | 0.3931 | 0.3299 | 0.2508 | 0.5800 |

### 4.3 只看四个主流工具的综合印象

如果只看 `PaddleOCR-VL-1.5 / MinerU / HunyuanOCR / MonkeyOCR` 这四个主流工具：

- `PaddleOCR-VL-1.5` 是这次本机 `lite benchmark` 的综合第一
- `HunyuanOCR` 在 `OmniDocBench Lite` 单集最强
- `MinerU` 两个数据集都不差，但都不是第一，更像稳定第二梯队
- `MonkeyOCR` 在修正接入方式后，`OmniDocBench Lite` 已经明显回升，但跨数据集稳定性依然偏弱

如果把两套 lite 数据的 `rank_score` 简单取均值，四个主流工具的本机综合排序是：

1. `PaddleOCR-VL-1.5`: `0.8482`
2. `MinerU`: `0.7623`
3. `HunyuanOCR`: `0.7464`
4. `MonkeyOCR`: `0.6844`

## 5. 怎么理解这组结果

### 5.1 PaddleOCR-VL-1.5：最稳的综合选手

它在这次本机数据里的特点很清楚：

- 两个数据集都进入前二
- `MDPBench Lite` 直接第一
- 文本块、表格、公式整体都比较均衡
- 既没有像 `HunyuanOCR` 那样在第二个数据集明显掉队，也没有像 `MinerU` 那样在公式上吃亏

如果你不想为不同文档类型准备不同路线，`PaddleOCR-VL-1.5` 是最像“默认推荐项”的。

### 5.2 MinerU：工程能力很强，但这次本机分数略低于 PaddleOCR-VL

从官方定位看，MinerU 的优势不是只拼单一页级得分，而是：

- 多格式输入
- 多种输出格式
- CPU/GPU 可跑
- CLI / REST API / Docker / SDK 齐全
- 对 RAG、Agent、私有部署很友好

而从这次本机 `lite benchmark` 看：

- 它并不差
- 但在两个数据集上都没有超过 `PaddleOCR-VL-1.5`
- `MDPBench Lite` 上和 `PaddleOCR-VL-1.5` 差距更明显

所以它更像：`工程系统能力很强，但在这次本机 lite 分数里不是第一`。

### 5.3 HunyuanOCR：单集爆发力强，但部署门槛高、跨集波动更大

`HunyuanOCR` 在 `OmniDocBench Lite` 这次是第一，这说明它在复杂文档解析上确实有很强的单集表现。

但问题也很明显：

- 到了 `MDPBench Lite` 掉到第四
- 官方推荐部署环境是 Linux + CUDA 12.9 + 20GB GPU
- 对普通本地机和 Windows 用户不够友好

所以它更像：

- 你愿意接受更高部署门槛
- 想要一条端到端单模型路线
- 并且更关注特定复杂文档集上的强表现

那就值得试。

但如果你更在意“总体稳、好部署、通用性”，这次还是 `PaddleOCR-VL-1.5` 更合适。

### 5.4 MonkeyOCR：修正接入后明显回升，但跨场景稳定性仍然不足

这块需要单独说清楚。

官方 README 里，MonkeyOCR 的介绍和公开 benchmark 很强：

- 官方强调它是轻量级 LMM 文档解析路线
- 官方 end-to-end parse 能输出 markdown、tables、formulas 和 middle json
- 官方自己的 README 里也给了和多种方法的 benchmark 对比

但在我这次本机 benchmark 里，`MonkeyOCR` 一开始因为接入方式只走了 text-only 路线，结果被明显低估。修正为完整 parse 路线后，结果有了明显改善，尤其：

- `OmniDocBench Lite` 的 `Table TEDS` 从 `0.0000` 提升到了 `0.8996`
- `OmniDocBench Lite` 的 `rank_score` 从 `0.4620` 提升到了 `0.8818`
- 它在 `OmniDocBench Lite` 上已经超过了 `PP-StructureV3`

这里我更倾向于做一个谨慎解释：

- 之前那组 0 分表格结果，根因在于 repo 接入方式，而不是模型天生没有表格能力
- 修正后，它的结构化恢复能力已经能在 `OmniDocBench Lite` 上体现出来
- 但它在 `MDPBench Lite` 上仍然只拿到 `0.4869`，而且 `24` 页里有 `1` 页失败

所以更合理的表述是：

- `MonkeyOCR` 不是“没有表格能力”，之前是接入方式有误
- 修正接法后，它在结构化文档上的潜力已经体现出来
- 但在更复杂、更多语言、更偏拍照场景的 `MDPBench Lite` 上，稳定性仍然明显不如 `PaddleOCR-VL-1.5`

## 6. 这些工具各自更适合什么场景

### 6.1 如果你想要一个默认推荐项

选 `PaddleOCR-VL-1.5`。

适合：

- 想要综合效果最稳
- 关注表格、公式、复杂版面
- 希望同时兼顾部署清晰度和最终质量
- 做 PDF 转 Markdown、文档解析 benchmark、复杂业务文档处理

### 6.2 如果你更在意工程系统能力

选 `MinerU`。

适合：

- 私有部署
- RAG / Agent 流水线
- 多格式输入
- 需要 API、CLI、Docker、CPU/GPU 多种形态
- 更看重“整条解析系统”而不是只盯住页级分数

### 6.3 如果你接受更高部署门槛，想尝试端到端单模型路线

选 `HunyuanOCR`。

适合：

- Linux + 较新 GPU 环境
- 多语言复杂文档
- 愿意围绕 vLLM 做部署
- 想用单模型做更完整的 OCR / 文档解析任务

### 6.4 如果你是在做研究验证或探索轻量 LMM 路线

可以试 `MonkeyOCR`。

适合：

- 中英文 PDF 研究验证
- 想研究轻量 LMM 文档解析
- 对 parse.py、middle json、layout pdf 这类产物感兴趣

但如果你要直接拿它做稳定生产基线，这次本机结果并不支持我给出激进推荐。

## 7. 一句话结论

如果只给一句结论：

- 想要 `综合效果 + 部署清晰 + 实测最稳`，优先选 `PaddleOCR-VL-1.5`
- 想要 `工程系统能力和私有部署形态`，看 `MinerU`
- 想要 `单模型端到端 + 多语言强项`，可以重点试 `HunyuanOCR`
- 想要 `研究型轻量 LMM 路线`，可以看 `MonkeyOCR`；但如果要直接做稳定生产基线，它目前仍然不如 `PaddleOCR-VL-1.5`

## 8. 参考资料

- PaddleOCR-VL 官方文档: <https://www.paddleocr.ai/main/version3.x/pipeline_usage/PaddleOCR-VL.html>
- MinerU 官方 GitHub: <https://github.com/opendatalab/MinerU>
- MinerU 官方文档站: <https://opendatalab.github.io/MinerU/>
- HunyuanOCR 官方 GitHub: <https://github.com/Tencent-Hunyuan/HunyuanOCR>
- Hunyuan 官方站: <https://hunyuan.tencent.com/>
- MonkeyOCR 官方 GitHub: <https://github.com/Yuliang-Liu/MonkeyOCR>

## 9. 附注

本文里的 benchmark 数据来自我自己的本地 benchmark pipeline，属于 `lite` 版本快速对比结果。  
因此它更适合做工程选型和第一轮筛选，不适合替代全量 benchmark 的最终论文级结论。
