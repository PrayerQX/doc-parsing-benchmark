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
  run_benchmark_pipeline.py
  run_*_batch.py
  standardize_predictions.py
  score_with_official.py
  summarize_leaderboard.py
manifests/
  lite/
    omnidocbench_sample_manifest.json
    mdpbench_sample_manifest.json
README_DEPLOY.md
README_BENCHMARK.md
```

## Included

- benchmark orchestration scripts
- resilient batch runners for multiple models
- sample manifests for a smaller "lite" benchmark profile
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
- `benchmark/`, `benchmark_quick/`, or other output roots

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

Run the lite benchmark profile:

```powershell
.\scripts\launch_benchmark_quick_lite.cmd
```

If your benchmark Python is not under `.\venvs\bench\Scripts\python.exe`, set `OCR_BENCH_PYTHON` first:

```powershell
$env:OCR_BENCH_PYTHON = 'D:\path\to\python.exe'
.\scripts\launch_benchmark_quick_lite.cmd
```

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

## Recommended GitHub Description

`Benchmark and deployment toolkit for document parsing models with OmniDocBench and MDPBench evaluation.`
