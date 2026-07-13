# EVPN VXLAN 랩

이 랩들의 목표는 AVD가 Day 2 이후의 네트워크 운영을 얼마나 쉽게 만들어주는지 보여주는 것입니다. 아래 다섯 개의 랩을 진행합니다.

> 아래 예시들은 이 저장소의 실제 AVD 6.3.0 스키마(`sites/dc{n}/group_vars/dc{n}_fabric.yml`, `dc{n}_fabric_services.yml`의 현재 내용)를 그대로 따릅니다. 값을 넣기 전에 해당 파일을 먼저 열어 기존 항목의 들여쓰기와 구조를 확인하세요.

<br>
<br>

## Lab 1 - EVPN VXLAN 토폴로지에 VLAN 추가

이 랩에서는 EVPN VXLAN 토폴로지에 새 VLAN을 추가하는 설정 변경을 얼마나 간단하게 자동화할 수 있는지 보여줍니다. 자동화되지 않은 EVPN VXLAN 토폴로지에서는 새 VLAN을 추가하고 확장할 때마다 모든 스위치에 VLAN을 생성하고, VXLAN에 매핑하고, 관련 장비의 BGP 설정에도 추가해야 합니다. 이 랩에서는 `dc1_fabric_services.yml`과 `dc2_fabric_services.yml` vars 파일을 수정하여 아래 나열된 새 VLAN을 추가합니다.

두 파일 모두 `tenants[0].vrfs[0].svis` 리스트 아래에 기존 VLAN 10/20과 동일한 구조로 항목을 추가하면 됩니다. 아래는 `dc1_fabric_services.yml`(및 `dc2_fabric_services.yml`) 기준 실제 예시입니다:

```yaml
tenants:
  - name: ATD_DC
    mac_vrf_vni_base: 10000
    vrfs:
      - name: A
        vrf_vni: 50001
        mlag_ibgp_peering_vlan: 4001
        mlag_ibgp_peering_ipv4_pool: 192.2.2.0/23
        svis:
          - id: 10
            name: ten
            description: ten
            tags: ['DC']
            enabled: true
            mtu: 9014
            ip_address_virtual: 10.10.10.1/24
          - id: 20
            name: twenty
            description: twenty
            tags: ['DC']
            enabled: true
            mtu: 9014
            ip_address_virtual: 10.20.20.1/24
          - id: 30
            name: thirty
            description: thirty
            tags: ['DC']
            enabled: true
            mtu: 9014
            ip_address_virtual: 10.30.30.1/24
          - id: 40
            name: forty
            description: forty
            tags: ['DC']
            enabled: true
            mtu: 9014
            ip_address_virtual: 10.40.40.1/24
          - id: 50
            name: fifty
            description: fifty
            tags: ['DC']
            enabled: true
            mtu: 9014
            ip_address_virtual: 10.50.50.1/24
```

새로 추가하는 `svis` 항목은 마지막 세 개(`id: 30`, `id: 40`, `id: 50`)이며, `tenants`/`vrfs`와 기존 VLAN 10/20 항목은 두 파일에 이미 있는 내용이므로 그대로 둡니다. `ip_address_virtual`은 이 VLAN의 anycast gateway IP이며, 두 데이터센터 모두 같은 값을 넣어야 VXLAN 스트레치가 동일하게 동작합니다.

vars 파일을 수정하고 저장한 뒤, 아래 단계를 진행하세요:

1) `make build_dc1`과 `make build_dc2`를 실행하여 새 structured config와 장비 config를 생성합니다.

2) 각 디렉토리의 설정을 검토하여 변경 사항이 올바른지 확인합니다.

3) 자동으로 생성된 문서의 변경 내용을 검토합니다.

4) `make deploy_dc1_cvp`와 `make deploy_dc2_cvp`를 실행하고, CVP에 생성된 change control을 검토한 뒤 승인합니다.

5) leaf 스위치에 로그인하여 새 VLAN과 SVI 설정이 반영되었는지 확인합니다.

<br>
<br>


## Lab 2 - Border Leaf 추가 (EVPN Gateway 없이 fabric 편입)

저장소를 처음 clone한 상태의 dc1/dc2는 각각 **독립된 단일 데이터센터 EVPN/VXLAN 패브릭**으로만 빌드됩니다. Border Leaf(`s{n}-brdr1`/`s{n}-brdr2`) 관련 설정이 아래 세 파일에 주석(`#`) 처리되어 있기 때문입니다.

- `sites/dc{n}/inventory.yml` — `s{n}-brdr1`/`s{n}-brdr2` 인벤토리 항목
- `sites/dc{n}/group_vars/dc{n}_fabric.yml` — `l3leaf.node_groups` 아래 `BrdrLeafs` 블록(단, `evpn_gateway` 서브 블록은 별도로 주석 처리되어 있어 이 랩에서는 건드리지 않습니다 — Lab 3에서 다룹니다)
- `sites/dc{n}/group_vars/dc{n}_fabric.yml` — 파일 하단 `core_interfaces` 섹션(Border Leaf ↔ DCI core 라우터 P2P 링크)

