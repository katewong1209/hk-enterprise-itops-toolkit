# SOP: Daily Equipment Room / Comms Room Inspection (機房日常巡檢)

**Scope:** Comms rooms and server/network rooms on all floors of the supported office.
**Frequency:** Once per working day (morning), plus after any alarm or power event.
**Owner:** Desktop & Network Operations team. **Record:** Inspection log (table below) filed in the ticket system.

## 1. Before entering
- [ ] Access approved / logged in the visitor or access register
- [ ] Wear ID, no food or drink, no photography unless authorised
- [ ] Carry: torch, label printer, cable tester, spare patch leads

## 2. Environment
| Item | Normal | Action if abnormal |
|---|---|---|
| Room temperature | 18-27 °C | Report to Building Management; check CRAC/AC alarm; escalate if > 30 °C |
| Humidity | 40-60 % RH | Report to Building Management |
| Water leak / condensation | None | Isolate area, report immediately |
| Smoke/heat detector, extinguisher seal and date | Present, in date | Raise facilities ticket |
| Floor/rack area | Clear, no combustible storage | Remove / report |

## 3. Power
- [ ] UPS status: mains OK, load < 80 %, no battery fault, runtime as expected
- [ ] PDU: no overload alarm, power cables seated and strain-relieved
- [ ] Redundant PSUs: both lit on each core device

## 4. Network equipment
- [ ] Core/distribution/access switches: power, fan and system LEDs normal (no amber)
- [ ] Uplink/trunk ports: link up, no excessive errors (`show interfaces counters errors` / `display interface brief`)
- [ ] Spanning tree: expected root bridge, no unexpected topology changes
- [ ] Wi-Fi controller / APs: all APs online, no repeated reboots
- [ ] Firewall / router: HA pair healthy, VPN tunnels up
- [ ] Monitoring system (e.g. SNMP/Zabbix/PRTG): no open critical alerts

## 5. Cabling & labelling
- [ ] Patch panel port labels match the cabling register
- [ ] No loose, over-bent or unlabelled cables; Velcro (not zip ties) on bundles
- [ ] No unauthorised devices connected

## 6. Servers / storage / backup (if in scope)
- [ ] Hardware status LEDs normal
- [ ] Last backup job successful (check console, not just email)

## 7. Close-out
- [ ] Door locked, access log completed
- [ ] Findings recorded; incidents raised per `docs/itil/incident-template.md`

## Inspection log (copy per day)
| Date | Room | Inspector | Temp °C | RH % | UPS OK | Network OK | Issues / Ticket # |
|---|---|---|---|---|---|---|---|
| | | | | | | | |
