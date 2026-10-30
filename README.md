# HK Enterprise IT Ops Toolkit
### 桌面及網路運維工具包 · Desktop & Network Operations for a Financial-Office Environment

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-blue)

**English** · [繁體中文](#繁體中文)

A practical, tested toolkit that mirrors the day-to-day work of an on-site **Desktop & Network Operations Engineer** in a large Hong Kong financial / insurance office: workstation support, Microsoft 365 troubleshooting, router/switch fault isolation, comms-room inspection, and ITIL-style documentation.

Everything here is read-only by default, safe to run on a support laptop, and designed to produce **evidence you can paste into a ticket**.

## What's inside

| Area | What it does | Where |
|---|---|---|
| Desktop health snapshot | Hardware, OS, disk, RAM, uptime, pending reboot, NICs, recent critical events, Defender status, with a built-in "findings" engine | [`scripts/windows/Get-DesktopHealth.ps1`](scripts/windows/Get-DesktopHealth.ps1) |
| M365 readiness check | Office version/channel, OST size, DNS+HTTPS to core M365 endpoints, time skew, Teams/OneDrive/Outlook state | [`scripts/windows/Test-M365Readiness.ps1`](scripts/windows/Test-M365Readiness.ps1) |
| Layered network diagnosis | Gateway → DNS → TCP port → HTTP, then names the likely fault domain; JSON output for tickets | [`scripts/network/netcheck.py`](scripts/network/netcheck.py) |
| Switch config auditor | Flags telnet, default SNMP, missing BPDU guard/port-security, default VLAN, etc. for **Cisco IOS and Huawei VRP** | [`scripts/network/switch_audit.py`](scripts/network/switch_audit.py) |
| Lab configs | Hardened access-switch configs (Cisco + Huawei) with VLAN/voice/trunk/STP design, plus a deliberately insecure "before" config | [`labs/`](labs) |
| SOPs | Daily comms-room inspection (機房日常巡檢) and a layered network-troubleshooting flow with Cisco/Huawei command cheat-sheet | [`docs/sop/`](docs/sop) |
| ITIL templates | Incident record with priority matrix; change request with rollback plan | [`docs/itil/`](docs/itil) |
| CI | pytest, config audit gate, PSScriptAnalyzer on every push | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |

## Quick start

```powershell
# Windows desktop snapshot (saves JSON for the ticket)
.\scripts\windows\Get-DesktopHealth.ps1 -OutDir C:\Temp

# Microsoft 365 connectivity / client checks
.\scripts\windows\Test-M365Readiness.ps1
```

```bash
# Where does the connection break?
python scripts/network/netcheck.py --gateway 192.168.1.1 --host intranet.example.com --port 443

# Audit a switch config (exit code 1 if HIGH findings)
python scripts/network/switch_audit.py labs/cisco/insecure-switch-before.cfg
python scripts/network/switch_audit.py labs/huawei/access-switch.cfg

# Run the tests
pip install pytest && pytest -q
```

Sample audit output on the insecure config: 15 findings, including `telnet-enabled`, `enable-secret-missing`, `snmp-default-community`, `default-vlan`. The hardened Cisco and Huawei configs audit clean.

## Design principles
1. **Read-only first**: diagnostics never change the machine or the network.
2. **Evidence for tickets**: structured output (JSON) so escalations include facts, not guesses.
3. **Layered thinking**: scope → physical → switching → IP → DNS → application, in that order.
4. **Documented & repeatable**: every recurring task has an SOP and a template; changes have a rollback plan.
5. **Tested**: parsing logic and network checks are unit-tested and run in CI.

## Repository layout
```
scripts/windows/   PowerShell desktop & M365 diagnostics
scripts/network/   Python network + switch-config tools
labs/cisco|huawei/ Lab configurations (packet-tracer / eNSP style)
docs/sop/          Inspection and troubleshooting procedures
docs/itil/         Incident & change templates
tests/             pytest suite
```

## Notes
- All hostnames, IPs, and hashes in the labs are fictional lab values.
- Run scripts only on systems you are authorised to administer.

---

<a id="繁體中文"></a>
## 繁體中文

本專案模擬香港大型金融／保險企業辦公室內，**桌面及網路運維工程師**的日常工作：電腦及系統支援、Microsoft 365 排障、路由器／交換機故障定位、機房巡檢，以及符合 ITIL 的文件化流程。

**主要內容**
- **桌面健康檢查**（PowerShell）：硬件、系統、磁碟、記憶體、開機時間、待重啟、網卡、近期嚴重事件、Defender 狀態，並自動列出需跟進項目。
- **M365 就緒檢查**：Office 版本與更新通道、Outlook OST 大小、核心 M365 網域 DNS／HTTPS 連通、時間偏差、Teams／OneDrive 狀態。
- **分層網路診斷**（Python）：閘道 → DNS → TCP 端口 → HTTP，自動判斷故障所在層級，可輸出 JSON 附於工單。
- **交換機配置審計**：支援 **Cisco IOS 與華為 VRP**，檢查 Telnet、預設 SNMP、BPDU 保護、端口安全、預設 VLAN 等常見問題。
- **實驗配置**：Cisco／華為接入交換機（VLAN、語音 VLAN、Trunk、RSTP）以及刻意設計的「整改前」配置。
- **SOP**：機房日常巡檢清單、網路排障流程與 Cisco／華為命令對照表。
- **ITIL 範本**：事件記錄（含優先級矩陣）、變更請求（含回退方案）。
- **CI 自動化**：每次提交自動執行測試與配置審計。

**使用方式** 請參考上方 Quick start。腳本預設為唯讀，只應在已獲授權的系統上運行。

## License
MIT
