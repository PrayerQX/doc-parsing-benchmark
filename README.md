# Doc Parsing Benchmark

Benchmark and deployment toolkit for document parsing models on Windows, with unified output formatting and official-rule evaluation for OmniDocBench and MDPBench.

## Scope

This repository is for local evaluation of document parsing systems rather than plain text-only OCR. It covers:

- model deployment with ASCII-only cache paths
- unified output formatting into `result.md`, `result.json`, and `meta.json`
- resilient per-page batch execution
- official scoring wrappers for OmniDocBench and MDPBench
- leaderboard summarization across multiple models

## Supported Models

- MinerU-2.5-VLM
- HunyuanOCR
- MonkeyOCR v1.5
- PaddleOCR-VL-1.5
- olmOCR2

## Supported Benchmarks

- OmniDocBench
- MDPBench

The pipeline is designed for end-to-end document parsing comparisons, including text blocks, reading order, table recovery, and formula-related metrics exposed by the official scorers.

## Repository Layout

```text
scripts/
  Set-OcrEnv.ps1
  launch_benchmark_full.cmd
  launch_benchmark_quick_resilient.cmd
  launch_benchmark_quick_lite.cmd
  run_benchmark_pipeline.py
  run_*_batch.py
  standardize_predictions.py
  score_with_official.py
  summarize_leaderboard.py
manifests/
  resilient/
    omnidocbench_sample_manifest.json
    mdpbench_sample_manifest.json
  lite/
    omnidocbench_sample_manifest.json
    mdpbench_sample_manifest.json
README_DEPLOY.md
README_BENCHMARK.md
```

## Included

- benchmark orchestration scripts
- resilient batch runners for multiple models
- built-in manifests for "resilient" and "lite" benchmark profiles
- deployment notes
- benchmark workflow notes

## Not Included

- model weights
- datasets
- upstream benchmark repositories
- local caches
- virtual environments
- benchmark raw outputs, logs, and intermediate artifacts

## Expected Local Layout

The scripts assume this repository is the workspace root. Create these folders locally as needed:

- `datasets/`
- `repos/`
- `venvs/`
- `cache/`
- `benchmark/`, `benchmark_quick_resilient/`, and `benchmark_quick_lite/`

## Benchmark Profiles

The repository exposes three ready-to-find benchmark profiles:

| Profile | Typical use | Dataset scope | Built-in manifest | Launcher | Output root |
| --- | --- | --- | --- | --- | --- |
| Full / Long | final benchmark run | full OmniDocBench + full MDPBench | not needed | `scripts/launch_benchmark_full.cmd` | `benchmark/` |
| Resilient / Medium | broader sampled comparison | 150 OmniDocBench pages + 150 MDPBench pages | `manifests/resilient/` | `scripts/launch_benchmark_quick_resilient.cmd` | `benchmark_quick_resilient/` |
| Lite / Short | fastest smoke benchmark | 80 OmniDocBench pages + 24 MDPBench pages | `manifests/lite/` | `scripts/launch_benchmark_quick_lite.cmd` | `benchmark_quick_lite/` |

Only the sampled profiles ship with versioned manifests. The full profile reads directly from the full datasets under `datasets/`.

## Quick Start

Load the shared cache environment:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
. .\scripts\Set-OcrEnv.ps1
```

Run the main benchmark pipeline:

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\run_benchmark_pipeline.py
```

Run the full / long profile:

```powershell
.\scripts\launch_benchmark_full.cmd
```

Run the resilient / medium profile:

```powershell
.\scripts\launch_benchmark_quick_resilient.cmd
```

Run the lite / short profile:

```powershell
.\scripts\launch_benchmark_quick_lite.cmd
```

If your benchmark Python is not under `.\venvs\bench\Scripts\python.exe`, set `OCR_BENCH_PYTHON` first:

```powershell
$env:OCR_BENCH_PYTHON = 'D:\path\to\python.exe'
.\scripts\launch_benchmark_quick_lite.cmd
```

For custom sampled subsets, generate your own manifest files with `scripts/sample_benchmark_manifest.py` and pass them through `scripts/run_benchmark_pipeline.py --manifest-root ... --use-sampled-manifests`.

## Unified Output Format

Each sample is normalized into:

```text
<run_root>/<sample_id>/
  result.md
  result.json
  meta.json
```

- `result.md`: markdown used by end-to-end scorers
- `result.json`: unified machine-readable prediction record
- `meta.json`: runtime metadata, success/failure state, and execution info

## Notes

- This repository is currently Windows / PowerShell oriented.
- Official dataset scorers must be cloned separately under `repos/`.
- The leaderboard `rank_score` is a local sorting score, not an official benchmark metric.
- Use each score directory as the source of truth for raw benchmark outputs.

## Documentation

- Deployment notes: [README_DEPLOY.md](README_DEPLOY.md)
- Benchmark workflow: [README_BENCHMARK.md](README_BENCHMARK.md)

## Lite Benchmark Results

`rank_score` is a local aggregate used for sorting.  
For `text_block`, `reading_order`, and `formula`, lower is better.  
For `table_teds`, higher is better.

### OmniDocBench Lite

| Rank | Model | Rank Score | Text Block | Reading Order | Table TEDS | Formula |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | HunyuanOCR | 0.9537 | 0.0534 | 0.0000 | 0.9869 | 0.1186 |
| 2 | PaddleOCR-VL | 0.9274 | 0.0416 | 0.0361 | 0.9027 | 0.1155 |
| 3 | MinerU | 0.8967 | 0.0700 | 0.0581 | 0.9189 | 0.2042 |
| 4 | MonkeyOCR | 0.4620 | 0.3862 | 0.3492 | 0.0000 | 0.4167 |

### MDPBench Lite

| Rank | Model | Rank Score | Text Block | Reading Order | Table TEDS | Formula |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | PaddleOCR-VL | 0.7690 | 0.2248 | 0.1604 | 0.7988 | 0.3375 |
| 2 | MinerU | 0.6279 | 0.3214 | 0.2697 | 0.6563 | 0.5536 |
| 3 | HunyuanOCR | 0.5390 | 0.3581 | 0.3648 | 0.3797 | 0.5006 |
| 4 | MonkeyOCR | 0.3667 | 0.5079 | 0.4351 | 0.0000 | 0.5901 |

### Summary

| Dataset | Winner | Runner-up | Notes |
| --- | --- | --- | --- |
| OmniDocBench Lite | HunyuanOCR | PaddleOCR-VL | HunyuanOCR led on the aggregate score; PaddleOCR-VL stayed very close. |
| MDPBench Lite | PaddleOCR-VL | MinerU | PaddleOCR-VL was the strongest cross-scene result on this set. |

### Takeaway

- Overall most stable: `PaddleOCR-VL`
- Best on OmniDocBench Lite: `HunyuanOCR`
- Solid second-tier overall: `MinerU`
- Weakest in this lite run: `MonkeyOCR`

## Recommended GitHub Description

`Benchmark and deployment toolkit for document parsing models with OmniDocBench and MDPBench evaluation.`
