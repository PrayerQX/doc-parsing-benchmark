import argparse
import csv
import json
from pathlib import Path


def _safe_get(payload: dict, path: list[str], default=None):
    current = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def _read_metric_json(score_dir: Path) -> tuple[Path | None, dict]:
    candidates = sorted(score_dir.rglob("*metric_result.json"))
    if not candidates:
        return None, {}
    metric_path = candidates[0]
    return metric_path, json.loads(metric_path.read_text(encoding="utf-8"))


def _build_row(score_dir: Path) -> dict | None:
    metric_path, payload = _read_metric_json(score_dir)
    if not metric_path:
        return None

    row = {
        "run_name": score_dir.name,
        "dataset": score_dir.name.split("_", 1)[0],
        "metric_path": str(metric_path),
        "text_block_all_page_avg": _safe_get(payload, ["text_block", "all", "Edit_dist", "ALL_page_avg"]),
        "text_block_edit_whole": _safe_get(payload, ["text_block", "all", "Edit_dist", "edit_whole"]),
        "reading_order_all_page_avg": _safe_get(payload, ["reading_order", "all", "Edit_dist", "ALL_page_avg"]),
        "reading_order_edit_whole": _safe_get(payload, ["reading_order", "all", "Edit_dist", "edit_whole"]),
        "table_teds_all": _safe_get(payload, ["table", "all", "TEDS", "all"]),
        "table_teds_structure_all": _safe_get(payload, ["table", "all", "TEDS_structure_only", "all"]),
        "table_edit_whole": _safe_get(payload, ["table", "all", "Edit_dist", "edit_whole"]),
        "formula_all_page_avg": _safe_get(payload, ["display_formula", "all", "Edit_dist", "ALL_page_avg"]),
        "formula_edit_whole": _safe_get(payload, ["display_formula", "all", "Edit_dist", "edit_whole"]),
    }

    rank_parts = []
    if isinstance(row["text_block_all_page_avg"], (int, float)):
        rank_parts.append(1 - row["text_block_all_page_avg"])
    if isinstance(row["reading_order_all_page_avg"], (int, float)):
        rank_parts.append(1 - row["reading_order_all_page_avg"])
    if isinstance(row["table_teds_all"], (int, float)):
        rank_parts.append(row["table_teds_all"])
    if isinstance(row["formula_all_page_avg"], (int, float)):
        rank_parts.append(1 - row["formula_all_page_avg"])
    row["rank_score"] = round(sum(rank_parts) / len(rank_parts), 6) if rank_parts else None
    return row


def _rows_to_markdown(rows: list[dict]) -> str:
    headers = [
        "run_name",
        "dataset",
        "rank_score",
        "text_block_all_page_avg",
        "reading_order_all_page_avg",
        "table_teds_all",
        "formula_all_page_avg",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values = []
        for key in headers:
            value = row.get(key)
            if isinstance(value, float):
                values.append(f"{value:.6f}")
            else:
                values.append("" if value is None else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores-root", required=True)
    parser.add_argument("--output-csv", required=True)
    parser.add_argument("--output-md", required=True)
    args = parser.parse_args()

    scores_root = Path(args.scores_root).resolve()
    rows = []
    for score_dir in sorted([path for path in scores_root.iterdir() if path.is_dir()]):
        row = _build_row(score_dir)
        if row is not None:
            rows.append(row)

    rows.sort(key=lambda item: (item["dataset"], -(item["rank_score"] or -1)))

    output_csv = Path(args.output_csv).resolve()
    output_md = Path(args.output_md).resolve()
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(rows[0].keys()) if rows else [
        "run_name",
        "dataset",
        "rank_score",
        "text_block_all_page_avg",
        "reading_order_all_page_avg",
        "table_teds_all",
        "formula_all_page_avg",
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output_md.write_text(_rows_to_markdown(rows), encoding="utf-8")
    print(json.dumps({"scores_root": str(scores_root), "row_count": len(rows)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