이 랩에서는 Border Leaf를 fabric에 leaf 하나 추가하듯 **기본 언더레이/로컬 EVPN 오버레이만** 있는 상태로 편입시킵니다. `evpn_gateway`(EVPN Gateway 기능, 즉 원격 도메인과의 재발신 피어링)는 아직 켜지 않습니다 — 그래서 이 랩이 끝나도 dc1과 dc2는 여전히 서로 독립된 EVPN 도메인입니다. dc1은 이미 DCI 정적 설정(`sites/dc1/dci_configs/`)이 `make deploy_dc1_dci`로 배포되어 있다고 가정합니다(README 초기 구축 순서 1~2단계 참고).

1) `sites/dc1/inventory.yml`을 열어 `dc1_leafs` 그룹 아래 주석 처리된 `s1-brdr1`/`s1-brdr2` 항목의 주석을 해제합니다.

```yaml
            s1-leaf4:
              ansible_host: 192.168.0.15
            s1-brdr1:
              ansible_host: 192.168.0.100
            s1-brdr2:
              ansible_host: 192.168.0.101
```

2) `sites/dc1/group_vars/dc1_fabric.yml`을 열어 `l3leaf.node_groups` 맨 위, 주석 처리된 `BrdrLeafs` 블록의 주석을 해제합니다 — **단 `evpn_gateway` 서브 블록은 그대로 주석 상태로 남겨 두세요**(따로 표시되어 있습니다). 우선 아래 형태가 되어야 합니다.

```yaml
    ####################################################
    # DC1 Border Leafs                                 #
    ####################################################
    - group: BrdrLeafs
      platform: ceos
      structured_config:
        router_bgp:
          address_family_ipv4:
            networks:
              - prefix: 10.231.0.2/32
              - prefix: 10.231.0.4/32
              - prefix: 10.231.1.2/32
      filter:
        tenants: [ATD_DC]
        tags: ['DC']
      bgp_as: 65099
      # evpn_gateway:                <- Lab 3까지는 주석 유지
      #   evpn_l2:
      #     enabled: true
      #   remote_peers:
      #     - hostname: s2-brdr1
      #       ip_address: 10.1.0.102
      #       bgp_as: 65199
      #     - hostname: s2-brdr2
      #       ip_address: 10.1.0.104
      #       bgp_as: 65199
      nodes:
        - name: s1-brdr1
          id: 2
          mgmt_ip: 192.168.0.100/24
          uplink_switch_interfaces: [Ethernet7, Ethernet7]
          uplink_interfaces: [Ethernet2, Ethernet3]
          mlag_interfaces: [Ethernet1, Ethernet6]
          structured_config:
            router_bgp:
              neighbors:
                - ip_address: 172.16.255.1
                  remote_as: 65501
                  description: s1-core1 VRF Default
                  peer_group: IPV4-UNDERLAY-PEERS
                - ip_address: 172.16.255.3
                  remote_as: 65501
                  description: s1-core2 VRF Default
                  peer_group: IPV4-UNDERLAY-PEERS
        - name: s1-brdr2
          id: 4
          mgmt_ip: 192.168.0.101/24
          uplink_switch_interfaces: [Ethernet8, Ethernet8]
          uplink_interfaces: [Ethernet2, Ethernet3]
          mlag_interfaces: [Ethernet1, Ethernet6]
          structured_config:
            router_bgp:
              neighbors:
                - ip_address: 172.16.255.5
                  remote_as: 65501
                  description: s1-core1 VRF Default
                  peer_group: IPV4-UNDERLAY-PEERS
                - ip_address: 172.16.255.7
                  remote_as: 65501
                  description: s1-core2 VRF Default
                  peer_group: IPV4-UNDERLAY-PEERS
```

3) 같은 파일 맨 아래, 주석 처리된 `core_interfaces` 섹션 전체의 주석을 해제합니다. Border Leaf와 DCI core 라우터(`s1-core1`/`s1-core2`) 사이의 순수 IP P2P 링크입니다.

```yaml
####################################################
# External Fabric PtP L3 Conncectivity             #
####################################################
core_interfaces:
  p2p_links:
    ############################################################
    # s1-brdr1 to s1-cores UNDERLAY (Default VRF) Peerings     #
    ############################################################
    - ip: [ 172.16.255.0/31, 172.16.255.1/31 ]
      nodes: [ s1-brdr1, s1-core1 ]
      interfaces: [ Ethernet4, Ethernet2 ]
      include_in_underlay_protocol: false
      mtu: 9214
    - ip: [ 172.16.255.2/31, 172.16.255.3/31 ]
      nodes: [ s1-brdr1, s1-core2 ]
      interfaces: [ Ethernet5, Ethernet2 ]
      include_in_underlay_protocol: false
      mtu: 9214
    ############################################################
    # s1-brdr2 to s1-cores UNDERLAY (Default VRF) Peerings     #
    ############################################################
    - ip: [ 172.16.255.4/31, 172.16.255.5/31 ]
      nodes: [ s1-brdr2, s1-core1 ]
      interfaces: [ Ethernet4, Ethernet3 ]
      include_in_underlay_protocol: false
      mtu: 9214
    - ip: [  172.16.255.6/31, 172.16.255.7/31 ]
      nodes: [ s1-brdr2, s1-core2 ]
      interfaces: [ Ethernet5, Ethernet3 ]
      include_in_underlay_protocol: false
      mtu: 9214
```

