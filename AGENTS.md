# AGENTS.md

This file provides guidance to OpenAI Codex CLI (and other AI coding agents that read `AGENTS.md`) when working with code in this repository. It mirrors `CLAUDE.md`, which Claude Code reads for the same purpose — see `lab guide/claude-code-guide.md` and `lab guide/codex-cli-guide.md` for how to install and use each agent against this repo.

## What this repo is

An Arista AVD (Ansible Validated Designs) 6.3.0 proof-of-concept: two independent L3LS EVPN-VXLAN datacenter
fabrics (`dc1`, `dc2`) deployed via Ansible + CloudVision (CVP), stretched over a DCI so the same tenant VLANs
(10/20, subnets `10.10.10.0/24` and `10.20.20.0/24`) exist in both DCs. `s1-*` devices belong to `sites/dc1`,
`s2-*` devices belong to `sites/dc2`. It runs inside Arista's ATD (Arista Test Drive) programmability IDE.

## Environment setup (one-time per lab session)

```bash
python3 -m pip install --upgrade \
  "pyavd==6.3.0" \
  "pyavd-utils==0.0.6" \
  "python-socks[asyncio]>=2.7.2" \
  "anta==1.8.0" \
  "distlib>=0.3.9"
ansible-galaxy collection install arista.avd:==6.3.0
```

Lab credentials must be injected before anything will authenticate against the switches/CVP. `dc1.yml`/`dc2.yml`
ship with `ansible_password: "###########"` as a placeholder — never commit a real password over that
placeholder:

```bash
export LABPASSPHRASE=`cat /home/coder/.config/code-server/config.yaml| grep "password:" | awk '{print $2}'`
sed -i "s/^ansible_password:.*/ansible_password: ${LABPASSPHRASE}/" \
  sites/dc1/group_vars/dc1.yml \
  sites/dc2/group_vars/dc2.yml
```

## Commands (Makefile targets, see `Makefile` for the full list)

All commands run from the repo root and take `-i sites/dc{1,2}/inventory.yml` implicitly via the Makefile.

- `make build_dc1` / `make build_dc2` — run `arista.avd.eos_designs` then `arista.avd.eos_cli_config_gen`
  against the `dc{n}_fabric` inventory group. Regenerates `sites/dc{n}/intended/configs/*.cfg`,
  `sites/dc{n}/intended/structured_configs/*.yml`, and `sites/dc{n}/documentation/**/*.md`. Run this any time
  a `group_vars/dc{n}_*.yml` file changes.
- `make deploy_dc1_cvp` / `make deploy_dc2_cvp` — push the AVD-generated configs to CVP as configlets. DC1
  sets `cv_run_change_control: true` (change control auto-created and executed); DC2 sets it `false`
  (configlets upload but the change control must be created/approved manually in the CVP UI) — this asymmetry
  is intentional, to demonstrate both CVP workflows side by side. The same true/false split exists between
  `deploy_dc1_dci_cvp.yml` (true) and `deploy_dc2_dci_cvp.yml` (false).
- `make deploy_dc1_eapi` / `make deploy_dc2_eapi` — bypass CVP, push AVD-generated configs directly via eAPI,
  then run `arista.avd.anta_runner` (catalogs in `sites/dc{n}/anta/avd_catalogs/`, reports written to
  `sites/dc{n}/anta/reports/`) to validate state.
- `make deploy_dc1_dci` / `make deploy_dc2_dci` (eAPI) and `make deploy_dc1_dci_cvp` / `make deploy_dc2_dci_cvp`
  (CVP) — deploy the s{1,2}-core1/core2 DCI routers from **static** configs in `sites/dc{n}/dci_configs/`.
- `make deploy_dc1_host_cvp` / `make deploy_dc2_host_cvp` — deploy the s{1,2}-host1/host2 dual-homed server
  endpoints from **static** configs in `sites/dc{n}/host_configs/`.
