#!/usr/bin/env python3
"""EOS MCP Server로 랩 장비의 주요 정보를 수집해 토폴로지를 HTML 한 장으로 그립니다 (읽기 전용).

Claude Code가 쓰는 것과 같은 eos-mcp-server(./mcp/run-eos-mcp.sh serve)를 stdio로 띄우고,
MCP 도구(eos_get_facts, eos_run_show)만 호출합니다. 장비 설정은 절대 바꾸지 않습니다.

  python3 mcp/topology.py                   # dc1 + dc2 → mcp/topology.html, mcp/topology.json
  python3 mcp/topology.py --targets dc1     # 특정 그룹/장비만
  python3 mcp/topology.py --from-json mcp/topology.json   # 수집 없이 HTML만 다시 그리기

수집 항목: show version(facts), show lldp neighbors, show ip interface brief,
           show bgp summary, show mlag, show vxlan vtep
"""
import argparse
import html
import ipaddress
import json
import os
import re
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SHOW_CMDS = ["show lldp neighbors", "show ip interface brief", "show bgp summary", "show mlag", "show vxlan vtep",
             "show interfaces status", "show port-channel"]


# --------------------------------------------------------------------------- MCP client (stdio JSON-RPC)
class MCP:
    def __init__(self):
        self.p = subprocess.Popen([os.path.join(HERE, "run-eos-mcp.sh"), "serve"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.i = 0
        self.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "atd-topology", "version": "1"}})
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _send(self, msg):
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()

    def call(self, method, params):
        self.i += 1
        self._send({"jsonrpc": "2.0", "id": self.i, "method": method, "params": params})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("eos-mcp-server가 종료되었습니다. ./mcp/run-eos-mcp.sh validate-inventory 로 확인하세요.")
            msg = json.loads(line)
            if msg.get("id") == self.i:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg["result"]

    def tool(self, name, **args):
        res = self.call("tools/call", {"name": name, "arguments": args})
        return json.loads(res["content"][0]["text"])

    def close(self):
        self.p.terminate()


