# Formats and sources

v0.1 supports TunerStudio-style MSQ XML `page/constant` and plain exported CSV.
MaxxECU XML/TSV, MLG binary, DBC/INI semantic analysis and live adapters are planned.
The MCP `capabilities` response is the executable support boundary.

- MSExtra official manuals: https://www.msextra.com/manuals/
- MaxxECU formats: https://www.maxxecu.com/webhelp/mtune-file_formats.html
- MaxxECU CAN: https://www.maxxecu.com/webhelp/can-default_maxxecu_protocol.html
- rusEFI MCP: https://github.com/rusefi/rusefi/blob/master/README-mcp.md
- Speeduino: https://github.com/speeduino/speeduino

These are sources, not shipped firmware or permission to redistribute files.
Query exact ECU firmware/board identity before interpreting code or units.
MaxxECU's documented Lua user scripts are GEN2-only. GEN1 MINI/STREET/SPORT/
RACE/PRO must not be described as supporting those scripts; see
https://www.maxxecu.com/webhelp/advanced-lua_user_scripts.html.
Install the repository package in its own environment and configure stdio
`python -m ecuworkbench.server` with `ECU_WORKBENCH_ROOT` naming one allowed
artifact directory. Paths supplied to tools are relative to that directory.
