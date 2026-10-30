import socket
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "network"))

import netcheck  # noqa: E402


def test_tcp_open_and_closed():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    threading.Thread(target=lambda: srv.accept(), daemon=True).start()
    assert netcheck.tcp("127.0.0.1", port).ok
    srv.close()
    assert not netcheck.tcp("127.0.0.1", port, timeout=0.5).ok


def test_dns_localhost():
    assert netcheck.dns("localhost").ok


def test_diagnose_messages():
    gw_fail = [netcheck.Result("L3", "ping 1.1.1.1", False, "")]
    assert "Gateway unreachable" in netcheck.diagnose(gw_fail)
    dns_fail = [netcheck.Result("L3", "ping gw", True, ""), netcheck.Result("L7-DNS", "resolve x", False, "")]
    assert "DNS" in netcheck.diagnose(dns_fail)
    port_fail = dns_fail[:1] + [netcheck.Result("L7-DNS", "resolve x", True, ""), netcheck.Result("L4", "tcp x:1", False, "")]
    assert "port closed" in netcheck.diagnose(port_fail)
