"""Synthetic exports exercise parsing and refusal boundaries, not engine accuracy."""

import hashlib
import json
import pytest

from ecuworkbench.artifacts import ArtifactError, capabilities, compare_tunes, inspect_tune, summarize_log


@pytest.fixture
def root(tmp_path, monkeypatch):
    directory = tmp_path / "artifacts"
    directory.mkdir()
    monkeypatch.setenv("ECU_WORKBENCH_ROOT", str(directory))
    return directory


def msq(signature="SYNTHETIC-FW-1", value="100", units="rpm", namespace="", extras="", firmware_info="Synthetic version 1"):
    ns = f' xmlns="{namespace}"' if namespace else ""
    signature_attr = f' signature="{signature}"' if signature is not None else ""
    firmware_info_attr = f' firmwareInfo="{firmware_info}"' if firmware_info is not None else ""
    units_attr = f' units="{units}"' if units is not None else ""
    return (f'<msq{ns}><versionInfo{signature_attr}{firmware_info_attr}/><page number="1">'
            f'<constant name="syntheticRPM"{units_attr}>{value}</constant>{extras}</page></msq>')


def write(root, name, content):
    path = root / name
    path.write_text(content, encoding="utf-8", newline="")
    return path


def test_inspect_namespace_preserves_value_unit_and_evidence(root):
    path = write(root, "sample.msq", msq(value="100 200\n300 400", namespace="urn:synthetic"))
    result = inspect_tune("sample.msq")
    assert result["firmware_signature"] == "SYNTHETIC-FW-1"
    assert result["firmware_info"] == "Synthetic version 1"
    assert result["constants"] == [{"page": "1", "name": "syntheticRPM", "units": "rpm", "value": "100 200\n300 400"}]
    assert result["source"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert result["generated_at"].endswith("Z")
    assert result["schema_version"] == 1


def test_inspection_can_report_unknown_signature_and_units(root):
    write(root, "sample.msq", msq(signature=None, units=None))
    result = inspect_tune("sample.msq")
    assert result["firmware_signature"] is None
    assert result["constants"][0]["units"] is None


@pytest.mark.parametrize("attribute", ["firmwareSignature", "firmwareInfo"])
def test_display_metadata_and_unverified_alias_do_not_supply_signature(root, attribute):
    body = msq(firmware_info=None).replace("signature=", f"{attribute}=")
    write(root, "before.msq", body)
    write(root, "after.msq", body)
    assert inspect_tune("before.msq")["firmware_signature"] is None
    with pytest.raises(ArtifactError, match="firmware signatures"):
        compare_tunes("before.msq", "after.msq")


def test_signature_and_display_metadata_remain_separate_raw_values(root):
    write(root, "before.msq", msq(signature=" SERIAL-1 ", firmware_info=" Version 1 "))
    write(root, "after.msq", msq(signature=" SERIAL-1 ", firmware_info=" Version 2 "))
    inspected = inspect_tune("before.msq")
    assert inspected["firmware_signature"] == " SERIAL-1 "
    assert inspected["firmware_info"] == " Version 1 "
    compared = compare_tunes("before.msq", "after.msq")
    assert compared["left_firmware_info"] == " Version 1 "
    assert compared["right_firmware_info"] == " Version 2 "
    assert compared["changes"] == []


def test_compare_reports_changed_added_removed_without_writing(root):
    first = write(root, "before.msq", msq(extras='<constant name="removed" units="kPa">2</constant>'))
    second = write(root, "after.msq", msq(value="101", extras='<constant name="added" units="kPa">3</constant>'))
    original = (first.read_bytes(), second.read_bytes())
    differences = compare_tunes("before.msq", "after.msq")
    assert [item["change"] for item in differences["changes"]] == ["added", "removed", "changed"]
    assert (first.read_bytes(), second.read_bytes()) == original


@pytest.mark.parametrize("signature", ["OTHER-FW", None])
def test_compare_refuses_unknown_or_different_firmware(root, signature):
    write(root, "before.msq", msq())
    write(root, "after.msq", msq(signature=signature))
    with pytest.raises(ArtifactError, match="firmware signatures"):
        compare_tunes("before.msq", "after.msq")


@pytest.mark.parametrize("unit", ["rad/s", None])
def test_compare_refuses_changed_or_missing_units(root, unit):
    write(root, "before.msq", msq())
    write(root, "after.msq", msq(units=unit))
    with pytest.raises(ArtifactError, match="Unit mismatch|Unknown units"):
        compare_tunes("before.msq", "after.msq")


def test_both_unknown_units_refused_but_explicit_dimensionless_allowed(root):
    write(root, "before.msq", msq(units=None))
    write(root, "after.msq", msq(units=None, value="101"))
    with pytest.raises(ArtifactError, match="Unknown units"):
        compare_tunes("before.msq", "after.msq")
    write(root, "before.msq", msq(units=""))
    write(root, "after.msq", msq(units="", value="101"))
    assert len(compare_tunes("before.msq", "after.msq")["changes"]) == 1


@pytest.mark.parametrize("body", [
    '<!DOCTYPE msq [<!ENTITY secret SYSTEM "file:///etc/passwd">]><msq><page number="1"><constant name="x">&secret;</constant></page></msq>',
    '<!DOCTYPE msq><msq><page number="1"><constant name="x">1</constant></page></msq>',
    '<msq><page>',
    '<not-msq/>',
    msq(extras='<constant name="syntheticRPM" units="rpm">999</constant>'),
    '<msq><page number="1"><constant name="x"><nested>1</nested></constant></page></msq>',
    '<msq><page number="1"><constant name="x">1</constant></page><page number="1"><constant name="y">2</constant></page></msq>',
    '<msq><versionInfo firmwareInfo="ONE"/><versionInfo firmwareInfo="TWO"/><page number="1"><constant name="x">1</constant></page></msq>',
    '<msq><versionInfo signature="ONE"/><versionInfo signature="TWO"/><page number="1"><constant name="x">1</constant></page></msq>',
    '<msq><page number="1"/></msq>',
])
def test_malformed_ambiguous_or_entity_xml_refused(root, body):
    write(root, "bad.msq", body)
    with pytest.raises(ArtifactError):
        inspect_tune("bad.msq")


def test_csv_stats_missing_text_and_nonfinite_are_distinct(root):
    write(root, "log.csv", 'rpm,note,pressure\r\n100,"hello, world",1\r\n200,,nan\r\n,ok,3\r\ninf,stop,4\r\n')
    result = summarize_log("log.csv", {"rpm": "rpm", "pressure": "kPa"})
    assert result["rows"] == 4
    assert result["channels"]["rpm"] == {
        "unit": "rpm", "unit_source": "caller", "numeric_count": 2, "missing_count": 1,
        "nonnumeric_count": 0, "nonfinite_count": 1, "min": 100.0, "max": 200.0, "mean": 150.0,
    }
    assert result["channels"]["note"]["unit"] is None
    assert result["channels"]["note"]["nonnumeric_count"] == 3
    assert result["channels"]["pressure"]["nonfinite_count"] == 1
    json.dumps(result, allow_nan=False)


def test_large_finite_csv_values_do_not_overflow_mean(root):
    write(root, "log.csv", "x\n1e308\n1e308\n")
    result = summarize_log("log.csv")
    assert result["channels"]["x"]["mean"] == 1e308
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("body", ["rpm,rpm\n1,2\n", "rpm,\n1,2\n", "rpm,x\n1\n", 'rpm\n"unterminated', "", "rpm\nx\x00y\n"])
def test_invalid_csv_refused(root, body):
    write(root, "log.csv", body)
    with pytest.raises(ArtifactError):
        summarize_log("log.csv")


def test_unknown_unit_channel_refused(root):
    write(root, "log.csv", "rpm\n100\n")
    with pytest.raises(ArtifactError, match="Units"):
        summarize_log("log.csv", {"speed": "km/h"})


def test_root_required(monkeypatch):
    monkeypatch.delenv("ECU_WORKBENCH_ROOT", raising=False)
    with pytest.raises(ArtifactError, match="explicitly"):
        inspect_tune("some.msq")


def test_outside_path_traversal_absolute_and_suffix_refused(root):
    outside = write(root.parent, "private.msq", msq())
    for path in ["../private.msq", str(outside), "missing.msq", "file.msq:stream"]:
        with pytest.raises(ArtifactError):
            inspect_tune(path)
    write(root, "native.mlg", "rpm\n1\n")
    with pytest.raises(ArtifactError, match=".csv"):
        summarize_log("native.mlg")


def test_symlink_cannot_escape(root):
    outside = write(root.parent, "private.msq", msq())
    link = root / "escape.msq"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Operating system does not permit symlink creation: {exc}")
    with pytest.raises(ArtifactError, match="inside"):
        inspect_tune("escape.msq")


def test_size_and_count_limits(root, monkeypatch):
    from ecuworkbench import artifacts
    write(root, "large.msq", msq())
    monkeypatch.setattr(artifacts, "MAX_BYTES", 16)
    with pytest.raises(ArtifactError, match="size limit"):
        inspect_tune("large.msq")
    monkeypatch.setattr(artifacts, "MAX_BYTES", 10 * 1024 * 1024)
    monkeypatch.setattr(artifacts, "MAX_CONSTANTS", 1)
    write(root, "large.msq", msq(extras='<constant name="y">2</constant>'))
    with pytest.raises(ArtifactError, match="constant"):
        inspect_tune("large.msq")
    monkeypatch.setattr(artifacts, "MAX_CONSTANTS", 4096)
    monkeypatch.setattr(artifacts, "MAX_TUNE_TEXT", 4)
    with pytest.raises(ArtifactError, match="output budget"):
        inspect_tune("large.msq")
    monkeypatch.setattr(artifacts, "MAX_ROWS", 1)
    write(root, "large.csv", "x\n1\n2\n")
    with pytest.raises(ArtifactError, match="row limit"):
        summarize_log("large.csv")


def test_capabilities_scope_does_not_claim_native_ecu_access():
    result = capabilities()
    assert result["mode"] == "offline_read_only"
    assert result["external_requests"] is False
    assert "native MaxxECU tune/log" in result["unsupported"]
