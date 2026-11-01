#!/usr/bin/env python3
"""preflight.py가 실제로 문제를 잡아내는지 확인하는 자가 진단.

정상 설정 스냅샷을 복제한 뒤 일부러 고장을 내고, 해당 검사 항목이 FAIL로 바뀌는지 본다.
저장소의 원본 설정 파일은 건드리지 않는다 (스냅샷 사본만 수정).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from preflight import FAIL, PASS, Preflight  # noqa: E402


def break_evpn_gateway(cfgdir: Path):
    """Lab 3 미완료 상태 재현: Border Leaf에서 원격 EVPN 피어링/재발신 설정을 제거."""
    for cfg in cfgdir.glob("*brdr*.cfg"):
        lines = [l for l in cfg.read_text().splitlines()
                 if "EVPN-OVERLAY-REMOTE-PEERS" not in l and "domain remote" not in l]
        cfg.write_text("\n".join(lines) + "\n")


def break_mtu(cfgdir: Path):
    """DCI 방향 P2P 링크 한쪽의 MTU만 낮춘다 (전형적인 사람 실수)."""
    cfg = cfgdir / "s1-brdr1.cfg"
    text = cfg.read_text()
    text = re.sub(r"(interface Ethernet4\n(?:.*\n)*?   mtu )9214", r"\g<1>1500", text, count=1)
    cfg.write_text(text)


def break_duplicate_ip(cfgdir: Path):
    """서로 다른 leaf에 같은 Loopback0(라우터 ID) 주소를 준다."""
    cfg = cfgdir / "s1-leaf3.cfg"
    text = cfg.read_text()
    text = re.sub(r"(interface Loopback0\n(?:.*\n)*?   ip address )10\.1\.0\.\d+/32",
                  r"\g<1>10.1.0.14/32", text, count=1)
    cfg.write_text(text)


def break_dci_link(cfgdir: Path):
    """DCI core 간 링크를 shutdown — 언더레이가 끊겨 DC 간 BGP가 죽어야 한다."""
    cfg = cfgdir / "s1-core1.cfg"
    text = cfg.read_text().replace(
        "description DCI_P2P_LINK_TO_s2-core1_Ethernet4\nno switchport\nno shutdown",
        "description DCI_P2P_LINK_TO_s2-core1_Ethernet4\nno switchport\nshutdown")
    cfg.write_text(text)


def break_edge_vtep_route(cfgdir: Path):
    """Edge(Border Leaf)에 원격 DC VTEP을 Null0으로 보내는 정적 경로를 넣는다.

    EVPN 피어링은 Loopback0(10.1.0.102), VXLAN 캡슐화는 Loopback1(10.1.1.102)을 쓰므로
    BGP 세션은 전부 Established로 남고 데이터 평면만 죽는다 — `show bgp evpn summary`나
    ANTA의 BGP 검사로는 보이지 않는 장애다.
    """
    for name in ("s1-brdr1", "s1-brdr2"):
        cfg = cfgdir / f"{name}.cfg"
        cfg.write_text(cfg.read_text().replace(
            "ip route 0.0.0.0/0 192.168.0.1",
            "ip route 0.0.0.0/0 192.168.0.1\nip route 10.1.1.102/32 Null0", 1))


GOOD_DCI_ACL = [
    "10 permit icmp any any",
    "20 permit tcp any any eq bgp",
    "30 permit tcp any eq bgp any",
    "40 permit udp any any eq 4784",
    "50 permit udp any any eq 4789",
    "1000 deny ip any any",
]


def _apply_dci_acl(cfgdir: Path, entries: list[str]):
    """s1-brdr1/2의 DCI 방향(Ethernet4/5) 인바운드에 DCI-EDGE-IN ACL을 건다."""
    acl = "ip access-list DCI-EDGE-IN\n" + "".join(f"   {e}\n" for e in entries) + "!\n"
    for name in ("s1-brdr1", "s1-brdr2"):
        cfg = cfgdir / f"{name}.cfg"
        text = cfg.read_text()
        text = re.sub(r"(interface Ethernet[45]\n(?:   .*\n)*?   ip address \S+\n)",
                      r"\g<1>   ip access-group DCI-EDGE-IN in\n", text)
        text = text.replace("\nend", "\n" + acl + "end", 1)
        cfg.write_text(text)


def break_dci_acl_no_vxlan(cfgdir: Path):
    """DCI ACL을 '조이다가' VXLAN(UDP 4789) 허용 줄을 빠뜨린다.

    ICMP와 BGP는 허용되므로 ping·BGP·ICMP 기반 VTEP 검사는 모두 정상으로 보이고,
    원격 DC로 가는 VXLAN 패킷만 Border Leaf에서 버려진다.
    """
    _apply_dci_acl(cfgdir, [e for e in GOOD_DCI_ACL if "4789" not in e])


def break_dci_acl_shadowed(cfgdir: Path):
    """seq 15에 'deny tcp any any'를 끼워 넣어 뒤의 BGP 허용 줄을 가린다(순서 실수)."""
    _apply_dci_acl(cfgdir, GOOD_DCI_ACL[:1] + ["15 deny tcp any any"] + GOOD_DCI_ACL[1:])


CASES = [
    ("Lab 3 evpn_gateway 미적용", break_evpn_gateway,
     ["EVPN Gateway 원격 피어링", "EVPN 경로 재발신 표시"], [3]),
    ("DCI P2P 링크 MTU 불일치", break_mtu, ["L3 링크 MTU"], []),
    ("leaf 라우터 ID 중복", break_duplicate_ip, ["중복 IP"], []),
    ("DCI core 간 링크 shutdown", break_dci_link, ["BGP 세션 수립(모델)"], [3]),
    ("Edge(Border Leaf)에서 원격 VTEP 블랙홀", break_edge_vtep_route, ["VTEP 간 도달성"], [3]),
    ("DCI ACL에서 VXLAN(UDP 4789) 누락", break_dci_acl_no_vxlan,
     ["VXLAN(UDP 4789) 도달성", "DCI ACL 정책"], []),
    ("DCI ACL 라인 순서 실수(BGP 허용 줄이 가려짐)", break_dci_acl_shadowed,
     ["ACL 라인 도달성", "DCI ACL 정책", "BGP 세션 수립(모델)"], []),
]


def main():
    rc = 0
    for i, (title, mutator, expect_fail, labs) in enumerate(CASES):
        print(f"\n{'='*72}\n[자가 진단 {i+1}/{len(CASES)}] {title}\n{'='*72}")
        pf = Preflight(["dc1", "dc2"], snap_name=f"selftest-{i+1}", mutator=mutator)
        pf.run(labs)
        got = {r.name: r.status for r in pf.results}
        for name in expect_fail:
            status = got.get(name, "(검사 안 됨)")
            ok = status == FAIL
            rc |= 0 if ok else 1
            print(f"\n  기대: '{name}' → FAIL / 실제: {status}  {'OK' if ok else '<<< 문제'}")
        others = [n for n, s in got.items() if s == FAIL and n not in expect_fail]
        if others:
            print(f"  참고: 연쇄로 함께 FAIL된 항목 — {', '.join(others)}")
    print(f"\n{'='*72}\n자가 진단 종료: {'모든 고장이 정상 탐지됨' if rc == 0 else '탐지 실패 있음'}\n{'='*72}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
