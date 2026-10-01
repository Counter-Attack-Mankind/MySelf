# MyselfLM 一键启动脚本

Set-Location $PSScriptRoot

# 当前 PowerShell 临时允许执行脚本
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

# 检查 Ollama 服务是否已经启动
$ollamaRunning = Get-NetTCPConnection `
    -LocalPort 11434 `
    -State Listen `
    -ErrorAction SilentlyContinue

if (-not $ollamaRunning) {

    Write-Host "[MyselfLM] Ollama starting..."

    Start-Process `
        -FilePath "E:\mine\ollama\ollama.exe" `
        -ArgumentList "serve" `
        -WindowStyle Hidden

    # 等待 Ollama 服务起来
    Start-Sleep -Seconds 2
}

# 激活 Python 虚拟环境
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"

# 启动 MyselfLM
python "$PSScriptRoot\main.py"