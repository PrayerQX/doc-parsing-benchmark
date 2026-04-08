# Benchmark Workflow

Note: the original local workspace root was `D:\OCR`. In this repository, replace that path with your own repo root.

## Local Assets

Datasets:

- `D:\OCR\datasets\omnidocbench`
- `D:\OCR\datasets\mdpbench`

Official scorers:

- `D:\OCR\repos\OmniDocBench-main`
- `D:\OCR\repos\MultimodalOCR-main\MDPBench`

Benchmark venv:

- `D:\OCR\venvs\bench`

Shared benchmark folders:

- `D:\OCR\benchmark\runs`
- `D:\OCR\benchmark\exports`
- `D:\OCR\benchmark\scores`
- `D:\OCR\benchmark\inputs`
- `D:\OCR\benchmark\raw`
- `D:\OCR\benchmark\leaderboards`

## Standard Output Format

Each sample is normalized into:

```text
<run_root>/<sample_id>/
  result.md
  result.json
  meta.json
```

Meaning:

- `result.md`: markdown used by official end-to-end scorers
- `result.json`: unified machine-readable record
- `meta.json`: runtime and execution metadata

## Supported Adapters

- `mineru`
- `hunyuanocr`
- `monkeyocr`
- `paddlevl`
- `olmocr2`
- `markdown`

## Build Dataset Manifest

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
. D:\OCR\scripts\Set-OcrEnv.ps1

D:\OCR\venvs\bench\Scripts\python.exe D:\OCR\scripts\build_benchmark_manifest.py `
  --dataset-name omnidocbench `
  --dataset-root D:\OCR\datasets\omnidocbench `
  --output D:\OCR\benchmark\omnidocbench_manifest.json
```

## Standardize Raw Model Outputs

Example for a markdown-style model output folder:

```powershell
D:\OCR\venvs\bench\Scripts\python.exe D:\OCR\scripts\standardize_predictions.py `
  --dataset-name mdpbench `
  --dataset-root D:\OCR\datasets\mdpbench `
  --model-name mineru `
  --adapter mineru `
  --input-root D:\OCR\raw\mdpbench\mineru `
  --pattern **\*.md `
  --output-root D:\OCR\benchmark\runs\mdpbench_mineru
```

Notes:

- file stem must match dataset sample id
- standardized run metadata is saved to `run_manifest.json`

## Export To Official Markdown Folder

```powershell
D:\OCR\venvs\bench\Scripts\python.exe D:\OCR\scripts\export_predictions_to_official.py `
  --run-root D:\OCR\benchmark\runs\mdpbench_mineru `
  --export-dir D:\OCR\benchmark\exports\mdpbench_mineru
```

## Score With Official Rules

### OmniDocBench

```powershell
D:\OCR\venvs\bench\Scripts\python.exe D:\OCR\scripts\score_with_official.py `
  --dataset-name omnidocbench `
  --dataset-root D:\OCR\datasets\omnidocbench `
  --run-root D:\OCR\benchmark\runs\omnidocbench_mineru `
  --export-dir D:\OCR\benchmark\exports\omnidocbench_mineru `
  --result-root D:\OCR\benchmark\scores\omnidocbench_mineru `
  --scorer-root D:\OCR\repos\OmniDocBench-main `
  --python-exe D:\OCR\venvs\bench\Scripts\python.exe
```

### MDPBench

```powershell
D:\OCR\venvs\bench\Scripts\python.exe D:\OCR\scripts\score_with_official.py `
  --dataset-name mdpbench `
  --dataset-root D:\OCR\datasets\mdpbench `
  --run-root D:\OCR\benchmark\runs\mdpbench_mineru `
  --export-dir D:\OCR\benchmark\exports\mdpbench_mineru `
  --result-root D:\OCR\benchmark\scores\mdpbench_mineru `
  --scorer-root D:\OCR\repos\MultimodalOCR-main\MDPBench `
  --python-exe D:\OCR\venvs\bench\Scripts\python.exe
```

For `MDPBench`, the wrapper also runs official `tools/calculate_scores.py`.

## Verified End-To-End

Verified with official demo predictions:

- `D:\OCR\benchmark\scores\omnidocbench_demo_end2end`
- `D:\OCR\benchmark\scores\mdpbench_demo_gemini`

These runs confirm:

1. normalization works
2. markdown export works
3. official scorers run successfully in the local environment

## End-To-End Batch Pipeline

Prepare flat image inputs for one dataset:

```powershell
D:\OCR\venvs\bench\Scripts\python.exe D:\OCR\scripts\prepare_benchmark_inputs.py `
  --dataset-name omnidocbench `
  --dataset-root D:\OCR\datasets\omnidocbench `
  --output-dir D:\OCR\benchmark\inputs\omnidocbench
```

Run the full benchmark pipeline for all 5 models on a dataset subset:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
. D:\OCR\scripts\Set-OcrEnv.ps1

D:\OCR\venvs\bench\Scripts\python.exe D:\OCR\scripts\run_benchmark_pipeline.py `
  --datasets omnidocbench `
  --models mineru hunyuanocr monkeyocr paddlevl olmocr2 `
  --limit 5
```

Run all configured datasets and models:

```powershell
D:\OCR\venvs\bench\Scripts\python.exe D:\OCR\scripts\run_benchmark_pipeline.py
```

Leaderboard outputs:

- `D:\OCR\benchmark\leaderboards\leaderboard.csv`
- `D:\OCR\benchmark\leaderboards\leaderboard.md`

Notes:

- `rank_score` in the leaderboard is a local aggregation used only for sorting.
- Official raw metric files remain under each run's score directory and should be treated as the source of truth.
- Batch inference now runs in resilient mode:
  - per-page failures are recorded in each model's `_batch_summary.json`
  - a failed page is still standardized into the run directory with `meta.json.success=false`
  - one model failing no longer stops the remaining models in `run_benchmark_pipeline.py`
- Each model run writes `_pipeline_status.json` under its standardized run directory.
- On this `GTX 1080 Ti 11GB` machine, `olmOCR2` runs in a compatibility mode inside the pipeline:
  - `attn=eager`
  - `use_cache=False`
  - `max_side=256`
  - `max_new_tokens=16`
- That setting is intended to keep `olmOCR2` runnable locally. Its benchmark quality is expected to be significantly below what the model can deliver on a larger GPU.
