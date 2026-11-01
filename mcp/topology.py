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
SHOW_CMDS = ["show lldp neighbors", "show ip interface brief", "show bgp summary", "show mlag", "show vxlan vtep"]


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


def build_model(data):
    devs = data["devices"]
    nodes, ip_owner = {}, {}
    for name, d in devs.items():
        s, f = d.get("show", {}), d.get("facts", {})
        intfs = s.get("show ip interface brief", {}).get("interfaces", {})
        ips = {}
        for ifn, i in intfs.items():
            a = (i.get("interfaceAddress") or {}).get("ipAddr") or {}
            if a.get("address") and a.get("address") != "0.0.0.0":
                ips[ifn] = f'{a["address"]}/{a["maskLen"]}'
                ip_owner[a["address"]] = (name, ifn)
        bgp = s.get("show bgp summary", {}).get("vrfs", {}).get("default", {})
        peers = bgp.get("peers", {})
        est = sum(1 for p in peers.values() if p.get("peerState") == "Established")
        mlag = s.get("show mlag", {})
        vtep = s.get("show vxlan vtep", {})
        remote_vteps = sorted({v for i in (vtep.get("interfaces") or {}).values() for v in i.get("vteps", [])})
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
            "mlag": (f'{mlag["state"]} ({mlag.get("domainId")})' if mlag.get("state") not in (None, "disabled") else None), "remote_vteps": remote_vteps, "ips": ips,
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
            a_ip, b_ip = nodes[name]["ips"].get(n["port"]), nodes[peer]["ips"].get(n["neighborPort"])
            kind, state = "l2", "n/a"
            if a_ip and b_ip:
                kind = "l3"
                pa, pb = a_ip.split("/")[0], b_ip.split("/")[0]
                sa = nodes[name]["peers"].get(pb, {}).get("peerState")
                sb = nodes[peer]["peers"].get(pa, {}).get("peerState")
                state = "up" if "Established" in (sa, sb) else ("down" if (sa or sb) else "no-bgp")
            if {role_of(name), role_of(peer)} == {"core"} and nodes[name]["dc"] != nodes[peer]["dc"]:
                kind = "dci"
            elif role_of(name) == role_of(peer) and nodes[name]["dc"] == nodes[peer]["dc"] and not (a_ip and b_ip):
                kind = "peer"  # MLAG peer-link / core port-channel
            links.append({"a": name, "a_if": n["port"], "a_ip": a_ip, "b": peer, "b_if": n["neighborPort"],
                          "b_ip": b_ip, "kind": kind, "bgp": state})
    for n in nodes.values():
        n.pop("peers")
    return {"collected_at": data["collected_at"], "nodes": nodes, "links": links}


# --------------------------------------------------------------------------- layout + HTML
TIER = {"core": 0, "spine": 1, "leaf": 2, "brdr": 2, "host": 3, "other": 3}


def layout(model):
    W, colgap, dcgap = 150, 18, 90
    pos, rows = {}, {}
    for n in model["nodes"].values():
        rows.setdefault((n["dc"], TIER[n["role"]]), []).append(n["name"])
    order = lambda nm: (0 if role_of(nm) != "brdr" else 1, nm)  # leafs first, border leafs on the outer side
    widest = max(len(v) for v in rows.values())
    dc_w = widest * (W + colgap)
    for (dc, tier), names in rows.items():
        names.sort(key=order, reverse=(dc == "dc2"))
        x0 = 0 if dc == "dc1" else dc_w + dcgap
        span = len(names) * (W + colgap) - colgap
        if tier == 0:  # cores sit on the inner side, next to the DCI
            start = x0 + dc_w - span - colgap if dc == "dc1" else x0
        else:
            start = x0 + (dc_w - colgap - span) / 2
        for i, nm in enumerate(names):
            pos[nm] = (start + i * (W + colgap), 40 + tier * 170)
    return pos, W, 2 * dc_w + dcgap, 40 + 4 * 170