4) dc2도 동일한 방식으로 진행합니다: `sites/dc2/inventory.yml`의 `s2-brdr1`/`s2-brdr2`, `sites/dc2/group_vars/dc2_fabric.yml`의 `BrdrLeafs` 블록(`evpn_gateway`는 역시 주석 유지)과 `core_interfaces` 섹션 주석을 해제합니다. `bgp_as`(65199), `id`(102/104), `mgmt_ip`(.200/.201)는 dc1과 대칭이므로 값이 다른 점에 유의하세요 — dc1의 값을 그대로 복사하지 말고 파일에 이미 채워진 값을 그대로 사용하면 됩니다(주석만 해제).

주석을 해제하고 저장한 뒤, 아래 단계를 진행하세요:

1) `make build_dc1`과 `make build_dc2`를 실행하여 새 structured config와 장비 config를 생성합니다. `s{n}-brdr1.cfg`/`s{n}-brdr2.cfg`가 새로 생성되고, `s{n}-spine1.cfg`/`s{n}-spine2.cfg`에 Border Leaf 방향 BGP 네이버·인터페이스가 추가됩니다.

2) 각 디렉토리의 설정을 검토하여 변경 사항이 올바른지 확인합니다.

3) 자동으로 생성된 문서의 변경 내용을 검토합니다.

4) `make deploy_dc1_cvp`와 `make deploy_dc2_cvp`를 실행하고, CVP에 생성된 change control을 검토한 뒤 승인합니다.

5) Border Leaf 스위치에 로그인해 fabric에 정상적으로 편입되었는지 확인합니다(`show bgp evpn summary`에 로컬 스파인/leaf와의 `EVPN-OVERLAY-LOCAL-PEERS` 세션만 `Established`로 보이고, 아직 `EVPN-OVERLAY-REMOTE-PEERS`는 설정 자체가 없는 것이 정상입니다). `s1-host1`에서 `s2-host1`로 핑을 시도하면 이 시점에는 **아직 실패**해야 합니다 — DCI 언더레이는 연결됐지만 EVPN Gateway가 없어 두 도메인의 오버레이가 아직 스티칭되지 않았기 때문입니다. 이 상태를 Lab 3에서 이어서 다룹니다.

<br>
<br>


## Lab 3 - EVPN Gateway 활성화 및 Multi-Domain 검증

Lab 2에서 Border Leaf를 fabric에 편입시켰지만 `evpn_gateway` 블록은 계속 주석 상태로 남겨 두었습니다. 이 랩에서는 그 `evpn_gateway` 블록의 주석을 해제해서 실제로 dc1과 dc2를 하나의 스트레치된 EVPN/VXLAN처럼 연동시키고, 그 동작 원리를 직접 명령어로 확인합니다(배경 설명은 `lab guide/multi-domain-evpn-vxlan-guide.md` 참고). **Lab 2를 먼저 완료해야** 진행할 수 있습니다.

1) `sites/dc1/group_vars/dc1_fabric.yml`을 열어 `BrdrLeafs` 블록 안, `bgp_as: 65099` 바로 아래 주석 처리된 `evpn_gateway` 서브 블록의 주석을 해제합니다.

```yaml
      bgp_as: 65099
      evpn_gateway:
        evpn_l2:
          enabled: true
        evpn_l3:
          enabled: true
        remote_peers:
          - hostname: s2-brdr1
            ip_address: 10.1.0.102
            bgp_as: 65199
          - hostname: s2-brdr2
            ip_address: 10.1.0.104
            bgp_as: 65199
      nodes:
```

2) `sites/dc2/group_vars/dc2_fabric.yml`도 동일하게 `BrdrLeafs` 블록 안 `evpn_gateway` 서브 블록의 주석을 해제합니다. `bgp_as`(65099)와 `remote_peers`(`s1-brdr1`/`s1-brdr2` 대상)는 dc1과 대칭이므로 값이 다른 점에 유의하세요 — dc1의 값을 복사하지 말고 파일에 이미 채워진 값을 그대로 사용하면 됩니다(주석만 해제).

```yaml
      bgp_as: 65199
      evpn_gateway:
        evpn_l2:
          enabled: true
        evpn_l3:
          enabled: true
        remote_peers:
        - hostname: s1-brdr1
          ip_address: 10.1.0.2
          bgp_as: 65099
        - hostname: s1-brdr2
          ip_address: 10.1.0.4
          bgp_as: 65099
      nodes:
```

