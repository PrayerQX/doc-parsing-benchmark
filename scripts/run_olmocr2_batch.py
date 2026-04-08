import argparse
import json
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

from olmocr.prompts import build_no_anchoring_yaml_prompt


def iter_images(input_dir: Path) -> list[Path]:
    return sorted(
        [path for path in input_dir.rglob("*") if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}]
    )


def resize_if_needed(image: Image.Image, max_side: int | None) -> Image.Image:
    if not max_side:
        return image
    width, height = image.size
    longest = max(width, height)
    if longest <= max_side:
        return image
    scale = max_side / float(longest)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="allenai/olmOCR-2-7B-1025-FP8")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--attn", choices=["auto", "sdpa", "eager"], default="eager")
    parser.add_argument("--greedy", action="store_true")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--summary-json")
    parser.add_argument("--max-side", type=int)
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    device = "cpu" if args.cpu or not torch.cuda.is_available() else "cuda"
    dtype = torch.float32 if device == "cpu" else torch.float16
    attn = "eager" if args.attn == "auto" else args.attn

    processor = AutoProcessor.from_pretrained(args.model)
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.model,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        attn_implementation=attn,
        low_cpu_mem_usage=True,
    ).eval()
    if device != "cuda":
        model = model.to(device)

    prompt = build_no_anchoring_yaml_prompt()
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
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": str(image_path)},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

            generate_kwargs = {
                "max_new_tokens": args.max_new_tokens,
                "num_return_sequences": 1,
                "do_sample": not args.greedy,
                "use_cache": not args.no_cache,
            }
            if not args.greedy:
                generate_kwargs["temperature"] = args.temperature

            attempt_sizes = [args.max_side] if args.max_side else [None, 1280, 1024, 896, 768, 640, 512, 384]
            output = None
            used_max_side = None
            last_error = None
            for max_side in attempt_sizes:
                try:
                    image = Image.open(image_path).convert("RGB")
                    image = resize_if_needed(image, max_side)
                    inputs = processor(text=[text], images=[image], padding=True, return_tensors="pt")
                    inputs = {key: value.to(model.device) for key, value in inputs.items()}
                    with torch.no_grad():
                        output = model.generate(**inputs, **generate_kwargs)
                    used_max_side = max_side
                    break
                except torch.OutOfMemoryError as exc:
                    last_error = exc
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    continue
                except RuntimeError as exc:
                    if "out of memory" not in str(exc).lower():
                        raise
                    last_error = exc
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    continue

            if output is None:
                raise last_error if last_error else RuntimeError("olmOCR2 generation failed without output")

            prompt_length = inputs["input_ids"].shape[1]
            new_tokens = output[:, prompt_length:]
            text_output = processor.tokenizer.batch_decode(new_tokens, skip_special_tokens=True)[0]
            output_path.write_text(text_output, encoding="utf-8")

            gpu_mem_mb = None
            if torch.cuda.is_available():
                gpu_mem_mb = int(torch.cuda.max_memory_allocated() / (1024 * 1024))

            per_sample[sample_id] = {
                "status": "ok",
                "output_path": str(output_path),
                "runtime_seconds": round(time.perf_counter() - start, 4),
                "gpu_mem_mb": gpu_mem_mb,
                "used_max_side": used_max_side,
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
