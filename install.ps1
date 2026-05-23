$ErrorActionPreference = "Stop"

$RepoOwner = "caofei277"
$RepoName = "ezlx-skills"
$RepoUrl = "https://github.com/${RepoOwner}/${RepoName}"
$Branch = "main"
$TargetDir = Join-Path $env:USERPROFILE ".config\opencode\skills"

if (!(Get-Command curl -ErrorAction SilentlyContinue) -and !(Get-Command Invoke-WebRequest -ErrorAction SilentlyContinue)) {
    Write-Host "Error: curl or Invoke-WebRequest is required." -ForegroundColor Red
    exit 1
}

if (!(Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

$TempZip = Join-Path $env:TEMP "${RepoName}.zip"
$TempDir = Join-Path $env:TEMP "${RepoName}-extract"

Write-Host "==> Downloading ${RepoName}..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "${RepoUrl}/archive/refs/heads/${Branch}.zip" -OutFile $TempZip

if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
Expand-Archive -Path $TempZip -DestinationPath $TempDir -Force

$SkillsSource = Join-Path $TempDir "${RepoName}-${Branch}\skills"

if (!(Test-Path $SkillsSource)) {
    Write-Host "Error: skills/ directory not found in repository." -ForegroundColor Red
    Remove-Item $TempZip -Force
    Remove-Item $TempDir -Recurse -Force
    exit 1
}

if ($args.Count -gt 0) {
    $SkillNames = $args
} else {
    $SkillNames = @()
    Get-ChildItem -LiteralPath $SkillsSource -Directory | ForEach-Object {
        $SkillNames += $_.Name
    }
}

$Installed = 0
$Failed = 0

foreach ($SkillName in $SkillNames) {
    $SourcePath = Join-Path $SkillsSource $SkillName
    if (!(Test-Path $SourcePath)) {
        Write-Host "Error: Skill '${SkillName}' not found." -ForegroundColor Red
        $Failed++
        continue
    }

    $DestPath = Join-Path $TargetDir $SkillName
    if (Test-Path $DestPath) {
        Write-Host "==> Updating: ${SkillName}" -ForegroundColor Yellow
        Remove-Item $DestPath -Recurse -Force
    } else {
        Write-Host "==> Installing: ${SkillName}" -ForegroundColor Cyan
    }

    Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force

    if (Test-Path (Join-Path $DestPath "SKILL.md")) {
        Write-Host "    OK: ${SkillName}" -ForegroundColor Green
        $Installed++
    } else {
        Write-Host "    Error: SKILL.md not found in ${SkillName}" -ForegroundColor Red
        $Failed++
    }
}

Remove-Item $TempZip -Force
Remove-Item $TempDir -Recurse -Force

Write-Host ""
Write-Host "==> Done: ${Installed} installed, ${Failed} failed" -ForegroundColor Cyan

if ($Failed -gt 0) { exit 1 }
exit 0
