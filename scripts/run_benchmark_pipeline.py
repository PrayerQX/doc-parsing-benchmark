import argparse
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / "cache"
CACHE_ENV = {
    "HF_HOME": str(CACHE_ROOT / "hf"),
    "HUGGINGFACE_HUB_CACHE": str(CACHE_ROOT / "hf"),
    "TRANSFORMERS_CACHE": str(CACHE_ROOT / "hf"),
    "TORCH_HOME": str(CACHE_ROOT / "torch"),
    "XDG_CACHE_HOME": str(CACHE_ROOT / "xdg"),
    "MODELSCOPE_CACHE": str(CACHE_ROOT / "modelscope"),
    "PADDLE_HOME": str(CACHE_ROOT / "paddle"),
    "PADDLE_PDX_CACHE_HOME": str(CACHE_ROOT / "paddle"),
    "PIP_CACHE_DIR": str(CACHE_ROOT / "pip"),
    "UV_CACHE_DIR": str(CACHE_ROOT / "uv"),
    "TMP": str(CACHE_ROOT / "tmp"),
    "TEMP": str(CACHE_ROOT / "tmp"),
    "HF_HUB_DISABLE_SYMLINKS_WARNING": "1",
    "HF_HUB_DISABLE_XET": "1",
    "PYTHONUTF8": "1",
    "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True",
}

