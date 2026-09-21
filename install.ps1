param(
    [switch]$Legacy,
    [switch]$DryRun,
    [switch]$Update,
    [string]$CodexHome = $env:CODEX_HOME
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($CodexHome)) {
    $CodexHome = Join-Path $env:USERPROFILE '.codex'
}
$petId = if ($Legacy) { 'gugu-pig-v1' } else { 'gugu-pig' }
$sourcePath = Join-Path (Join-Path $PSScriptRoot 'dist') $petId
$petRoot = [System.IO.Path]::GetFullPath((Join-Path $CodexHome 'pets'))
$targetPath = [System.IO.Path]::GetFullPath((Join-Path $petRoot $petId))
if (-not $targetPath.StartsWith($petRoot.TrimEnd('\') + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Invalid pet destination.'
}
$petManifest = Get-Content -LiteralPath (Join-Path $sourcePath 'pet.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($petManifest.id -ne $petId -or $petManifest.spritesheetPath -ne 'spritesheet.webp') {
    throw 'Invalid source manifest.'
}
$needsUpdate = $false
foreach ($name in @('pet.json', 'spritesheet.webp')) {
    $sourceFile = Join-Path $sourcePath $name
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) { throw "Missing: $sourceFile" }
    $targetFile = Join-Path $targetPath $name
    if (Test-Path -LiteralPath $targetFile) {
        if ((Get-FileHash -LiteralPath $sourceFile).Hash -ne (Get-FileHash -LiteralPath $targetFile).Hash) {
            if (-not $Update) { throw "Existing pet differs. Use -Update to back up and update it: $targetFile" }
            $needsUpdate = $true
        }
    }
}
if ($needsUpdate -and (Test-Path -LiteralPath (Join-Path $targetPath 'pet.json'))) {
    $previousManifest = Get-Content -LiteralPath (Join-Path $targetPath 'pet.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($previousManifest.id -ne $petId) { throw 'Existing package has a different ID; no files changed.' }
}
if ($DryRun) {
    Write-Output "Dry run OK: $sourcePath -> $targetPath"
    exit 0
}
if ($needsUpdate) {
    $backupRoot = Join-Path (Join-Path $CodexHome 'pet-backups') $petId
    $backupPath = Join-Path $backupRoot (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
    New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    foreach ($name in @('pet.json', 'spritesheet.webp')) {
        $previousFile = Join-Path $targetPath $name
        if (Test-Path -LiteralPath $previousFile) { Copy-Item -LiteralPath $previousFile -Destination (Join-Path $backupPath $name) }
    }
    Write-Output "Previous package backed up: $backupPath"
}
New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $sourcePath 'spritesheet.webp') -Destination (Join-Path $targetPath 'spritesheet.webp')
Copy-Item -LiteralPath (Join-Path $sourcePath 'pet.json') -Destination (Join-Path $targetPath 'pet.json')
foreach ($name in @('pet.json', 'spritesheet.webp')) {
    if ((Get-FileHash -LiteralPath (Join-Path $sourcePath $name)).Hash -ne (Get-FileHash -LiteralPath (Join-Path $targetPath $name)).Hash) {
        throw "Verification failed: $name"
    }
}
Write-Output "Installed and verified: $targetPath"
Write-Output 'Open Codex Settings > Pets and choose the new Gugu pig. Refresh/reopen settings if needed.'
