# Slice every plate in the consolidated Ghoul's Grip print project.
# Usage: powershell -File scripts\slice_ghouls_grip.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$orca = 'C:\Program Files\OrcaSlicer\orca-slicer.exe'
if (-not (Test-Path $orca)) { throw "OrcaSlicer not found at $orca" }

$out = Join-Path $root 'build\ghoul-final-slices'
$project = Join-Path $root 'models\ghouls-grip-print.3mf'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [System.IO.Compression.ZipFile]::OpenRead($project)
try {
    $reader = [System.IO.StreamReader]::new(
        $archive.GetEntry('Metadata/model_settings.config').Open())
    try { [xml]$settings = $reader.ReadToEnd() } finally { $reader.Dispose() }
    $plateCount = @($settings.config.plate).Count
} finally { $archive.Dispose() }
$dir = Join-Path $out 'print'
if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
New-Item -ItemType Directory -Path $dir -Force | Out-Null
$log = Join-Path $dir 'slice.log'
$stdout = Join-Path $dir 'stdout.log'
$stderr = Join-Path $dir 'stderr.log'
$proc = Start-Process -FilePath $orca -PassThru -Wait -NoNewWindow `
    -RedirectStandardOutput $stdout -RedirectStandardError $stderr `
    -ArgumentList @("`"$project`"", '--slice=0', "--outputdir=`"$dir`"",
                   '--debug=3', "--logfile=`"$log`"")
$gcode = Get-ChildItem $dir -Filter 'plate_*.gcode' -ErrorAction SilentlyContinue
Write-Host "print project exit=$($proc.ExitCode) plates=$($gcode.Count)"
$python = Join-Path $root '.venv\Scripts\python.exe'
foreach ($diagnosticLog in @($stdout, $stderr, $log)) {
    if (Test-Path $diagnosticLog) {
        & $python (Join-Path $PSScriptRoot 'compact_output.py') log $diagnosticLog --limit 6 --tail 3
        if ($LASTEXITCODE -ne 0) { throw "Could not summarize $diagnosticLog; inspect the full log" }
    }
}
if ($proc.ExitCode -ne 0 -or $gcode.Count -ne $plateCount) {
    throw "slicing failed or expected $plateCount plates, found $($gcode.Count)"
}
Write-Host 'consolidated print project sliced'
