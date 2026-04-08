import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from benchmark_common import load_dataset_index


def _bucket_language(value: str | None) -> str:
    if not value:
        return "unknown"
    text = str(value)
    return text


def _bucket_layout(value: str | None) -> str:
    if not value:
        return "unknown"
    return str(value)


def _bucket_source(value: str | None) -> str:
    if not value:
        return "unknown"
    return str(value)


def _infer_source_from_image_path(image_path: str | None) -> str:
    if not image_path:
        return "unknown"
    stem = Path(str(image_path)).stem
    parts = stem.split("_")
    if len(parts) >= 2:
        return parts[1]
    return "unknown"


def _language_bucket_for_profile(dataset_name: str, value: str | None, profile: str) -> str:
    if profile != "lite":
        return _bucket_language(value)
    text = str(value or "unknown").lower()
    if dataset_name == "omnidocbench":
        if "english" in text and ("chinese" in text or "mixed" in text or "en_ch" in text):
            return "mixed_other"
        if "english" in text:
            return "english"
        if "chinese" in text:
            return "chinese"
        return "mixed_other"
    if "english" in text:
        return "english"
    if "chinese" in text:
        return "chinese"
    return "other"


def _layout_bucket_for_profile(value: str | None, profile: str) -> str:
    if profile != "lite":
        return _bucket_layout(value)
    text = str(value or "unknown").lower()
    if "single" in text:
        return "single"
    if "double" in text or "three" in text or "1andmore" in text or "multi" in text:
        return "multi"
    return "complex_or_unknown"


def _source_bucket_for_profile(dataset_name: str, value: str | None, image_path: str | None, profile: str) -> str:
    source = _bucket_source(value)
    if profile != "lite":
        return source
    if source == "unknown":
        source = _infer_source_from_image_path(image_path)
    text = str(source).lower()
    if dataset_name == "mdpbench":
        for token in ("newspaper", "magazine", "book", "report", "paper", "exam", "ppt", "slide"):
            if token in text:
                return token
    return source


def _sample_features(dataset_name: str, entry: dict, profile: str) -> dict:
    page_attr = entry.get("page_info", {}).get("page_attribute", {}) or {}
    image_path = entry.get("page_info", {}).get("image_path")
    language = _language_bucket_for_profile(dataset_name, page_attr.get("language") or page_attr.get("text_language"), profile)
    layout = _layout_bucket_for_profile(page_attr.get("layout"), profile)
    source = _source_bucket_for_profile(dataset_name, page_attr.get("data_source"), image_path, profile)
    has_formula = False
    has_table = False
    for det in entry.get("layout_dets", []):
        category = str(det.get("category_type", "")).lower()
        if "formula" in category or "equation" in category:
            has_formula = True
        if "table" in category:
            has_table = True
    return {
        "language": _bucket_language(language),
        "layout": _bucket_layout(layout),
        "source": _bucket_source(source),
        "has_formula": has_formula,
        "has_table": has_table,
    }


def _score_candidate(features: dict, profile: str) -> tuple:
    if profile == "lite":
        return (
            1 if features["has_formula"] else 0,
            1 if features["has_table"] else 0,
            0 if features["layout"] == "complex_or_unknown" else 1,
        )
    return (
        1 if features["has_formula"] else 0,
        1 if features["has_table"] else 0,
    )


def build_stratified_sample(dataset_name: str, dataset_root: Path, target_pages: int, seed: int, profile: str) -> list[dict]:
    dataset_path = dataset_root / ("OmniDocBench.json" if dataset_name == "omnidocbench" else "MDPBench_public.json")
    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    dataset_index = load_dataset_index(dataset_name, dataset_root)

    records = []
    for entry in payload:
        image_path = entry.get("page_info", {}).get("image_path")
        if not image_path:
            continue
        sample_id = Path(image_path).stem
        sample = dataset_index[sample_id]
        features = _sample_features(dataset_name, entry, profile)
        records.append(
            {
                "sample_id": sample_id,
                "image_path": sample.image_path,
                "image_abspath": sample.image_abspath,
                "features": features,
            }
        )

    rng = random.Random(seed)
    groups = defaultdict(list)
    for record in records:
        feats = record["features"]
        if profile == "lite":
            if dataset_name == "omnidocbench":
                key = (feats["language"], feats["layout"], feats["has_table"], feats["has_formula"])
            else:
                key = (feats["language"], feats["source"], feats["has_table"], feats["has_formula"])
        else:
            key = (
                feats["language"],
                feats["layout"],
                feats["source"],
                feats["has_table"],
                feats["has_formula"],
            )
        groups[key].append(record)

    for group_records in groups.values():
        rng.shuffle(group_records)
        group_records.sort(key=lambda item: _score_candidate(item["features"], profile), reverse=True)

    sorted_groups = sorted(groups.items(), key=lambda item: len(item[1]))
    selected: list[dict] = []
    selected_ids: set[str] = set()

    for _, group_records in sorted_groups:
        if len(selected) >= target_pages:
            break
        choice = group_records[0]
        selected.append(choice)
        selected_ids.add(choice["sample_id"])

    if len(selected) < target_pages:
        remaining = [record for record in records if record["sample_id"] not in selected_ids]
        rng.shuffle(remaining)
        remaining.sort(key=lambda item: _score_candidate(item["features"], profile), reverse=True)
        selected.extend(remaining[: target_pages - len(selected)])

    selected = selected[:target_pages]
    selected.sort(key=lambda item: item["sample_id"])
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-name", required=True, choices=["omnidocbench", "mdpbench"])
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--target-pages", type=int, required=True)
    parser.add_argument("--seed", type=int, default=20260407)
    parser.add_argument("--profile", choices=["default", "lite"], default="default")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root).resolve()
    sample = build_stratified_sample(args.dataset_name, dataset_root, args.target_pages, args.seed, args.profile)
    summary = {
        "dataset_name": args.dataset_name,
        "dataset_root": str(dataset_root),
        "target_pages": args.target_pages,
        "seed": args.seed,
        "profile": args.profile,
        "sample_count": len(sample),
        "samples": sample,
    }
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "samples"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