def render_html(model):
    pos, W, width, height = layout(model)
    H = 92
    esc = html.escape
    svg = []
    for l in model["links"]:
        (x1, y1), (x2, y2) = pos[l["a"]], pos[l["b"]]
        ax, bx = x1 + W / 2, x2 + W / 2
        ay, by = (y1 + H, y2) if y1 < y2 else ((y1, y2 + H) if y1 > y2 else (y1 + H / 2, y2 + H / 2))
        if y1 == y2:
            ax, bx = (x1 + W, x2) if x1 < x2 else (x1, x2 + W)
        cls = {"up": "up", "down": "down", "no-bgp": "nobgp"}.get(l["bgp"], l["kind"])
        tip = f'{l["a"]} {l["a_if"]} {l["a_ip"] or ""} ↔ {l["b"]} {l["b_if"]} {l["b_ip"] or ""} · ' \
              f'{ {"l3": "L3 P2P", "l2": "L2/Port-Channel member", "dci": "DCI", "peer": "MLAG/peer link"}[l["kind"]] }' \
              + (f' · BGP {l["bgp"]}' if l["kind"] in ("l3", "dci") else "")
        svg.append(f'<line class="lk {cls} k-{l["kind"]}" x1="{ax:.0f}" y1="{ay:.0f}" x2="{bx:.0f}" y2="{by:.0f}">'
                   f'<title>{esc(tip)}</title></line>')
    for n in model["nodes"].values():
        x, y = pos[n["name"]]
        bad = n["status"] != "success" or n["bgp_down"]
        sub = n["lo0"] or n["mgmt_ip"] or ""
        line3 = f'AS {n["asn"]} · BGP {n["bgp_est"]}/{n["bgp_total"]}' if n["bgp_total"] else (n["mlag"] and f'MLAG {n["mlag"]}' or n["mgmt_ip"] or "")
        tip = "\n".join(f"{k}: {v}" for k, v in [("mgmt", n["mgmt_ip"]), ("model", n["model"]), ("EOS", n["eos"]),
                        ("ASN", n["asn"]), ("router-id", n["router_id"]), ("Loopback0", n["lo0"]), ("Loopback1 (VTEP)", n["lo1"]),
                        ("BGP", f'{n["bgp_est"]}/{n["bgp_total"]} Established'), ("MLAG", n["mlag"]),
                        ("remote VTEPs", ", ".join(n["remote_vteps"]))] if v)
        svg.append(f'<g class="nd r-{n["role"]}{" bad" if bad else ""}" data-n="{esc(n["name"])}"><title>{esc(tip)}</title>'
                   f'<rect x="{x:.0f}" y="{y:.0f}" width="{W}" height="{H}" rx="10"/>'
                   f'<text class="t1" x="{x + 12:.0f}" y="{y + 24:.0f}">{esc(n["name"])}</text>'
                   f'<text class="t2" x="{x + 12:.0f}" y="{y + 44:.0f}">{esc(sub)}</text>'
                   f'<text class="t2" x="{x + 12:.0f}" y="{y + 62:.0f}">{esc(line3)}</text>'
                   f'<text class="t3" x="{x + 12:.0f}" y="{y + 80:.0f}">{esc(n["role"].upper())} · {esc(str(n["eos"]))}</text></g>')
    for i, dc in enumerate(("DC1", "DC2")):
        svg.insert(0, f'<text class="dcl" x="{(width / 4) + i * width / 2:.0f}" y="22" text-anchor="middle">{dc}</text>')

    nodes = sorted(model["nodes"].values(), key=lambda n: (n["dc"], TIER[n["role"]], n["name"]))
    l3 = [l for l in model["links"] if l["kind"] in ("l3", "dci")]
    up = sum(1 for l in l3 if l["bgp"] == "up")
    bgp_e = sum(n["bgp_est"] for n in nodes); bgp_t = sum(n["bgp_total"] for n in nodes)
    ok = sum(1 for n in nodes if n["status"] == "success")
    rows = "".join(
        f'<tr><td><b>{esc(n["name"])}</b></td><td>{esc(n["role"])}</td><td>{esc(n["mgmt_ip"] or "-")}</td>'
        f'<td>{esc(str(n["model"]))}</td><td>{esc(str(n["eos"]))}</td><td>{esc(str(n["asn"] or "-"))}</td>'
        f'<td>{esc(n["lo0"] or "-")}</td><td>{esc(n["lo1"] or "-")}</td>'
        f'<td class="{"bad" if n["bgp_down"] else ""}">{n["bgp_est"]}/{n["bgp_total"]}</td>'
        f'<td>{esc(n["mlag"] or "-")}</td><td>{esc(", ".join(n["remote_vteps"]) or "-")}</td></tr>' for n in nodes)
    lrows = "".join(
        f'<tr><td>{esc(l["a"])} {esc(l["a_if"])}</td><td>{esc(l["a_ip"] or "-")}</td><td>{esc(l["b"])} {esc(l["b_if"])}</td>'
        f'<td>{esc(l["b_ip"] or "-")}</td><td>{l["kind"].upper()}</td><td class="s-{l["bgp"]}">{l["bgp"]}</td></tr>'
        for l in sorted(model["links"], key=lambda l: (l["kind"], l["a"], l["a_if"])))
    return TEMPLATE.format(
        collected=esc(model["collected_at"]), width=f"{width:.0f}", height=height, svg="\n".join(svg),
        n_dev=len(nodes), n_ok=ok, n_links=len(model["links"]), l3_up=up, l3_total=len(l3),
        bgp_e=bgp_e, bgp_t=bgp_t, rows=rows, lrows=lrows)


