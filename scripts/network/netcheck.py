#!/usr/bin/env python3
"""netcheck - layered network troubleshooting helper (L1 -> L7 mindset).

Runs the same sequence a support engineer follows by hand:
  1. local interface / default gateway reachable?
  2. DNS resolves?
  3. target TCP port open?
  4. optional HTTP(S) status

Standard library only, so it runs on any helpdesk laptop.

Usage:
    python netcheck.py --gateway 192.168.1.1 --host intranet.example.com --port 443
    python netcheck.py --host 10.0.0.5 --port 3389 --json
"""
from __future__ import annotations

import argparse
import json
import platform
import socket
import subprocess
import sys
import time
import urllib.request
from dataclasses import asdict, dataclass


@dataclass
class Result:
    layer: str
    check: str
    ok: bool
    detail: str


def ping(host: str, count: int = 2, timeout: int = 2) -> Result:
    flag = "-n" if platform.system().lower() == "windows" else "-c"
    cmd = ["ping", flag, str(count), host]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=count * timeout + 3)
        return Result("L3", f"ping {host}", out.returncode == 0, out.stdout.strip().splitlines()[-1] if out.stdout else "no output")
    except Exception as exc:  # noqa: BLE001
        return Result("L3", f"ping {host}", False, str(exc))


def dns(host: str) -> Result:
    start = time.perf_counter()
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos})
        ms = (time.perf_counter() - start) * 1000
        return Result("L7-DNS", f"resolve {host}", True, f"{', '.join(ips)} ({ms:.0f} ms)")
    except socket.gaierror as exc:
        return Result("L7-DNS", f"resolve {host}", False, str(exc))


def tcp(host: str, port: int, timeout: float = 3.0) -> Result:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            ms = (time.perf_counter() - start) * 1000
            return Result("L4", f"tcp {host}:{port}", True, f"open ({ms:.0f} ms)")
    except OSError as exc:
        return Result("L4", f"tcp {host}:{port}", False, str(exc))


def http(url: str, timeout: float = 5.0) -> Result:
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return Result("L7", f"http {url}", resp.status < 400, f"HTTP {resp.status}")
    except Exception as exc:  # noqa: BLE001
        return Result("L7", f"http {url}", False, str(exc))


def diagnose(results: list[Result]) -> str:
    """Translate raw results into the most likely fault domain."""
    by = {r.check.split()[0]: r for r in results}
    gw = next((r for r in results if r.layer == "L3"), None)
    d = next((r for r in results if r.layer == "L7-DNS"), None)
    t = next((r for r in results if r.layer == "L4"), None)
    if gw and not gw.ok:
        return "Gateway unreachable: check cable/Wi-Fi, VLAN, switch port, DHCP lease (L1-L3)."
    if d and not d.ok:
        return "Gateway OK but DNS fails: check DNS server settings / DNS service."
    if t and not t.ok:
        return "DNS OK but port closed/filtered: check firewall ACL, service state, routing to destination."
    if results and all(r.ok for r in results):
        return "All layers OK: problem is likely application/account level."
    return "Partial failure: review failed checks above."


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gateway", help="default gateway IP to ping")
    p.add_argument("--host", help="target hostname or IP")
    p.add_argument("--port", type=int, help="target TCP port")
    p.add_argument("--url", help="optional URL for HTTP HEAD check")
    p.add_argument("--json", action="store_true", help="emit JSON (for ticket attachment)")
    args = p.parse_args(argv)

    results: list[Result] = []
    if args.gateway:
        results.append(ping(args.gateway))
    if args.host:
        if not args.host.replace(".", "").isdigit():
            results.append(dns(args.host))
        if args.port:
            results.append(tcp(args.host, args.port))
    if args.url:
        results.append(http(args.url))
    if not results:
        p.error("nothing to check: give --gateway and/or --host [--port] and/or --url")

    verdict = diagnose(results)
    if args.json:
        print(json.dumps({"results": [asdict(r) for r in results], "verdict": verdict}, indent=2))
    else:
        for r in results:
            print(f"[{'OK' if r.ok else 'FAIL':4}] {r.layer:7} {r.check:35} {r.detail}")
        print(f"\nVerdict: {verdict}")
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
