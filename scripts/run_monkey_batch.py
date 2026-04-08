import argparse
import json
import subprocess
import time
from pathlib import Path


def iter_images(input_dir: Path) -> list[Path]:
    return sorted(
        [path for path in input_dir.rglob("*") if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}]
    )


def find_output_markdown(output_dir: Path, sample_id: str) -> Path | None:
    expected = output_dir / sample_id / f"{sample_id}.md"
    if expected.exists():
        return expected
    legacy = output_dir / sample_id / f"{sample_id}_text_result.md"
    if legacy.exists():
        return legacy
    matches = sorted(output_dir.glob(f"**/{sample_id}.md"))
    if matches:
        return matches[0]
    matches = sorted(output_dir.glob(f"**/{sample_id}_text_result.md"))
    return matches[0] if matches else None


def tail_text(text: str | None, limit: int = 2000) -> str | None:
    if not text:
        return None
    return text[-limit:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-exe", required=True)
    parser.add_argument("--parse-script", required=True)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--summary-json")
    parser.add_argument("--workdir")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    workdir = Path(args.workdir).resolve() if args.workdir else None

    samples = iter_images(input_dir)
    if args.limit:
        samples = samples[: args.limit]

    per_sample: dict[str, dict] = {}
    for image_path in samples:
        sample_id = image_path.stem
        existing_output = find_output_markdown(output_dir, sample_id)
        if args.resume and existing_output and existing_output.exists():
            per_sample[sample_id] = {
                "status": "skipped_existing",
                "output_path": str(existing_output),
            }
            continue

        start = time.perf_counter()
        cmd = [
            args.python_exe,
            args.parse_script,
            str(image_path),
            "-c",
            args.config,
            "-o",
            str(output_dir),
        ]
        try:
            completed = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=workdir,
            )
            output_path = find_output_markdown(output_dir, sample_id)
            per_sample[sample_id] = {
                "status": "ok" if output_path else "failed",
                "output_path": str(output_path) if output_path else "",
                "content_list_path": str(output_path.with_name(f"{output_path.stem}_content_list.json")) if output_path else "",
                "runtime_seconds": round(time.perf_counter() - start, 4),
                "stdout_tail": tail_text(completed.stdout),
                "stderr_tail": tail_text(completed.stderr),
                "error": None if output_path else "monkey_completed_without_markdown_output",
            }
        except subprocess.CalledProcessError as exc:
            per_sample[sample_id] = {
                "status": "failed",
                "output_path": "",
                "content_list_path": "",
                "runtime_seconds": round(time.perf_counter() - start, 4),
                "returncode": exc.returncode,
                "stdout_tail": tail_text(exc.stdout),
                "stderr_tail": tail_text(exc.stderr),
                "error": f"monkey_exit_{exc.returncode}",
            }

    summary = {
        "model": "MonkeyOCR v1.5",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "sample_count": len(samples),
        "completed_count": sum(1 for item in per_sample.values() if item["status"] == "ok"),
        "failed_count": sum(1 for item in per_sample.values() if item["status"] == "failed"),
        "skipped_count": sum(1 for item in per_sample.values() if item["status"] == "skipped_existing"),
        "samples": per_sample,
    }
    summary_path = Path(args.summary_json).resolve() if args.summary_json else output_dir / "_batch_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "samples"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
