#requires -Version 5.1
<#
.SYNOPSIS
    用本地 Key 文件跑 Midscene 用例（Key 只进环境变量，不落盘、不进仓库）。
.EXAMPLE
    powershell -File run-local.ps1 -KeyFile ..\..\..\.key
    powershell -File run-local.ps1 -KeyFile C:\path\to\.key -Model qwen3-vl-plus
#>
param(
    [string]$KeyFile = "..\..\..\.key",
    [string]$Model = "qwen3-vl-plus",
    [string]$BaseUrl = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    [string]$Family = "qwen3-vl"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root
try {
    if (-not (Test-Path $KeyFile)) { throw "找不到 Key 文件: $KeyFile（用 -KeyFile 指定）" }

    $env:MIDSCENE_MODEL_API_KEY = (Get-Content $KeyFile -Raw).Trim()
    $env:MIDSCENE_MODEL_NAME = $Model
    $env:MIDSCENE_MODEL_BASE_URL = $BaseUrl
    $env:MIDSCENE_MODEL_FAMILY = $Family
    # 0 = 浏览器装在本包 node_modules 里，和根目录套件互不干扰
    $env:PLAYWRIGHT_BROWSERS_PATH = "0"

    Write-Host "[midscene] model=$Model family=$Family" -ForegroundColor Cyan
    npx playwright test --config=playwright.config.js @args
    exit $LASTEXITCODE
}
finally {
    Remove-Item Env:MIDSCENE_MODEL_API_KEY -ErrorAction SilentlyContinue
    Pop-Location
}
