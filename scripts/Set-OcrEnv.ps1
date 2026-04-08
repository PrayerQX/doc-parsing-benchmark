$root = Split-Path -Parent $PSScriptRoot
$cacheRoot = Join-Path $root "cache"

$dirs = @(
    $cacheRoot,
    (Join-Path $cacheRoot "hf"),
    (Join-Path $cacheRoot "torch"),
    (Join-Path $cacheRoot "xdg"),
    (Join-Path $cacheRoot "paddle"),
    (Join-Path $cacheRoot "modelscope"),
    (Join-Path $cacheRoot "pip"),
    (Join-Path $cacheRoot "uv"),
    (Join-Path $cacheRoot "tmp")
)

foreach ($dir in $dirs) {
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
}

$env:HF_HOME = Join-Path $cacheRoot "hf"
$env:HUGGINGFACE_HUB_CACHE = Join-Path $cacheRoot "hf"
$env:TRANSFORMERS_CACHE = Join-Path $cacheRoot "hf"
$env:TORCH_HOME = Join-Path $cacheRoot "torch"
$env:XDG_CACHE_HOME = Join-Path $cacheRoot "xdg"
$env:MODELSCOPE_CACHE = Join-Path $cacheRoot "modelscope"
$env:PADDLE_HOME = Join-Path $cacheRoot "paddle"
$env:PADDLE_PDX_CACHE_HOME = Join-Path $cacheRoot "paddle"
$env:PIP_CACHE_DIR = Join-Path $cacheRoot "pip"
$env:UV_CACHE_DIR = Join-Path $cacheRoot "uv"
$env:TMP = Join-Path $cacheRoot "tmp"
$env:TEMP = Join-Path $cacheRoot "tmp"
$env:HF_HUB_DISABLE_SYMLINKS_WARNING = "1"
$env:HF_HUB_DISABLE_XET = "1"
$env:PYTHONUTF8 = "1"

Write-Host "OCR env loaded."
Write-Host "HF_HOME=$env:HF_HOME"
Write-Host "TORCH_HOME=$env:TORCH_HOME"
Write-Host "PADDLE_HOME=$env:PADDLE_HOME"
Write-Host "PIP_CACHE_DIR=$env:PIP_CACHE_DIR"
