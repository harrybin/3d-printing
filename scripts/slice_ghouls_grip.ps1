# Slice every plate in the consolidated Ghoul's Grip print project.
# Usage: powershell -File scripts\slice_ghouls_grip.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$orca = 'C:\Program Files\OrcaSlicer\orca-slicer.exe'
if (-not (Test-Path $orca)) { throw "OrcaSlicer not found at $orca" }

$out = Join-Path $root 'build\ghoul-final-slices'
$project = Join-Path $root 'models\ghouls-grip-print.3mf'
$dir = Join-Path $out 'print'
if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$log = Join-Path $dir 'slice.log'
$proc = Start-Process -FilePath $orca -PassThru -Wait -NoNewWindow -ArgumentList @(
    "`"$project`"", '--slice=0', "--outputdir=`"$dir`"", '--debug=3', "--logfile=`"$log`"")
$gcode = Get-ChildItem $dir -Filter 'plate_*.gcode' -ErrorAction SilentlyContinue
Write-Host "print project exit=$($proc.ExitCode) plates=$($gcode.Count)"
if ($proc.ExitCode -ne 0 -or $gcode.Count -ne 6) {
    throw "slicing failed or expected six plates, found $($gcode.Count)"
}
Write-Host 'consolidated print project sliced'
