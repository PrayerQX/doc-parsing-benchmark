# Benchmark Workflow

Note: examples below assume this repository is your workspace root. Replace `.\` paths if your local layout differs.

## Local Assets

Datasets:

- `.\datasets\omnidocbench`
- `.\datasets\mdpbench`

Official scorers:

- `.\repos\OmniDocBench-main`
- `.\repos\MultimodalOCR-main\MDPBench`

Benchmark venv:

- `.\venvs\bench`

Shared benchmark folders:

- `.\benchmark\...`
- `.\benchmark_quick_resilient\...`
- `.\benchmark_quick_lite\...`

## Benchmark Profiles

The repository keeps three benchmark profiles so people can quickly find the right entrypoint:

| Profile | Intended use | Dataset scope | Manifest location | Launcher | Output root |
| --- | --- | --- | --- | --- | --- |
| Full / Long | final or paper-style benchmark | full OmniDocBench + full MDPBench | none | `scripts/launch_benchmark_full.cmd` | `benchmark/` |
| Resilient / Medium | broader sampled comparison | 150 OmniDocBench pages + 150 MDPBench pages | `manifests/resilient/` | `scripts/launch_benchmark_quick_resilient.cmd` | `benchmark_quick_resilient/` |
| Lite / Short | quickest comparison run | 80 OmniDocBench pages + 24 MDPBench pages | `manifests/lite/` | `scripts/launch_benchmark_quick_lite.cmd` | `benchmark_quick_lite/` |

Rules of thumb:

- use `Full / Long` when you want the final ranking and can afford the runtime
- use `Resilient / Medium` when you want a broader sampled benchmark on slower GPUs
- use `Lite / Short` when you want the fastest reproducible comparison
- only sampled profiles ship with versioned manifests; the full profile reads directly from the full datasets

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
. .\scripts\Set-OcrEnv.ps1

.\venvs\bench\Scripts\python.exe .\scripts\build_benchmark_manifest.py `
  --dataset-name omnidocbench `
  --dataset-root .\datasets\omnidocbench `
  --output .\benchmark\omnidocbench_manifest.json
```

## Standardize Raw Model Outputs

Example for a markdown-style model output folder:

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\standardize_predictions.py `
  --dataset-name mdpbench `
  --dataset-root .\datasets\mdpbench `
  --model-name mineru `
  --adapter mineru `
  --input-root .\raw\mdpbench\mineru `
  --pattern **\*.md `
  --output-root .\benchmark\runs\mdpbench_mineru
```

Notes:

- file stem must match dataset sample id
- standardized run metadata is saved to `run_manifest.json`

## Export To Official Markdown Folder

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\export_predictions_to_official.py `
  --run-root .\benchmark\runs\mdpbench_mineru `
  --export-dir .\benchmark\exports\mdpbench_mineru
```

## Score With Official Rules

### OmniDocBench

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\score_with_official.py `
  --dataset-name omnidocbench `
  --dataset-root .\datasets\omnidocbench `
  --run-root .\benchmark\runs\omnidocbench_mineru `
  --export-dir .\benchmark\exports\omnidocbench_mineru `
  --result-root .\benchmark\scores\omnidocbench_mineru `
  --scorer-root .\repos\OmniDocBench-main `
  --python-exe .\venvs\bench\Scripts\python.exe
```

### MDPBench

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\score_with_official.py `
  --dataset-name mdpbench `
  --dataset-root .\datasets\mdpbench `
  --run-root .\benchmark\runs\mdpbench_mineru `
  --export-dir .\benchmark\exports\mdpbench_mineru `
  --result-root .\benchmark\scores\mdpbench_mineru `
  --scorer-root .\repos\MultimodalOCR-main\MDPBench `
  --python-exe .\venvs\bench\Scripts\python.exe
```

For `MDPBench`, the wrapper also runs official `tools/calculate_scores.py`.

## Verified End-To-End

Verified with official demo predictions:

- `.\benchmark\scores\omnidocbench_demo_end2end`
- `.\benchmark\scores\mdpbench_demo_gemini`

These runs confirm:

1. normalization works
2. markdown export works
3. official scorers run successfully in the local environment

## End-To-End Batch Pipeline

Prepare flat image inputs for one dataset:

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\prepare_benchmark_inputs.py `
  --dataset-name omnidocbench `
  --dataset-root .\datasets\omnidocbench `
  --output-dir .\benchmark\inputs\omnidocbench
```

Run the full benchmark pipeline for all 5 models on a dataset subset:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
. .\scripts\Set-OcrEnv.ps1

.\venvs\bench\Scripts\python.exe .\scripts\run_benchmark_pipeline.py `
  --datasets omnidocbench `
  --models mineru hunyuanocr monkeyocr paddlevl olmocr2 `
  --limit 5
```

Run all configured datasets and models:

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\run_benchmark_pipeline.py
```

## Profile Launch Commands

Full / Long:

```powershell
.\scripts\launch_benchmark_full.cmd
```

Resilient / Medium:

```powershell
.\scripts\launch_benchmark_quick_resilient.cmd
```

Lite / Short:

```powershell
.\scripts\launch_benchmark_quick_lite.cmd
```

If you want your own sampled subset instead of the bundled `resilient` or `lite` manifests:

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\sample_benchmark_manifest.py `
  --dataset-name omnidocbench `
  --dataset-root .\datasets\omnidocbench `
  --target-pages 120 `
  --profile lite `
  --output .\manifests\custom\omnidocbench_sample_manifest.json
```

Then point the pipeline at that folder:

```powershell
.\venvs\bench\Scripts\python.exe .\scripts\run_benchmark_pipeline.py `
  --datasets omnidocbench mdpbench `
  --models mineru hunyuanocr monkeyocr paddlevl `
  --manifest-root .\manifests\custom `
  --use-sampled-manifests
```

Leaderboard outputs:

- `.\benchmark\leaderboards\leaderboard.csv`
- `.\benchmark\leaderboards\leaderboard.md`
- `.\benchmark_quick_resilient\leaderboards\leaderboard.csv`
- `.\benchmark_quick_lite\leaderboards\leaderboard.csv`

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
