param(
    [ValidateSet('Offline','Full')][string]$Mode = 'Offline',
    [ValidateSet('3.11','3.12')][string]$PythonVersion = '3.11',
    [switch]$Demo,
    [switch]$SkipFrontend,
    [switch]$SkipTests
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$setupArguments = @('-' + $PythonVersion, (Join-Path $PSScriptRoot 'setup.py'), '--mode', $Mode.ToLower())
if ($Demo) { $setupArguments += '--demo' }
if ($SkipFrontend) { $setupArguments += '--skip-frontend' }
if ($SkipTests) { $setupArguments += '--skip-tests' }
Push-Location $projectRoot
try {
    & py @setupArguments
    if ($LASTEXITCODE -ne 0) { throw "Setup failed with exit code $LASTEXITCODE" }
} finally { Pop-Location }
