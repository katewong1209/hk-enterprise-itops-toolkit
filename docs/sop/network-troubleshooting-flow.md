# SOP: Network Troubleshooting Flow (Layered)

Goal: find the fault domain fast, fix or escalate with evidence.

```
User reports: "Can't connect / slow"
        │
        ▼
1. Scope  ── one user? one floor? everyone? one app?
        │      (one user → client/port; one floor → access switch/VLAN/AP; all → core/WAN/DNS/DHCP)
        ▼
2. L1 Physical ── link light, cable, patch lead, port LED, Wi-Fi signal
        ▼
3. L2 Switching ── right VLAN? port err-disabled? duplex/speed? MAC learned? STP loop?
        ▼
4. L3 IP ── valid IP (not 169.254.x.x)? correct gateway? ping gateway → ping far side
        ▼
5. DNS ── nslookup name; compare internal vs public DNS
        ▼
6. L4/L7 ── test port (Test-NetConnection / netcheck.py); firewall ACL; proxy; app/account
        ▼
7. Fix → verify with user → document → close / escalate
```

## Command cheat sheet
| Task | Windows | Cisco IOS | Huawei VRP |
|---|---|---|---|
| Own IP config | `ipconfig /all` | `show ip interface brief` | `display ip interface brief` |
| Renew DHCP | `ipconfig /release && /renew` | — | — |
| Ping / trace | `ping`, `tracert`, `pathping` | `ping`, `traceroute` | `ping`, `tracert` |
| DNS | `nslookup`, `Resolve-DnsName` | — | — |
| Port test | `Test-NetConnection host -Port 443` | — | — |
| ARP / MAC | `arp -a` | `show mac address-table` | `display mac-address` |
| Port status | — | `show interfaces status` | `display interface brief` |
| Errors | — | `show interfaces <int>` | `display interface <int>` |
| VLANs | — | `show vlan brief` | `display vlan` |
| STP | — | `show spanning-tree` | `display stp brief` |
| Config | — | `show running-config` | `display current-configuration` |

## Common symptoms → likely cause
| Symptom | Likely cause | Check |
|---|---|---|
| IP 169.254.x.x | DHCP unreachable | Cable, VLAN, DHCP scope / relay (`ip helper-address`) |
| Can ping IP, not name | DNS | `nslookup`, DNS server in `ipconfig /all` |
| Port err-disabled | BPDU guard / port-security / loop | Switch log; remove cause, then `shutdown`/`no shutdown` |
| Intermittent drops, CRC errors | Bad cable / duplex mismatch | Interface counters, replace patch lead |
| Whole floor down | Uplink / access switch power | Uplink status, UPS/PDU |
| Slow only on Wi-Fi | RF interference / roaming | AP channel, signal, client count |
| Duplicate-IP warning | Static IP clash | `arp -a`, DHCP leases |

## Escalation note (copy into ticket)
```
Who/where affected:
Since when:
What changed:
Tests done (with results):
Fault domain (my assessment):
Evidence attached (netcheck.json, screenshots, interface counters):
```