TEMPLATE = """<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>ATD Fabric Topology</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+KR:wght@400;600;700&display=swap">
<style>
/* layout: two DC columns mirrored around the DCI; tiers core / spine / leaf+border / host */
:root{{--bg:#f5f6f8;--card:#fff;--ink:#1d1d1b;--mute:#5f6670;--line:#d6dae1;--up:#1f8a4c;--down:#c8372d;--l2:#9a9a94;--dci:#7a4fd0;
--spine:#e8f0fb;--leaf:#eaf6ee;--brdr:#fdf3e2;--core:#f1ecfb;--host:#f2f2ef;color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#151514;--card:#1f1f1d;--ink:#ecebe6;--mute:#a09f98;--line:#3a3a36;
--up:#45c07a;--down:#ff6b5e;--l2:#77776f;--dci:#a98bf0;--spine:#1d2a3d;--leaf:#1c3125;--brdr:#3a2e19;--core:#2a2240;--host:#262624;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#151514;--card:#1f1f1d;--ink:#ecebe6;--mute:#a09f98;--line:#3a3a36;--up:#45c07a;--down:#ff6b5e;--l2:#77776f;
--dci:#a98bf0;--spine:#1d2a3d;--leaf:#1c3125;--brdr:#3a2e19;--core:#2a2240;--host:#262624;color-scheme:dark}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 "IBM Plex Sans KR",system-ui,"Noto Sans KR",sans-serif}}
svg text,table{{font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace}} h1{{text-wrap:balance}}
main{{max-width:1500px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:20px 40px}}
h1{{font-size:22px;margin:0 0 4px}} .sub{{color:var(--mute);margin:0 0 16px}}
.kpis{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:140px}}
.kpi b{{display:block;font-size:20px}} .kpi span{{color:var(--mute);font-size:12px}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:18px}}
.scroll{{overflow-x:auto}} svg{{display:block;min-width:900px;width:100%;height:auto}}
.lk{{stroke-width:2.2}} .lk.up{{stroke:var(--up)}} .lk.down{{stroke:var(--down);stroke-dasharray:6 4}} .lk.nobgp{{stroke:var(--mute)}}
.lk.l2,.lk.peer{{stroke:var(--l2);stroke-dasharray:3 3}} .lk.k-dci{{stroke-width:4}} .lk.k-dci.up{{stroke:var(--dci)}}
.lk:hover{{stroke-width:5}}
.nd rect{{stroke:var(--line);stroke-width:1.2}} .nd.bad rect{{stroke:var(--down);stroke-width:2.5}}
.r-spine rect{{fill:var(--spine)}} .r-leaf rect{{fill:var(--leaf)}} .r-brdr rect{{fill:var(--brdr)}} .r-core rect{{fill:var(--core)}} .r-host rect,.r-other rect{{fill:var(--host)}}
.nd text{{fill:var(--ink)}} .t1{{font-weight:650;font-size:14px}} .t2{{font-size:12px;fill:var(--mute)!important;font-variant-numeric:tabular-nums}}
.t3{{font-size:10.5px;letter-spacing:.04em;fill:var(--mute)!important}} .dcl{{font-weight:700;font-size:15px;fill:var(--mute)}}
.legend{{display:flex;flex-wrap:wrap;gap:16px;color:var(--mute);font-size:12px;margin:6px 4px 0}}
.legend i{{display:inline-block;width:26px;height:0;border-top:3px solid;vertical-align:middle;margin-right:6px}}
table{{border-collapse:collapse;width:100%;font-size:12.5px;font-variant-numeric:tabular-nums}}
th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);white-space:nowrap}} th{{color:var(--mute);font-weight:600}}
td.bad,.s-down{{color:var(--down);font-weight:600}} .s-up{{color:var(--up)}}
h2{{font-size:16px;margin:4px 4px 10px}}
</style></head><body><main>
<h1>ATD Fabric Topology</h1>
<p class="sub">EOS MCP Server(읽기 전용)로 수집 · {collected} · LLDP 기반 물리 연결 + BGP 세션 상태. 장비/링크에 마우스를 올리면 상세 정보가 보입니다.</p>
<div class="kpis">
<div class="kpi"><b>{n_ok}/{n_dev}</b><span>MCP 응답 장비</span></div>
<div class="kpi"><b>{l3_up}/{l3_total}</b><span>L3/DCI 링크 BGP Established</span></div>
<div class="kpi"><b>{bgp_e}/{bgp_t}</b><span>BGP 세션 합계 (장비 기준)</span></div>
<div class="kpi"><b>{n_links}</b><span>LLDP 링크</span></div>
</div>
<div class="panel"><div class="scroll"><svg viewBox="-10 0 {width} {height}" role="img" aria-label="fabric topology">{svg}</svg></div>
<div class="legend"><span><i style="border-color:var(--up)"></i>L3 P2P · BGP Established</span>
<span><i style="border-color:var(--dci);border-top-width:4px"></i>DCI (core↔core)</span>
<span><i style="border-color:var(--down);border-top-style:dashed"></i>BGP 세션 다운</span>
<span><i style="border-color:var(--l2);border-top-style:dotted"></i>L2 / MLAG / Port-Channel member</span></div></div>
<div class="panel scroll"><h2>장비 요약</h2><table><thead><tr><th>장비</th><th>역할</th><th>Mgmt</th><th>모델</th><th>EOS</th><th>ASN</th>
<th>Loopback0</th><th>Loopback1 (VTEP)</th><th>BGP Est.</th><th>MLAG</th><th>Remote VTEPs</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="panel scroll"><h2>링크 목록 (LLDP)</h2><table><thead><tr><th>A</th><th>A IP</th><th>B</th><th>B IP</th><th>종류</th><th>BGP</th></tr></thead>
<tbody>{lrows}</tbody></table></div>
</main></body></html>
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
