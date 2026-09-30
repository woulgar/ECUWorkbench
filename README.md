# ECUWorkbench

[Public repository](https://github.com/woulgar/ECUWorkbench) · [Verified CI](https://github.com/woulgar/ECUWorkbench/actions/runs/36736023360)

Local ECU artifact tools and an engineering skill for Claude Code and Codex.
This v0.1 starter inspects exported files; it does not connect to an ECU,
flash firmware, burn tunes or generate engine calibration targets.

## Implemented

| MCP tool | Result |
| --- | --- |
| `capabilities` | Executable format support, limits and unsupported operations |
| `inspect_tune` | TunerStudio-style MSQ page/constant values, original units, firmware metadata and SHA256 |
| `compare_tunes` | Raw changes between matching nonempty firmware signatures and compatible declared units |
| `summarize_log` | Exported comma-CSV statistics, missing/text/nonfinite counts and unit provenance |

MSQ parsing is generic format support verified with synthetic fixtures, not a
certification for every firmware/board. `firmwareInfo` display text is preserved
separately from actual firmware signature. Missing identity remains unknown.

## Direction

MSExtra source visibility is not a blanket open-source license. MaxxECU provides
downloads, documented exports and CAN definitions; its firmware open-source
license was not established. rusEFI already has substantial ECU/CAN MCP tools.
We do not claim the first or only AI ECU tool.

Our scope: a cross-vendor artifact workbench, file provenance, version checks,
explicit units, and later reviewable change proposals. Vendor-native transports
can be integrated rather than cloned.

Read [primary-source research](docs/ECOSYSTEM_RESEARCH.md),
[Claude-authored roadmap](docs/PLAN.md) and [acceptance evidence](HANDOVER.md).
Native MaxxECU XML/TSV, INI/DBC semantics, simulator and hardware adapters are
planned. Engine calibration correctness is unmeasured.

## Install and test

Python 3.12+, a separate environment, no model or API key required.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
New-Item -ItemType Directory -Path workspace -Force
```

On Linux/macOS use `python3` and `.venv/bin/python`. `requirements.lock.txt`
records the tested Windows environment; `pyproject.toml` defines portable
dependency ranges. All four tools use official MCP SDK stdio transport.

## Claude Code / Codex

```powershell
.\.venv\Scripts\python.exe scripts\install_skill.py --host claude
.\.venv\Scripts\python.exe scripts\install_skill.py --host codex
```

Register the MCP using your actual paths. Example local Windows installation:

```powershell
claude mcp add --transport stdio --scope local ecuworkbench --env ECU_WORKBENCH_ROOT=C:/MyCodes/ECUWorkbench/workspace -- C:/MyCodes/ECUWorkbench/.venv/Scripts/python.exe -m ecuworkbench.server
codex mcp add ecuworkbench --env ECU_WORKBENCH_ROOT=C:/MyCodes/ECUWorkbench/workspace -- C:/MyCodes/ECUWorkbench/.venv/Scripts/python.exe -m ecuworkbench.server
```

Start a new coding session to discover the installed capabilities. Try:
**“Use ecu-workbench to inspect baseline.msq and proposed.msq, explain
firmware/unit compatibility, then summarize run.csv without changing files.”**

Put artifacts inside the configured directory. Tool paths are relative to
`ECU_WORKBENCH_ROOT`. Reads reject traversal, resolved symlink escapes, invalid
XML, DTD/entities, incompatible comparisons and oversized artifacts.

Portable Agent Plugins manifests and Claude/Codex compatibility manifests are
included. Plugin loading requires the installed Python package; generic
`python` must resolve to that environment. Local CLI registration was tested;
public plugin directory/account submission was not performed.

## License and storage

Authored code/skill: MIT. [Third-party boundaries](THIRD_PARTY.md) keep vendor
firmware, manuals, definitions and private tunes out of this package.
`workspace/`, `.work/`, environments and native captures are Git-ignored.

The shared company template created this project. Owner T-0063 explicitly
authorizes this new public repository; all other local-only projects stay local.
Read AGENTS.md, constitution.md and HANDOVER.md before working.


<!-- company-project-standard:v1 -->
## Company documentation standard

Read [PROJECT_STANDARDS.md](C:/MyCodes/company/docs/PROJECT_STANDARDS.md) for shared file formats and new-project templates.
Existing project requirements, storage contracts and model policies remain authoritative;
this reference does not migrate domain data or change those requirements.
Read AGENTS.md, constitution.md and HANDOVER.md before working. Record handovers with
evidence and UTC timestamps. Do not publish or create a remote for a local-only project.
<!-- /company-project-standard -->
