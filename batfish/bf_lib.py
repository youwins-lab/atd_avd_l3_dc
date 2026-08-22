"""Batfish 스냅샷 빌더 + 세션 헬퍼.

이 저장소의 설정 소스는 세 갈래다:
  1. AVD가 생성한 fabric 설정      sites/dc{n}/intended/configs/*.cfg   (완전한 running-config)
  2. DCI core 정적 설정            sites/dc{n}/dci_configs/*.cfg        (부분 설정 조각)
  3. 서버 엔드포인트 정적 설정      sites/dc{n}/host_configs/*.cfg       (부분 설정 조각)

2/3번은 eos_config로 밀어넣는 "조각"이라 hostname 줄이 없다. Batfish는 설정 파일마다
hostname을 요구하므로 스냅샷을 만들 때 파일명 기준으로 hostname 줄을 붙여 정규화한다.
원본 파일은 건드리지 않는다.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SNAPSHOT_ROOT = REPO / "batfish" / "snapshots"

# description에서 대향 장비/인터페이스를 뽑아내는 패턴.
# AVD가 붙이는 P2P_s1-spine1_Ethernet2 / MLAG_s1-leaf2_Ethernet1 / SERVER_s1-host1_Ethernet1 과
# 정적 설정이 쓰는 P2P_LINK_TO_s1-brdr1_Ethernet4 / DCI_P2P_LINK_TO_s2-core1_Ethernet4 /
# PortChan1_s1-leaf1_Ethernet4 를 모두 커버한다.
PEER_RE = re.compile(r"(s[12]-[a-z0-9]+)_(Ethernet[\d/]+)\s*$", re.IGNORECASE)

# description이 없어 자동 추출이 불가능한 물리 링크 (core1 <-> core2 포트채널 멤버).
# 설정상 channel-group 16 으로만 표현되어 있어 대향 정보가 파일 어디에도 없다.
L1_OVERRIDES = [
    ("s1-core1", "Ethernet1", "s1-core2", "Ethernet1"),
    ("s1-core1", "Ethernet6", "s1-core2", "Ethernet6"),
    ("s2-core1", "Ethernet1", "s2-core2", "Ethernet1"),
    ("s2-core1", "Ethernet6", "s2-core2", "Ethernet6"),
]

DC_SOURCES = {
    "dc1": ["sites/dc1/intended/configs", "sites/dc1/dci_configs", "sites/dc1/host_configs"],
    "dc2": ["sites/dc2/intended/configs", "sites/dc2/dci_configs", "sites/dc2/host_configs"],
}


# EOS `show running-config`의 첫 줄. Batfish는 이 헤더가 없으면 설정을 Cisco IOS로 오탐하고
# `vrf instance`, `neighbor X peer group Y` 같은 EOS 전용 문법을 전부 파싱하지 못한다.
EOS_HEADER = "! device: {hostname} (cEOS-lab, EOS-4.36.0F)\n!\n"


def _normalize(text: str, hostname: str) -> str:
    """Batfish가 파싱할 수 있도록 설정을 정규화한다 (원본 파일은 건드리지 않는다)."""
    if not re.search(r"^hostname\s+\S+", text, re.MULTILINE):
        text = f"hostname {hostname}\n!\n" + text
    text = EOS_HEADER.format(hostname=hostname) + text
    # 'interface ethernet1' / 'interface port-channel 16' 같은 소문자·띄어쓰기 표기를 EOS 표준형으로
    text = re.sub(r"^interface ethernet\s*", "interface Ethernet", text, flags=re.MULTILINE)
    text = re.sub(r"^interface port-channel\s*", "interface Port-Channel", text, flags=re.MULTILINE)
    text = re.sub(r"^interface vlan\s*", "interface Vlan", text, flags=re.MULTILINE)
    return text


def _iter_interfaces(text: str):
    """(interface 이름, 블록 내부 줄들) 을 순회한다.

    AVD가 만든 설정은 인터페이스 하위 명령을 들여쓰지만, 손으로 관리하는 dci_configs/
    host_configs의 조각 설정은 들여쓰기가 없다. 그래서 "들여쓰기 여부"로 블록 끝을 판단할 수
    없고, 다음 stanza(interface/router/vlan/vrf/hostname)가 시작될 때만 블록을 닫는다.
    """
    block_start = re.compile(r"^(interface|router|vlan|vrf|hostname)\b", re.IGNORECASE)
    current = None
    body: list[str] = []
    for line in text.splitlines():
        if block_start.match(line):
            if current:
                yield current, body
            m = re.match(r"^interface (\S+)\s*$", line)
            current, body = (m.group(1) if m else None), []
            continue
        if current is not None:
            body.append(line.strip())
    if current:
        yield current, body


def build_layer1(config_dir: Path) -> dict:
    """설정 파일의 인터페이스 description에서 물리 토폴로지를 역산한다."""
    edges = []
    seen = set()

    def add(n1, i1, n2, i2):
        key = (n1, i1, n2, i2)
        if key in seen:
            return
        seen.add(key)
        edges.append(
            {
                "node1": {"hostname": n1, "interfaceName": i1},
                "node2": {"hostname": n2, "interfaceName": i2},
            }
        )

    hostnames = set()
    for cfg in sorted(config_dir.glob("*.cfg")):
        hostnames.add(cfg.stem)

    for cfg in sorted(config_dir.glob("*.cfg")):
        node = cfg.stem
        text = cfg.read_text()
        for ifname, body in _iter_interfaces(text):
            if not ifname.lower().startswith("ethernet"):
                continue
            desc = next((l for l in body if l.lower().startswith("description ")), None)
            if not desc:
                continue
            m = PEER_RE.search(desc[len("description "):].strip())
            if not m:
                continue
            peer, peer_if = m.group(1), m.group(2)
            if peer not in hostnames:
                continue
            add(node, ifname, peer, peer_if)
            add(peer, peer_if, node, ifname)

    for n1, i1, n2, i2 in L1_OVERRIDES:
        if n1 in hostnames and n2 in hostnames:
            add(n1, i1, n2, i2)
            add(n2, i2, n1, i1)

    return {"edges": edges}


def build_snapshot(name: str, dcs: list[str]) -> Path:
    """스냅샷 디렉토리(configs/ + batfish/layer1_topology.json)를 만들고 경로를 돌려준다."""
    snap = SNAPSHOT_ROOT / name
    if snap.exists():
        shutil.rmtree(snap)
    cfgdir = snap / "configs"
    cfgdir.mkdir(parents=True)

    copied = []
    for dc in dcs:
        for rel in DC_SOURCES[dc]:
            src = REPO / rel
            if not src.is_dir():
                continue
            for cfg in sorted(src.glob("*.cfg")):
                text = _normalize(cfg.read_text(), cfg.stem)
                (cfgdir / cfg.name).write_text(text)
                copied.append(cfg.stem)

    l1 = build_layer1(cfgdir)
    bfdir = snap / "batfish"
    bfdir.mkdir()
    (bfdir / "layer1_topology.json").write_text(json.dumps(l1, indent=2))
    return snap


def anycast_ips() -> set[str]:
    """`ip address virtual` / `ip virtual-router address` 로 선언된 anycast 주소 집합."""
    ips = set()
    for dc, rels in DC_SOURCES.items():
        for rel in rels:
            src = REPO / rel
            if not src.is_dir():
                continue
            for cfg in src.glob("*.cfg"):
                for line in cfg.read_text().splitlines():
                    line = line.strip()
                    m = re.match(r"ip (?:address virtual|virtual-router address) (\d+\.\d+\.\d+\.\d+)", line)
                    if m:
                        ips.add(m.group(1))
    return ips


def mlag_pairs() -> dict[str, str]:
    """MLAG 피어 관계를 설정의 `description MLAG_<peer>_...`에서 역산한다."""
    pairs: dict[str, str] = {}
    for rels in DC_SOURCES.values():
        for rel in rels:
            src = REPO / rel
            if not src.is_dir():
                continue
            for cfg in src.glob("*.cfg"):
                m = re.search(r"description MLAG_(s[12]-[a-z0-9]+)_", cfg.read_text())
                if m:
                    pairs[cfg.stem] = m.group(1)
    return pairs


def vtep_source_interfaces() -> dict[str, str]:
    """장비별 VXLAN source-interface (보통 Loopback1)."""
    out: dict[str, str] = {}
    for rels in DC_SOURCES.values():
        for rel in rels:
            src = REPO / rel
            if not src.is_dir():
                continue
            for cfg in src.glob("*.cfg"):
                m = re.search(r"^\s*vxlan source-interface (\S+)", cfg.read_text(), re.MULTILINE)
                if m:
                    out[cfg.stem] = m.group(1)
    return out
