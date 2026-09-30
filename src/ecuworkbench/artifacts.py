"""Bounded artifact readers; these functions never communicate with an ECU."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import ParseError

MAX_BYTES = 10 * 1024 * 1024
MAX_CONSTANTS = 4096
MAX_TUNE_TEXT = 1024 * 1024
MAX_COLUMNS = 512
MAX_ROWS = 100_000


class ArtifactError(ValueError):
    """An unsupported, ambiguous, malformed, or out-of-root input."""


def _record(kind: str, **values: Any) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "kind": kind,
        **values,
    }


def workspace_root() -> Path:
    configured = os.environ.get("ECU_WORKBENCH_ROOT")
    if not configured:
        raise ArtifactError("ECU_WORKBENCH_ROOT must explicitly name the allowed artifact directory.")
    try:
        root = Path(configured).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ArtifactError("The configured artifact root does not resolve.") from exc
    if not root.is_dir():
        raise ArtifactError("The configured artifact root must be a directory.")
    return root


def _read(path: str, suffix: str) -> tuple[bytes, dict[str, Any]]:
    root = workspace_root()
    if not isinstance(path, str) or not path or "\x00" in path:
        raise ArtifactError("A nonempty artifact path is required.")
    requested = Path(path)
    # Windows alternate streams must never bypass extension or size checks.
    if ":" in path.replace(requested.drive, "", 1):
        raise ArtifactError("Alternate streams and colon-containing paths are unsupported.")
    try:
        resolved = (requested if requested.is_absolute() else root / requested).resolve(strict=True)
        relative = resolved.relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        raise ArtifactError("Artifact must resolve to a file inside ECU_WORKBENCH_ROOT.") from exc
    if not resolved.is_file() or resolved.suffix.lower() != suffix:
        raise ArtifactError(f"Only ordinary {suffix} files are supported by this reader.")
    try:
        with resolved.open("rb") as stream:
            if os.fstat(stream.fileno()).st_size > MAX_BYTES:
                raise ArtifactError("Artifact exceeds the 10 MiB size limit.")
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ArtifactError("Artifact exceeds the 10 MiB size limit.")
        # Reject a changed link target after reading rather than returning escaped content.
        if resolved.resolve(strict=True) != resolved:
            raise ArtifactError("Artifact path changed while it was read.")
    except OSError as exc:
        raise ArtifactError("Artifact could not be read.") from exc
    return data, {
        "path": relative.as_posix(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def inspect_tune(path: str) -> dict[str, Any]:
    """Inspect an MSQ export, preserving strings and units without changing values."""
    data, source = _read(path, ".msq")
    try:
        document = ElementTree.fromstring(data, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    except (ParseError, DefusedXmlException, ValueError) as exc:
        raise ArtifactError("MSQ must be well-formed XML without DTDs or entities.") from exc
    if _local(document.tag).lower() != "msq":
        raise ArtifactError("Only TunerStudio-style MSQ XML is supported.")
    signatures: set[str] = set()
    firmware_infos: set[str] = set()
    for node in document.iter():
        if _local(node.tag) == "versionInfo":
            # firmwareInfo describes a version; it is not the serial/INI signature.
            # Unverified attribute aliases must not manufacture firmware identity.
            signature = node.attrib.get("signature", "")
            if signature.strip():
                signatures.add(signature)
            firmware_info = node.attrib.get("firmwareInfo", "")
            if firmware_info.strip():
                firmware_infos.add(firmware_info)
    if len(signatures) > 1:
        raise ArtifactError("Conflicting firmware signatures make this export ambiguous.")
    if len(firmware_infos) > 1:
        raise ArtifactError("Conflicting firmware display metadata makes this export ambiguous.")
    constants: list[dict[str, str | None]] = []
    keys: set[tuple[str, str]] = set()
    pages: set[str] = set()
    constant_text_size = 0
    for page in document.iter():
        if _local(page.tag) != "page":
            continue
        page_id = page.attrib.get("number", "").strip()
        if not page_id or page_id in pages:
            raise ArtifactError("MSQ pages must have distinct nonempty number attributes.")
        pages.add(page_id)
        for node in page:
            if _local(node.tag) != "constant":
                continue
            name = node.attrib.get("name", "").strip()
            key = (page_id, name)
            if not name or key in keys:
                raise ArtifactError("Constants must have distinct nonempty names within each page.")
            if len(node):
                raise ArtifactError("Nested constant values are unsupported; use a plain-text MSQ export.")
            keys.add(key)
            value = (node.text or "").strip()
            units = node.attrib.get("units")
            constant_text_size += sum(len(text) for text in (name, units or "", value))
            if constant_text_size > MAX_TUNE_TEXT:
                raise ArtifactError("Constant text exceeds the 1 MiB inspection output budget.")
            constants.append({
                "page": page_id,
                "name": name,
                "units": units,
                "value": value,
            })
            if len(constants) > MAX_CONSTANTS:
                raise ArtifactError("MSQ exceeds the 4096-constant inspection limit.")
    if not constants:
        raise ArtifactError("MSQ has no supported page/constant entries.")
    return _record("tune_inspection", source=source,
                   firmware_signature=next(iter(signatures), None),
                   firmware_info=next(iter(firmware_infos), None), constants=constants,
                   interpretation="Raw export metadata only; no calibration validation or tuning recommendations.")


def compare_tunes(left: str, right: str) -> dict[str, Any]:
    """Compare raw constants only when firmware signatures and shared units agree."""
    before, after = inspect_tune(left), inspect_tune(right)
    signature = before["firmware_signature"]
    if not signature or signature != after["firmware_signature"]:
        raise ArtifactError("Comparison requires matching nonempty firmware signatures.")
    old = {(item["page"], item["name"]): item for item in before["constants"]}
    new = {(item["page"], item["name"]): item for item in after["constants"]}
    for key in old.keys() & new.keys():
        if old[key]["units"] is None or new[key]["units"] is None:
            raise ArtifactError(f"Unknown units for page {key[0]}, constant {key[1]}; explicit unit metadata is required.")
        if old[key]["units"] != new[key]["units"]:
            raise ArtifactError(f"Unit mismatch for page {key[0]}, constant {key[1]}; no conversion is inferred.")
    changes = []
    for page, name in sorted(old.keys() | new.keys()):
        previous, current = old.get((page, name)), new.get((page, name))
        if previous == current:
            continue
        changes.append({"page": page, "name": name,
                        "change": "added" if previous is None else "removed" if current is None else "changed",
                        "before": previous, "after": current})
    return _record("tune_comparison", left=before["source"], right=after["source"],
                   firmware_signature=signature,
                   left_firmware_info=before["firmware_info"],
                   right_firmware_info=after["firmware_info"], changes=changes,
                   interpretation="String-level export differences; no physical equivalence or safe calibration is asserted.")


def summarize_log(path: str, units: dict[str, str] | None = None) -> dict[str, Any]:
    """Summarize a plain header-first comma CSV; units come only from the caller."""
    data, source = _read(path, ".csv")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ArtifactError("CSV must be UTF-8.") from exc
    if "\x00" in text:
        raise ArtifactError("Binary log formats are unsupported; export a plain CSV first.")
    try:
        reader = csv.reader(io.StringIO(text, newline=""), strict=True)
        headers = next(reader, [])
        if not headers or any(not header.strip() for header in headers) or len(set(headers)) != len(headers):
            raise ArtifactError("CSV requires unique nonempty column headers.")
        if len(headers) > MAX_COLUMNS:
            raise ArtifactError("CSV exceeds the 512-channel limit.")
        supplied_units = units or {}
        if not isinstance(supplied_units, dict) or any(
            key not in headers or not isinstance(value, str) or not value.strip()
            for key, value in supplied_units.items()
        ):
            raise ArtifactError("Units must map existing CSV headers to nonempty unit strings.")
        channels: dict[str, dict[str, Any]] = {
            header: {"unit": supplied_units.get(header), "unit_source": "caller" if header in supplied_units else "unknown",
                     "numeric_count": 0, "missing_count": 0, "nonnumeric_count": 0, "nonfinite_count": 0,
                     "min": None, "max": None, "mean": None}
            for header in headers
        }
        sums = {header: 0.0 for header in headers}
        rows = 0
        for row in reader:
            if len(row) != len(headers):
                raise ArtifactError(f"CSV row {rows + 2} has a different field count from its header.")
            rows += 1
            if rows > MAX_ROWS:
                raise ArtifactError("CSV exceeds the 100000-row limit.")
            for header, field in zip(headers, row):
                channel = channels[header]
                if not field.strip():
                    channel["missing_count"] += 1
                    continue
                try:
                    value = float(field)
                except ValueError:
                    channel["nonnumeric_count"] += 1
                    continue
                if not math.isfinite(value):
                    channel["nonfinite_count"] += 1
                    continue
                channel["numeric_count"] += 1
                count = channel["numeric_count"]
                # Weighted online mean avoids overflow when summing large finite values.
                sums[header] = sums[header] * ((count - 1) / count) + value / count
                channel["min"] = value if channel["min"] is None else min(value, channel["min"])
                channel["max"] = value if channel["max"] is None else max(value, channel["max"])
        for header, channel in channels.items():
            if channel["numeric_count"]:
                channel["mean"] = sums[header]
    except csv.Error as exc:
        raise ArtifactError("Malformed or oversized CSV fields.") from exc
    return _record("log_summary", source=source, rows=rows, channels=channels,
                   interpretation="Descriptive numeric statistics only; timestamps, units and calibration correctness are not inferred.")


def capabilities() -> dict[str, Any]:
    """Describe measured format scope without claiming ECU connectivity."""
    return _record("capabilities", mode="offline_read_only", tools=[
        "capabilities", "inspect_tune", "compare_tunes", "summarize_log"],
        formats={"msq": "TunerStudio-style page/constant XML; synthetic fixture verified",
                 "csv": "UTF-8, header-first, comma-separated numeric/text channels"},
        unsupported=["native MLG", "native MaxxECU tune/log", "serial", "CAN transmission", "firmware flashing", "calibration writes"],
        limits={"bytes": MAX_BYTES, "constants": MAX_CONSTANTS, "tune_text_characters": MAX_TUNE_TEXT,
                "columns": MAX_COLUMNS, "rows": MAX_ROWS},
        external_requests=False, local_inference=False)
