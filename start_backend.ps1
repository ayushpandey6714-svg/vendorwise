param([ValidateSet('fixture','live')][string]$Mode = 'fixture',
      [ValidateSet('fastembed','tfidf')][string]$Embeddings = 'fastembed')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:VENDORWISE_MODE = $Mode
$env:EMBEDDING_BACKEND = $Embeddings
& .\.venv\Scripts\python.exe -m uvicorn vendorwise.api:app --host 127.0.0.1 --port 8000