MODELS = {
    "mineru": {
        "command": [
            "{bench_python}",
            str(ROOT / "scripts" / "run_mineru_batch.py"),
            "--mineru-exe",
            str(ROOT / "venvs" / "mineru" / "Scripts" / "mineru.exe"),
            "--input-dir",
            "{input_dir}",
            "--output-dir",
            "{raw_dir}",
            "--backend",
            "vlm-auto-engine",
            "--resume",
            "--summary-json",
            "{summary_json}",
        ],
        "adapter": "mineru",
        "pattern": "**/*.md",
        "backend": "mineru-cli",
        "model_version": "MinerU-2.5-VLM",
    },
    "hunyuanocr": {
        "command": [
            str(ROOT / "venvs" / "hunyuan" / "Scripts" / "python.exe"),
            str(ROOT / "scripts" / "run_hunyuan_batch.py"),
            "--input-dir",
            "{input_dir}",
            "--output-dir",
            "{raw_dir}",
            "--resume",
            "--summary-json",
            "{summary_json}",
        ],
        "adapter": "hunyuanocr",
        "pattern": "*.txt",
        "backend": "transformers",
        "model_version": "tencent/HunyuanOCR",
    },
    "monkeyocr": {
        "command": [
            "{bench_python}",
            str(ROOT / "scripts" / "run_monkey_batch.py"),
            "--python-exe",
            str(ROOT / "venvs" / "monkey" / "Scripts" / "python.exe"),
            "--parse-script",
            str(ROOT / "repos" / "MonkeyOCR-main" / "parse.py"),
            "--input-dir",
            "{input_dir}",
            "--output-dir",
            "{raw_dir}",
            "--config",
            "model_configs.local.yaml",
            "--workdir",
            str(ROOT / "repos" / "MonkeyOCR-main"),
            "--resume",
            "--summary-json",
            "{summary_json}",
        ],
        "adapter": "monkeyocr",
        "pattern": "**/*_text_result.md",
        "backend": "transformers",
        "model_version": "MonkeyOCR v1.5",
    },
    "paddlevl": {
        "command": [
            "{bench_python}",
            str(ROOT / "scripts" / "run_paddlevl_batch.py"),
            "--paddleocr-exe",
            str(ROOT / "venvs" / "paddlevl" / "Scripts" / "paddleocr.exe"),
            "--input-dir",
            "{input_dir}",
            "--output-dir",
            "{raw_dir}",
            "--pipeline-version",
            "v1.5",
            "--device",
            "gpu:0",
            "--max-new-tokens",
            "512",
            "--resume",
            "--summary-json",
            "{summary_json}",
        ],
        "adapter": "paddlevl",
        "pattern": "**/*.md",
        "backend": "paddleocr-cli",
        "model_version": "PaddleOCR-VL-1.5",
        "env": {"PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "True"},
    },
    "olmocr2": {
        "command": [
            str(ROOT / "venvs" / "olmocr" / "Scripts" / "python.exe"),
            str(ROOT / "scripts" / "run_olmocr2_batch.py"),
            "--input-dir",
            "{input_dir}",
            "--output-dir",
            "{raw_dir}",
            "--resume",
            "--summary-json",
            "{summary_json}",
            "--attn",
            "eager",
            "--greedy",
            "--no-cache",
            "--max-side",
            "256",
            "--max-new-tokens",
            "16",
        ],
        "adapter": "olmocr2",
        "pattern": "*.txt",
        "backend": "transformers",
        "model_version": "allenai/olmOCR-2-7B-1025-FP8",
    },
}

DATASET_SCORERS = {
    "omnidocbench": ROOT / "repos" / "OmniDocBench-main",
    "mdpbench": ROOT / "repos" / "MultimodalOCR-main" / "MDPBench",
}


def run_cmd(cmd: list[str], *, env: dict | None = None, workdir: Path | None = None) -> None:
    merged_env = os.environ.copy()
    merged_env.update(CACHE_ENV)
    if env:
        merged_env.update(env)
    print(json.dumps({"cwd": str(workdir or ROOT), "cmd": cmd}, ensure_ascii=False))
    subprocess.run(cmd, check=True, cwd=workdir or ROOT, env=merged_env)


def has_standardized_results(run_dir: Path) -> bool:
    return run_dir.exists() and any(path.is_dir() for path in run_dir.iterdir())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--datasets", nargs="+", default=["omnidocbench", "mdpbench"], choices=["omnidocbench", "mdpbench"])
    parser.add_argument(
        "--models",
        nargs="+",
        default=["mineru", "hunyuanocr", "monkeyocr", "paddlevl", "olmocr2"],
        choices=list(MODELS.keys()),
    )
    parser.add_argument("--input-root", default=str(ROOT / "benchmark" / "inputs"))
    parser.add_argument("--raw-root", default=str(ROOT / "benchmark" / "raw"))
    parser.add_argument("--run-root", default=str(ROOT / "benchmark" / "runs"))
    parser.add_argument("--export-root", default=str(ROOT / "benchmark" / "exports"))
    parser.add_argument("--score-root", default=str(ROOT / "benchmark" / "scores"))
    parser.add_argument("--leaderboard-root", default=str(ROOT / "benchmark" / "leaderboards"))
    parser.add_argument("--manifest-root", default=str(ROOT / "benchmark" / "manifests"))
    parser.add_argument("--bench-python", default=str(ROOT / "venvs" / "bench" / "Scripts" / "python.exe"))
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--skip-infer", action="store_true")
    parser.add_argument("--skip-score", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--use-sampled-manifests", action="store_true")
    args = parser.parse_args()

    input_root = Path(args.input_root).resolve()
    raw_root = Path(args.raw_root).resolve()
    run_root = Path(args.run_root).resolve()
    export_root = Path(args.export_root).resolve()
    score_root = Path(args.score_root).resolve()
    leaderboard_root = Path(args.leaderboard_root).resolve()
    manifest_root = Path(args.manifest_root).resolve()

    for path in {
        input_root,
        raw_root,
        run_root,
        export_root,
        score_root,
        leaderboard_root,
        manifest_root,
        *(Path(value) for value in CACHE_ENV.values() if "\\" in value or "/" in value),
    }:
        path.mkdir(parents=True, exist_ok=True)

    for dataset_name in args.datasets:
        dataset_root = ROOT / "datasets" / dataset_name
        prepared_input_dir = input_root / dataset_name
        manifest_path = manifest_root / f"{dataset_name}_sample_manifest.json"
        prepare_cmd = [
            args.bench_python,
            str(ROOT / "scripts" / "prepare_benchmark_inputs.py"),
            "--dataset-name",
            dataset_name,
            "--dataset-root",
            str(dataset_root),
            "--output-dir",
            str(prepared_input_dir),
        ]
        if args.use_sampled_manifests:
            prepare_cmd += ["--manifest-json", str(manifest_path)]
        elif args.limit:
            prepare_cmd += ["--limit", str(args.limit)]
        run_cmd(prepare_cmd)
        if args.prepare_only:
            continue

        for model_name in args.models:
            config = MODELS[model_name]
            raw_dir = raw_root / dataset_name / model_name
            raw_dir.mkdir(parents=True, exist_ok=True)
            summary_json = raw_dir / "_batch_summary.json"
            model_report = {
                "dataset_name": dataset_name,
                "model_name": model_name,
                "infer_status": "pending",
                "standardize_status": "pending",
                "score_status": "pending",
            }

            if not args.skip_infer:
                infer_cmd = [
                    part.format(
                        bench_python=args.bench_python,
                        input_dir=prepared_input_dir,
                        raw_dir=raw_dir,
                        summary_json=summary_json,
                    )
                    for part in config["command"]
                ]
                if args.limit:
                    infer_cmd += ["--limit", str(args.limit)]
                try:
                    run_cmd(infer_cmd, env=config.get("env"), workdir=config.get("workdir"))
                    model_report["infer_status"] = "ok"
                except subprocess.CalledProcessError as exc:
                    model_report["infer_status"] = "failed"
                    model_report["infer_error"] = f"{type(exc).__name__}: {exc}"
                    print(json.dumps(model_report, ensure_ascii=False))

            run_dir = run_root / f"{dataset_name}_{model_name}"
            standardize_cmd = [
                args.bench_python,
                str(ROOT / "scripts" / "standardize_predictions.py"),
                "--dataset-name",
                dataset_name,
                "--dataset-root",
                str(dataset_root),
                "--model-name",
                model_name,
                "--model-version",
                config["model_version"],
                "--backend",
                config["backend"],
                "--adapter",
                config["adapter"],
                "--input-root",
                str(raw_dir),
                "--pattern",
                config["pattern"],
                "--output-root",
                str(run_dir),
                "--metrics-json",
                str(summary_json),
            ]
            try:
                run_cmd(standardize_cmd)
                model_report["standardize_status"] = "ok"
            except subprocess.CalledProcessError as exc:
                model_report["standardize_status"] = "failed"
                model_report["standardize_error"] = f"{type(exc).__name__}: {exc}"
                print(json.dumps(model_report, ensure_ascii=False))
                report_path = run_dir / "_pipeline_status.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(json.dumps(model_report, ensure_ascii=False, indent=2), encoding="utf-8")
                continue

            if args.skip_score:
                report_path = run_dir / "_pipeline_status.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(json.dumps(model_report, ensure_ascii=False, indent=2), encoding="utf-8")
                continue

            if not has_standardized_results(run_dir):
                model_report["score_status"] = "skipped_no_results"
                report_path = run_dir / "_pipeline_status.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(json.dumps(model_report, ensure_ascii=False, indent=2), encoding="utf-8")
                continue

            score_cmd = [
                args.bench_python,
                str(ROOT / "scripts" / "score_with_official.py"),
                "--dataset-name",
                dataset_name,
                "--dataset-root",
                str(dataset_root),
                "--run-root",
                str(run_dir),
                "--export-dir",
                str(export_root / f"{dataset_name}_{model_name}"),
                "--result-root",
                str(score_root / f"{dataset_name}_{model_name}"),
                "--scorer-root",
                str(DATASET_SCORERS[dataset_name]),
                "--python-exe",
                args.bench_python,
            ]
            try:
                run_cmd(score_cmd)
                model_report["score_status"] = "ok"
            except subprocess.CalledProcessError as exc:
                model_report["score_status"] = "failed"
                model_report["score_error"] = f"{type(exc).__name__}: {exc}"
                print(json.dumps(model_report, ensure_ascii=False))

            report_path = run_dir / "_pipeline_status.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(model_report, ensure_ascii=False, indent=2), encoding="utf-8")

    leaderboard_root.mkdir(parents=True, exist_ok=True)
    run_cmd(
        [
            args.bench_python,
            str(ROOT / "scripts" / "summarize_leaderboard.py"),
            "--scores-root",
            str(score_root),
            "--output-csv",
            str(leaderboard_root / "leaderboard.csv"),
            "--output-md",
            str(leaderboard_root / "leaderboard.md"),
        ]
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
