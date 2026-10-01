# MyselfLM 一键启动脚本
# 切换到脚本所在目录
Set-Location $PSScriptRoot
# 临时允许当前 PowerShell 运行脚本
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
# 激活虚拟环境
& "$PSScriptRoot\.venv\Scripts\Activate.ps1"
# 启动 MyselfLM
python "$PSScriptRoot\main.py"