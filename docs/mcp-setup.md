# Local Blender and OrcaSlicer MCP setup

The repository keeps the project-level MCP contract in `.vscode/mcp.json`.
Executable paths, downloaded servers, Blender add-ons, and user-specific settings
remain outside the repository.

## Blender MCP

The `blender` entry uses the official Blender Lab MCP server through `uv`. Blender
CLI and MCP are intentionally both supported: CLI scripts provide deterministic
scene builds, imports, exports and renders; MCP provides bounded interactive
inspection and visual edits in the live scene. Before enabling MCP locally:

1. Install a supported Blender version and the Blender Lab MCP add-on.
2. Install the MCP server in a user-owned directory.
3. Set `BLENDER_MCP_DIR` to the checkout's `mcp` directory.
4. Configure the add-on to listen only on `127.0.0.1:9876`.
5. Start Blender with the project `.blend` file before connecting the MCP client.

Example PowerShell environment setup:

```powershell
$env:BLENDER_MCP_DIR = "C:\Tools\blender_mcp\mcp"
$env:BLENDER_MCP_HOST = "127.0.0.1"
$env:BLENDER_MCP_PORT = "9876"
```

For a deterministic background bridge against a saved project:

```powershell
& "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" `
  --background models\project.blend --online-mode `
  --command blender_mcp --host 127.0.0.1 --port 9876
```

Use a CLI-generated `.blend` baseline before interactive MCP edits and save those
edits to a new checkpoint. MCP never owns measured pivots, bores, clearances,
mating surfaces or mechanical verification.

The official Blender page warns that the server executes LLM-generated code in
Blender without a data-protection sandbox. Use a disposable or isolated Blender
environment for sensitive files, keep the port local, and save a `.blend` checkpoint
before agent-controlled edits.

Official references:

- https://www.blender.org/lab/mcp-server/
- https://projects.blender.org/lab/blender_mcp

## OrcaSlicer MCP

OrcaSlicer has an official command-line interface for loading STL/3MF files,
inspecting model information, slicing plates, exporting sliced data, and exporting
effective settings. The project does not currently treat a third-party
`orcaslicer-mcp` package as an official OrcaSlicer component.

The `orcaslicer` entry is therefore present as an **opt-in template** and is disabled
by default. Enable it only after installing and auditing the exact MCP server you
intend to use:

1. Set `ORCASLICER_MCP_DIR` to the checked-out server directory.
2. Set `ORCASLICER_PATH` to the local OrcaSlicer executable.
3. Confirm that the server binds locally and does not upload models, profiles, or
   generated G-code.
4. Remove `"disabled": true` only after the server has been tested with a harmless
   sample project.

On Windows, OrcaSlicer is commonly installed at:

```powershell
$env:ORCASLICER_PATH = "C:\Program Files\OrcaSlicer\orca-slicer.exe"
```

If no trusted OrcaSlicer MCP server is installed, use the official CLI directly
through the `orcaslicer-print-validation` skill. Verify the installed executable's
help output before using flags:

```powershell
& $env:ORCASLICER_PATH --help
& $env:ORCASLICER_PATH --info models\part.stl
& $env:ORCASLICER_PATH models\part.3mf --slice 0 --export-slicedata artifacts\slicedata
```

The exact printer, process, and filament profiles must still be selected and
recorded. CLI availability alone does not prove that a model was successfully
sliced or that the resulting print time is valid.

Official references:

- https://www.orcaslicer.com/wiki/cli/cli_actions
- https://github.com/SoftFever/OrcaSlicer

## Configuration policy

- Do not commit secrets, API keys, absolute user paths, downloaded binaries, or
  personal profile databases.
- Keep project-wide server names and environment variable names stable.
- Keep optional or unverified integrations disabled by default.
- Treat any MCP server as local code execution and review its source and license
  before enabling it.
