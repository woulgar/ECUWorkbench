# Working in ECUWorkbench

Read constitution.md, README.md and HANDOVER.md first. Existing project instructions and owner-approved requirements govern implementation.

- Work from a bounded company ticket; record evidence and verification in its History.
- Read applicable nested AGENTS.md before modifying files.
- Preserve project data and requirements. Use the project's own environments.
- Never commit, publish, create a remote or change a model without applicable owner authorization.
- Owner T-0063 explicitly authorizes a new public GitHub repository and initial
  publication of this project's authored starter. No other project is covered.
  Keep vendor downloads, private engine tunes/logs, credentials and captures out.
- MCP v0.1 is offline and read-only. Never add ECU write/flash/actuator tools
  without their own reviewed transport, simulator/bench verification and request.
- Claude owns docs/PLAN.md architecture; Codex implements src/ and tests/ against
  the bounded artifact contract. Shared files have a single editor.
- Record completed work, actual checks, unresolved issues and next action in the handover.
- Do not describe discovered launch commands as tested until they have been run and verified.

- Local generation follows `C:/MyCodes/company/local-ai-policy.json`; validate model/environment/request overrides with its shared `company/runner/local_ai_policy.py`. New models require owner authorization. Specialized vector/audio contracts require separate compatibility review.


<!-- company-project-standard:v1 -->
## Company documentation standard

Read [PROJECT_STANDARDS.md](C:/MyCodes/company/docs/PROJECT_STANDARDS.md) for shared file formats and new-project templates.
Existing project requirements, storage contracts and model policies remain authoritative;
this reference does not migrate domain data or change those requirements.
Read AGENTS.md, constitution.md and HANDOVER.md before working. Record handovers with
evidence and UTC timestamps. Do not publish or create a remote for a local-only project.
<!-- /company-project-standard -->
