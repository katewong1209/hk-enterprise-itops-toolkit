#!/usr/bin/env python3
"""switch_audit - static security/hygiene audit for Cisco IOS and Huawei VRP configs.

Reads a text config and flags common issues that a network engineer would
catch in a routine review (telnet enabled, no SNMP v3, unused ports not
shutdown, default VLAN in use, no banner, missing port security / BPDU guard...).

Usage:
    python switch_audit.py labs/cisco/access-switch.cfg
    python switch_audit.py labs/huawei/access-switch.cfg --vendor huawei
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    severity: str  # HIGH / MED / LOW
    rule: str
    detail: str


def detect_vendor(text: str) -> str:
    if re.search(r"^\s*sysname\s", text, re.M) or "return" in text.splitlines()[-1:]:
        return "huawei"
    return "cisco"


def audit_cisco(text: str) -> list[Finding]:
    f: list[Finding] = []
    if re.search(r"transport input .*telnet", text) or re.search(r"transport input all", text):
        f.append(Finding("HIGH", "telnet-enabled", "VTY allows telnet; use 'transport input ssh'."))
    if "ip ssh version 2" not in text:
        f.append(Finding("MED", "ssh-v2-missing", "SSH version 2 not enforced."))
    if not re.search(r"enable secret", text):
        f.append(Finding("HIGH", "enable-secret-missing", "Use 'enable secret', not 'enable password'."))
    if "service password-encryption" not in text:
        f.append(Finding("LOW", "password-encryption", "service password-encryption not set."))
    if re.search(r"snmp-server community \S+ (RW|rw)", text):
        f.append(Finding("HIGH", "snmp-rw-community", "SNMP RW community configured."))
    if re.search(r"snmp-server community (public|private)\b", text):
        f.append(Finding("HIGH", "snmp-default-community", "Default SNMP community string."))
    if not re.search(r"^banner (login|motd)", text, re.M):
        f.append(Finding("LOW", "no-banner", "No login/MOTD banner."))
    if "spanning-tree portfast bpduguard default" not in text:
        f.append(Finding("MED", "bpduguard-default", "BPDU guard not enabled by default on PortFast ports."))
    if not re.search(r"logging host|logging \d+\.\d+\.\d+\.\d+", text):
        f.append(Finding("LOW", "no-syslog", "No remote syslog server."))
    if not re.search(r"ntp server", text):
        f.append(Finding("LOW", "no-ntp", "No NTP server (log timestamps unreliable)."))

    # per-interface checks
    for name, body in re.findall(r"^interface (\S+)\n((?:[ \t]+.*\n?)*)", text, re.M):
        if not name.lower().startswith(("fastethernet", "gigabitethernet")):
            continue
        is_access = "switchport mode access" in body
        shut = re.search(r"^\s*shutdown", body, re.M) is not None
        if "switchport access vlan 1\n" in body + "\n":
            f.append(Finding("MED", "default-vlan", f"{name}: access port in VLAN 1."))
        if is_access and not shut and "switchport port-security" not in body:
            f.append(Finding("LOW", "no-port-security", f"{name}: access port without port-security."))
        if not shut and not is_access and "switchport mode trunk" not in body and "ip address" not in body:
            f.append(Finding("MED", "unconfigured-active-port", f"{name}: active but no mode set; shutdown unused ports."))
    return f


def audit_huawei(text: str) -> list[Finding]:
    f: list[Finding] = []
    if re.search(r"protocol inbound (telnet|all)", text):
        f.append(Finding("HIGH", "telnet-enabled", "VTY allows telnet; use 'protocol inbound ssh'."))
    if "stelnet server enable" not in text:
        f.append(Finding("MED", "stelnet-disabled", "'stelnet server enable' not present."))
    if re.search(r"snmp-agent community (read|write) (public|private)\b", text):
        f.append(Finding("HIGH", "snmp-default-community", "Default SNMP community."))
    if "snmp-agent sys-info version v3" not in text and "snmp-agent" in text:
        f.append(Finding("MED", "snmp-not-v3", "SNMP not restricted to v3."))
    if "stp bpdu-protection" not in text:
        f.append(Finding("MED", "bpdu-protection", "Global 'stp bpdu-protection' missing."))
    if not re.search(r"info-center loghost", text):
        f.append(Finding("LOW", "no-syslog", "No info-center loghost configured."))
    if not re.search(r"ntp-service unicast-server", text):
        f.append(Finding("LOW", "no-ntp", "No NTP server configured."))
    if not re.search(r"header (login|shell)", text):
        f.append(Finding("LOW", "no-banner", "No login header."))
    if "undo ssh server compatible-ssh1x" not in text and "ssh server" in text:
        f.append(Finding("LOW", "ssh1-compat", "SSH1 compatibility not disabled."))
    return f


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", type=Path)
    ap.add_argument("--vendor", choices=["cisco", "huawei"], help="force vendor (default: auto-detect)")
    ap.add_argument("--fail-on", choices=["HIGH", "MED", "LOW"], default="HIGH",
                    help="exit 1 if any finding at or above this severity")
    args = ap.parse_args(argv)

    text = args.config.read_text(encoding="utf-8", errors="replace")
    vendor = args.vendor or detect_vendor(text)
    findings = audit_cisco(text) if vendor == "cisco" else audit_huawei(text)

    order = {"HIGH": 0, "MED": 1, "LOW": 2}
    findings.sort(key=lambda x: order[x.severity])
    print(f"Audit of {args.config} ({vendor}) - {len(findings)} finding(s)\n")
    for x in findings:
        print(f"[{x.severity:4}] {x.rule:26} {x.detail}")
    if not findings:
        print("No findings.")
    threshold = order[args.fail_on]
    return 1 if any(order[x.severity] <= threshold for x in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
