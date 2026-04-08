import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--export-dir", required=True)
    args = parser.parse_args()

    run_root = Path(args.run_root).resolve()
    export_dir = Path(args.export_dir).resolve()
    export_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for sample_dir in sorted(p for p in run_root.iterdir() if p.is_dir()):
        result_md = sample_dir / "result.md"
        if not result_md.exists():
            continue
        shutil.copyfile(result_md, export_dir / f"{sample_dir.name}.md")
        count += 1

    print(f"Exported {count} markdown files to {export_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

