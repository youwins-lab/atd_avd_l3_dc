# EVPN VXLAN 랩

이 랩들의 목표는 AVD가 Day 2 이후의 네트워크 운영을 얼마나 쉽게 만들어주는지 보여주는 것입니다. 아래 네 개의 랩을 진행합니다.

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


## Lab 2 - Border Leaf(EVPN Gateway) 추가로 DCI 연동

저장소를 처음 clone한 상태의 dc1/dc2는 각각 **독립된 단일 데이터센터 EVPN/VXLAN 패브릭**으로만 빌드됩니다. Border Leaf(`s{n}-brdr1`/`s{n}-brdr2`) 관련 설정이 아래 세 파일에 주석(`#`) 처리되어 있기 때문입니다.

- `sites/dc{n}/inventory.yml` — `s{n}-brdr1`/`s{n}-brdr2` 인벤토리 항목
- `sites/dc{n}/group_vars/dc{n}_fabric.yml` — `l3leaf.node_groups` 아래 `BrdrLeafs` 블록
- `sites/dc{n}/group_vars/dc{n}_fabric.yml` — 파일 하단 `core_interfaces` 섹션(Border Leaf ↔ DCI core 라우터 P2P 링크)

Border Leaf는 EVPN Gateway 역할을 하며 dc1/dc2 각각의 독립된 EVPN 도메인을 서로 재발신(re-origination)해 연결하는 지점입니다. 즉 이 랩을 완료해야 두 데이터센터가 `multi-domain-evpn-vxlan-guide.md`에서 설명하는 것처럼 하나의 스트레치된 VXLAN처럼 동작하기 시작합니다. dc1은 이미 DCI 정적 설정(`sites/dc1/dci_configs/`)이 `make deploy_dc1_dci`로 배포되어 있다고 가정합니다(README 초기 구축 순서 1~2단계 참고).

1) `sites/dc1/inventory.yml`을 열어 `dc1_leafs` 그룹 아래 주석 처리된 `s1-brdr1`/`s1-brdr2` 항목의 주석을 해제합니다.

```yaml
            s1-leaf4:
              ansible_host: 192.168.0.15
            s1-brdr1:
              ansible_host: 192.168.0.100
            s1-brdr2:
              ansible_host: 192.168.0.101
```

2) `sites/dc1/group_vars/dc1_fabric.yml`을 열어 `l3leaf.node_groups` 맨 위, 주석 처리된 `BrdrLeafs` 블록 전체의 주석을 해제합니다.

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
      evpn_gateway:
        evpn_l2:
          enabled: true
        remote_peers:
          - hostname: s2-brdr1
            ip_address: 10.1.0.102
            bgp_as: 65199
          - hostname: s2-brdr2
            ip_address: 10.1.0.104
            bgp_as: 65199
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

4) dc2도 동일한 방식으로 진행합니다: `sites/dc2/inventory.yml`의 `s2-brdr1`/`s2-brdr2`, `sites/dc2/group_vars/dc2_fabric.yml`의 `BrdrLeafs` 블록과 `core_interfaces` 섹션 주석을 해제합니다. `bgp_as`(65199), `id`(102/104), `mgmt_ip`(.200/.201), `remote_peers`(`s1-brdr1`/`s1-brdr2` 대상)는 dc1과 대칭이므로 값이 다른 점에 유의하세요 — dc1의 값을 그대로 복사하지 말고 파일에 이미 채워진 값을 그대로 사용하면 됩니다(주석만 해제).

주석을 모두 해제하고 저장한 뒤, 아래 단계를 진행하세요:

1) `make build_dc1`과 `make build_dc2`를 실행하여 새 structured config와 장비 config를 생성합니다. `s{n}-brdr1.cfg`/`s{n}-brdr2.cfg`가 새로 생성되고, `s{n}-spine1.cfg`/`s{n}-spine2.cfg`에 Border Leaf 방향 BGP 네이버·인터페이스가 추가됩니다.

2) 각 디렉토리의 설정을 검토하여 변경 사항이 올바른지 확인합니다.

3) 자동으로 생성된 문서의 변경 내용을 검토합니다.

4) `make deploy_dc1_cvp`와 `make deploy_dc2_cvp`를 실행하고, CVP에 생성된 change control을 검토한 뒤 승인합니다.

5) Border Leaf 스위치에 로그인해 EVPN Gateway BGP 세션이 정상적으로 올라오는지 확인합니다(`show bgp evpn summary` 등). DCI가 이미 배포되어 있다면 `s1-host1`에서 `s2-host1`로 핑이 되는지 확인해 EVPN/VXLAN 스트레치를 검증합니다.

<br>
<br>


## Lab 3 - 새 Tenant(New-Tenant) 추가, VLAN별 전용 VRF

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


## Lab 4 - AVD로 Connectivity Monitoring 설정 (s1-host1 ↔ s2-host2)

지금까지의 랩은 사람이 직접 `ping`을 실행해서 EVPN/VXLAN 스트레치를 검증했습니다. 이 랩에서는 EOS의 **Connectivity Monitor** 기능(`monitor connectivity`)을 AVD로 구성해, leaf 스위치가 원격 호스트를 주기적으로 자동 프로빙(ICMP)하고 그 결과를 `show monitor connectivity` 등으로 상시 확인할 수 있게 만듭니다. AVD 6.3.0 스키마의 `monitor_connectivity` 키(`eos_designs`/`eos_cli_config_gen` 모두 지원)를 `structured_config`로 얹는 방식입니다.

