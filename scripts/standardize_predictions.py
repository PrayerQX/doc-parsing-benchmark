import argparse
import json
from pathlib import Path

from benchmark_common import StandardizedResult, ensure_adapter, load_dataset_index, write_standardized_sample


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-name", required=True, choices=["omnidocbench", "mdpbench"])
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--model-name", required=True)
    parser.add_argument("--model-version")
    parser.add_argument("--backend")
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--pattern", required=True, help="Example: **/*.md")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--input-mode", default="image", choices=["image", "pdf"])
    parser.add_argument("--runtime-seconds", type=float)
    parser.add_argument("--gpu-mem-mb", type=int)
    parser.add_argument("--metrics-json", help="Optional batch summary JSON with per-sample runtime_seconds and gpu_mem_mb.")
    args = parser.parse_args()

    dataset_index = load_dataset_index(args.dataset_name, args.dataset_root)
    adapter = ensure_adapter(args.adapter)
    input_root = Path(args.input_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    metrics_map: dict[str, dict] = {}

    if args.metrics_json and Path(args.metrics_json).exists():
        metrics_payload = json.loads(Path(args.metrics_json).read_text(encoding="utf-8"))
        metrics_map = metrics_payload.get("samples", {})

    standardized_count = 0
    failure_placeholder_count = 0
    skipped: list[dict] = []
    processed_ids: set[str] = set()

    for raw_path in sorted(input_root.glob(args.pattern)):
        if raw_path.is_dir():
            continue
        normalized = adapter(raw_path)
        sample = dataset_index.get(normalized.sample_id)
        if sample is None:
            skipped.append({"raw_path": str(raw_path), "sample_id": normalized.sample_id, "reason": "sample_id_not_in_dataset"})
            continue
        sample_metrics = metrics_map.get(normalized.sample_id, {})
        normalized.extras = {
            **(normalized.extras or {}),
            "status": sample_metrics.get("status", "ok"),
            "error": sample_metrics.get("error"),
            "stdout_tail": sample_metrics.get("stdout_tail"),
            "stderr_tail": sample_metrics.get("stderr_tail"),
        }

        write_standardized_sample(
            sample=sample,
            standardized=normalized,
            output_root=output_root,
            model_name=args.model_name,
            model_version=args.model_version,
            backend=args.backend,
            input_mode=args.input_mode,
            runtime_seconds=sample_metrics.get("runtime_seconds", args.runtime_seconds),
            gpu_mem_mb=sample_metrics.get("gpu_mem_mb", args.gpu_mem_mb),
        )
        processed_ids.add(normalized.sample_id)
        standardized_count += 1

    for sample_id, metrics in sorted(metrics_map.items()):
        status = str(metrics.get("status", "")).lower()
        if sample_id in processed_ids or status in {"", "ok", "skipped_existing"}:
            continue
        sample = dataset_index.get(sample_id)
        if sample is None:
            skipped.append({"raw_path": None, "sample_id": sample_id, "reason": "failed_sample_not_in_dataset"})
            continue

        write_standardized_sample(
            sample=sample,
            standardized=StandardizedResult(
                sample_id=sample_id,
                markdown="",
                text="",
                raw_output_format="missing",
                raw_output_path=str(metrics.get("output_path") or ""),
                adapter=args.adapter,
                extras={
                    "status": metrics.get("status"),
                    "error": metrics.get("error"),
                    "stdout_tail": metrics.get("stdout_tail"),
                    "stderr_tail": metrics.get("stderr_tail"),
                },
            ),
            output_root=output_root,
            model_name=args.model_name,
            model_version=args.model_version,
            backend=args.backend,
            input_mode=args.input_mode,
            runtime_seconds=metrics.get("runtime_seconds", args.runtime_seconds),
            gpu_mem_mb=metrics.get("gpu_mem_mb", args.gpu_mem_mb),
        )
        failure_placeholder_count += 1

    summary = {
        "dataset_name": args.dataset_name,
        "model_name": args.model_name,
        "model_version": args.model_version,
        "backend": args.backend,
        "adapter": args.adapter,
        "input_root": str(input_root),
        "output_root": str(output_root),
        "standardized_count": standardized_count,
        "failure_placeholder_count": failure_placeholder_count,
        "skipped_count": len(skipped),
        "skipped": skipped[:200],
    }
    (output_root / "run_manifest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
