# OCR Benchmark Pipeline

Windows-first local deployment and benchmark tooling for multiple OCR / OCR-VLM models:

- MinerU-2.5-VLM
- HunyuanOCR
- MonkeyOCR v1.5
- PaddleOCR-VL-1.5
- olmOCR2

The repository focuses on three things:

1. local model deployment with ASCII-only cache paths
2. unified prediction formatting into `result.md / result.json / meta.json`
3. official-rule scoring for OmniDocBench and MDPBench, plus leaderboard summarization

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

## What Is Included

- benchmark orchestration scripts
- resilient per-page batch runners
- sample manifests used for the lite benchmark
- deployment and benchmark notes

## What Is Not Included

- model weights
- datasets
- local caches
- virtual environments
- upstream scorer repos
- benchmark raw outputs and logs

## Expected Local Layout

The scripts assume this repository is the workspace root and that the following folders are created locally when needed:

- `datasets/`
- `repos/`
- `venvs/`
- `cache/`
- `benchmark*` output folders

## Quick Start

Load the shared local cache environment:

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

If your benchmark Python is not under `.\venvs\bench\Scripts\python.exe`, set `OCR_BENCH_PYTHON` before running the launcher:

```powershell
$env:OCR_BENCH_PYTHON = 'D:\path\to\python.exe'
.\scripts\launch_benchmark_quick_lite.cmd
```

## Docs

- Deployment notes: [README_DEPLOY.md](README_DEPLOY.md)
- Benchmark workflow: [README_BENCHMARK.md](README_BENCHMARK.md)

## Notes

- The current scripts are Windows / PowerShell oriented.
- Official dataset scorers must be cloned separately under `repos/`.
- The leaderboard `rank_score` is only a local sort key; use each score directory as the source of truth.