`evpn_l2`는 VLAN 10/20 자체의 stretch(Type-2/3 경로)를 담당합니다. `evpn_l3`(Type-5/IP-prefix 경로 릴레이)는 이 랩에서 검증할 호스트 간 통신에는 필요 없지만, Border Leaf가 반대쪽 도메인으로 릴레이할 수 있는 경로 타입을 넓혀 두는 것이라 함께 켜 둡니다 — Lab 5(Connectivity Monitoring)에서 leaf마다 만드는 전용 Loopback 주소가 바로 이 `evpn_l3` 덕분에 DC 경계를 넘어갑니다.

주석을 해제하고 저장한 뒤, `make build_dc1`과 `make build_dc2`를 실행해 structured config와 장비 config를 다시 생성하고, `make deploy_dc1_cvp`/`make deploy_dc2_cvp`로 배포·승인합니다. 이제부터 아래 단계로 실제 동작을 검증합니다.

3) Border Leaf의 EVPN Gateway 원격 피어링이 정상인지 확인합니다. `s1-brdr1`(또는 `s1-brdr2`)에 로그인해서:

```
show bgp evpn summary
```

`10.1.0.102`(`s2-brdr1`), `10.1.0.104`(`s2-brdr2`)가 `EVPN-OVERLAY-REMOTE-PEERS` 피어그룹으로 `Established` 상태여야 합니다(Lab 2 직후에는 이 세션 자체가 없었다는 걸 기억하세요). `s2-brdr1`/`s2-brdr2`에서도 대칭으로 `10.1.0.2`/`10.1.0.4`(`s1-brdr1`/`s1-brdr2`)를 확인하세요.

4) EVPN 경로 재발신(re-origination) 설정이 실제로 들어갔는지, 생성된 config에서 확인합니다.

```bash
grep -A3 "address-family evpn" sites/dc1/intended/configs/s1-brdr1.cfg
grep "domain remote" sites/dc1/intended/configs/s1-brdr1.cfg
```

`neighbor EVPN-OVERLAY-REMOTE-PEERS domain remote`(피어그룹 자체를 원격 도메인으로 표시)와, 각 VLAN 아래 `rd evpn domain remote ...`/`route-target import export evpn domain remote ...` 줄이 있어야 합니다. 이게 바로 §6에서 설명한 "도메인 정보를 남겨서 루프를 막는" 표시입니다. `s{n}-leaf*.cfg`에는 이 줄이 없다는 것도 함께 확인해 보세요 — 재발신은 Border Leaf만 하는 일입니다.

5) 스티칭 경계를 직접 확인합니다 — DC2가 실제로 보는 "원격 VTEP"이 DC1의 실제 leaf가 아니라 `s1-brdr1`/`s1-brdr2`인지 검증합니다. `s2-leaf1`(또는 `s2-leaf2`)에 로그인해서:

```
show bgp evpn route-type mac-ip vni 10010
```

`s1-host1`이 붙어 있는 VLAN 10(VNI 10010)의 Type-2 경로를 찾아 next-hop을 확인하세요. next-hop은 `10.1.1.2`(`s1-brdr1`의 Loopback1) 또는 `10.1.1.4`(`s1-brdr2`의 Loopback1)여야 합니다 — `s1-leaf1`의 실제 Loopback1인 `10.1.1.14`가 아닙니다. DC2 입장에서는 DC1의 실제 leaf VTEP을 전혀 모르고, Border Leaf만 "원격 VTEP"으로 보인다는 것이 §6에서 말한 stitching(스티칭)의 실체입니다.

6) 실제 트래픽으로 검증합니다. 호스트 쪽 VLAN 10 SVI는 로컬 VRF `10`에 있으므로, `s1-host1`에서:

```
ping vrf 10 10.10.10.21
```

`s2-host1`(`10.10.10.21`)까지 0% 손실로 도달해야 합니다 — Lab 2 직후에는 실패했던 바로 그 핑입니다. `s1-host2 ↔ s2-host2`(`10.10.10.12` ↔ `10.10.10.22`)도 같은 방식으로 확인하세요.

7) ANTA로 자동 검증합니다. `make deploy_dc1_eapi`를 실행하면 배포 직후 `arista.avd.anta_runner`가 BGP·인터페이스·MLAG·VXLAN/VNI 매핑을 구조화된 설정 기준으로 자동 점검하고 `sites/dc1/anta/reports/`에 리포트를 남깁니다(§10 참고). 리포트에서 BGP/EVPN/VXLAN 관련 테스트가 실패하면, 이번 랩에서 방금 확인한 EVPN Gateway 피어링·재발신 설정을 다시 점검하세요. `deploy_dc2_eapi.yml`에는 아직 이 ANTA 검증 단계가 없다는 점도 §10에서 언급한 대로입니다.

<br>
<br>


## Lab 4 - 새 Tenant(New-Tenant) 추가, VLAN별 전용 VRF

