#!/usr/bin/env python3
"""ANTA PSIRT(Security Advisory) 점검 래퍼.

sites/dc{n}/inventory.yml(Ansible)에서 *활성화된* EOS 장비만 골라 ANTA inventory를 만들고,
`anta psirt md-report` / `anta psirt csv`를 실행한 뒤 Affected/Inconclusive 요약을 출력한다.

- Lab 단계에 따라 inventory.yml에서 주석 처리/해제되는 장비(Border Leaf 등)를 그대로 따라간다.
- CVP 그룹은 제외한다 (EOS 장비가 아님).
- 장비 정보는 읽기만 하며(show 명령), 설정은 변경하지 않는다.

사용법:
    python3 psirt/run_psirt.py --dc all        # dc1 + dc2
    python3 psirt/run_psirt.py --dc dc1

자격 증명:
    ANTA_USERNAME (기본: arista)
    ANTA_PASSWORD → LABPASSPHRASE → code-server config.yaml의 password 순으로 찾는다.
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CODE_SERVER_CONFIG = Path.home() / ".config/code-server/config.yaml"
EXCLUDED_GROUPS = {"CVP"}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def collect_hosts(group: dict, excluded: bool = False, out: dict | None = None) -> dict:
    """Ansible YAML inventory 그룹 트리를 재귀로 돌며 {hostname: ansible_host}를 모은다."""
    out = {} if out is None else out
    if not isinstance(group, dict):
        return out
    for name, hostvars in (group.get("hosts") or {}).items():
        if excluded:
            continue
        host = (hostvars or {}).get("ansible_host") or name  # core1/2는 ansible_host 없이 이름으로 해석됨
        out.setdefault(name, host)
    for child_name, child in (group.get("children") or {}).items():
        collect_hosts(child, excluded or child_name in EXCLUDED_GROUPS, out)
    return out


def build_inventory(dc: str, out_file: Path) -> int:
    data = yaml.safe_load((REPO / "sites" / dc / "inventory.yml").read_text())
    hosts = collect_hosts(data[dc])
    inv = {
        "anta_inventory": {
            "hosts": [{"name": n, "host": h, "tags": [dc]} for n, h in sorted(hosts.items())]
        }
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(yaml.safe_dump(inv, sort_keys=False))
    return len(hosts)


def find_password() -> str | None:
    for var in ("ANTA_PASSWORD", "LABPASSPHRASE"):
        if os.environ.get(var):
            return os.environ[var]
    if CODE_SERVER_CONFIG.exists():
        for line in CODE_SERVER_CONFIG.read_text().splitlines():
            if line.strip().startswith("password:"):
                return line.split(":", 1)[1].strip()
    return None


def run_anta(inventory: Path, subcmd: list[str], env: dict) -> None:
    cmd = ["anta", "psirt", "-i", str(inventory), "--insecure", "--ignore-status", *subcmd]
    print("$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, env=env, check=True)


def summarize(dc: str, csv_file: Path) -> list[dict]:
    """advisory별로 장비 결과를 묶어 Affected/Inconclusive/Error만 반환한다."""
    per_sa: dict[str, dict] = {}
    for row in csv.DictReader(csv_file.open()):
        sa = per_sa.setdefault(
            row["Advisory ID"],
            {"severity": row["Advisory Severity"], "title": row["Advisory Title"],
             "url": row["Advisory URL"], "devices": {}},
        )
        sa["devices"][row["Device"]] = row["Advisory Result"]

    findings = []
    for sa_id, sa in per_sa.items():
        by_result = defaultdict(list)
        for dev, res in sa["devices"].items():
            by_result[res].append(dev)
        for res in ("affected", "inconclusive", "error"):
            if by_result[res]:
                findings.append({"dc": dc, "sa": sa_id, "severity": sa["severity"], "result": res,
                                 "devices": sorted(by_result[res]), "total": len(sa["devices"]),
                                 "url": sa["url"]})
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9), f["sa"]))
    print(f"\n[{dc}] advisories checked: {len(per_sa)}, devices: "
          f"{len({d for sa in per_sa.values() for d in sa['devices']})}")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dc", choices=["dc1", "dc2", "all"], default="all")
    args = ap.parse_args()

    if not shutil.which("anta"):
        print("anta CLI not found. Install with: pip install 'anta[cli]==1.11.0'", file=sys.stderr)
        return 2
    password = find_password()
    if not password:
        print("No password: set ANTA_PASSWORD or LABPASSPHRASE.", file=sys.stderr)
        return 2
    env = {**os.environ, "ANTA_USERNAME": os.environ.get("ANTA_USERNAME", "arista"),
           "ANTA_PASSWORD": password}

    findings = []
    for dc in (["dc1", "dc2"] if args.dc == "all" else [args.dc]):
        report_dir = REPO / "sites" / dc / "anta" / "reports"
        inventory = REPO / "sites" / dc / "anta" / "psirt_inventory.yml"
        n = build_inventory(dc, inventory)
        print(f"\n===== {dc}: {n} EOS devices -> {inventory.relative_to(REPO)}")
        md = report_dir / "psirt_report.md"
        csvf = report_dir / "psirt_report.csv"
        run_anta(inventory, ["md-report", "--md-output", str(md)], env)
        run_anta(inventory, ["csv", "--csv-output", str(csvf)], env)
        findings += summarize(dc, csvf)
        print(f"  reports: {md.relative_to(REPO)}, {csvf.relative_to(REPO)}")

    print("\n===== PSIRT summary (affected / inconclusive / error only)")
    if not findings:
        print("No affected or inconclusive advisories.")
    for f in findings:
        devs = "all" if len(f["devices"]) == f["total"] else ", ".join(f["devices"])
        print(f"  {f['dc']}  {f['sa']:7} {f['severity']:9} {f['result'].upper():13} "
              f"{len(f['devices'])}/{f['total']} ({devs})")
        print(f"        {f['url']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
