$ErrorActionPreference = "Stop"

$RepoOwner = "caofei277"
$RepoName = "ezlx-skills"
$RepoUrl = "https://github.com/${RepoOwner}/${RepoName}"
$Branch = "main"
$SkillName = "opencode-cross-platform-setup"
$TargetDir = Join-Path $env:USERPROFILE ".config\opencode\skills"

Write-Host "==> Installing skill: ${SkillName}" -ForegroundColor Cyan
Write-Host "==> Target: ${TargetDir}\${SkillName}\"

if (!(Get-Command curl -ErrorAction SilentlyContinue) -and !(Get-Command Invoke-WebRequest -ErrorAction SilentlyContinue)) {
    Write-Host "Error: curl or Invoke-WebRequest is required." -ForegroundColor Red
    exit 1
}

if (!(Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

$TempZip = Join-Path $env:TEMP "${RepoName}.zip"
$TempDir = Join-Path $env:TEMP "${RepoName}-extract"

Write-Host "==> Downloading ${RepoName}..."
Invoke-WebRequest -Uri "${RepoUrl}/archive/refs/heads/${Branch}.zip" -OutFile $TempZip

if (Test-Path $TempDir) {
    Remove-Item $TempDir -Recurse -Force
}
Expand-Archive -Path $TempZip -DestinationPath $TempDir -Force

$SourcePath = Join-Path $TempDir "${RepoName}-${Branch}\skills\${SkillName}"
if (!(Test-Path $SourcePath)) {
    Write-Host "Error: Skill '${SkillName}' not found in repository." -ForegroundColor Red
    Remove-Item $TempZip -Force
    Remove-Item $TempDir -Recurse -Force
    exit 1
}

$DestPath = Join-Path $TargetDir $SkillName
if (Test-Path $DestPath) {
    Write-Host "==> Updating existing skill..."
    Remove-Item $DestPath -Recurse -Force
}

Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force

Remove-Item $TempZip -Force
Remove-Item $TempDir -Recurse -Force

if (Test-Path (Join-Path $DestPath "SKILL.md")) {
    Write-Host "==> OK: ${SkillName} installed successfully" -ForegroundColor Green
    Write-Host "    Location: ${DestPath}\"
} else {
    Write-Host "Error: Installation failed - SKILL.md not found" -ForegroundColor Red
    exit 1
}
