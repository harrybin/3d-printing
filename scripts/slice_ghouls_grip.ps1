# Slice every delivered Ghoul's Grip print project with OrcaSlicer.
# Usage: powershell -File scripts\slice_ghouls_grip.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$orca = 'C:\Program Files\OrcaSlicer\orca-slicer.exe'
if (-not (Test-Path $orca)) { throw "OrcaSlicer not found at $orca" }

$out = Join-Path $root 'build\ghoul-final-slices'
foreach ($slug in @('black-pla', 'bone-pla', 'mechanism-pla', 'accent-pla')) {
    $project = Join-Path $root "models\ghouls-grip-print-$slug.3mf"
    $dir = Join-Path $out $slug
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $log = Join-Path $dir 'slice.log'
    $proc = Start-Process -FilePath $orca -PassThru -Wait -NoNewWindow -ArgumentList @(
        "`"$project`"", '--slice=0', "--outputdir=`"$dir`"", '--debug=3', "--logfile=`"$log`"")
    $gcode = Get-ChildItem $dir -Filter 'plate_*.gcode' -ErrorAction SilentlyContinue
    Write-Host "$slug exit=$($proc.ExitCode) plates=$($gcode.Count)"
    if ($proc.ExitCode -ne 0 -or $gcode.Count -eq 0) { throw "slicing failed for $slug" }
}
Write-Host 'all projects sliced'
