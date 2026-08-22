# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

Lab credentials must be injected before anything will authenticate against the switches/CVP. `group_vars/dc1/main.yml`,
`group_vars/dc2/main.yml`, `group_vars/dc1_srv6/main.yml` all set `ansible_password: "{{ vault_ansible_password }}"` —
this line is a permanent placeholder and is never edited. The real password is ansible-vault-encrypted into a sibling
`group_vars/<group>/vault.yml` per site (gitignored, never committed), decrypted automatically via the
`vault_password_file` set in `ansible.cfg` pointing at a local, gitignored `.vault_pass.txt`:

```bash
export LABPASSPHRASE=`cat /home/coder/.config/code-server/config.yaml| grep "password:" | awk '{print $2}'`
openssl rand -base64 24 > .vault_pass.txt && chmod 600 .vault_pass.txt
for f in sites/dc1/group_vars/dc1/vault.yml sites/dc2/group_vars/dc2/vault.yml \
         sites/srv6-dc1/group_vars/dc1_srv6/vault.yml; do
  ansible-vault encrypt_string \
    "$LABPASSPHRASE" --name 'vault_ansible_password' > "$f"
done
```

Note the `group_vars/<group>.yml` files were converted to `group_vars/<group>/main.yml` directories — Ansible does
not merge a `group_vars/<group>.yml` file and a same-named `group_vars/<group>/` directory; only one is loaded, so
`main.yml` and `vault.yml` must live side by side inside the directory.

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
- `make verify_dc1` / `make verify_dc2` — run only the ANTA validation play (no config push) against whatever is
  currently live on `dc{n}_fabric`, e.g. after a CVP-based deploy. Same `arista.avd.anta_runner` role and output
  paths as above.
- `make deploy_dc1_dci` / `make deploy_dc2_dci` (eAPI) and `make deploy_dc1_dci_cvp` / `make deploy_dc2_dci_cvp`
  (CVP) — deploy the s{1,2}-core1/core2 DCI routers from **static** configs in `sites/dc{n}/dci_configs/`.
- `make deploy_dc1_host_cvp` / `make deploy_dc2_host_cvp` — deploy the s{1,2}-host1/host2 dual-homed server
  endpoints from **static** configs in `sites/dc{n}/host_configs/`.
