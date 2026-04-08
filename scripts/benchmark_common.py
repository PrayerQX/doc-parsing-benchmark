from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable


DATASET_FILES = {
    "omnidocbench": "OmniDocBench.json",
    "mdpbench": "MDPBench_public.json",
}


@dataclass
class DatasetSample:
    dataset_name: str
    sample_id: str
    image_path: str
    image_abspath: str
    page_info: dict
    raw_entry: dict


@dataclass
class StandardizedResult:
    sample_id: str
    markdown: str
    text: str
    raw_output_format: str
    raw_output_path: str
    adapter: str
    extras: dict | None = None


def _normalize_dataset_name(dataset_name: str) -> str:
    key = dataset_name.strip().lower()
    if key not in DATASET_FILES:
        raise ValueError(f"Unsupported dataset: {dataset_name}")
    return key


def load_dataset_index(dataset_name: str, dataset_root: str | Path) -> dict[str, DatasetSample]:
    dataset_key = _normalize_dataset_name(dataset_name)
    root = Path(dataset_root).resolve()
    gt_path = root / DATASET_FILES[dataset_key]
    with gt_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    index: dict[str, DatasetSample] = {}
    for entry in payload:
        page_info = entry.get("page_info", {})
        image_rel = page_info.get("image_path")
        if not image_rel:
            continue
        sample_id = Path(image_rel).stem
        image_subdir = "images" if dataset_key == "omnidocbench" else "MDPBench_img_public"
        image_abs = root / image_subdir / image_rel
        index[sample_id] = DatasetSample(
            dataset_name=dataset_key,
            sample_id=sample_id,
            image_path=image_rel,
            image_abspath=str(image_abs),
            page_info=page_info,
            raw_entry=entry,
        )
    return index


def build_manifest(dataset_name: str, dataset_root: str | Path) -> list[dict]:
    index = load_dataset_index(dataset_name, dataset_root)
    return [
        {
            "dataset_name": sample.dataset_name,
            "sample_id": sample.sample_id,
            "image_path": sample.image_path,
            "image_abspath": sample.image_abspath,
            "page_info": sample.page_info,
        }
        for sample in index.values()
    ]