Lab 1이 기존 tenant(`ATD_DC`)의 공유 VRF(`A`) 안에 VLAN을 추가하는 랩이었다면, 이 랩은 **완전히 새로운 tenant**를 추가하면서 동시에 **VLAN마다 전용 VRF를 분리**하는 패턴을 보여줍니다 — 기존 VLAN 10/20이 VRF `A` 하나를 공유하는 것과 달리, 새로 추가하는 VLAN 100은 VRF `100`에, VLAN 200은 VRF `200`에 각각 격리됩니다. VRF 이름을 VLAN ID와 동일하게 맞춰 두면 어떤 VLAN이 어떤 VRF에 속하는지 config만 보고도 바로 알 수 있습니다.

`New-Tenant` 블록은 `sites/dc{n}/group_vars/dc{n}_fabric_services.yml`에 이미 작성되어 있지만 주석(`#`) 처리되어 있습니다. AVD 스키마에서 tenant는 여러 VRF/VLAN을 묶는 최상위 단위이며, 새 tenant를 추가할 때는 `fabric_services.yml`에 tenant 정의를 두는 것만으로는 부족하고 — 어떤 leaf가 이 tenant의 서비스를 실제로 렌더링할지 `fabric.yml`의 `filter.tenants`에도 추가해야 합니다. 이 두 단계가 함께 있어야 하는 이유를 보여주는 것이 이 랩의 핵심입니다. 호스트 쪽(`s{n}-host1`/`s{n}-host2`의 정적 설정과 `fabric_ports.yml`의 트렁크 VLAN)은 이미 VLAN 100/200을 포함해 배포까지 끝나 있으므로, 이 랩에서는 fabric 쪽만 손보면 됩니다.

> Tenant 이름은 `New-Tenant`, VLAN은 100(서브넷 `10.100.100.0/24`, VRF `100`)과 200(서브넷 `10.200.200.0/24`, VRF `200`)을 사용합니다. `mac_vrf_vni_base`는 기존 tenant(10000)와 겹치지 않는 `20000`을 사용합니다. 아래 값은 실제로 `make build_dc1`/`make build_dc2`를 돌려 정상 빌드됨을 확인한 값입니다.

1) `sites/dc1/group_vars/dc1_fabric_services.yml`과 `sites/dc2/group_vars/dc2_fabric_services.yml`을 열어 `ATD_DC` tenant 항목 다음에 주석 처리된 `New-Tenant` 블록의 주석을 해제합니다.

```yaml
  - name: New-Tenant
    mac_vrf_vni_base: 20000
    vrfs:
      - name: "100"
        vrf_vni: 50003
        mlag_ibgp_peering_vlan: 4003
        mlag_ibgp_peering_ipv4_pool: 192.4.4.0/23
        svis:
          - id: 100
            name: onehundred
            description: onehundred
            tags: ['DC']
            enabled: true
            mtu: 9014
            ip_address_virtual: 10.100.100.1/24
      - name: "200"
        vrf_vni: 50004
        mlag_ibgp_peering_vlan: 4004
        mlag_ibgp_peering_ipv4_pool: 192.5.5.0/23
        svis:
          - id: 200
            name: twohundred
            description: twohundred
            tags: ['DC']
            enabled: true
            mtu: 9014
            ip_address_virtual: 10.200.200.1/24
```

VRF 이름은 문자열이므로 YAML에서 `"100"`, `"200"`처럼 반드시 따옴표로 감싸야 합니다(따옴표 없이 숫자만 쓰면 정수로 해석되어 스키마 오류가 납니다). `vrf_vni`(50003/50004), `mlag_ibgp_peering_vlan`(4003/4004), `mlag_ibgp_peering_ipv4_pool`(192.4.4.0/23, 192.5.5.0/23)은 기존 tenant `ATD_DC`의 vrf `A`가 쓰는 값(50001, 4001, 192.2.2.0/23)과 겹치지 않게 이미 골라져 있습니다.

2) 이 tenant를 실제로 배포받을 leaf pair의 `filter.tenants`에 `New-Tenant`를 추가합니다. `sites/dc{n}/group_vars/dc{n}_fabric.yml`에서 `LeafPair1`과 `LeafPair2` 블록을 찾아 아래처럼 수정합니다(`LeafPair1`만 예시):

```yaml
    - group: LeafPair1
      filter:
        tenants: [ATD_DC, New-Tenant]
        tags: ['DC']
      bgp_as: 65001
```

이 단계를 건너뛰면 tenant/VLAN 정의는 있지만 `make build_dc{n}`을 돌려도 어떤 leaf에도 VLAN 100/200이 렌더링되지 않습니다(실제로 확인된 동작입니다). Lab 2를 이미 완료해서 Border Leaf가 살아있다면, dc 간 EVPN Gateway가 `New-Tenant`의 경로도 재발신하도록 (여전히 주석 처리되어 있는) `BrdrLeafs` 블록의 `filter.tenants`에도 `New-Tenant`를 추가하세요.