- Initial bring-up order: DCI configs → `build_dc{n}` → `deploy_dc{n}_cvp` → host configs (see README "초기
  설정 빌드 및 배포" for the full numbered sequence).
- `make bf_install` / `make bf_start` / `make bf_stop` / `make bf_status` — manage the local Batfish service
  (see "Pre-deploy validation with Batfish" below).
- `make preflight` (or `preflight_dc1` / `preflight_dc2`) — run `batfish/preflight.py`: builds a Batfish snapshot
  from `intended/configs/` + `dci_configs/` + `host_configs/` and validates it **without touching any device**.
  `make preflight_selftest` injects faults into snapshot copies to prove the checks still catch them.
- Recommended per-lab loop: edit `group_vars` → `make build_dc{n}` → `make preflight` → `make deploy_dc{n}_*` →
  `make verify_dc{n}`.

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

**CloudVision topology tags are generated for AVD-managed devices, but DCI core switches need a separate,
staged path.** `generate_cv_tags.topology_hints: true` is set in both `dc{n}_fabric.yml` (plus a `dc_name` and
per-node-group `rack`, and `cv_tags_topology_type: edge` on `BrdrLeafs`), so spines/leafs/border-leafs get
`topology_hint_*` tags automatically at `make build_dc{n}` time and are pushed by the existing
`make deploy_dc{n}_cvp`. The DCI cores (`s{n}-core1/2`) are static-config devices outside `eos_designs`, so
`generate_cv_tags` doesn't reach them; `sites/dc{n}/group_vars/dc{n}_dci.yml` has a commented-out
`cv_device_tags: [{name: topology_hint_type, value: core}, {name: topology_hint_network_type, value: wan}]`
block instead — this is the flat Ansible-variable input `cv_deploy` reads when called with
`read_structured_config_from_file: false` (as `deploy_dc{n}_dci_cvp.yml` does), in place of the
`metadata.cv_tags.device_tags` that `eos_designs` would otherwise populate. Uncommenting both is
`lab guide/evpn-vxlan-labs.md` Lab 5.

**EOS Connectivity Monitor is staged too.** A commented `structured_config.monitor_connectivity` block sits on
`LeafPair1` in `dc1_fabric.yml` (probing `s2-host2` at `10.10.10.22`) and on `LeafPair2` in `dc2_fabric.yml`
(probing `s1-host1` at `10.10.10.11`), both under VRF `A` — matching the leaf-side VRF for VLAN 10, *not* the
host-local VRF `10` from Lab 4. Uncommenting both is `lab guide/evpn-vxlan-labs.md` Lab 6; it requires Lab 2
(Border Leaf) to actually show `Reachable` since it probes across the DCI.

**global_vars/global_dc_vars.yml** holds settings common to both DCs (mgmt gateway, `management_eapi`,
cEOS management-interface override, etc.) and is loaded explicitly by `build_dc{n}.yml` via `include_vars`
before the AVD roles run — it is not picked up by inventory group membership.

**Inventory quirk**: the `dc{n}_hosts` group has *two* meanings in `sites/dc{n}/inventory.yml` — a top-level
group (sibling of `dc{n}_dci`) with real `ansible_host` entries used for the static-config CVP/eAPI deploys
above, and a commented-out nested placeholder under `dc{n}_fabric` for a possible future AVD-managed
(`l2leaf`-style) version of the hosts. Only the top-level group is currently active.

**SRv6 uSID demo (`sites/srv6-dc1`, `make deploy_dc1_srv6_cvp`) is a destructive, opt-in side-quest** unrelated
to the EVPN-VXLAN labs above, and lives as its own standalone site — separate `inventory.yml` and
`group_vars/dc1_srv6/` (own copy of the lab credentials), not nested under `sites/dc1`. There's no spare
hardware for the upstream 9-node clab topology (https://github.com/brokenpackets/clab_Topos/tree/main/srv6_uSID),
so it repurposes live DC1 fabric devices (`s1-spine1`, `s1-spine2`, `s1-leaf1`, `s1-leaf2`, `s1-leaf3`,
`s1-host1`, `s1-host2`) via static configs in `sites/srv6-dc1/srv6_configs/` — tearing down their
EVPN-VXLAN/MLAG/BGP config in the process, breaking DC1's fabric until `make build_dc1` +
`make deploy_dc1_cvp` (+ `make deploy_dc1_host_cvp`) redeploys it. See `sites/srv6-dc1/README.md` for the
physical-cabling-to-topology mapping and full caveats before touching this.

## Pre-deploy validation with Batfish

`batfish/` holds a config-only validation layer that runs *between* `make build_dc{n}` and any deploy. It is
documented for lab users in `lab guide/batfish-preflight-guide.md`; a full recorded run (pre-flight → deploy →
ANTA → host pings) is in `lab guide/batfish-avd-anta-verification-report.md`. Batfish reads configs and never
connects to a device, so it is safe to run against a live fabric. The non-obvious parts:

- **No Docker here.** Batfish normally ships as `docker run batfish/allinone`, but the ATD programmability IDE is
  itself a container with no Docker daemon. `batfish/install_batfish.sh` therefore pulls the same image's layers
  straight from the registry API into `../batfish-service/rootfs/` (a sibling of this repo, like the
  `ansible-avd`/`ansible-cvp` collections) and runs `allinone-bundle.jar` on the host JVM (OpenJDK 17, apt).
  `pybatfish` is installed from the wheel bundled *inside that image* so client and service versions match
  exactly. `batfish/batfishctl.sh` start/stops it on `localhost:9996`.
- **Snapshots are normalized copies; `sites/` originals are never modified.** `batfish/bf_lib.py` copies configs
  into `batfish/snapshots/<name>/configs/` and (a) prepends `hostname <name>` to the `dci_configs`/`host_configs`
  fragments, which are `eos_config` snippets with no hostname line, (b) normalizes `interface ethernet1` to
  `interface Ethernet1`, and (c) prepends `! device: <hostname> (cEOS-lab, EOS-4.36.0F)` to **every** file.
  That last one is load-bearing: without the Arista `show running-config` header Batfish detects the configs as
  CISCO_IOS, the spine files fail to parse entirely, and EOS-only syntax (`vrf instance`, `neighbor X peer group
  Y`) is rejected everywhere.
- **Layer-1 topology is derived from interface descriptions.** Without it Batfish infers adjacency from subnets
  and reports paths that have no cable. `bf_lib.build_layer1()` parses the `<node>_<Interface>` suffix that both
  AVD (`P2P_s1-spine1_Ethernet2`, `MLAG_s1-leaf2_Ethernet1`, `SERVER_s1-host1_Ethernet1`) and the hand-written
  static configs (`P2P_LINK_TO_s1-brdr1_Ethernet4`, `DCI_P2P_LINK_TO_s2-core1_Ethernet4`,
  `PortChan1_s1-leaf1_Ethernet4`) put in descriptions, yielding 58 links. The `s{n}-core1`↔`s{n}-core2`
  port-channel members carry no peer info in config at all and are hardcoded in `L1_OVERRIDES`. Note
  `_iter_interfaces()` cannot use indentation to find block ends — the static config fragments are unindented.
- **Two allowlists encode "this is fine by design".** `preflight.py`'s `KNOWN_UNSUPPORTED` lists EOS syntax
  Batfish cannot model (`rd evpn domain remote`, `monitor connectivity`, `ip address virtual source-nat`, …) so
  that only *new* parse warnings surface; the duplicate-IP check exempts anycast gateways (`ip address virtual`)
  and the VTEP Loopback1 address that AVD deliberately shares across each MLAG pair (peers derived from
  `description MLAG_<peer>_...`, VTEP interface from `vxlan source-interface`).
- **What it cannot see.** Whether a config was actually deployed (a real run found the DCI cores unconfigured
  while every pre-flight check passed — ANTA caught it), EVPN route re-origination behavior (checked only as
  config text), and same-subnet host-to-host VXLAN forwarding, which Batfish shortcuts as L2-accepted — so
  cross-DC host pings still have to be verified for real after deploy.
- **Control-plane checks alone are not enough, hence `check_vtep_reachability`.** EVPN peering rides Loopback0
  (router ID) while VXLAN encapsulation rides Loopback1 (VTEP), so blackholing just a VTEP address leaves every
  BGP session Established and ANTA green while all cross-DC host traffic dies. That check runs one Batfish
  `reachability` query (`actions="failure"`, ~0.3s) over every (VTEP node → VTEP IP) pair instead of N
  traceroutes. A single representative leaf↔leaf path — what Lab 3's check traces — is *not* sufficient: it
  passed while the fabric was fully broken.
- **A staged failure scenario lives in `dc1_fabric.yml`.** The `BrdrLeafs` group carries a commented-out
  `structured_config.static_routes` blackholing `10.1.1.102/32` (the remote DC's border-leaf VTEP) to `null0`.
  Uncommenting it is `lab guide/batfish-preflight-guide.md` §7-A; it breaks all DC1↔DC2 host traffic while
  leaving BGP/EVPN and ANTA reporting healthy. Note AVD 6.0.0 renamed `destination_address_prefix` to `prefix`
  — the old key fails schema validation at `make build_dc1`. Reverting needs an explicit
  `no ip route 10.1.1.102/32 Null0` on `s1-brdr1`/`s1-brdr2` if it was deployed, because `eos_config` with
  `src` only adds missing lines and never removes extra ones.
- `batfish/selftest.py` (`make preflight_selftest`) re-inits snapshot copies with five injected faults
  (evpn_gateway removed, one-sided MTU, duplicate router ID, DCI link shutdown, edge VTEP blackhole) and asserts
  the matching check flips to FAIL. Run it after changing any check.
- `batfish/snapshots/` and `batfish/reports/` are regenerated per run and gitignored.

## Conventions

- Ansible connection is `httpapi` over eAPI (port 443) for all real devices; CVP-only playbooks use
  `connection: local` and call CVP's own API instead.
- `ansible.cfg` points `collections_paths` at `../ansible-cvp:../ansible-avd:...` — the AVD/CVP collections are
  expected to live as siblings of this repo under `labfiles/`, not just in the default Galaxy install path.
- README.md is maintained in Korean.