def normalize_markdown(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned + "\n" if cleaned else ""


def strip_hunyuan_boxes(text: str) -> str:
    stripped = re.sub(r"\(\d+,\d+\),\(\d+,\d+\)", "\n", text)
    stripped = re.sub(r"\(\d+,\d+\)", "\n", stripped)
    stripped = re.sub(r"(?<=[A-Za-z0-9])(?=[A-Z][a-z])", "\n", stripped)
    return normalize_markdown(stripped)


def _infer_default_sample_id(path: Path) -> str:
    return path.stem


def _infer_monkey_sample_id(path: Path) -> str:
    stem = path.stem
    if stem.endswith("_text_result"):
        return stem[: -len("_text_result")]
    return stem


def read_markdown_file(path: Path) -> StandardizedResult:
    text = normalize_markdown(path.read_text(encoding="utf-8", errors="ignore"))
    sample_id = _infer_default_sample_id(path)
    return StandardizedResult(
        sample_id=sample_id,
        markdown=text,
        text=text,
        raw_output_format="markdown",
        raw_output_path=str(path.resolve()),
        adapter="markdown",
        extras=None,
    )


def adapter_mineru(path: Path) -> StandardizedResult:
    base = read_markdown_file(path)
    base.adapter = "mineru"
    return base


def adapter_paddlevl(path: Path) -> StandardizedResult:
    base = read_markdown_file(path)
    base.adapter = "paddlevl"
    return base


def adapter_ppstructurev3(path: Path) -> StandardizedResult:
    base = read_markdown_file(path)
    base.adapter = "ppstructurev3"
    return base


def adapter_monkey(path: Path) -> StandardizedResult:
    text = normalize_markdown(path.read_text(encoding="utf-8", errors="ignore"))
    content_list_path = path.with_name(f"{path.stem}_content_list.json")
    tables: list[dict] = []
    formulas: list[dict] = []
    text_blocks: list[dict] = []
    layout: list[dict] = []

    if content_list_path.exists():
        try:
            payload = json.loads(content_list_path.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(payload, list):
                for idx, item in enumerate(payload):
                    if not isinstance(item, dict):
                        continue
                    item_type = str(item.get("type", "")).lower()
                    page_idx = item.get("page_idx")
                    if item_type == "table":
                        table_body = item.get("table_body") or ""
                        tables.append(
                            {
                                "index": idx,
                                "page_idx": page_idx,
                                "caption": item.get("table_caption") or [],
                                "footnote": item.get("table_footnote") or [],
                                "html": table_body,
                            }
                        )
                    elif item_type == "equation":
                        formulas.append(
                            {
                                "index": idx,
                                "page_idx": page_idx,
                                "text": item.get("text") or "",
                                "format": item.get("text_format") or "",
                            }
                        )
                    elif item_type == "text":
                        text_value = item.get("text") or ""
                        if text_value:
                            text_blocks.append(
                                {
                                    "index": idx,
                                    "page_idx": page_idx,
                                    "text": text_value,
                                    "text_level": item.get("text_level"),
                                }
                            )
                    layout.append(
                        {
                            "index": idx,
                            "page_idx": page_idx,
                            "type": item_type,
                        }
                    )
        except json.JSONDecodeError:
            pass

    return StandardizedResult(
        sample_id=_infer_monkey_sample_id(path),
        markdown=text,
        text=text,
        raw_output_format="markdown",
        raw_output_path=str(path.resolve()),
        adapter="monkeyocr",
        extras={"content_list_path": str(content_list_path.resolve())} if content_list_path.exists() else None,
        content={
            "layout": layout,
            "tables": tables,
            "formulas": formulas,
            "text_blocks": text_blocks,
        },
    )


def adapter_hunyuan(path: Path) -> StandardizedResult:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    cleaned = strip_hunyuan_boxes(raw)
    return StandardizedResult(
        sample_id=_infer_default_sample_id(path),
        markdown=cleaned,
        text=cleaned,
        raw_output_format="text",
        raw_output_path=str(path.resolve()),
        adapter="hunyuanocr",
        extras=None,
    )


def adapter_olmocr2(path: Path) -> StandardizedResult:
    text = normalize_markdown(path.read_text(encoding="utf-8", errors="ignore"))
    return StandardizedResult(
        sample_id=_infer_default_sample_id(path),
        markdown=text,
        text=text,
        raw_output_format="text",
        raw_output_path=str(path.resolve()),
        adapter="olmocr2",
        extras=None,
    )


ADAPTERS: dict[str, Callable[[Path], StandardizedResult]] = {
    "mineru": adapter_mineru,
    "paddlevl": adapter_paddlevl,
    "ppstructurev3": adapter_ppstructurev3,
    "monkeyocr": adapter_monkey,
    "hunyuanocr": adapter_hunyuan,
    "olmocr2": adapter_olmocr2,
    "markdown": read_markdown_file,
}


def ensure_adapter(adapter_name: str) -> Callable[[Path], StandardizedResult]:
    key = adapter_name.strip().lower()
    if key not in ADAPTERS:
        raise ValueError(f"Unsupported adapter: {adapter_name}")
    return ADAPTERS[key]


def write_standardized_sample(
    *,
    sample: DatasetSample | None,
    standardized: StandardizedResult,
    output_root: str | Path,
    model_name: str,
    model_version: str | None,
    backend: str | None,
    input_mode: str,
    runtime_seconds: float | None,
    gpu_mem_mb: int | None,
) -> Path:
    root = Path(output_root).resolve()
    sample_dir = root / standardized.sample_id
    sample_dir.mkdir(parents=True, exist_ok=True)

    result_md_path = sample_dir / "result.md"
    result_json_path = sample_dir / "result.json"
    meta_json_path = sample_dir / "meta.json"

    result_md_path.write_text(standardized.markdown, encoding="utf-8")

    result_json = {
        "schema_version": "1.0",
        "dataset_name": sample.dataset_name if sample else None,
        "sample_id": standardized.sample_id,
        "model_name": model_name,
        "model_version": model_version,
        "backend": backend,
        "input_mode": input_mode,
        "raw_output_format": standardized.raw_output_format,
        "raw_output_path": standardized.raw_output_path,
        "adapter": standardized.adapter,
        "image_path": sample.image_path if sample else None,
        "image_abspath": sample.image_abspath if sample else None,
        "page_info": sample.page_info if sample else None,
        "content": {
            "markdown": standardized.markdown,
            "text": standardized.text,
            "layout": [],
            "tables": [],
            "formulas": [],
            "text_blocks": [],
        },
        "extras": standardized.extras or {},
    }
    result_json_path.write_text(json.dumps(result_json, ensure_ascii=False, indent=2), encoding="utf-8")

    status_value = None
    if standardized.extras:
        status_value = standardized.extras.get("status")
    success = bool(standardized.markdown.strip()) and status_value not in {"failed", "error"}

    meta_json = {
        "model_name": model_name,
        "model_version": model_version,
        "backend": backend,
        "runtime_seconds": runtime_seconds,
        "pages": 1,
        "success": success,
        "gpu_mem_mb": gpu_mem_mb,
        "input_mode": input_mode,
        "input_path": sample.image_abspath if sample else None,
        "raw_output_path": standardized.raw_output_path,
        "standardized_at": datetime.now().isoformat(timespec="seconds"),
    }
    meta_json_path.write_text(json.dumps(meta_json, ensure_ascii=False, indent=2), encoding="utf-8")
    return sample_dir
