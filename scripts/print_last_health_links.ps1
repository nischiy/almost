\
    Param()
    $root = (Resolve-Path ".").Path
    $healthRoot = Join-Path $root "logs\health"
    if (!(Test-Path $healthRoot)) {
        Write-Host "No health directory found: $healthRoot"
        exit 0
    }
    $dateDirs = Get-ChildItem -Path $healthRoot -Directory | Sort-Object Name -Descending
    if ($dateDirs.Count -eq 0) {
        Write-Host "No dated health folders under $healthRoot"
        exit 0
    }
    $latest = $dateDirs[0].FullName
    $jsonl = Get-ChildItem -Path $latest -Filter "health_*.jsonl" | Sort-Object Name -Descending | Select-Object -First 1
    $md    = Get-ChildItem -Path $latest -Filter "health_*.md"    | Sort-Object Name -Descending | Select-Object -First 1

    Write-Host "Latest health folder: $latest"
    if ($jsonl) {
        $p = $jsonl.FullName
        Write-Host ("JSONL:       " + $p)
        Write-Host ("JSONL (URI): " + ("file:///" + ($p -replace '\\','/')))
    } else {
        Write-Host "JSONL: not found"
    }
    if ($md) {
        $p = $md.FullName
        Write-Host ("Markdown:       " + $p)
        Write-Host ("Markdown (URI): " + ("file:///" + ($p -replace '\\','/')))
    } else {
        Write-Host "Markdown: not found"
    }