3) 호스트가 새 VLAN을 트렁크로 받도록 `sites/dc{n}/group_vars/dc{n}_fabric_ports.yml`의 `s{n}-host1`/`s{n}-host2` 항목의 `vlans` 값을 확장합니다.

```yaml
servers:
  - name: s1-host1
    adapters:
      - endpoint_ports: [Ethernet1, Ethernet2]
        switch_ports: [Ethernet4, Ethernet4]
        switches: [s1-leaf1, s1-leaf2]
        mode: trunk
        vlans: "10,20,100,200"
        port_channel:
          mode: active
```

`sites/dc{n}/host_configs/s{n}-host1.cfg`, `s{n}-host2.cfg`는 이미 VLAN 100/200 local vlan 항목, trunk allowed vlan, 테스트 IP까지 반영되어 배포까지 끝난 상태이므로 — 이 랩에서는 호스트 쪽 파일을 수정할 필요가 없습니다. 참고로 이 호스트들은 `vlan10`/`vlan20`/`vlan100`/`vlan200` SVI를 각각 VLAN ID와 이름이 같은 로컬 VRF(`vrf 10`/`20`/`100`/`200`)에 배치하고, 각 VRF마다 해당 leaf anycast VIP를 향하는 기본 경로(`ip route vrf ... 0.0.0.0/0 ...`)를 갖도록 구성되어 있습니다 — 이건 호스트 장비 자체의 로컬 라우팅 설정이며, 아래에서 다루는 fabric 쪽 VRF(leaf/tenant 레벨)와는 별개입니다.

주석을 해제하고 저장한 뒤, 아래 단계를 진행하세요:

1) `make build_dc1`과 `make build_dc2`를 실행하여 새 structured config와 장비 config를 생성합니다.

2) `sites/dc{n}/intended/configs/s{n}-leaf1.cfg`, `s{n}-leaf2.cfg`에 `vrf instance 100`/`vrf instance 200`, VLAN 100/200, `vxlan vlan 100 vni 20100`/`vxlan vlan 200 vni 20200`, `vxlan vrf 100 vni 50003`/`vxlan vrf 200 vni 50004`가 추가되었는지 확인합니다. `s{n}-leaf3.cfg`/`s{n}-leaf4.cfg`에도 (2단계에서 `LeafPair2`도 함께 수정했다면) 동일하게 나타나야 합니다.

3) 자동으로 생성된 문서의 변경 내용을 검토합니다.

4) `make deploy_dc1_cvp`와 `make deploy_dc2_cvp`를 실행하고, CVP에 생성된 change control을 검토한 뒤 승인합니다.

5) 호스트의 모든 VLAN SVI(10/20/100/200)가 각각 이름이 같은 로컬 VRF에 있으므로, 호스트에서 ping을 실행할 때는 항상 `ping vrf <vrf 이름> <목적지 IP>` 형태로 VRF를 지정해야 합니다(`ping 10.100.100.21`처럼 기본 VRF로 실행하면 목적지 경로가 없어 실패합니다).
   - `s1-host1`에서 `ping vrf 100 10.100.100.21` — VRF `100` 안에서 `s2-host1`까지 EVPN/VXLAN 스트레치를 검증합니다.
   - `s1-host1`에서 `ping vrf 200 10.200.200.21` — VRF `200` 안에서 `s2-host1`까지 EVPN/VXLAN 스트레치를 검증합니다.
   - `s1-host2`/`s2-host2`(`.12`/`.22`)도 같은 방식으로 `ping vrf 100 ...`/`ping vrf 200 ...`으로 확인합니다.
   - `s1-host1`에서 `ping vrf 100 10.200.200.11`처럼 VRF `100`에서 VRF `200`의 IP로 핑하면 실패하는 것이 정상입니다 — 호스트 자체가 두 VRF를 완전히 분리된 라우팅 테이블로 관리하고, fabric(leaf) 쪽에서도 tenant `New-Tenant`의 VRF `100`/`200`이 서로 다른 VNI(50003/50004)로 격리되어 있기 때문입니다.
   - 반면 `ping vrf 10 10.20.20.11`(VLAN10 → VLAN20, 같은 호스트 내부)처럼 VRF `10`에서 VRF `20`의 IP로 핑하면, 호스트 자체의 라우팅 테이블은 분리되어 있어도 fabric의 leaf 쪽은 VLAN10/20이 여전히 같은 VRF `A`를 공유하므로 **leaf를 거쳐서** 도달합니다(호스트 → leaf 게이트웨이 → leaf의 VRF `A` 내부 라우팅 → 목적지 VLAN → 호스트 순서). VLAN 100/200은 leaf 쪽도 서로 다른 VRF라 leaf에서도 막히지만, VLAN 10/20은 호스트만 분리되어 있고 leaf는 하나로 합쳐져 있어 결과적으로 통신이 된다는 차이를 보여줍니다.
   - Lab 2까지 완료된 상태여야 DC 간(`s1-host* ↔ s2-host*`) 스트레치가 동작합니다. Lab 2 없이도 같은 DC 안(`s1-host1 ↔ s1-host2`, 서로 다른 leaf pair)에서는 VRF별 라우팅을 확인할 수 있습니다.

