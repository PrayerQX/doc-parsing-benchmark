import argparse
import json
from pathlib import Path

from benchmark_common import build_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-name", required=True, choices=["omnidocbench", "mdpbench"])
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = build_manifest(args.dataset_name, args.dataset_root)
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} records to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