> **모니터링 대상**: `s1-host1`(dc1, `10.10.10.11`)과 `s2-host2`(dc2, `10.10.10.22`)를 서로 반대쪽 DC에서 감시하도록 구성합니다 — dc1의 `LeafPair1`(`s1-leaf1`/`s1-leaf2`, 원래 `s1-host1`이 붙어 있는 leaf pair)이 `s2-host2`를, dc2의 `LeafPair2`(`s2-leaf3`/`s2-leaf4`, 원래 `s2-host2`가 붙어 있는 leaf pair)가 `s1-host1`을 서로 감시합니다. 이렇게 하면 두 leaf pair가 "내 로컬 호스트는 정상인데, 상대편 DC의 호스트까지 도달 가능한가"를 지속적으로 확인하는 구조가 됩니다.
>
> **VRF 이름 주의**: Lab 3에서 호스트 장비 자체에는 VLAN 10 전용 로컬 VRF `10`을 만들었지만, 이건 호스트에만 있는 로컬 구성입니다. **leaf/fabric 쪽에서 VLAN 10을 실어나르는 VRF는 여전히 `A`**입니다(Lab 3에서 fabric 쪽은 손대지 않기로 했으므로). 그래서 아래 `monitor_connectivity` 설정은 `vrfs: - name: A`를 사용합니다 — leaf 입장에서는 VLAN 10이 속한 VRF가 `A`이기 때문입니다.

1) `sites/dc1/group_vars/dc1_fabric.yml`을 열어 `LeafPair1` 블록 안에 주석 처리된 `structured_config` 블록을 찾아 주석을 해제합니다.

```yaml
    - group: LeafPair1
      filter:
        tenants: [ATD_DC]
        tags: ['DC']
      bgp_as: 65001
      structured_config:
        monitor_connectivity:
          interval: 5
          vrfs:
            - name: A
              hosts:
                - name: s2-host2
                  ip: 10.10.10.22
      nodes:
        ...
```

2) `sites/dc2/group_vars/dc2_fabric.yml`을 열어 `LeafPair2` 블록 안에 주석 처리된 `structured_config` 블록의 주석을 해제합니다.

```yaml
    - group: LeafPair2
      filter:
        tenants: [ATD_DC]
        tags: ['DC']
      bgp_as: 65102
      structured_config:
        monitor_connectivity:
          interval: 5
          vrfs:
            - name: A
              hosts:
                - name: s1-host1
                  ip: 10.10.10.11
      nodes:
        ...
```

`interval: 5`는 5초마다 ICMP 프로브를 보낸다는 뜻입니다(값을 넣지 않으면 EOS 기본값을 사용합니다). `hosts`는 VRF `A` 안에서 프로빙할 대상 목록이며, `name`은 `show monitor connectivity`에 표시되는 라벨일 뿐 실제 장비 이름과 무관해도 되지만, 여기서는 어떤 호스트를 보는지 바로 알 수 있도록 대상 호스트명과 맞췄습니다.

주석을 해제하고 저장한 뒤, 아래 단계를 진행하세요:

1) `make build_dc1`과 `make build_dc2`를 실행하여 새 structured config와 장비 config를 생성합니다.

2) `sites/dc1/intended/configs/s1-leaf1.cfg`(및 `s1-leaf2.cfg`)에 아래와 같은 블록이 추가되었는지 확인합니다.

```
monitor connectivity
   interval 5
   !
   vrf A
      !
      host s2-host2
         ip 10.10.10.22
!
```

`sites/dc2/intended/configs/s2-leaf3.cfg`(및 `s2-leaf4.cfg`)에는 대칭으로 `host s1-host1`, `ip 10.10.10.11` 블록이 있어야 합니다.

3) 자동으로 생성된 문서의 변경 내용을 검토합니다.

4) `make deploy_dc1_cvp`와 `make deploy_dc2_cvp`를 실행하고, CVP에 생성된 change control을 검토한 뒤 승인합니다.

5) Lab 2(Border Leaf)까지 완료된 상태라면, leaf 스위치에 로그인해 아래 명령으로 실시간 모니터링 상태를 확인합니다.

```
show monitor connectivity
show monitor connectivity host s2-host2   ! s1-leaf1/s1-leaf2에서
show monitor connectivity host s1-host1   ! s2-leaf3/s2-leaf4에서
```

`Reachable` 상태로 표시되면 EVPN/VXLAN 스트레치를 통해 상대편 DC의 호스트까지 지속적으로 도달 가능하다는 뜻입니다. Lab 2를 아직 하지 않았다면(Border Leaf 미배포) DCI 연결이 없어 `Unreachable`로 표시되는 것이 정상이며, 이 자체가 "모니터링이 실제로 장애를 감지한다"는 걸 보여주는 좋은 예시입니다.

6) (선택) 필요하면 `hosts` 목록에 VLAN 20/100/200 IP도 같은 방식으로 추가해 다른 VRF까지 모니터링을 확장할 수 있습니다. 다만 VLAN 100/200은 fabric 쪽 VRF 이름이 `A`가 아니라 `100`/`200`(Lab 3에서 만든 tenant `New-Tenant`)이므로, `vrfs` 리스트에 `name: "100"`, `name: "200"` 항목을 각각 추가해야 합니다.
