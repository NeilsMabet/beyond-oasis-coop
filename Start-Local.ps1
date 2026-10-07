param([string]$RetroArch)
$ErrorActionPreference = 'Stop'
if (-not $RetroArch) {
    $workspaceRuntime = Join-Path $PSScriptRoot '..\..\work\retroarch\RetroArch-Win64\retroarch.exe'
    if (Test-Path -LiteralPath $workspaceRuntime) { $RetroArch = $workspaceRuntime }
}
if (-not $RetroArch) {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Title = 'Select RetroArch (tested: 1.22.2)'
    $picker.Filter = 'RetroArch|retroarch.exe'
    try {
        if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return }
        $RetroArch = $picker.FileName
    } finally { $picker.Dispose() }
}
$exe = (Resolve-Path -LiteralPath $RetroArch).Path
$version = (& $exe --version 2>&1 | Out-String)
if ($version -notmatch '1\.22\.2') { Write-Warning 'This launcher was tested with RetroArch 1.22.2; other versions have not been verified.' }
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$core = Join-Path $PSScriptRoot 'core\genesis_plus_gx_libretro.dll'
if ((Get-FileHash -LiteralPath $core -Algorithm SHA256).Hash -ne $manifest.core_sha256) { throw 'Core checksum mismatch.' }
$rom = Join-Path $PSScriptRoot 'generated\Beyond Oasis Coop.bin'
if (-not (Test-Path -LiteralPath $rom)) { & (Join-Path $PSScriptRoot 'Apply-Patch.ps1') }
elseif ((Get-FileHash -LiteralPath $rom -Algorithm SHA256).Hash -ne $manifest.patched_sha256) { & (Join-Path $PSScriptRoot 'Apply-Patch.ps1') }
if ((Get-FileHash -LiteralPath $rom -Algorithm SHA256).Hash -ne $manifest.patched_sha256) { throw 'ROM checksum mismatch.' }
$config = Join-Path $PSScriptRoot 'local.cfg'
& $exe --appendconfig $config -L $core $rom
