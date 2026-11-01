#!/usr/bin/env python3
"""AVD 배포 전 Batfish 사전 검증 (pre-flight).

`make build_dc{1,2}` 가 만들어 놓은 `sites/dc{n}/intended/configs/*.cfg` 와 손으로 관리하는
`dci_configs/`, `host_configs/` 를 하나의 Batfish 스냅샷으로 묶어, **장비에 아무것도 배포하지
않은 상태에서** 설정만 보고 검증한다.

  공통 검사   : 파싱 / 미정의 참조 / 중복 IP / L1-L3 토폴로지 / MTU / BGP 세션 /
                VTEP 도달성(ICMP·UDP 4789) / ACL 라인 도달성 / DCI 경계 ACL 정책
  시나리오 검사: evpn-vxlan-labs.md 의 Lab 1~6 각각이 의도한 결과가 설정에 반영됐는지

사용법:
    python3 batfish/preflight.py                 # 공통 + 전체 랩
    python3 batfish/preflight.py --labs 2,3      # 특정 랩만
    python3 batfish/preflight.py --labs none     # 공통 검사만
    python3 batfish/preflight.py --dc dc1        # dc1 설정만으로 스냅샷 구성
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bf_lib  # noqa: E402

logging.getLogger("pybatfish").setLevel(logging.ERROR)

from pybatfish.client.session import Session  # noqa: E402
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints  # noqa: E402

REPO = bf_lib.REPO
REPORT_DIR = REPO / "batfish" / "reports"

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"

# Batfish가 모델링하지 않는 EOS 문법. 랩 설정에 정상적으로 존재하는 줄들이라 파싱 경고가 떠도
# 문제가 아니다. 여기에 없는 새로운 경고가 나오면 "검토 필요"로 올린다.
KNOWN_UNSUPPORTED = [
    r"^rd evpn domain remote",                              # Lab 3 EVPN Gateway 재발신
    r"^route-target (import|export|import export) evpn domain remote",
    r"^neighbor \S+ domain remote",
    r"^neighbor default next-hop-self received-evpn-routes",
    r"^ip address virtual source-nat",                      # Lab 6 프로브 소스 주소
    r"^(interval|host|vrf|interface set|local-interfaces|ip) ",  # Lab 6 monitor connectivity 블록
    r"^transceiver qsfp default-mode",
    r"^(no )?spanning-tree (vlan-id|edge-port)",
    r"^vlan internal order",
    r"^router bfd$",
    r"^multihop interval",
    r"^maximum-routes",
    r"^route import match-failure action discard",
    r"^redistribute learned",
    r"^virtual-router mac-address",
]

ANYCAST_GW = {  # Lab 1/4에서 두 DC가 공유하는 anycast gateway
    10: "10.10.10.1", 20: "10.20.20.1", 30: "10.30.30.1",
    40: "10.40.40.1", 50: "10.50.50.1", 100: "10.100.100.1", 200: "10.200.200.1",
}
L2VNI = {10: 10010, 20: 10020, 30: 10030, 40: 10040, 50: 10050, 100: 20100, 200: 20200}


@dataclass
class Result:
    lab: str
    name: str
    status: str
    summary: str
    detail: list[str] = field(default_factory=list)


class Preflight:
    def __init__(self, dcs: list[str], network: str = "atd-avd-l3-dc",
                 snap_name: str | None = None, mutator=None):
        """mutator: 스냅샷 초기화 직전에 configs/ 디렉토리를 손보는 함수.

        검사기 자체가 제대로 동작하는지 확인하는 selftest.py 전용 훅이다. 실제 pre-flight
        실행에서는 항상 None이며, 원본 저장소 파일은 어떤 경우에도 수정하지 않는다.
        """
        self.dcs = dcs
        self.results: list[Result] = []
        self.bf = Session(host="localhost")
        self.bf.set_network(network)
        snap_name = snap_name or "-".join(dcs)
        self.snapshot_path = bf_lib.build_snapshot(snap_name, dcs)
        if mutator:
            mutator(self.snapshot_path / "configs")
        self.bf.init_snapshot(str(self.snapshot_path), name=snap_name, overwrite=True)
        self.nodes = sorted(
            self.bf.q.nodeProperties(properties="Hostname").answer().frame()["Node"].tolist()
        )
        self.leafs = [n for n in self.nodes if re.match(r"s\d-leaf\d$", n)]
        self.brdrs = [n for n in self.nodes if re.match(r"s\d-brdr\d$", n)]

    # ------------------------------------------------------------------ helpers
    def add(self, lab, name, status, summary, detail=None):
        self.results.append(Result(lab, name, status, summary, detail or []))
        icon = {PASS: "✔", FAIL: "✘", WARN: "!", SKIP: "-"}[status]
        print(f"  [{icon}] {name:<38} {summary}")
        for line in (detail or [])[:12]:
            print(f"        {line}")

    def traces(self, start, src, dst):
        f = self.bf.q.traceroute(
            startLocation=start,
            headers=HeaderConstraints(srcIps=src, dstIps=dst, applications="icmp"),
        ).answer().frame()
        out = []
        for _, row in f.iterrows():
            for t in row["Traces"]:
                out.append((str(t.disposition), [h.node for h in t.hops]))
        return out

    # ------------------------------------------------------------------ 공통 검사
    def check_parse(self):
        df = self.bf.q.fileParseStatus().answer().frame()
        bad_fmt = df[df.File_Format != "ARISTA"]
        failed = df[df.Status == "FAILED"]
        if len(bad_fmt) or len(failed):
            self.add("공통", "설정 파싱", FAIL,
                     f"{len(failed)}개 파일 파싱 실패 / {len(bad_fmt)}개 벤더 오탐",
                     [f"{r.File_Name}: {r.Status} ({r.File_Format})"
                      for r in list(failed.itertuples()) + list(bad_fmt.itertuples())])
            return
        issues = self.bf.q.initIssues().answer().frame()
        unknown = []
        for _, r in issues.iterrows():
            text = re.sub(r"\s+", " ", str(r["Line_Text"]).strip())
            if not any(re.match(p, text) for p in KNOWN_UNSUPPORTED):
                unknown.append(f"{r['Nodes']}: {text[:90]}")
        if unknown:
            self.add("공통", "설정 파싱", WARN,
                     f"{len(df)}개 파일 파싱 OK, 미분류 경고 {len(unknown)}건", unknown)
        else:
            self.add("공통", "설정 파싱", PASS,
                     f"{len(df)}개 파일 모두 ARISTA로 파싱, 노드 {len(self.nodes)}개 "
                     f"(경고 {len(issues)}건은 Batfish 미지원 문법으로 확인됨)")

    def check_undefined_refs(self):
        df = self.bf.q.undefinedReferences().answer().frame()
        if len(df):
            self.add("공통", "미정의 참조", FAIL, f"{len(df)}건",
                     [f"{r.File_Name}: {r.Struct_Type} '{r.Ref_Name}' ({r.Context})"
                      for r in df.itertuples()])
        else:
            self.add("공통", "미정의 참조", PASS,
                     "존재하지 않는 ACL/route-map/peer-group/prefix-list 참조 없음")

    def check_duplicate_ip(self):
        """같은 IP를 두 장비가 들고 있으면 사고다 — 단, 설계상 공유하는 주소 두 종류는 뺀다.

          1. anycast gateway (`ip address virtual`)  — 모든 leaf가 같은 VIP를 공유
          2. MLAG 쌍의 공유 VTEP 주소 (Loopback1)     — AVD가 MLAG 쌍에 같은 VTEP IP를 준다
        """
        df = self.bf.q.ipOwners(duplicatesOnly=True).answer().frame()
        anycast = bf_lib.anycast_ips()
        mlag = bf_lib.mlag_pairs()
        vtep_if = bf_lib.vtep_source_interfaces()

        owners: dict[str, list[tuple[str, str]]] = {}
        for _, r in df.iterrows():
            ip = str(r["IP"])
            if ip in anycast:
                continue
            owners.setdefault(ip, []).append((str(r["Node"]), str(r["Interface"])))

        real, shared_vtep = {}, []
        for ip, own in owners.items():
            nodes = sorted({n for n, _ in own})
            if len(nodes) < 2:
                continue
            is_mlag_vtep = (
                len(nodes) == 2
                and mlag.get(nodes[0]) == nodes[1]
                and mlag.get(nodes[1]) == nodes[0]
                and all(i == vtep_if.get(n) for n, i in own)
            )
            if is_mlag_vtep:
                shared_vtep.append(f"{ip}: {nodes[0]}/{nodes[1]} 공유 VTEP")
            else:
                real[ip] = [f"{n}[{i}]" for n, i in own]

        if real:
            self.add("공통", "중복 IP", FAIL, f"{len(real)}개 주소가 중복 할당됨",
                     [f"{ip}: {', '.join(sorted(set(o)))}" for ip, o in real.items()])
        else:
            self.add("공통", "중복 IP", PASS,
                     f"설계상 공유 주소(anycast GW {len(anycast)}개, MLAG 공유 VTEP "
                     f"{len(shared_vtep)}개) 외 중복 없음", shared_vtep)

    def check_topology(self):
        l1 = json.loads((self.snapshot_path / "batfish" / "layer1_topology.json").read_text())
        l3 = self.bf.q.layer3Edges().answer().frame()
        ifp = self.bf.q.interfaceProperties(
            properties="Active,Primary_Address,Switchport,Channel_Group,MTU"
        ).answer().frame()
        l1_ifaces = {(e["node1"]["hostname"], e["node1"]["interfaceName"]) for e in l1["edges"]}
        dangling = []
        for r in ifp.itertuples():
            node, iface = str(r.Interface).split("[")[0], str(r.Interface).split("[")[1][:-1]
            if not iface.startswith("Ethernet"):
                continue
            if (node, iface) not in l1_ifaces:
                dangling.append(f"{node}[{iface}] (addr={r.Primary_Address})")
        if dangling:
            self.add("공통", "물리 토폴로지", WARN,
                     f"L1 링크 {len(l1['edges'])//2}개, 대향 미확인 인터페이스 {len(dangling)}개",
                     dangling)
        else:
            self.add("공통", "물리 토폴로지", PASS,
                     f"L1 링크 {len(l1['edges'])//2}개 / L3 인접 {len(l3)}개, "
                     f"모든 Ethernet 인터페이스의 대향이 확인됨")

    def check_mtu(self):
        l1 = json.loads((self.snapshot_path / "batfish" / "layer1_topology.json").read_text())
        ifp = self.bf.q.interfaceProperties(properties="MTU,Primary_Address").answer().frame()
        mtu = {}
        addr = {}
        for r in ifp.itertuples():
            key = str(r.Interface).replace("[", "|").replace("]", "").split("|")
            mtu[(key[0], key[1])] = r.MTU
            addr[(key[0], key[1])] = r.Primary_Address
        bad = []
        seen = set()
        for e in l1["edges"]:
            a = (e["node1"]["hostname"], e["node1"]["interfaceName"])
            b = (e["node2"]["hostname"], e["node2"]["interfaceName"])
            if (b, a) in seen:
                continue
            seen.add((a, b))
            # 라우팅되는 링크(양쪽 다 IP가 있는 P2P)만 비교한다
            if not (addr.get(a) and addr.get(b)):
                continue
            if mtu.get(a) != mtu.get(b):
                bad.append(f"{a[0]}[{a[1]}] MTU {mtu.get(a)} <-> {b[0]}[{b[1]}] MTU {mtu.get(b)}")
        if bad:
            self.add("공통", "L3 링크 MTU", FAIL, f"{len(bad)}개 링크 MTU 불일치", bad)
        else:
            self.add("공통", "L3 링크 MTU", PASS, "IP가 붙은 모든 P2P 링크의 양단 MTU 일치")

    def check_bgp(self):
        comp = self.bf.q.bgpSessionCompatibility().answer().frame()
        bad = comp[comp.Configured_Status != "UNIQUE_MATCH"]
        if len(bad):
            self.add("공통", "BGP 세션 호환성", FAIL, f"{len(bad)}/{len(comp)} 세션 비호환",
                     [f"{r.Node}({r.Local_IP}) -> {r.Remote_IP}: {r.Configured_Status}"
                      for r in bad.itertuples()])
        else:
            self.add("공통", "BGP 세션 호환성", PASS,
                     f"{len(comp)}개 세션 모두 UNIQUE_MATCH (AS/IP/peer-group 정합)")

        st = self.bf.q.bgpSessionStatus().answer().frame()
        bad = st[st.Established_Status != "ESTABLISHED"]
        if len(bad):
            self.add("공통", "BGP 세션 수립(모델)", FAIL,
                     f"{len(bad)}/{len(st)} 세션이 수립 불가",
                     [f"{r.Node}({r.Local_IP}) -> {r.Remote_Node}({r.Remote_IP}) "
                      f"[{r.Session_Type}] {r.Established_Status}" for r in bad.itertuples()])
        else:
            self.add("공통", "BGP 세션 수립(모델)", PASS,
                     f"{len(st)}개 세션 모두 ESTABLISHED (언더레이 도달성까지 성립)")

    def check_vtep_reachability(self):
        """모든 VXLAN 터널 종단(VTEP)이 서로 언더레이로 도달 가능한가.

        EVPN 세션이 붙는 것과 VXLAN 터널이 실제로 통하는 것은 별개다. EVPN 피어링은
        Loopback0(라우터 ID)를 쓰고 VXLAN 캡슐화는 Loopback1(VTEP)을 쓰기 때문에, 언더레이에서
        VTEP 주소만 막히면 **BGP 세션은 전부 Established인데 트래픽만 죽는다**. 그 상태를
        잡아내는 검사다 — `show bgp evpn summary`로는 절대 보이지 않는다.
        """
        self._vtep_reach("VTEP 간 도달성", dict(applications="icmp"), "ICMP")

    def check_vxlan_udp(self):
        """VTEP 사이에 실제 VXLAN 패킷(UDP 4789)이 지나갈 수 있는가.

        `VTEP 간 도달성`은 ICMP로 본다. 경로상 ACL이 ICMP·BGP는 허용하고 UDP 4789만 막으면
        ping도 되고 BGP도 Established인데 VXLAN 트래픽만 죽는다 — 운영자가 가장 늦게
        의심하는 유형이라 데이터 평면 프로토콜 그대로 따로 확인한다.
        """
        self._vtep_reach("VXLAN(UDP 4789) 도달성",
                         dict(ipProtocols="udp", srcPorts="1024-65535", dstPorts="4789"),
                         "UDP 4789")

    def _vtep_reach(self, name, hdr, proto_label):
        vni = self.bf.q.vxlanVniProperties().answer().frame()
        if len(vni) == 0:
            self.add("공통", name, SKIP, "스냅샷에 VXLAN VTEP이 없음")
            return
        vtep_ips = sorted({str(r.Local_VTEP_IP) for r in vni.itertuples() if r.Local_VTEP_IP})
        nodes = sorted({str(r.Node) for r in vni.itertuples()})
        srcif = bf_lib.vtep_source_interfaces()
        ifaces = sorted({srcif.get(n, "Loopback1") for n in nodes})
        start = f"/{'|'.join(nodes)}/[{'|'.join(ifaces)}]"

        ans = self.bf.q.reachability(
            pathConstraints=PathConstraints(startLocation=start),
            headers=HeaderConstraints(dstIps=",".join(vtep_ips), **hdr),
            actions="failure",
        ).answer().frame()

        pairs = len(nodes) * len(vtep_ips)
        if len(ans):
            detail = []
            for _, r in ans.iterrows():
                tr = r["Traces"][0]
                detail.append(f"{r['Flow'].ingressNode} {r['Flow'].srcIp} → {r['Flow'].dstIp}: "
                              f"{tr.disposition} ({' → '.join(h.node for h in tr.hops)})")
            self.add("공통", name, FAIL,
                     f"{proto_label}: VTEP {len(vtep_ips)}개 중 도달 불가 조합 {len(ans)}건 — VXLAN 터널 단절",
                     sorted(detail))
        else:
            self.add("공통", name, PASS,
                     f"{proto_label}: VTEP {len(vtep_ips)}개 × 출발 노드 {len(nodes)}대 = {pairs}개 조합 모두 도달 가능")

    def check_acl_lines(self):
        """앞줄에 가려 절대 매칭되지 않는 ACL 라인(shadowing)이 있는가.

        `deny tcp any any`가 `permit tcp any any eq bgp`보다 앞에 오는 식의 순서 실수는
        문법상 정상이라 장비가 그대로 받아들인다. Batfish filterLineReachability로 잡는다.
        """
        acls = self.bf.q.namedStructures(structureTypes="IP_ACCESS_LIST").answer().frame()
        if len(acls) == 0:
            self.add("공통", "ACL 라인 도달성", SKIP, "스냅샷에 IP ACL이 없음")
            return
        df = self.bf.q.filterLineReachability().answer().frame()
        if len(df):
            self.add("공통", "ACL 라인 도달성", FAIL,
                     f"절대 매칭되지 않는 ACL 라인 {len(df)}건 (앞 라인에 가려짐)",
                     [f"{', '.join(map(str, r.Sources))}: '{r.Unreachable_Line}' ← "
                      f"가린 라인 {list(r.Blocking_Lines)} ({r.Reason})" for r in df.itertuples()])
        else:
            self.add("공통", "ACL 라인 도달성", PASS,
                     f"IP ACL {len(acls)}개(장비별)의 모든 라인이 매칭 가능")

    # DCI 경계 ACL이 반드시 통과시켜야 하는 것 / 반드시 막아야 하는 것
    DCI_ACL_MUST_PERMIT = [
        ("ICMP", dict(applications="icmp")),
        ("BGP 접속 (dst TCP 179)", dict(ipProtocols="tcp", srcPorts="40000", dstPorts="179")),
        ("BGP 응답 (src TCP 179)", dict(ipProtocols="tcp", srcPorts="179", dstPorts="40000")),
        ("BFD multihop (UDP 4784)", dict(ipProtocols="udp", srcPorts="49152", dstPorts="4784")),
        ("VXLAN (UDP 4789)", dict(ipProtocols="udp", srcPorts="50000", dstPorts="4789")),
    ]
    DCI_ACL_MUST_DENY = [
        ("SSH (TCP 22)", dict(ipProtocols="tcp", srcPorts="40000", dstPorts="22")),
        ("Telnet (TCP 23)", dict(ipProtocols="tcp", srcPorts="40000", dstPorts="23")),
        ("SNMP (UDP 161)", dict(ipProtocols="udp", srcPorts="40000", dstPorts="161")),
    ]

    def check_dci_acl_policy(self):
        """Border Leaf의 DCI(core) 방향 인터페이스에 걸린 인바운드 ACL이 정책대로 동작하는가.

        ACL이 하나도 없으면 SKIP(실습 전 기본 상태). 하나라도 있으면
          1) 모든 DCI 방향 인터페이스에 빠짐없이 같은 ACL이 걸렸는지
          2) 운영에 필요한 트래픽은 PERMIT, 관리 프로토콜은 DENY인지 (testFilters)
        를 본다.
        """
        ifp = self.bf.q.interfaceProperties(
            nodes="/brdr/", properties="Description,Incoming_Filter_Name"
        ).answer().frame()
        dci = [(str(r.Interface).split("[")[0], str(r.Interface).split("[")[1][:-1],
                r.Incoming_Filter_Name)
               for r in ifp.itertuples() if re.search(r"_s\d-core\d_", str(r.Description or ""))]
        applied = [d for d in dci if d[2]]
        if not applied:
            self.add("공통", "DCI ACL 정책", SKIP,
                     f"Border Leaf DCI 방향 인터페이스 {len(dci)}개에 인바운드 ACL 없음")
            return
        detail, bad = [], 0
        sites = {n[:2] for n, _, _ in applied}
        missing = [f"{n}[{i}]: ACL 없음" for n, i, f in dci if not f and n[:2] in sites]
        names = {f for _, _, f in applied}
        if missing or len(names) > 1:
            bad += len(missing) + (len(names) > 1)
            detail += missing + ([f"인터페이스마다 다른 ACL: {sorted(names)}"] if len(names) > 1 else [])

        for node, acl in sorted({(n, f) for n, _, f in applied}):
            for want, cases in (("PERMIT", self.DCI_ACL_MUST_PERMIT), ("DENY", self.DCI_ACL_MUST_DENY)):
                for label, hdr in cases:
                    f = self.bf.q.testFilters(
                        headers=HeaderConstraints(srcIps="10.1.1.102", dstIps="10.1.1.2", **hdr),
                        nodes=node, filters=acl,
                    ).answer().frame()
                    got = str(f.iloc[0]["Action"]) if len(f) else "?"
                    line = str(f.iloc[0]["Line_Content"]) if len(f) else ""
                    if got != want:
                        bad += 1
                        detail.append(f"{node} {acl}: {label} 기대 {want} / 실제 {got} ({line})")
        if bad:
            self.add("공통", "DCI ACL 정책", FAIL,
                     f"{len(applied)}개 인터페이스 중 정책 위반 {bad}건", detail)
        else:
            self.add("공통", "DCI ACL 정책", PASS,
                     f"{len(applied)}개 인터페이스에 '{next(iter(names))}' 적용, "
                     f"필수 허용 {len(self.DCI_ACL_MUST_PERMIT)}종 PERMIT / 관리 프로토콜 "
                     f"{len(self.DCI_ACL_MUST_DENY)}종 DENY 확인",
                     [f"{n}[{i}] ← {f}" for n, i, f in applied])

    # ------------------------------------------------------------------ 랩 시나리오
    def _svi_check(self, lab, label, vlans, vrf_of):
        """지정한 VLAN들의 SVI/anycast GW/VNI 매핑이 모든 leaf에 동일하게 있는지."""
        ifp = self.bf.q.interfaceProperties(
            nodes="/leaf/", interfaces="/Vlan/", properties="Primary_Address,VRF,Active"
        ).answer().frame()
        have = {}
        for r in ifp.itertuples():
            node, iface = str(r.Interface).split("[")[0], str(r.Interface).split("[")[1][:-1]
            m = re.match(r"Vlan(\d+)$", iface)
            if m:
                have[(node, int(m.group(1)))] = (r.VRF, r.Primary_Address)
        missing, wrong = [], []
        for node in self.leafs:
            for v in vlans:
                got = have.get((node, v))
                if not got:
                    missing.append(f"{node}: Vlan{v} 없음")
                    continue
                exp_vrf, exp_ip = vrf_of(v), ANYCAST_GW[v]
                if got[0] != exp_vrf:
                    wrong.append(f"{node} Vlan{v}: VRF {got[0]} (기대 {exp_vrf})")
                if got[1] and not str(got[1]).startswith(exp_ip + "/"):
                    wrong.append(f"{node} Vlan{v}: IP {got[1]} (기대 {exp_ip}/24)")
        if missing or wrong:
            self.add(lab, f"{label} SVI/게이트웨이", FAIL,
                     f"누락 {len(missing)}건, 불일치 {len(wrong)}건", missing + wrong)
        else:
            self.add(lab, f"{label} SVI/게이트웨이", PASS,
                     f"leaf {len(self.leafs)}대 모두 VLAN {','.join(map(str,vlans))} SVI 존재, "
                     f"anycast GW/VRF 양 DC 동일")

        vni = self.bf.q.vxlanVniProperties(nodes="/leaf/").answer().frame()
        mapped = {(str(r.Node), int(r.VLAN)): int(r.VNI) for r in vni.itertuples() if r.VLAN}
        vni_bad = []
        for node in self.leafs:
            for v in vlans:
                got = mapped.get((node, v))
                if got != L2VNI[v]:
                    vni_bad.append(f"{node}: VLAN {v} -> VNI {got} (기대 {L2VNI[v]})")
        if vni_bad:
            self.add(lab, f"{label} VXLAN VNI 매핑", FAIL, f"{len(vni_bad)}건 불일치", vni_bad)
        else:
            self.add(lab, f"{label} VXLAN VNI 매핑", PASS,
                     "  ".join(f"VLAN {v}->VNI {L2VNI[v]}" for v in vlans))

    def lab1(self):
        self._svi_check("Lab 1", "VLAN 30/40/50", [30, 40, 50], lambda v: "A")

    def lab2(self):
        if not self.brdrs:
            self.add("Lab 2", "Border Leaf 편입", FAIL,
                     "스냅샷에 s{n}-brdr* 노드가 없음 (inventory/fabric.yml 주석 해제 필요)")
            return
        self.add("Lab 2", "Border Leaf 편입", PASS,
                 f"Border Leaf {len(self.brdrs)}대 렌더링됨: {', '.join(self.brdrs)}")

        st = self.bf.q.bgpSessionStatus().answer().frame()
        # brdr <-> core 언더레이 (172.16.255.x)
        underlay = st[(st.Node.isin(self.brdrs)) & (st.Remote_IP.astype(str).str.startswith("172.16.255."))]
        bad = underlay[underlay.Established_Status != "ESTABLISHED"]
        if len(underlay) == 0:
            self.add("Lab 2", "Border Leaf ↔ DCI core 언더레이", FAIL,
                     "brdr에 core 방향 BGP 네이버가 없음 (core_interfaces 주석 해제 확인)")
        elif len(bad):
            self.add("Lab 2", "Border Leaf ↔ DCI core 언더레이", FAIL,
                     f"{len(bad)}/{len(underlay)} 세션 수립 불가",
                     [f"{r.Node} -> {r.Remote_IP}: {r.Established_Status}" for r in bad.itertuples()])
        else:
            self.add("Lab 2", "Border Leaf ↔ DCI core 언더레이", PASS,
                     f"P2P eBGP {len(underlay)}개 세션 수립 (172.16.255.0/24 대역)")

        # brdr <-> spine 로컬 오버레이
        local = st[(st.Node.isin(self.brdrs)) & (st.Address_Families.astype(str).str.contains("EVPN"))
                   & (st.Remote_Node.astype(str).str.contains("spine"))]
        if len(local) and all(local.Established_Status == "ESTABLISHED"):
            self.add("Lab 2", "Border Leaf 로컬 EVPN 오버레이", PASS,
                     f"spine과 EVPN 세션 {len(local)}개 수립")
        else:
            self.add("Lab 2", "Border Leaf 로컬 EVPN 오버레이", FAIL,
                     f"spine 방향 EVPN 세션 {len(local)}개 중 수립 실패 존재")

    def lab3(self):
        st = self.bf.q.bgpSessionStatus().answer().frame()
        remote = st[(st.Node.astype(str).str.contains("brdr"))
                    & (st.Remote_Node.astype(str).str.contains("brdr"))
                    & (st.Node.astype(str).str[:2] != st.Remote_Node.astype(str).str[:2])]
        if len(remote) == 0:
            self.add("Lab 3", "EVPN Gateway 원격 피어링", FAIL,
                     "DC 간 brdr↔brdr EVPN 세션 없음 (evpn_gateway 블록 주석 해제 필요)")
        else:
            bad = remote[remote.Established_Status != "ESTABLISHED"]
            if len(bad):
                self.add("Lab 3", "EVPN Gateway 원격 피어링", FAIL,
                         f"{len(bad)}/{len(remote)} 세션 수립 불가",
                         [f"{r.Node} -> {r.Remote_Node}({r.Remote_IP})" for r in bad.itertuples()])
            else:
                self.add("Lab 3", "EVPN Gateway 원격 피어링", PASS,
                         f"DC 간 EBGP_MULTIHOP EVPN 세션 {len(remote)}개 수립 "
                         f"(Loopback0 10.1.0.x ↔ 10.1.0.1xx)")

        # 재발신(도메인 표시)은 Batfish가 모델링하지 않으므로 설정 텍스트로 확인한다
        cfgdir = self.snapshot_path / "configs"
        with_marker = sorted(p.stem for p in cfgdir.glob("*.cfg")
                             if "domain remote" in p.read_text())
        leaked = [n for n in with_marker if "brdr" not in n]
        if not with_marker:
            self.add("Lab 3", "EVPN 경로 재발신 표시", FAIL, "'domain remote' 설정이 어디에도 없음")
        elif leaked:
            self.add("Lab 3", "EVPN 경로 재발신 표시", FAIL,
                     "Border Leaf가 아닌 장비에 재발신 설정이 있음", leaked)
        else:
            self.add("Lab 3", "EVPN 경로 재발신 표시", PASS,
                     f"'domain remote'가 Border Leaf {len(with_marker)}대에만 존재: "
                     f"{', '.join(with_marker)}")

        # VTEP 간 언더레이 도달성 (DC1 leaf -> DC2 leaf)
        src = [n for n in self.leafs if n.startswith("s1")]
        dst = [n for n in self.leafs if n.startswith("s2")]
        if src and dst:
            lo1 = self.bf.q.interfaceProperties(
                nodes="/leaf/", interfaces="Loopback1", properties="Primary_Address"
            ).answer().frame()
            ips = {str(r.Interface).split("[")[0]: str(r.Primary_Address).split("/")[0]
                   for r in lo1.itertuples()}
            a, b = src[0], dst[0]
            tr = self.traces(f"{a}[Loopback1]", ips[a], ips[b])
            ok = [t for t in tr if t[0] == "ACCEPTED"]
            if ok:
                self.add("Lab 3", "VTEP 간 언더레이 도달성", PASS,
                         f"{a}({ips[a]}) → {b}({ips[b]}) 경로 {len(ok)}개 ACCEPTED",
                         [" → ".join(ok[0][1])])
            else:
                self.add("Lab 3", "VTEP 간 언더레이 도달성", FAIL,
                         f"{a} → {b} 도달 불가", [f"{d}: {' → '.join(h)}" for d, h in tr[:5]])

    def lab4(self):
        self._svi_check("Lab 4", "VLAN 100/200", [100, 200], lambda v: str(v))
        vrfs = self.bf.q.nodeProperties(nodes="/leaf/", properties="VRFs").answer().frame()
        missing = []
        for r in vrfs.itertuples():
            have = set(r.VRFs)
            for want in ("100", "200"):
                if want not in have:
                    missing.append(f"{r.Node}: vrf {want} 없음")
        if missing:
            self.add("Lab 4", "테넌트 VRF 분리", FAIL, f"{len(missing)}건 누락", missing)
        else:
            self.add("Lab 4", "테넌트 VRF 분리", PASS,
                     f"leaf {len(self.leafs)}대에 vrf 100 / vrf 200 인스턴스 존재 "
                     f"(VLAN별 전용 VRF)")

        # VRF 격리: VRF 100에서 VRF 200 대역으로 나가는 경로가 없어야 한다
        rt = self.bf.q.routes(nodes="/leaf/", vrfs="100").answer().frame()
        leak = rt[rt.Network.astype(str).str.startswith("10.200.200.")]
        if len(leak):
            self.add("Lab 4", "VRF 100/200 격리", FAIL,
                     f"VRF 100 라우팅 테이블에 10.200.200.0/24 경로 {len(leak)}건 누출",
                     [f"{r.Node}: {r.Network} via {r.Next_Hop}" for r in leak.itertuples()][:8])
        else:
            self.add("Lab 4", "VRF 100/200 격리", PASS,
                     "VRF 100 라우팅 테이블에 VLAN 200 대역(10.200.200.0/24) 경로 없음")

    def lab5(self):
        # core 스위치는 eos_designs 대상이 아니므로 Batfish로는 "설정이 깨지지 않았는지"만 본다.
        cores = [n for n in self.nodes if "core" in n]
        if not cores:
            self.add("Lab 5", "DCI core 설정", SKIP, "스냅샷에 core 장비 없음")
        else:
            self.add("Lab 5", "DCI core 설정 파싱", PASS,
                     f"core {len(cores)}대 파싱/라우팅 모델 정상: {', '.join(cores)}")
        # 태그는 CVP 메타데이터라 설정 파일에 나타나지 않는다 → group_vars에서 확인
        found, missing = [], []
        for dc in self.dcs:
            f = REPO / "sites" / dc / "group_vars" / f"{dc}_dci.yml"
            if not f.exists():
                continue
            text = f.read_text()
            active = [l for l in text.splitlines() if l.strip().startswith("cv_device_tags")]
            (found if active else missing).append(f.relative_to(REPO).as_posix())
        if missing:
            self.add("Lab 5", "CVP topology 태그 변수", FAIL,
                     f"{len(missing)}개 파일에서 cv_device_tags가 주석 상태", missing)
        else:
            self.add("Lab 5", "CVP topology 태그 변수", PASS,
                     f"cv_device_tags 활성: {', '.join(found)} "
                     f"(태그 자체는 Batfish 검증 대상이 아님 — CVP 메타데이터)")

    def lab6(self):
        lo = self.bf.q.interfaceProperties(
            nodes="/leaf/", interfaces="Loopback210", properties="Primary_Address,VRF,Active"
        ).answer().frame()
        if len(lo) == 0:
            self.add("Lab 6", "프로브 소스 Loopback210", FAIL,
                     "어떤 leaf에도 Loopback210이 없음 (structured_config 주석 해제 필요)")
            return
        addrs, detail = [], []
        for r in lo.itertuples():
            node = str(r.Interface).split("[")[0]
            addrs.append(str(r.Primary_Address))
            detail.append(f"{node}: {r.Primary_Address} (vrf {r.VRF})")
        dupes = {a for a in addrs if addrs.count(a) > 1}
        wrong_vrf = [d for d in detail if "vrf A" not in d]
        if dupes or wrong_vrf:
            self.add("Lab 6", "프로브 소스 Loopback210", FAIL,
                     f"중복 주소 {len(dupes)}개 / VRF 불일치 {len(wrong_vrf)}건",
                     sorted(dupes) + wrong_vrf)
        else:
            self.add("Lab 6", "프로브 소스 Loopback210", PASS,
                     f"leaf {len(lo)}대에 VRF A 전용 /32 고유 주소 구성", detail)

        cfgdir = self.snapshot_path / "configs"
        snat = sorted(p.stem for p in cfgdir.glob("*.cfg")
                      if "ip address virtual source-nat" in p.read_text())
        lo_nodes = sorted(str(r.Interface).split("[")[0] for r in lo.itertuples())
        if set(snat) != set(lo_nodes):
            self.add("Lab 6", "virtual source-nat 짝 맞춤", FAIL,
                     "Loopback210이 있는 장비와 source-nat 설정 장비가 다름",
                     [f"Loopback210: {lo_nodes}", f"source-nat: {snat}"])
        else:
            self.add("Lab 6", "virtual source-nat 짝 맞춤", PASS,
                     f"{len(snat)}대 모두 Loopback210 + source-nat 쌍 구성")

        # 프로브 소스 -> 감시 대상 호스트 도달성
        targets = {"s1": ("10.10.10.22", "s2-host2"), "s2": ("10.10.10.11", "s1-host1")}
        for r in lo.itertuples():
            node = str(r.Interface).split("[")[0]
            site = node[:2]
            if site not in targets:
                continue
            dst, dst_name = targets[site]
            src = str(r.Primary_Address).split("/")[0]
            tr = self.traces(f"{node}[Loopback210]", src, dst)
            ok = [t for t in tr if t[0] == "ACCEPTED"]
            if ok:
                self.add("Lab 6", f"프로브 경로 {node} → {dst_name}", PASS,
                         f"{src} → {dst} ACCEPTED", [" → ".join(ok[0][1])])
            else:
                self.add("Lab 6", f"프로브 경로 {node} → {dst_name}", FAIL,
                         f"{src} → {dst} 도달 불가",
                         [f"{d}: {' → '.join(h)}" for d, h in tr[:3]])

    # ------------------------------------------------------------------ 실행/보고
    def run(self, labs: list[int]):
        print(f"\n스냅샷: {self.snapshot_path}")
        print(f"노드 {len(self.nodes)}개: {', '.join(self.nodes)}\n")
        print("[공통 검사]")
        for fn in (self.check_parse, self.check_undefined_refs, self.check_duplicate_ip,
                   self.check_topology, self.check_mtu, self.check_bgp,
                   self.check_vtep_reachability, self.check_vxlan_udp,
                   self.check_acl_lines, self.check_dci_acl_policy):
            fn()
        for n in labs:
            print(f"\n[Lab {n} 시나리오 검사]")
            getattr(self, f"lab{n}")()
        return self.results

    def report(self, path: Path):
        counts = {s: sum(1 for r in self.results if r.status == s) for s in (PASS, FAIL, WARN, SKIP)}
        lines = [
            "# Batfish Pre-flight 검증 리포트", "",
            f"- 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- 스냅샷: `{self.snapshot_path.relative_to(REPO).as_posix()}` "
            f"(대상 {', '.join(self.dcs)}, 노드 {len(self.nodes)}개)",
            f"- 결과: **PASS {counts[PASS]} / FAIL {counts[FAIL]} / WARN {counts[WARN]} / SKIP {counts[SKIP]}**",
            "", "| 구분 | 검사 항목 | 결과 | 요약 |", "|---|---|---|---|",
        ]
        for r in self.results:
            lines.append(f"| {r.lab} | {r.name} | {r.status} | {r.summary} |")
        lines += ["", "## 상세", ""]
        for r in self.results:
            if not r.detail:
                continue
            lines += [f"### [{r.lab}] {r.name} — {r.status}", "", "```"]
            lines += r.detail
            lines += ["```", ""]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines))
        return counts


def main():
    ap = argparse.ArgumentParser(description="AVD 배포 전 Batfish 사전 검증")
    ap.add_argument("--dc", default="all", choices=["dc1", "dc2", "all"])
    ap.add_argument("--labs", default="all",
                    help="검사할 랩 번호 (예: 1,2,3 / all / none)")
    ap.add_argument("--report", default=None, help="마크다운 리포트 경로")
    args = ap.parse_args()

    dcs = ["dc1", "dc2"] if args.dc == "all" else [args.dc]
    if args.labs == "all":
        labs = [1, 2, 3, 4, 5, 6]
    elif args.labs == "none":
        labs = []
    else:
        labs = [int(x) for x in args.labs.split(",") if x.strip()]

    pf = Preflight(dcs)
    pf.run(labs)
    report = Path(args.report) if args.report else \
        REPORT_DIR / f"preflight_{'-'.join(dcs)}_{datetime.now():%Y%m%d_%H%M%S}.md"
    counts = pf.report(report)
    print(f"\n{'='*72}")
    print(f"PASS {counts[PASS]} / FAIL {counts[FAIL]} / WARN {counts[WARN]} / SKIP {counts[SKIP]}")
    print(f"리포트: {report}")
    print("=" * 72)
    return 1 if counts[FAIL] else 0


if __name__ == "__main__":
    sys.exit(main())
