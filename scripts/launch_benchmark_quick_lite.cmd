@echo off
setlocal

set REPO_ROOT=%~dp0..
for %%I in ("%REPO_ROOT%") do set REPO_ROOT=%%~fI

set ROOT=%REPO_ROOT%\benchmark_quick_lite
set BENCH_PYTHON=%REPO_ROOT%\venvs\bench\Scripts\python.exe
if not "%OCR_BENCH_PYTHON%"=="" set BENCH_PYTHON=%OCR_BENCH_PYTHON%

if not exist "%ROOT%\jobs" mkdir "%ROOT%\jobs"

"%BENCH_PYTHON%" "%REPO_ROOT%\scripts\run_benchmark_pipeline.py" ^
  --datasets omnidocbench mdpbench ^
  --models mineru hunyuanocr monkeyocr paddlevl ^
  --input-root "%ROOT%\inputs" ^
  --raw-root "%ROOT%\raw" ^
  --run-root "%ROOT%\runs" ^
  --export-root "%ROOT%\exports" ^
  --score-root "%ROOT%\scores" ^
  --leaderboard-root "%ROOT%\leaderboards" ^
  --manifest-root "%REPO_ROOT%\manifests\lite" ^
  --use-sampled-manifests ^
  1>>"%ROOT%\jobs\benchmark_quick_lite_current.out.log" ^
  2>>"%ROOT%\jobs\benchmark_quick_lite_current.err.log"
