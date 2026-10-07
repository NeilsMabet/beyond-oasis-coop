param(
    [string]$Rom = '',
    [string]$Output = (Join-Path $PSScriptRoot 'generated\Beyond Oasis Coop.bin')
)
$ErrorActionPreference = 'Stop'
if ([string]::IsNullOrWhiteSpace($Rom) -or -not (Test-Path -LiteralPath $Rom -PathType Leaf)) {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Title = 'Select original Beyond Oasis (U) ROM'
    $picker.Filter = 'Mega Drive ROM|*.bin;*.gen;*.md|All files|*.*'
    try {
        if ($picker.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) { return }
        $Rom = $picker.FileName
    } finally { $picker.Dispose() }
}
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
$inputPath = (Resolve-Path -LiteralPath $Rom).Path
$outputPath = [IO.Path]::GetFullPath($Output)
if ($inputPath -eq $outputPath) { throw 'Output must differ from the original ROM.' }
if ((Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash -ne $manifest.original_sha256) { throw 'Unsupported ROM SHA-256.' }
$patchPath = Join-Path $PSScriptRoot 'beyond-oasis-coop.bps'
if ((Get-FileHash -LiteralPath $patchPath -Algorithm SHA256).Hash -ne $manifest.bps_sha256) { throw 'BPS checksum mismatch.' }
$source = [IO.File]::ReadAllBytes($inputPath)
$patch = [IO.File]::ReadAllBytes($patchPath)
if (-not ('BeyondOasisBps' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'src\BpsPatch.cs') }
$target = [BeyondOasisBps]::Apply($source, $patch)
if ($target.Length -ne $manifest.patched_size) { throw 'Patched ROM size mismatch.' }
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = [BitConverter]::ToString($sha.ComputeHash($target)).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
if ($hash -ne $manifest.patched_sha256) { throw 'Patched ROM checksum mismatch.' }
New-Item -ItemType Directory -Force ([IO.Path]::GetDirectoryName($outputPath)) | Out-Null
[IO.File]::WriteAllBytes($outputPath,$target)
Write-Host "Ready: $outputPath"
Write-Host "SHA-256: $hash"