# --------------------------------------------------------------------------- collection
def collect(targets):
    mcp = MCP()
    data = {"collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "devices": {}}
    try:
        inv = mcp.tool("eos_list_inventory")
        mgmt = {h.get("name") or h.get("inventory_hostname"): h.get("ansible_host") or h.get("host")
                for h in inv.get("hosts", []) if isinstance(h, dict)}
        for target in targets:
            facts = mcp.tool("eos_get_facts", target=target)
            for r in facts.get("results", []):
                d = data["devices"].setdefault(r["inventory_hostname"], {"show": {}})
                d["mgmt_ip"] = r.get("resolved_endpoint") or mgmt.get(r["inventory_hostname"])
                d["facts"] = r.get("facts") or r.get("output") or {}
                d["status"] = r.get("status")
            # 명령마다 따로 요청: host처럼 BGP가 없는 장비의 오류가 다른 명령 결과를 막지 않도록
            for cmd in SHOW_CMDS:
                out = mcp.tool("eos_run_show", target=target, commands=[cmd], output_format="json")
                for r in out.get("results", []):
                    d = data["devices"].setdefault(r["inventory_hostname"], {"show": {}})
                    cr = (r.get("command_results") or [{}])[0]
                    if r.get("status") == "success" and isinstance(cr.get("output"), dict):
                        d["show"][cmd] = cr["output"]
            print(f"  collected {target}: {len(facts.get('results', []))} devices", file=sys.stderr)
    finally:
        mcp.close()
    return data


# --------------------------------------------------------------------------- model
def short(name):
    return name.split(".")[0]


def role_of(name):
    for r in ("spine", "leaf", "brdr", "core", "host"):
        if r in name:
            return r
    return "other"


def ifshort(ifn):
    """Ethernet4 -> Et4, Port-Channel1000 -> Po1000, Loopback1 -> Lo1"""
    for long_, s_ in (("Ethernet", "Et"), ("Port-Channel", "Po"), ("Loopback", "Lo"), ("Vlan", "Vl"),
                      ("Management", "Ma")):
        if ifn.startswith(long_):
            return s_ + ifn[len(long_):]
    return ifn


def build_model(data):
    devs = data["devices"]
    nodes = {}
    for name, d in devs.items():
        s, f = d.get("show", {}), d.get("facts", {})
        intfs = s.get("show ip interface brief", {}).get("interfaces", {})
        ips = {}
        for ifn, i in intfs.items():
            a = (i.get("interfaceAddress") or {}).get("ipAddr") or {}
            if a.get("address") and a.get("address") != "0.0.0.0":
                ips[ifn] = f'{a["address"]}/{a["maskLen"]}'
        bgp = s.get("show bgp summary", {}).get("vrfs", {}).get("default", {})
        peers = bgp.get("peers", {})
        est = sum(1 for p in peers.values() if p.get("peerState") == "Established")
        mlag = s.get("show mlag", {})
        vtep = s.get("show vxlan vtep", {})
        remote_vteps = sorted({v for i in (vtep.get("interfaces") or {}).values() for v in i.get("vteps", [])})
        st = s.get("show interfaces status", {}).get("interfaceStatuses", {})
        po_of = {}
        for po, pd in (s.get("show port-channel", {}).get("portChannels") or {}).items():
            for m in list((pd.get("activePorts") or {})) + list((pd.get("inactivePorts") or {})):
                po_of[m] = po
        nodes[name] = {
            "name": name, "role": role_of(name), "dc": "dc1" if name.startswith("s1-") else "dc2",
            "mgmt_ip": d.get("mgmt_ip"), "status": d.get("status"),
            "model": f.get("model") or f.get("modelName") or "-",
            "eos": (f.get("eos_version") or f.get("version") or "-").split("-")[0],
            "asn": bgp.get("asn"), "router_id": bgp.get("routerId"),
            "lo0": ips.get("Loopback0"), "lo1": ips.get("Loopback1"),
            "bgp_est": est, "bgp_total": len(peers),
            "bgp_down": sorted(ip for ip, p in peers.items() if p.get("peerState") != "Established"),
            "peers": peers,
            "mlag": (f'{mlag["state"]} ({mlag.get("domainId")})' if mlag.get("state") not in (None, "disabled") else None),
            "mlag_peer": mlag.get("peerAddress"),
            "remote_vteps": remote_vteps, "ips": ips,
            "ifstatus": {k: {"status": v.get("linkStatus"), "desc": v.get("description", "")} for k, v in st.items()},
            "po_of": po_of,
        }
    links, seen = [], set()
    for name, d in devs.items():
        for n in d.get("show", {}).get("show lldp neighbors", {}).get("lldpNeighbors", []):
            peer = short(n["neighborDevice"])
            if peer not in nodes:
                continue
            key = tuple(sorted([(name, n["port"]), (peer, n["neighborPort"])]))
            if key in seen:
                continue
            seen.add(key)
            A, B = nodes[name], nodes[peer]
            a_ip, b_ip = A["ips"].get(n["port"]), B["ips"].get(n["neighborPort"])
            kind, state = "l2", "n/a"
            if a_ip and b_ip:
                kind = "l3"
                pa, pb = a_ip.split("/")[0], b_ip.split("/")[0]
                sa = A["peers"].get(pb, {}).get("peerState")
                sb = B["peers"].get(pa, {}).get("peerState")
                state = "up" if "Established" in (sa, sb) else ("down" if (sa or sb) else "no-bgp")
            if {A["role"], B["role"]} == {"core"} and A["dc"] != B["dc"]:
                kind = "dci"
            elif A["role"] == B["role"] and A["dc"] == B["dc"] and not (a_ip and b_ip):
                kind = "peer"  # MLAG peer-link / core port-channel
            a_st = A["ifstatus"].get(n["port"], {}).get("status")
            b_st = B["ifstatus"].get(n["neighborPort"], {}).get("status")
            links.append({"a": name, "a_if": n["port"], "a_ip": a_ip, "b": peer, "b_if": n["neighborPort"],
                          "b_ip": b_ip, "kind": kind, "bgp": state,
                          "a_po": A["po_of"].get(n["port"]), "b_po": B["po_of"].get(n["neighborPort"]),
                          "a_st": a_st, "b_st": b_st,
                          "oper": "up" if a_st in (None, "connected") and b_st in (None, "connected") else "down"})
    # VXLAN 터널: Loopback1(VTEP) 주소 단위로 묶는다 (MLAG 쌍은 같은 VTEP 주소를 공유)
    vtep_nodes = {}
    for n in nodes.values():
        if n["lo1"]:
            vtep_nodes.setdefault(n["lo1"].split("/")[0], []).append(n["name"])
    tunnels = set()
    for n in nodes.values():
        if not n["lo1"]:
            continue
        me = n["lo1"].split("/")[0]
        for v in n["remote_vteps"]:
            if v in vtep_nodes:
                tunnels.add(tuple(sorted((me, v))))
    for n in nodes.values():
        n.pop("peers")
    return {"collected_at": data["collected_at"], "nodes": nodes, "links": links,
            "vteps": {k: sorted(v) for k, v in vtep_nodes.items()}, "tunnels": sorted(tunnels)}


# --------------------------------------------------------------------------- layout
NW, NH, GAP = 128, 80, 84            # 기본 박스 크기, 같은 줄 박스 간격 (양쪽 포트 배지 + 선이 들어갈 폭)
PORT_W, PORT_H = 30, 16              # 포트 배지 크기 (박스 가장자리에 붙는 인터페이스 이름)
Y = {"spine": 40, "row": 310, "host": 570, "core1": 175, "core2": 445}
CORE_GAP = 300                        # DC1 core ↔ DC2 core 사이 (DCI 라벨 자리)


def _row_of(n):
    return {"spine": "spine", "leaf": "row", "brdr": "row", "host": "host", "other": "host"}.get(n["role"], "row")


def _y_of(model, name):
    n = model["nodes"][name]
    if n["role"] == "core":
        cores = sorted(k for k, v in model["nodes"].items() if v["dc"] == n["dc"] and v["role"] == "core")
        return Y["core1"] if cores.index(name) == 0 else Y["core2"]
    return Y[_row_of(n)]


def node_widths(model):
    """박스 폭 = 위/아래 변에 붙는 포트 수에 맞춘다 (spine은 아래에 6개)."""
    cnt = {}
    for l in model["links"]:
        for me, other in ((l["a"], l["b"]), (l["b"], l["a"])):
            dy = _y_of(model, other) - _y_of(model, me)
            if abs(dy) > 40:
                cnt[(me, dy > 0)] = cnt.get((me, dy > 0), 0) + 1
    return {n: max(NW, max(cnt.get((n, True), 0), cnt.get((n, False), 0)) * (PORT_W + 4) + 20)
            for n in model["nodes"]}


def layout(model, W):
    nodes = model["nodes"]
    by = lambda dc, role: sorted(n for n, v in nodes.items() if v["dc"] == dc and v["role"] == role)
    row_w = lambda names: sum(W[n] for n in names) + GAP * (len(names) - 1)
    rows = {}
    for dc in ("dc1", "dc2"):
        rows[(dc, "row")] = by(dc, "leaf") + by(dc, "brdr") if dc == "dc1" else by(dc, "brdr") + by(dc, "leaf")
        rows[(dc, "spine")] = by(dc, "spine")
    dc_w = max(row_w(v) for v in rows.values())
    core_w = max([W[n] for n in nodes if nodes[n]["role"] == "core"] or [NW])
    x_core1 = dc_w + 100
    x_core2 = x_core1 + core_w + CORE_GAP
    x_dc2 = x_core2 + core_w + 100
    pos = {}
    for dc, x0 in (("dc1", 0), ("dc2", x_dc2)):
        for key in ("row", "spine"):
            names = rows[(dc, key)]
            x = x0 + (dc_w - row_w(names)) / 2
            for nm in names:
                pos[nm] = (x, Y[key])
                x += W[nm] + GAP
        cx = x_core1 if dc == "dc1" else x_core2
        for nm in by(dc, "core"):
            pos[nm] = (cx + (core_w - W[nm]) / 2, _y_of(model, nm))
    for nm in nodes:           # host: 연결된 장비들의 가운데 아래
        if nm in pos:
            continue
        nb = [l["b"] if l["a"] == nm else l["a"] for l in model["links"] if nm in (l["a"], l["b"])]
        cs = [pos[x][0] + W[x] / 2 for x in nb if x in pos]
        pos[nm] = ((sum(cs) / len(cs) if cs else 0) - W[nm] / 2, _y_of(model, nm))
    return pos, x_dc2 + dc_w, Y["host"] + NH + 34, dc_w, x_core1, x_core2, core_w


def ports(model, pos, W):
    """링크 끝마다 포트 배지 위치와 선이 시작할 점을 정한다.

    같은 변의 포트는 상대 장비 위치 순으로 정렬해 일정 간격으로 놓으므로 선이 서로 엇갈리지 않는다.
    반환: {(링크 index, "a"|"b"): (배지 중심 x, y, 선 시작 x, y, 변)}
    """
    sides = {}
    for i, l in enumerate(model["links"]):
        for me, other, end in ((l["a"], l["b"], "a"), (l["b"], l["a"], "b")):
            (x1, y1), (x2, y2) = pos[me], pos[other]
            cx2 = x2 + W[other] / 2
            if abs(y2 - y1) > 40:
                side, sk = ("bottom" if y2 > y1 else "top"), cx2
            else:
                side, sk = ("right" if x2 > x1 else "left"), y2
            sides.setdefault((me, side), []).append((sk, len(l[f"{end}_if"]), l[f"{end}_if"], i, end))
    out = {}
    for (me, side), lst in sides.items():
        lst.sort()
        x, y = pos[me]
        w = W[me]
        n = len(lst)
        for k, (_, _, _, i, end) in enumerate(lst):
            if side in ("top", "bottom"):
                step = PORT_W + 4
                px = x + w / 2 + (k - (n - 1) / 2) * step
                if side == "top":
                    out[(i, end)] = (px, y - PORT_H / 2, px, y - PORT_H, side)
                else:
                    out[(i, end)] = (px, y + NH + PORT_H / 2, px, y + NH + PORT_H, side)
            else:
                step = PORT_H + 6
                py = y + NH / 2 + (k - (n - 1) / 2) * step
                if side == "left":
                    out[(i, end)] = (x - PORT_W / 2, py, x - PORT_W, py, side)
                else:
                    out[(i, end)] = (x + w + PORT_W / 2, py, x + w + PORT_W, py, side)
    return out


# --------------------------------------------------------------------------- HTML
def render_html(model):
    W = node_widths(model)
    pos, width, height, dc_w, x_core1, x_core2, core_w = layout(model, W)
    pp = ports(model, pos, W)
    esc = html.escape
    K = {"l3": "L3 P2P", "l2": "L2 / Port-Channel 멤버", "dci": "DCI (core↔core)", "peer": "MLAG / peer 링크"}
    lines, portg, mids = [], [], []

    def pill(x, y, text, cls):
        w = len(text) * 5.9 + 8
        return (f'<g class="pill {cls}"><rect x="{x - w / 2:.1f}" y="{y - 7.5:.1f}" width="{w:.1f}" height="15" rx="4"/>'
                f'<text x="{x:.1f}" y="{y + 3.6:.1f}" text-anchor="middle">{esc(text)}</text></g>')

    # 중앙 라벨(DCI, Po, IP) 겹침 방지용: 장비 박스 + 포트 배지 + 먼저 놓은 라벨
    occupied = [(x - 2, y - PORT_H - 2, W[n] + 4, NH + 2 * PORT_H + 4) for n, (x, y) in pos.items()]
    hit = lambda r: any(r[0] < o[0] + o[2] and o[0] < r[0] + r[2] and r[1] < o[1] + o[3] and o[1] < r[1] + r[3]
                        for o in occupied)

    def place(cands, text, cls, force=True):
        w = len(text) * 5.9 + 8
        for (cx, cy) in cands:
            r = (cx - w / 2 - 1, cy - 8.5, w + 2, 17)
            if not hit(r):
                occupied.append(r)
                return pill(cx, cy, text, cls)
        if force and cands:
            cx, cy = cands[0]
            occupied.append((cx - w / 2, cy - 7.5, w, 15))
            return pill(cx, cy, text, cls)
        return ""

    po_drawn = set()
    for i, l in enumerate(model["links"]):
        _, _, ax, ay, _ = pp[(i, "a")]
        _, _, bx, by_, _ = pp[(i, "b")]
        cls = "down" if l["oper"] == "down" else {"up": "up", "down": "down", "no-bgp": "nobgp"}.get(l["bgp"], l["kind"])
        tip = (f'{l["a"]} {l["a_if"]} {l["a_ip"] or ""}{" (" + l["a_po"] + ")" if l["a_po"] else ""}  ↔  '
               f'{l["b"]} {l["b_if"]} {l["b_ip"] or ""}{" (" + l["b_po"] + ")" if l["b_po"] else ""}\n'
               f'{K[l["kind"]]} · 링크 {l["oper"]}' + (f' · BGP {l["bgp"]}' if l["kind"] in ("l3", "dci") else ""))
        da = f'data-a="{esc(l["a"])}" data-b="{esc(l["b"])}"'
        lines.append(f'<line class="lk {cls} k-{l["kind"]}" {da} x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by_:.1f}">'
                     f'<title>{esc(tip)}</title></line>')
        # 포트 배지: 박스 가장자리에 붙고, 테두리 색 = 선 색
        for end in ("a", "b"):
            cx, cy, _, _, side = pp[(i, end)]
            ifn, po = ifshort(l[f"{end}_if"]), l[f"{end}_po"]
            t = f'{l[end]} {l[end + "_if"]}' + (f' ({po})' if po else "") + (f' {l[end + "_ip"]}' if l[end + "_ip"] else "")
            portg.append(f'<g class="port {cls} k-{l["kind"]}" {da}><title>{esc(t)}</title>'
                         f'<rect x="{cx - PORT_W / 2:.1f}" y="{cy - PORT_H / 2:.1f}" width="{PORT_W}" height="{PORT_H}" rx="3"/>'
                         f'<text x="{cx:.1f}" y="{cy + 3.8:.1f}" text-anchor="middle">{esc(ifn)}</text></g>')
            occupied.append((cx - PORT_W / 2, cy - PORT_H / 2, PORT_W, PORT_H))
        mx, my = (ax + bx) / 2, (ay + by_) / 2
        if l["kind"] == "dci":
            mids.append(place([(mx, my - 16)], f'DCI · {l["a_ip"] or "?"} ↔ .{(l["b_ip"] or "").split(".")[-1]}', "dcil"))
            mids.append(place([(mx, my + 16)], f'eBGP {l["bgp"]}', "dcil s-" + l["bgp"]))
        if l["kind"] == "peer" and l["a_po"] and (l["a"], l["b"]) not in po_drawn:
            po_drawn.add((l["a"], l["b"]))
            (x1, y1), (x2, y2) = pos[l["a"]], pos[l["b"]]
            if abs(y1 - y2) < 40:   # 좌우 배치 → 두 박스 사이, 포트 위쪽
                left = l["a"] if x1 < x2 else l["b"]
                gx = pos[left][0] + W[left] + GAP / 2
                mids.append(place([(gx, min(y1, y2) + 12)], ifshort(l["a_po"]), "pol"))
            else:                   # 상하 배치(core) → 링크 오른쪽
                cxm = pos[l["a"]][0] + W[l["a"]] / 2
                mids.append(place([(cxm + 62, (y1 + y2 + NH) / 2)], f'{ifshort(l["a_po"])} (Et1+Et6)', "pol"))
    for i, l in enumerate(model["links"]):   # (토글) L3 링크 IP — 자리가 없으면 생략
        if l["kind"] == "l3":
            _, _, ax, ay, _ = pp[(i, "a")]
            _, _, bx, by_, _ = pp[(i, "b")]
            mids.append(place([((ax + bx) / 2, (ay + by_) / 2)], l["a_ip"] or "", "ipl", force=False))

    # VXLAN 터널 오버레이 (기본 숨김)
    tun = []
    vt = model["vteps"]

    def vpt(ip):
        ns = vt[ip]
        xs = [pos[n][0] + W[n] / 2 for n in ns]
        return sum(xs) / len(xs), min(pos[n][1] for n in ns) - PORT_H - 4
    for a, b in model["tunnels"]:
        (x1, y1), (x2, y2) = vpt(a), vpt(b)
        inter = model["nodes"][vt[a][0]]["dc"] != model["nodes"][vt[b][0]]["dc"]
        cy = -70 if inter else min(y1, y2) - 120 - abs(x2 - x1) * 0.05
        tun.append(f'<path class="tun{" inter" if inter else ""}" d="M{x1:.1f},{y1:.1f} Q{(x1 + x2) / 2:.1f},{cy:.1f} {x2:.1f},{y2:.1f}">'
                   f'<title>VXLAN 터널 {a} ({"/".join(vt[a])}) ↔ {b} ({"/".join(vt[b])})</title></path>')

    nds = []
    for n in model["nodes"].values():
        x, y = pos[n["name"]]
        w = W[n["name"]]
        bad = n["status"] != "success" or n["bgp_down"]
        sub = n["lo0"] or n["mgmt_ip"] or ""
        line3 = (f'AS {n["asn"]} · BGP {n["bgp_est"]}/{n["bgp_total"]}' if n["bgp_total"] else (n["mgmt_ip"] or ""))
        role = {"brdr": "BORDER LEAF"}.get(n["role"], n["role"].upper())
        if n["lo1"]:
            role += f' · VTEP {n["lo1"].split("/")[0]}'
        nds.append(f'<g class="nd r-{n["role"]}{" bad" if bad else ""}" data-n="{esc(n["name"])}" tabindex="0">'
                   f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{NH}" rx="9"/>'
                   f'<text class="t1" x="{x + 10:.0f}" y="{y + 20:.0f}">{esc(n["name"])}</text>'
                   f'<text class="t2" x="{x + 10:.0f}" y="{y + 37:.0f}">{esc(sub)}</text>'
                   f'<text class="t2" x="{x + 10:.0f}" y="{y + 53:.0f}">{esc(line3)}</text>'
                   f'<text class="t3" x="{x + 10:.0f}" y="{y + 69:.0f}">{esc(role)}</text></g>')

    zx2 = x_core2 + core_w + 100 - 10
    zones = [
        f'<rect class="zone" x="-14" y="6" width="{dc_w + 28}" height="{height - 12}" rx="14"/>',
        f'<rect class="zone dcizone" x="{x_core1 - 40}" y="6" width="{x_core2 + core_w - x_core1 + 80}" height="{height - 12}" rx="14"/>',
        f'<rect class="zone" x="{zx2 - 4}" y="6" width="{dc_w + 28}" height="{height - 12}" rx="14"/>',
        f'<text class="dcl" x="{dc_w / 2:.0f}" y="{height - 14:.0f}" text-anchor="middle">DC1</text>',
        f'<text class="dcl dcit" x="{(x_core1 + x_core2 + core_w) / 2:.0f}" y="{height - 14:.0f}" text-anchor="middle">DCI · CORE</text>',
        f'<text class="dcl" x="{zx2 + 10 + dc_w / 2:.0f}" y="{height - 14:.0f}" text-anchor="middle">DC2</text>',
    ]
    svg = "\n".join(zones + ['<g id="links">'] + lines + ["</g>", '<g id="tunnels">'] + tun + ["</g>"]
                    + ['<g id="nodes">'] + nds + ["</g>", '<g id="ifl">'] + portg + ["</g>", '<g id="mids">'] + mids + ["</g>"])

    nodes = sorted(model["nodes"].values(), key=lambda n: (n["dc"], TIER[n["role"]], n["name"]))
    l3 = [l for l in model["links"] if l["kind"] in ("l3", "dci")]
    dci = [l for l in model["links"] if l["kind"] == "dci"]
    up = sum(1 for l in l3 if l["bgp"] == "up")
    bgp_e = sum(n["bgp_est"] for n in nodes); bgp_t = sum(n["bgp_total"] for n in nodes)
    ok = sum(1 for n in nodes if n["status"] == "success")
    oper_up = sum(1 for l in model["links"] if l["oper"] == "up")

    def ifcell(node, ifn, ip, po, st):
        return (f'<b>{esc(node)}</b> {esc(ifshort(ifn))}' + (f' <span class="po">{esc(ifshort(po))}</span>' if po else "")
                + (f'<br><span class="m">{esc(ip)}</span>' if ip else ""))
    rows = "".join(
        f'<tr data-n="{esc(n["name"])}"><td><b>{esc(n["name"])}</b></td><td>{esc(n["role"])}</td><td>{esc(n["mgmt_ip"] or "-")}</td>'
        f'<td>{esc(str(n["eos"]))}</td><td>{esc(str(n["asn"] or "-"))}</td>'
        f'<td>{esc(n["lo0"] or "-")}</td><td>{esc(n["lo1"] or "-")}</td>'
        f'<td class="{"bad" if n["bgp_down"] else ""}">{n["bgp_est"]}/{n["bgp_total"]}</td>'
        f'<td>{esc(n["mlag"] or "-")}</td><td>{esc(", ".join(n["remote_vteps"]) or "-")}</td></tr>' for n in nodes)
    lrows = "".join(
        f'<tr><td>{ifcell(l["a"], l["a_if"], l["a_ip"], l["a_po"], l["a_st"])}</td>'
        f'<td>{ifcell(l["b"], l["b_if"], l["b_ip"], l["b_po"], l["b_st"])}</td>'
        f'<td>{esc(K[l["kind"]])}</td><td class="s-{l["oper"]}">{l["oper"]}</td><td class="s-{l["bgp"]}">{l["bgp"]}</td></tr>'
        for l in sorted(model["links"], key=lambda l: (["dci", "l3", "peer", "l2"].index(l["kind"]), l["a"], l["a_if"])))
    # DCI 상세: core↔core + border↔core 언더레이
    dci_rows = "".join(
        f'<tr><td>{ifcell(l["a"], l["a_if"], l["a_ip"], l["a_po"], l["a_st"])}</td>'
        f'<td>{ifcell(l["b"], l["b_if"], l["b_ip"], l["b_po"], l["b_st"])}</td><td>{esc(K[l["kind"]])}</td>'
        f'<td class="s-{l["oper"]}">{l["oper"]}</td><td class="s-{l["bgp"]}">{l["bgp"]}</td></tr>'
        for l in sorted([l for l in model["links"] if "core" in l["a"] + l["b"]],
                        key=lambda l: (["dci", "l3", "peer"].index(l["kind"]) if l["kind"] in ("dci", "l3", "peer") else 9, l["a"], l["a_if"])))
    trows = "".join(
        f'<tr><td>{esc(a)}</td><td>{esc(" / ".join(vt[a]))}</td><td>{esc(b)}</td><td>{esc(" / ".join(vt[b]))}</td>'
        f'<td>{"DC 간" if model["nodes"][vt[a][0]]["dc"] != model["nodes"][vt[b][0]]["dc"] else "DC 내부"}</td></tr>'
        for a, b in model["tunnels"])
    detail = {}
    for n in model["nodes"].values():
        ifs = []
        for l in model["links"]:
            for me, mif, mip, mpo, mst, ot, oif, oip in (
                    ("a", l["a_if"], l["a_ip"], l["a_po"], l["a_st"], l["b"], l["b_if"], l["b_ip"]),
                    ("b", l["b_if"], l["b_ip"], l["b_po"], l["b_st"], l["a"], l["a_if"], l["a_ip"])):
                if l[me] == n["name"]:
                    ifs.append([ifshort(mif), mip or "", ifshort(mpo) if mpo else "", mst or "-",
                                f"{ot} {ifshort(oif)}", oip or "", K[l["kind"]], l["bgp"]])
        ifs.sort(key=lambda r: (len(r[0]), r[0]))
        detail[n["name"]] = {k: n[k] for k in ("name", "role", "mgmt_ip", "model", "eos", "asn", "router_id",
                                                "lo0", "lo1", "bgp_est", "bgp_total", "bgp_down", "mlag", "remote_vteps")}
        detail[n["name"]]["ifs"] = ifs
    return TEMPLATE.format(
        collected=esc(model["collected_at"]), width=f"{width:.0f}", height=f"{height:.0f}", svg=svg,
        n_dev=len(nodes), n_ok=ok, n_links=len(model["links"]), oper_up=oper_up, l3_up=up, l3_total=len(l3),
        dci_up=sum(1 for l in dci if l["bgp"] == "up"), dci_total=len(dci), n_tun=len(model["tunnels"]),
        bgp_e=bgp_e, bgp_t=bgp_t, rows=rows, lrows=lrows, dci_rows=dci_rows, trows=trows,
        detail=json.dumps(detail, ensure_ascii=False).replace("</", "<\\/"))


TIER = {"core": 0, "spine": 1, "leaf": 2, "brdr": 2, "host": 3, "other": 3}

TEMPLATE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ATD Fabric Topology</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+KR:wght@400;600;700&display=swap">
<style>
/* layout: DC1 | DCI core zone (2x2: core1 위, core2 아래) | DC2 ; rows spine / leaf+border / host */
:root{{--bg:#f4f5f7;--card:#fff;--ink:#1c1d1f;--mute:#5d6470;--line:#d5d9e0;--zone:#eceef2;--up:#1f8a4c;--down:#c8372d;--l2:#8e8f88;
--dci:#6b3fd4;--dcizone:#efe9fc;--tun:#d9822b;--pill:#ffffff;--spine:#e6effb;--leaf:#e8f5ec;--brdr:#fcf1de;--core:#ece5fb;--host:#f0f0ec;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#141413;--card:#1e1e1c;--ink:#ecebe6;--mute:#a3a29b;--line:#3a3a36;--zone:#1a1a19;
--up:#47c27c;--down:#ff6b5e;--l2:#7a7a72;--dci:#a88cf2;--dcizone:#211b31;--tun:#f0a050;--pill:#262624;--spine:#1c283a;--leaf:#1b3024;--brdr:#382c18;--core:#2a2240;--host:#252523;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#141413;--card:#1e1e1c;--ink:#ecebe6;--mute:#a3a29b;--line:#3a3a36;--zone:#1a1a19;--up:#47c27c;--down:#ff6b5e;--l2:#7a7a72;
--dci:#a88cf2;--dcizone:#211b31;--tun:#f0a050;--pill:#262624;--spine:#1c283a;--leaf:#1b3024;--brdr:#382c18;--core:#2a2240;--host:#252523;color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "IBM Plex Sans KR",system-ui,"Noto Sans KR",sans-serif}}
svg text,table,.mono{{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace}}
main{{max-width:1600px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 40px}}
h1{{font-size:22px;margin:0 0 4px;text-wrap:balance}} .sub{{color:var(--mute);margin:0 0 14px}}
h2{{font-size:15px;margin:2px 4px 10px}}
.kpis{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:14px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 14px;min-width:130px}}
.kpi b{{display:block;font-size:19px;font-variant-numeric:tabular-nums}} .kpi span{{color:var(--mute);font-size:12px}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:16px}}
.bar{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 4px 10px}}
.bar label{{display:flex;gap:6px;align-items:center;font-size:13px;cursor:pointer;padding:4px 10px;border:1px solid var(--line);border-radius:999px}}
.bar button{{font:inherit;font-size:13px;padding:4px 12px;border:1px solid var(--line);border-radius:999px;background:var(--card);color:var(--ink);cursor:pointer}}
.bar button:focus-visible,.bar label:focus-within,.nd:focus-visible{{outline:2px solid var(--dci);outline-offset:2px}}
.bar .sp{{flex:1}} .hint{{color:var(--mute);font-size:12px}}
.scroll{{overflow:auto}} #topo{{display:block}} #topo.fit{{width:100%;height:auto}}
.zone{{fill:var(--zone)}} .dcizone{{fill:var(--dcizone)}}
.dcl{{font-weight:700;font-size:13px;fill:var(--mute);letter-spacing:.06em}} .dcit{{fill:var(--dci)}}
.lk{{stroke-width:2}} .lk.up{{stroke:var(--up)}} .lk.down{{stroke:var(--down);stroke-dasharray:6 4}} .lk.nobgp{{stroke:var(--mute)}}
.lk.l2,.lk.peer{{stroke:var(--l2);stroke-dasharray:4 3}} .lk.k-dci{{stroke-width:5}} .lk.k-dci.up{{stroke:var(--dci)}}
.lk:hover{{stroke-width:5}} .lk.k-dci:hover{{stroke-width:8}}
.tun{{fill:none;stroke:var(--tun);stroke-width:2;stroke-dasharray:7 5;opacity:.9}} .tun.inter{{stroke-width:3}}
#topo:not(.show-tun) #tunnels{{display:none}}
#topo:not(.show-ip) .ipl{{display:none}}
.pill rect{{fill:var(--pill);stroke:var(--line);stroke-width:.8}} .pill text{{font-size:9.5px;fill:var(--ink)}}
.port rect{{fill:var(--card);stroke:var(--l2);stroke-width:1.4}} .port text{{font-size:10px;font-weight:600;fill:var(--ink)}}
.port.up rect{{stroke:var(--up)}} .port.down rect{{stroke:var(--down);fill:var(--down)}} .port.down text{{fill:#fff}}
.port.k-dci rect{{stroke:var(--dci);fill:var(--dci)}} .port.k-dci text{{fill:#fff}} .port.nobgp rect{{stroke:var(--mute)}}
.dcil rect{{fill:var(--dci);stroke:none}} .dcil text{{fill:#fff;font-size:10.5px;font-weight:600}}
.dcil.s-down rect{{fill:var(--down)}}
.pol rect{{stroke:var(--l2);stroke-dasharray:2 2}} .pol text{{fill:var(--mute);font-weight:600}}
.ipl text{{fill:var(--mute)}}
.nd{{cursor:pointer}} .nd rect{{stroke:var(--line);stroke-width:1.2}} .nd.bad rect{{stroke:var(--down);stroke-width:2.5}}
.nd.sel rect{{stroke:var(--ink);stroke-width:2.5}}
.r-spine rect{{fill:var(--spine)}} .r-leaf rect{{fill:var(--leaf)}} .r-brdr rect{{fill:var(--brdr)}} .r-core rect{{fill:var(--core)}} .r-host rect,.r-other rect{{fill:var(--host)}}
.r-core rect{{stroke:var(--dci);stroke-width:1.6}}
.nd text{{fill:var(--ink)}} .t1{{font-weight:650;font-size:13px}} .t2{{font-size:11px;fill:var(--mute)!important;font-variant-numeric:tabular-nums}}
.t3{{font-size:9.5px;letter-spacing:.04em;fill:var(--mute)!important}}
#topo.focus .lk:not(.hi),#topo.focus .pill:not(.hi),#topo.focus .port:not(.hi),#topo.focus .nd:not(.hi){{opacity:.15}}
.legend{{display:flex;flex-wrap:wrap;gap:14px;color:var(--mute);font-size:12px;margin:8px 4px 0}}
.legend i{{display:inline-block;width:26px;height:0;border-top:3px solid;vertical-align:middle;margin-right:6px}}
table{{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);white-space:nowrap;vertical-align:top}} th{{color:var(--mute);font-weight:600}}
td.bad,.s-down{{color:var(--down);font-weight:600}} .s-up{{color:var(--up)}} .m{{color:var(--mute)}}
.po{{font-size:10.5px;padding:0 5px;border:1px dashed var(--l2);border-radius:4px;color:var(--mute)}}
#detail[hidden]{{display:none}} #detail .facts{{display:flex;flex-wrap:wrap;gap:6px 18px;margin:0 4px 10px;font-size:12.5px}}
#detail .facts span b{{color:var(--mute);font-weight:600;margin-right:6px}}
.grid2{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:16px}}
@media (prefers-reduced-motion:no-preference){{.lk,.pill,.nd{{transition:opacity .15s}}}}
</style></head><body><main>
<h1>ATD Fabric Topology</h1>
<p class="sub">EOS MCP Server(읽기 전용)로 수집 · {collected} · LLDP 물리 연결 + 인터페이스 상태 + BGP + VXLAN</p>
<div class="kpis">
<div class="kpi"><b>{n_ok}/{n_dev}</b><span>응답 장비</span></div>
<div class="kpi"><b>{oper_up}/{n_links}</b><span>링크 up (LLDP)</span></div>
<div class="kpi"><b>{l3_up}/{l3_total}</b><span>L3 링크 BGP Established</span></div>
<div class="kpi"><b>{dci_up}/{dci_total}</b><span>DCI 링크 eBGP</span></div>
<div class="kpi"><b>{bgp_e}/{bgp_t}</b><span>BGP 세션 (장비 기준)</span></div>
<div class="kpi"><b>{n_tun}</b><span>VXLAN 터널 (VTEP 쌍)</span></div>
</div>
<div class="panel">
<div class="bar">
<label><input type="checkbox" id="o-ip"> L3 링크 IP</label>
<label><input type="checkbox" id="o-tun"> VXLAN 터널</label>
<span class="sp"></span><span class="hint">장비를 클릭하면 연결만 강조하고 아래에 상세가 열립니다</span>
<button type="button" id="z-fit">화면 맞춤</button><button type="button" id="z-100">원본 크기</button>
</div>
<div class="scroll" id="wrap"><svg id="topo" viewBox="-16 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="fabric topology">{svg}</svg></div>
<div class="legend"><span><i style="border-color:var(--up)"></i>L3 P2P · BGP Established</span>
<span><i style="border-color:var(--dci);border-top-width:5px"></i>DCI (core↔core)</span>
<span><i style="border-color:var(--l2);border-top-style:dashed"></i>L2 · MLAG peer · Port-Channel 멤버</span>
<span><i style="border-color:var(--down);border-top-style:dashed"></i>링크 down / BGP down</span>
<span><i style="border-color:var(--tun);border-top-style:dashed"></i>VXLAN 터널</span>
<span class="mono">Et=Ethernet · Po=Port-Channel</span></div>
</div>
<div class="panel" id="detail" hidden><h2 id="d-title"></h2><div class="facts" id="d-facts"></div>
<div class="scroll"><table><thead><tr><th>인터페이스</th><th>IP</th><th>Po</th><th>상태</th><th>상대 장비</th><th>상대 IP</th><th>종류</th><th>BGP</th></tr></thead><tbody id="d-ifs"></tbody></table></div></div>
<div class="grid2">
<div class="panel scroll"><h2>DCI · core 연결</h2><table><thead><tr><th>A</th><th>B</th><th>종류</th><th>링크</th><th>BGP</th></tr></thead><tbody>{dci_rows}</tbody></table></div>
<div class="panel scroll"><h2>VXLAN 터널 (show vxlan vtep)</h2><table><thead><tr><th>VTEP</th><th>장비</th><th>VTEP</th><th>장비</th><th>구분</th></tr></thead><tbody>{trows}</tbody></table>
<p class="hint" style="margin:8px 4px 0">DC 간 터널은 border leaf 사이 하나뿐 — EVPN Gateway가 경로를 재발신하므로 leaf는 원격 DC VTEP과 직접 터널을 맺지 않습니다.</p></div>
</div>
<div class="panel scroll"><h2>장비 요약</h2><table><thead><tr><th>장비</th><th>역할</th><th>Mgmt</th><th>EOS</th><th>ASN</th>
<th>Loopback0</th><th>Loopback1 (VTEP)</th><th>BGP Est.</th><th>MLAG</th><th>Remote VTEPs</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="panel scroll"><h2>링크 목록 (LLDP)</h2><table><thead><tr><th>A</th><th>B</th><th>종류</th><th>링크</th><th>BGP</th></tr></thead>
<tbody>{lrows}</tbody></table></div>
</main>
<script>
const D={detail};
const svg=document.getElementById('topo');
const tog=(id,cls)=>{{const c=document.getElementById(id);const f=()=>svg.classList.toggle(cls,c.checked);c.addEventListener('change',f);f();}};
tog('o-ip','show-ip');tog('o-tun','show-tun');
document.getElementById('z-fit').onclick=()=>svg.classList.add('fit');
document.getElementById('z-100').onclick=()=>svg.classList.remove('fit');
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
let cur=null;
function select(name){{
  svg.querySelectorAll('.hi,.sel').forEach(e=>e.classList.remove('hi','sel'));
  const det=document.getElementById('detail');
  if(!name||name===cur){{cur=null;svg.classList.remove('focus');det.hidden=true;return;}}
  cur=name;svg.classList.add('focus');
  const nb=new Set([name]);
  svg.querySelectorAll('.lk,.port').forEach(e=>{{if(e.dataset.a===name||e.dataset.b===name){{e.classList.add('hi');nb.add(e.dataset.a);nb.add(e.dataset.b);}}}});
  svg.querySelectorAll('.nd').forEach(e=>{{if(nb.has(e.dataset.n))e.classList.add('hi');if(e.dataset.n===name)e.classList.add('sel');}});
  const d=D[name];
  document.getElementById('d-title').textContent=d.name+' · '+d.role;
  const f=[['Mgmt',d.mgmt_ip],['모델',d.model],['EOS',d.eos],['ASN',d.asn],['Router-ID',d.router_id],['Loopback0',d.lo0],['VTEP',d.lo1],
    ['BGP',d.bgp_total?d.bgp_est+'/'+d.bgp_total+' Established':''],['BGP down',(d.bgp_down||[]).join(', ')],['MLAG',d.mlag],['Remote VTEP',(d.remote_vteps||[]).join(', ')]];
  document.getElementById('d-facts').innerHTML=f.filter(x=>x[1]).map(x=>'<span><b>'+esc(x[0])+'</b>'+esc(x[1])+'</span>').join('');
  document.getElementById('d-ifs').innerHTML=d.ifs.map(r=>'<tr><td><b>'+esc(r[0])+'</b></td><td>'+esc(r[1]||'-')+'</td><td>'+esc(r[2]||'-')+
    '</td><td class="'+(r[3]==='connected'||r[3]==='-'?'s-up':'s-down')+'">'+esc(r[3])+'</td><td>'+esc(r[4])+'</td><td>'+esc(r[5]||'-')+'</td><td>'+esc(r[6])+
    '</td><td class="s-'+esc(r[7])+'">'+esc(r[7])+'</td></tr>').join('');
  det.hidden=false;
}}
svg.querySelectorAll('.nd').forEach(g=>{{g.addEventListener('click',()=>select(g.dataset.n));
  g.addEventListener('keydown',e=>{{if(e.key==='Enter'||e.key===' '){{e.preventDefault();select(g.dataset.n);}}}});}});
svg.addEventListener('click',e=>{{if(e.target===svg)select(null);}});
document.querySelectorAll('tr[data-n]').forEach(t=>t.addEventListener('click',()=>{{select(t.dataset.n);svg.scrollIntoView({{block:'nearest'}});}}));
</script>
</body></html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--targets", nargs="+", default=["dc1", "dc2"], help="MCP 인벤토리 그룹/장비 이름 (기본: dc1 dc2)")
    ap.add_argument("--out", default=os.path.join(HERE, "topology.html"))
    ap.add_argument("--json", default=os.path.join(HERE, "topology.json"), help="수집 원본 저장 경로")
    ap.add_argument("--from-json", help="이미 수집한 JSON으로 HTML만 다시 생성")
    a = ap.parse_args()
    if a.from_json:
        data = json.load(open(a.from_json))
    else:
        data = collect(a.targets)
        json.dump(data, open(a.json, "w"), indent=1)
    model = build_model(data)
    open(a.out, "w").write(render_html(model))
    bad = [n["name"] for n in model["nodes"].values() if n["bgp_down"] or n["status"] != "success"]
    print(f"{len(model['nodes'])} devices, {len(model['links'])} links -> {a.out}")
    if bad:
        print("주의(BGP 다운 또는 응답 실패): " + ", ".join(sorted(bad)))


if __name__ == "__main__":
    main()
