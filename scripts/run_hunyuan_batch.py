import argparse
import json
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, HunYuanVLForConditionalGeneration


DOC_PARSE_PROMPT = "提取文档图片中正文的所有信息用markdown格式表示，其中页眉、页脚部分忽略，表格用html格式表示，文档中公式用latex格式表示，按照阅读顺序组织进行解析。"


def clean_repeated_substrings(text: str) -> str:
    n = len(text)
    if n < 8000:
        return text
    for length in range(2, n // 10 + 1):
        candidate = text[-length:]
        count = 0
        i = n - length
        while i >= 0 and text[i : i + length] == candidate:
            count += 1
            i -= length
        if count >= 10:
            return text[: n - length * (count - 1)]
    return text


def iter_images(input_dir: Path) -> list[Path]:
    return sorted(
        [path for path in input_dir.rglob("*") if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="tencent/HunyuanOCR")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=4096)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument("--summary-json")
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if args.device != "auto":
        device = args.device
    dtype = torch.float16 if device == "cuda" else torch.float32

    processor = AutoProcessor.from_pretrained(args.model, use_fast=False)
    model = HunYuanVLForConditionalGeneration.from_pretrained(
        args.model,
        attn_implementation="eager",
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
    ).eval()
    if device != "cuda":
        model = model.to(device)

    samples = iter_images(input_dir)
    if args.limit:
        samples = samples[: args.limit]

    per_sample = {}
    for image_path in samples:
        sample_id = image_path.stem
        output_path = output_dir / f"{sample_id}.txt"
        if args.resume and output_path.exists():
            per_sample[sample_id] = {"status": "skipped_existing", "output_path": str(output_path)}
            continue

        start = time.perf_counter()
        try:
            image = Image.open(image_path).convert("RGB")
            messages = [
                {"role": "system", "content": ""},
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": str(image_path)},
                        {"type": "text", "text": DOC_PARSE_PROMPT},
                    ],
                },
            ]
            prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = processor(text=[prompt], images=image, padding=True, return_tensors="pt")

            if device == "cuda":
                model_device = next(model.parameters()).device
                inputs = {key: value.to(model_device) for key, value in inputs.items()}

            with torch.no_grad():
                generated_ids = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
            input_ids = inputs["input_ids"]
            generated_ids_trimmed = [
                out_ids[len(in_ids) :] for in_ids, out_ids in zip(input_ids, generated_ids)
            ]
            output_text = processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]
            output_text = clean_repeated_substrings(output_text)
            output_path.write_text(output_text, encoding="utf-8")

            gpu_mem_mb = None
            if torch.cuda.is_available():
                gpu_mem_mb = int(torch.cuda.max_memory_allocated() / (1024 * 1024))

            per_sample[sample_id] = {
                "status": "ok",
                "output_path": str(output_path),
                "runtime_seconds": round(time.perf_counter() - start, 4),
                "gpu_mem_mb": gpu_mem_mb,
            }
        except Exception as exc:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            per_sample[sample_id] = {
                "status": "failed",
                "output_path": str(output_path),
                "runtime_seconds": round(time.perf_counter() - start, 4),
                "error": f"{type(exc).__name__}: {exc}",
            }

    summary = {
        "model": args.model,
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
