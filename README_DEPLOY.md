# OCR Models Deployment Notes

Note: the original local workspace root was `D:\OCR`. In this repository, replace that path with your own repo root.

## Shared Environment

Before running any model, load the shared cache environment so all model caches stay under ASCII-only paths:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
. D:\OCR\scripts\Set-OcrEnv.ps1
```

Shared cache roots:

- `D:\OCR\cache\hf`
- `D:\OCR\cache\torch`
- `D:\OCR\cache\modelscope`
- `D:\OCR\cache\paddle`
- `D:\OCR\cache\tmp`

## Smoke Inputs

Generated sample files:

- `D:\OCR\samples\smoke_input.png`
- `D:\OCR\samples\smoke_input.pdf`

## 1. MinerU-2.5-VLM

Environment:

```powershell
& D:\OCR\venvs\mineru\Scripts\Activate.ps1
```

Smoke run:

```powershell
mineru -p D:\OCR\samples\smoke_input.png -o D:\OCR\logs\mineru_smoke -b vlm-auto-engine
```

Verified output:

- `D:\OCR\logs\mineru_smoke`

## 2. HunyuanOCR

Environment:

```powershell
& D:\OCR\venvs\hunyuan\Scripts\Activate.ps1
```

Verified output:

- `D:\OCR\logs\hunyuan_smoke.txt`

Note:

- Installed `transformers` from the repo-recommended commit.
- Patched local `transformers` install to avoid hard-coded BF16 image casting on non-BF16 GPUs like GTX 1080 Ti.

## 3. MonkeyOCR v1.5

Environment:

```powershell
& D:\OCR\venvs\monkey\Scripts\Activate.ps1
Set-Location D:\OCR\repos\MonkeyOCR-main
```

Smoke run:

```powershell
python parse.py D:\OCR\samples\smoke_input.png -t text -c model_configs.local.yaml -o D:\OCR\logs\monkey_smoke
```

Verified output:

- `D:\OCR\logs\monkey_smoke\smoke_input\smoke_input_text_result.md`

Note:

- Uses the downloaded `MonkeyOCR-pro-1.2B` weights.
- Local config avoids unsupported Paddle layout dependency on this setup.
- Source patch added a fallback from `flash_attention_2` to `sdpa`.

## 4. PaddleOCR-VL-1.5

Environment:

```powershell
& D:\OCR\venvs\paddlevl\Scripts\Activate.ps1
```

Smoke run:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'
paddleocr doc_parser -i D:\OCR\samples\smoke_input.png --save_path D:\OCR\logs\paddlevl_smoke --pipeline_version v1.5 --device gpu:0 --max_new_tokens 256
```

Verified output:

- `D:\OCR\logs\paddlevl_smoke`

Note:

- Download issues were fixed by forcing Hugging Face cache under `D:\OCR\cache\hf` and disabling Xet in `Set-OcrEnv.ps1`.

## 5. PP-StructureV3

Environment:

```powershell
& D:\OCR\venvs\paddlevl\Scripts\Activate.ps1
```

Smoke run:

```powershell
$env:PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK='True'
paddleocr pp_structurev3 -i D:\OCR\samples\smoke_input.png --save_path D:\OCR\logs\ppstructurev3_smoke --device gpu:0
```

Verified output:

- `D:\OCR\logs\ppstructurev3_smoke`

Note:

- `PP-StructureV3` currently reuses the `D:\OCR\venvs\paddlevl` environment.
- `python-docx` is required because the CLI saves `.docx` output in addition to Markdown and JSON.
- Cache roots should still be loaded through `Set-OcrEnv.ps1` so Paddle assets stay under ASCII-only paths.

## 6. olmOCR2

Environment:

```powershell
& D:\OCR\venvs\olmocr\Scripts\Activate.ps1
```

Smoke run:

```powershell
python D:\OCR\scripts\run_olmocr2_smoke.py --image D:\OCR\samples\smoke_input.png --output D:\OCR\logs\olmocr2_smoke.txt --max-new-tokens 8 --attn eager --greedy --no-cache
```

Verified output:

- `D:\OCR\logs\olmocr2_smoke.txt`

Important limitation:

- `olmOCR-2-7B-1025-FP8` is not comfortable on GTX 1080 Ti 11GB.
- The working path on this machine is a degraded compatibility mode:
  - `attn=eager`
  - greedy decoding
  - `use_cache=False`
  - CPU offload by `device_map="auto"`
- This proves the model can load and generate locally, but it is much slower than the other four models and is below the official sweet spot for local deployment.

## Installed Virtual Envs

- `D:\OCR\venvs\mineru`
- `D:\OCR\venvs\hunyuan`
- `D:\OCR\venvs\monkey`
- `D:\OCR\venvs\paddlevl`
- `D:\OCR\venvs\olmocr`