- Initial bring-up order: DCI configs → `build_dc{n}` → `deploy_dc{n}_cvp` → host configs (see README "초기
  설정 빌드 및 배포" for the full numbered sequence).

There is no test suite; correctness is checked by re-running `make build_dc{n}` and diffing the generated
`intended/configs/*.cfg` / `documentation/`, and by the ANTA runs described above.

## Architecture

**Two device populations, two very different config paths:**

1. **AVD-managed devices** (spines, leafs, border-leafs) — inventory group `dc{n}_fabric`. Their config is
   *derived*, never hand-edited: `group_vars/dc{n}_fabric.yml` defines node topology (spine/l3leaf node_groups,
   BGP ASNs, uplinks, MLAG), `group_vars/dc{n}_fabric_services.yml` defines tenants/VRFs/SVIs/VLANs (shared
   across both DCs to realize the VXLAN stretch), `group_vars/dc{n}_fabric_ports.yml` defines the `servers:`
   list that leafs use to auto-generate their host-facing port config. `eos_designs` turns these into
   structured config, `eos_cli_config_gen` renders that into `intended/configs/*.cfg` + docs. Never edit files
   under `intended/` or `documentation/` directly — edit the `group_vars` inputs and re-run `make build_dc{n}`.

2. **Non-AVD devices** (DCI cores `s{n}-core1/2`, server endpoints `s{n}-host1/2`) — separate inventory groups
   (`dc{n}_dci`, `dc{n}_hosts`), config lives as hand-written static `.cfg` files in `dci_configs/` /
   `host_configs/` and is pushed with `arista.eos.eos_config` (eAPI) or `arista.avd.cv_deploy` with
   `read_structured_config_from_file: false` (CVP). These devices are intentionally kept outside
   `eos_designs`/`eos_cli_config_gen` — edit the `.cfg` file directly and redeploy with the matching playbook.

**Host endpoint topology**: `s{n}-host1` is dual-homed via MLAG port-channel (LACP active, trunk VLAN
10/20/100/200) to `s{n}-leaf1`/`s{n}-leaf2`; `s{n}-host2` to `s{n}-leaf3`/`s{n}-leaf4`. Each host has local
`vlan 10`/`20`/`100`/`200` entries (required — `switchport trunk allowed vlan` alone does not create the local
VLAN on EOS) plus a Vlan\<id\> SVI per VLAN with a per-host test IP, used to verify the EVPN-VXLAN stretch by
pinging across DCs (leaf anycast gateways are `10.10.10.1`/`10.20.20.1`/`10.100.100.1`/`10.200.200.1` in both
DCs). Each of these four SVIs sits in its own local VRF on the host (`vrf 10`/`20`/`100`/`200`, matching the
VLAN ID), each with a static default route to its leaf anycast VIP (`ip route vrf <n> 0.0.0.0/0 <VIP>`) — this
is a host-local routing construct only, independent of the fabric/tenant VRF design below, so pings from a host
must use `ping vrf <n> <ip>`, never the default VRF.

**Border Leafs ship commented out by default in both DCs, in two independently-gated layers.** `s{n}-brdr1`/
`s{n}-brdr2` are commented out in `sites/dc{n}/inventory.yml`, the `BrdrLeafs` node_group in `dc{n}_fabric.yml`,
and the `core_interfaces` section at the bottom of `dc{n}_fabric.yml` (DCI core P2P links) — uncommenting these
three spots in both DCs is `lab guide/evpn-vxlan-labs.md` Lab 2. But within `BrdrLeafs`, the `evpn_gateway`
sub-block (`evpn_l2.enabled` + `remote_peers`) is commented out *separately* and stays that way even after
Lab 2 — it's `lab guide/evpn-vxlan-labs.md` Lab 3. So after Lab 2 alone, Border Leafs are live fabric members
(local EVPN overlay, DCI underlay reachable) but the two domains are *not* stitched yet (`s1-host1 → s2-host1`
ping still fails); only after Lab 3 enables `evpn_gateway` does the multi-domain stretch described in
`lab guide/multi-domain-evpn-vxlan-guide.md` actually come up.

**A second tenant is staged but commented out too — on the fabric side only.** `New-Tenant` (VLAN 100 in its own
VRF `"100"`, VLAN 200 in its own VRF `"200"` — unlike `ATD_DC`'s VLANs 10/20, which still share one VRF `A` *on
the leaf/fabric side*) is written out but commented in `dc{n}_fabric_services.yml`, and `LeafPair1`/`LeafPair2`'s
`filter.tenants` in `dc{n}_fabric.yml` don't reference it yet — both are `lab guide/evpn-vxlan-labs.md` Lab 4.
The host side is *not* gated behind Lab 4: `s{n}-host1`/`s{n}-host2`'s static configs and `dc{n}_fabric_ports.yml`
already carry VLAN 100/200 (and, per the host-local VRF setup above, all four VLANs already sit in matching
per-VLAN VRFs on the host regardless of what the fabric side is doing) and have been deployed via
`make deploy_dc{n}_host_cvp`, so Lab 4 only touches the fabric side.

**EOS Connectivity Monitor is staged too.** A commented `structured_config.monitor_connectivity` block sits on
`LeafPair1` in `dc1_fabric.yml` (probing `s2-host2` at `10.10.10.22`) and on `LeafPair2` in `dc2_fabric.yml`
(probing `s1-host1` at `10.10.10.11`), both under VRF `A` — matching the leaf-side VRF for VLAN 10, *not* the
host-local VRF `10` from Lab 4. Uncommenting both is `lab guide/evpn-vxlan-labs.md` Lab 5; it requires Lab 2
(Border Leaf) to actually show `Reachable` since it probes across the DCI.

**global_vars/global_dc_vars.yml** holds settings common to both DCs (mgmt gateway, `management_eapi`,
cEOS management-interface override, etc.) and is loaded explicitly by `build_dc{n}.yml` via `include_vars`
before the AVD roles run — it is not picked up by inventory group membership.

**Inventory quirk**: the `dc{n}_hosts` group has *two* meanings in `sites/dc{n}/inventory.yml` — a top-level
group (sibling of `dc{n}_dci`) with real `ansible_host` entries used for the static-config CVP/eAPI deploys
above, and a commented-out nested placeholder under `dc{n}_fabric` for a possible future AVD-managed
(`l2leaf`-style) version of the hosts. Only the top-level group is currently active.

## Conventions

- Ansible connection is `httpapi` over eAPI (port 443) for all real devices; CVP-only playbooks use
  `connection: local` and call CVP's own API instead.
- `ansible.cfg` points `collections_paths` at `../ansible-cvp:../ansible-avd:...` — the AVD/CVP collections are
  expected to live as siblings of this repo under `labfiles/`, not just in the default Galaxy install path.
- README.md is maintained in Korean.
- Before making CVP/eAPI deploy calls, confirm with the user first — pushing config to switches or CVP is a
  real, hard-to-reverse action against lab infrastructure, not a local file edit.