<br>
<br>


## Lab 5 - AVD로 Connectivity Monitoring 설정 (s1-host1 ↔ s2-host2)

지금까지의 랩은 사람이 직접 `ping`을 실행해서 EVPN/VXLAN 스트레치를 검증했습니다. 이 랩에서는 EOS의 **Connectivity Monitor** 기능(`monitor connectivity`)을 AVD로 구성해, leaf 스위치가 원격 호스트를 주기적으로 자동 프로빙(ICMP)하고 그 결과를 `show monitor connectivity`로 상시 확인할 수 있게 만듭니다. AVD 6.3.0 스키마의 `monitor_connectivity` 키(`eos_designs`/`eos_cli_config_gen` 모두 지원)를 `structured_config`로 얹는 방식입니다.

> **모니터링 대상**: `s1-host1`(dc1, `10.10.10.11`)과 `s2-host2`(dc2, `10.10.10.22`)를 서로 반대쪽 DC에서 감시하도록 구성합니다 — dc1의 `LeafPair1`(`s1-leaf1`/`s1-leaf2`, 원래 `s1-host1`이 붙어 있는 leaf pair)이 `s2-host2`를, dc2의 `LeafPair2`(`s2-leaf3`/`s2-leaf4`, 원래 `s2-host2`가 붙어 있는 leaf pair)가 `s1-host1`을 서로 감시합니다. 이렇게 하면 두 leaf pair가 "내 로컬 호스트는 정상인데, 상대편 DC의 호스트까지 도달 가능한가"를 지속적으로 확인하는 구조가 됩니다.
>
> **VRF 이름 주의**: 호스트 장비 자체에는 VLAN 10 전용 로컬 VRF `10`이 있지만, 이건 호스트에만 있는 로컬 구성입니다. **leaf/fabric 쪽에서 VLAN 10을 실어나르는 VRF는 여전히 `A`**입니다(Lab 4에서도 `ATD_DC`의 fabric 쪽 VRF는 손대지 않았으므로). 그래서 아래 `monitor_connectivity` 설정은 `vrfs: - name: A`를 사용합니다 — leaf 입장에서는 VLAN 10이 속한 VRF가 `A`이기 때문입니다.
>
> **선행 조건**: 이 랩은 Lab 2(Border Leaf)와 Lab 3(EVPN Gateway)까지 완료되어 dc1 ↔ dc2 스트레치가 살아있는 상태를 전제로 합니다. Lab 3에서 `evpn_gateway`에 `evpn_l3`까지 함께 켰다면(Lab 3 참고), 이 랩에서 만들 leaf 전용 주소가 DC 경계를 넘어가는 데 필요한 준비는 이미 끝나 있습니다.

이 랩에서 구성할 내용은 크게 두 부분입니다.

- **프로브 자체** — `monitor_connectivity`로 5초 간격 ICMP 프로브를 켭니다.
- **프로브 전용 소스 주소** — VLAN 10의 게이트웨이는 두 DC 전체가 공유하는 anycast 주소(`10.10.10.1`)이므로, leaf가 자기 자신을 대표하는 고유 주소로 프로브를 보내도록 leaf마다 전용 Loopback과 source-nat를 하나씩 마련합니다.

### 1) leaf마다 전용 소스 주소 구성 — Loopback + `virtual_source_nat_vrfs`

`sites/dc1/group_vars/dc1_fabric.yml`의 `LeafPair1`(`s1-leaf1`/`s1-leaf2`) 각 `nodes` 항목에 노드별 `structured_config`를 추가합니다. IP는 노드마다 고유해야 하므로 `id` 값을 그대로 재사용합니다.

```yaml
      nodes:
        - name: s1-leaf1
          id: 14
          mgmt_ip: 192.168.0.12/24
          uplink_switch_interfaces: [Ethernet2, Ethernet2]
          structured_config:
            loopback_interfaces:
              - name: Loopback210
                description: Monitor-Connectivity-Diag
                vrf: A
                ip_address: 10.255.10.14/32
            virtual_source_nat_vrfs:
              - name: A
                ip_address: 10.255.10.14
        - name: s1-leaf2
          id: 16
          mgmt_ip: 192.168.0.13/24
          structured_config:
            loopback_interfaces:
              - name: Loopback210
                description: Monitor-Connectivity-Diag
                vrf: A
                ip_address: 10.255.10.16/32
            virtual_source_nat_vrfs:
              - name: A
                ip_address: 10.255.10.16
          uplink_switch_interfaces: [Ethernet3, Ethernet3]
```

