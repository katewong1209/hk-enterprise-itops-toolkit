import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "network"))

import switch_audit  # noqa: E402


def rules(path, vendor=None):
    text = (ROOT / path).read_text()
    vendor = vendor or switch_audit.detect_vendor(text)
    fn = switch_audit.audit_cisco if vendor == "cisco" else switch_audit.audit_huawei
    return {f.rule for f in fn(text)}, {f.severity for f in fn(text)}


def test_insecure_cisco_flags_high_risk():
    found, sev = rules("labs/cisco/insecure-switch-before.cfg")
    assert {"telnet-enabled", "enable-secret-missing", "snmp-default-community", "default-vlan"} <= found
    assert "HIGH" in sev


def test_hardened_cisco_has_no_high_findings():
    _, sev = rules("labs/cisco/access-switch.cfg")
    assert "HIGH" not in sev


def test_hardened_huawei_has_no_high_findings():
    found, sev = rules("labs/huawei/access-switch.cfg")
    assert "HIGH" not in sev
    assert "telnet-enabled" not in found


def test_vendor_detection():
    assert switch_audit.detect_vendor((ROOT / "labs/huawei/access-switch.cfg").read_text()) == "huawei"
    assert switch_audit.detect_vendor((ROOT / "labs/cisco/access-switch.cfg").read_text()) == "cisco"
