from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import yaml

from benchmark_common import DATASET_FILES


def build_config(dataset_name: str, dataset_root: Path, prediction_dir: Path) -> dict:
    if dataset_name == "omnidocbench":
        return {
            "end2end_eval": {
                "metrics": {
                    "text_block": {"metric": ["Edit_dist"]},
                    "display_formula": {"metric": ["Edit_dist"]},
                    "table": {"metric": ["TEDS", "Edit_dist"]},
                    "reading_order": {"metric": ["Edit_dist"]},
                },
                "dataset": {
                    "dataset_name": "end2end_dataset",
                    "ground_truth": {"data_path": str((dataset_root / DATASET_FILES[dataset_name]).resolve())},
                    "prediction": {"data_path": str(prediction_dir.resolve())},
                    "match_method": "quick_match",
                },
            }
        }
    if dataset_name == "mdpbench":
        return {
            "end2end_eval": {
                "metrics": {
                    "text_block": {"metric": ["Edit_dist"]},
                    "display_formula": {"metric": ["Edit_dist"]},
                    "table": {"metric": ["TEDS", "Edit_dist"]},
                    "reading_order": {"metric": ["Edit_dist"]},
                },
                "dataset": {
                    "dataset_name": "end2end_dataset",
                    "ground_truth": {"data_path": str((dataset_root / DATASET_FILES[dataset_name]).resolve())},
                    "prediction": {"data_path": str(prediction_dir.resolve())},
                    "match_method": "quick_match",
                },
            }
        }
    raise ValueError(f"Unsupported dataset: {dataset_name}")


def copy_matching_results(source_root: Path, pattern: str, dest_root: Path) -> list[str]:
    dest_root.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for candidate in source_root.glob(pattern):
        destination = dest_root / candidate.name
        if candidate.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(candidate, destination)
        else:
            shutil.copy2(candidate, destination)
        copied.append(str(destination))
    return copied


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-name", required=True, choices=["omnidocbench", "mdpbench"])
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--export-dir", required=True)
    parser.add_argument("--result-root", required=True)
    parser.add_argument("--scorer-root", required=True)
    parser.add_argument("--python-exe", required=True)
    args = parser.parse_args()

    dataset_name = args.dataset_name
    dataset_root = Path(args.dataset_root).resolve()
    run_root = Path(args.run_root).resolve()
    export_dir = Path(args.export_dir).resolve()
    result_root = Path(args.result_root).resolve()
    scorer_root = Path(args.scorer_root).resolve()
    python_exe = Path(args.python_exe).resolve()

    subprocess.run(
        [
            str(python_exe),
            str(Path(__file__).resolve().parent / "export_predictions_to_official.py"),
            "--run-root",
            str(run_root),
            "--export-dir",
            str(export_dir),
        ],
        check=True,
    )

    config = build_config(dataset_name, dataset_root, export_dir)
    config_dir = result_root / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / f"{dataset_name}_{export_dir.name}.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")

    scorer_result_dir = scorer_root / "result"
    scorer_result_dir.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in scorer_result_dir.iterdir()}

    cmd = [str(python_exe), "pdf_validation.py", "--config", str(config_path)]
    if dataset_name == "mdpbench":
        cmd.append("--slim")
    subprocess.run(cmd, cwd=str(scorer_root), check=True)

    save_name = export_dir.name + ("_result" if dataset_name == "mdpbench" else "_quick_match")
    copied = copy_matching_results(scorer_result_dir, f"{save_name}*", result_root / "official_result")

    if dataset_name == "mdpbench":
        score_target = scorer_result_dir / save_name
        subprocess.run(
            [str(python_exe), "tools/calculate_scores.py", "--result_folder", str(score_target)],
            cwd=str(scorer_root),
            check=True,
        )
        copied.extend(copy_matching_results(scorer_result_dir, f"{save_name}*", result_root / "official_result"))

    after = sorted(p.name for p in scorer_result_dir.iterdir() if p.name not in before)
    print("New scorer artifacts:", after)
    print("Copied artifacts:")
    for item in copied:
        print(item)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