`loopback_interfaces`는 이 장비만의 고유 `/32` 주소를 담을 그릇을 만들고, `virtual_source_nat_vrfs`는 "VRF `A`에서 로컬 발신 트래픽이 anycast VIP 대신 이 주소를 쓰게 하라"고 지시합니다(`ip address virtual source-nat vrf A address 10.255.10.14`로 렌더링됩니다). 두 설정은 항상 짝으로 다닙니다 — Loopback이 주소의 실체를 만들고, source-nat가 그 주소를 실제로 쓰게 만드는 역할입니다.

`sites/dc2/group_vars/dc2_fabric.yml`의 `LeafPair2`(`s2-leaf3`/`s2-leaf4`)에도 동일하게 적용합니다(예: `10.255.10.115`, `10.255.10.117`).

### 2) `monitor_connectivity` 구성 — 전용 소스 주소를 프로브에 바인딩

`LeafPair1`(dc1) 블록에 주석 처리된 `structured_config`(그룹 레벨)의 주석을 해제하고, 아래처럼 `interface_sets`와 `local_interfaces`를 포함해 작성합니다.

```yaml
    - group: LeafPair1
      filter:
        tenants: [ATD_DC, New-Tenant]
        tags: ['DC']
      bgp_as: 65001
      structured_config:
        monitor_connectivity:
          shutdown: false
          interval: 5
          vrfs:
            - name: A
              interface_sets:
                - name: MONITOR-DIAG
                  interfaces: Loopback210
              hosts:
                - name: s2-host2
                  ip: 10.10.10.22
                  local_interfaces: MONITOR-DIAG
      nodes:
        ...
```

`interval: 5`는 5초마다 ICMP 프로브를 보낸다는 뜻입니다. `interface_sets`는 1)에서 만든 `Loopback210`을 `MONITOR-DIAG`라는 이름으로 묶고, `hosts[].local_interfaces: MONITOR-DIAG`가 이 프로브의 소스를 그 이름으로 지정합니다. `name: s2-host2`는 `show monitor connectivity`에 표시되는 라벨일 뿐 실제 장비 이름과 무관해도 되지만, 여기서는 알아보기 쉽도록 대상 호스트명과 맞췄습니다.

> `interface_sets`는 반드시 `vrf A` 블록 **안에** 넣습니다(`monitor_connectivity` 최상위가 아닙니다) — EOS가 실제로 렌더링하는 CLI 구조가 아래와 같기 때문입니다.
>
> ```
> monitor connectivity
>    interval 5
>    no shutdown
>    !
>    vrf A
>       interface set MONITOR-DIAG Loopback210
>       !
>       host s2-host2
>          local-interfaces MONITOR-DIAG address-only
>          ip 10.10.10.22
> !
> ```

`sites/dc2/group_vars/dc2_fabric.yml`의 `LeafPair2`도 동일한 패턴으로 작성합니다(대상은 `s1-host1`/`10.10.10.11`, `interface_sets`는 `Loopback210` 그대로).

### 3) 빌드 · 배포 · 검증

1) `make build_dc1`, `make build_dc2`로 structured config와 장비 config를 생성합니다. `sites/dc{n}/intended/configs/s{n}-leaf{1,3}.cfg`(및 짝 leaf)에 `interface Loopback210`, `ip address virtual source-nat vrf A address ...`, 위 `monitor connectivity` 블록 세 가지가 모두 들어갔는지 확인합니다.

2) `make deploy_dc1_eapi`와 `make deploy_dc2_eapi`(또는 `make deploy_dc1_cvp`/`make deploy_dc2_cvp` + change control 승인)로 배포합니다 — 두 DC의 leaf pair 설정이 모두 바뀌므로 두 DC 다 배포합니다.

3) leaf 스위치에서 상태를 확인합니다.

```
show monitor connectivity
show monitor connectivity host s2-host2   ! s1-leaf1/s1-leaf2에서
show monitor connectivity host s1-host1   ! s2-leaf3/s2-leaf4에서
```

```
VRF: A
Host: s2-host2
Network statistics:
IP Address  Local Interface   Latency   Jitter Packet Loss Probe Error
----------- --------------- --------- -------- ----------- -----------
10.10.10.22 Loopback210     13.979 ms 0.612 ms          0% n/a
```

`Local Interface`가 `Loopback210`, `Packet Loss`가 `0%`로 나오면 성공입니다. `s2-leaf3`/`s2-leaf4`에서 `show monitor connectivity host s1-host1`도 동일하게 `0%`가 나와야 합니다.

4) (선택) 필요하면 `hosts` 목록에 VLAN 20/100/200 IP도 같은 방식으로 추가해 다른 VRF까지 모니터링을 확장할 수 있습니다. 다만 VLAN 100/200은 fabric 쪽 VRF 이름이 `A`가 아니라 `100`/`200`(Lab 4에서 만든 tenant `New-Tenant`)이므로, `vrfs` 리스트에 `name: "100"`, `name: "200"` 항목을 각각 추가하고, 1)·2)의 Loopback/source-nat/interface_sets도 VRF별로 반복해야 합니다.
