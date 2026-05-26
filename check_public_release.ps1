$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $repoRoot

$expectedRepoPattern = "github\.com[:/]fengqqqing/ecg-ai-monitor(\.git)?$"
$riskCount = 0

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Add-Risk {
    param([string]$Message)
    $script:riskCount += 1
    Write-Host "[RISK] $Message" -ForegroundColor Red
}

function Get-GitOutput {
    param([string[]]$GitArgs)
    $output = & git @GitArgs 2>&1
    if ($LASTEXITCODE -ne 0) {
        Add-Risk "git $($GitArgs -join ' ') failed: $output"
        return @()
    }
    return $output
}

Write-Info "Checking public release gate from: $repoRoot"

$branchOutput = Get-GitOutput -GitArgs @("branch", "--show-current")
$branch = ""
if ($branchOutput.Count -gt 0) {
    $branch = ($branchOutput | Select-Object -First 1).Trim()
}
if ($branch -eq "github-public") {
    Write-Ok "Current branch is github-public."
} else {
    Add-Risk "Current branch is '$branch'. Public release checks should pass on github-public before publishing."
}

$originUrls = Get-GitOutput -GitArgs @("remote", "get-url", "--all", "origin")
if ($originUrls.Count -eq 0) {
    Add-Risk "Remote 'origin' is missing."
} else {
    foreach ($url in $originUrls) {
        if ($url -match $expectedRepoPattern) {
            Write-Ok "origin points to expected repo: $url"
        } else {
            Add-Risk "origin points to unexpected repo: $url"
        }
    }
}

$allRemotes = Get-GitOutput -GitArgs @("remote")
if ($allRemotes -contains "ecg-ai-monitor") {
    $namedUrls = Get-GitOutput -GitArgs @("remote", "get-url", "--all", "ecg-ai-monitor")
    foreach ($url in $namedUrls) {
        if ($url -match $expectedRepoPattern) {
            Write-Ok "ecg-ai-monitor points to expected repo: $url"
        } else {
            Add-Risk "ecg-ai-monitor points to unexpected repo: $url"
        }
    }
}

$forbiddenPatterns = @(
    "^artifacts/training/ecg/raw_data/",
    "^artifacts/training/ecg/processed_data/",
    "^artifacts/training/ecg/models/.*\.pth$",
    "^artifacts/training/ecg/models/.*\.pt$",
    "ECGMonitor/models/archive/",
    "ECGMonitor/runs/",
    "(^|/)__pycache__/",
    "^build/",
    "^dist/"
)

$trackedFiles = Get-GitOutput -GitArgs @("-c", "core.quotepath=false", "ls-files")
$forbiddenTracked = @()
foreach ($file in $trackedFiles) {
    foreach ($pattern in $forbiddenPatterns) {
        if ($file -match $pattern) {
            $forbiddenTracked += $file
            break
        }
    }
}

if ($forbiddenTracked.Count -eq 0) {
    Write-Ok "No forbidden tracked assets found."
} else {
    $uniqueForbiddenTracked = $forbiddenTracked | Sort-Object -Unique
    $displayLimit = 80
    Add-Risk "Forbidden tracked assets found:"
    $uniqueForbiddenTracked | Select-Object -First $displayLimit | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Red
    }
    if ($uniqueForbiddenTracked.Count -gt $displayLimit) {
        $remaining = $uniqueForbiddenTracked.Count - $displayLimit
        Write-Host "  ... and $remaining more" -ForegroundColor Red
    }
}

$privateWordingTerms = @(
    ([string][char]0x9762 + [string][char]0x8BD5),
    ([string][char]0x6C42 + [string][char]0x804C),
    ([string][char]0x4F5C + [string][char]0x54C1 + [string][char]0x96C6)
)
$privateWordingPattern = [string]::Join("|", $privateWordingTerms)
$docFiles = @("README.md")
if (Test-Path -LiteralPath "docs") {
    $docFiles += Get-ChildItem -LiteralPath "docs" -Recurse -File |
        Where-Object { $_.Extension -in @(".md", ".txt") } |
        ForEach-Object { $_.FullName }
}
$wordingHits = @()

foreach ($file in $docFiles) {
    if (Test-Path -LiteralPath $file) {
        $hits = Select-String -Path $file -Pattern $privateWordingPattern -Encoding UTF8
        if ($hits) {
            $wordingHits += $hits
        }
    }
}

if ($wordingHits.Count -eq 0) {
    Write-Ok "No private-context wording found in README.md or docs/."
} else {
    Add-Risk "Private-context wording found in README.md or docs/:"
    foreach ($hit in $wordingHits) {
        Write-Host "  $($hit.Path):$($hit.LineNumber): $($hit.Line)" -ForegroundColor Red
    }
}

if ($riskCount -gt 0) {
    Write-Host "Public release gate failed with $riskCount risk(s)." -ForegroundColor Red
    exit 1
}

Write-Host "Public release gate passed." -ForegroundColor Green
