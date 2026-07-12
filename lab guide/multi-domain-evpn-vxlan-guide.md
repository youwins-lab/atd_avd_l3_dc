# Multi-Domain EVPN/VXLAN 아키텍처 가이드

이 문서는 이 저장소가 구현하고 있는 **Multi-Domain EVPN/VXLAN**(독립된 두 데이터센터 패브릭을 EVPN Gateway로 연동하는 설계)을 개념부터 실제 설정, 실제 IP 주소까지 한 번에 이해할 수 있도록 정리한 학습 자료입니다. `README.md`의 설치·배포 가이드와는 별개이며, 실습 과제는 `lab guide/evpn-vxlan-labs.md`에 따로 있습니다.

> **참고**: 이 문서는 Lab 2까지 완료한 **완성된 토폴로지**를 기준으로 설명합니다. 저장소를 처음 clone한 시점에는 dc1/dc2 모두 `LeafPair1`/`LeafPair2`(4-leaf)까지는 정상 빌드되지만, Border Leaf(`s{n}-brdr1`/`s{n}-brdr2`)와 DCI core 라우터로 향하는 `core_interfaces`가 `sites/dc{n}/inventory.yml`/`dc{n}_fabric.yml`에 주석 처리되어 있어 dc1과 dc2가 완전히 **독립된 단일 데이터센터 EVPN/VXLAN 패브릭**으로만 동작합니다. `lab guide/evpn-vxlan-labs.md`의 Lab 2(Border Leaf 추가)를 완료해야 아래 설명대로 EVPN Gateway를 통한 multi-domain 스트레치가 동작합니다. Lab 3(새 tenant `New-Tenant`, VLAN 100/200 추가)은 이 문서의 범위 밖입니다.

<br>

## 1. Multi-Domain EVPN/VXLAN이란

EVPN/VXLAN 패브릭을 여러 데이터센터로 확장하는 방법은 크게 두 가지입니다.

- **단일(Flat) 패브릭**: DC1과 DC2의 모든 spine/leaf가 하나의 언더레이, 하나의 컨트롤 플레인(동일한 Route-Reflector/BGP 정책)을 공유하는 방식입니다. 구성은 단순하지만, 한쪽 DC의 언더레이 장애나 컨트롤 플레인 이슈(경로 flapping, MAC 이동 등)가 다른 DC로 그대로 전파됩니다. 두 DC를 하나의 IGP/BGP 도메인으로 묶어야 하니 확장성과 장애 격리(blast radius) 측면에서도 불리합니다.
- **Multi-Domain(Multi-Fabric) 설계** — 이 저장소가 택한 방식입니다. DC1과 DC2를 **완전히 독립된 EVPN/VXLAN 도메인**으로 구성합니다. 각 도메인은 자신만의 언더레이 BGP AS 대역과 Route-Distinguisher/Loopback 대역을 가지며, 서로 상대방의 spine/leaf를 전혀 알지 못합니다. 두 도메인은 **Border Leaf(`s1-brdr*`, `s2-brdr*`)에 구성된 EVPN Gateway**를 통해서만 연동됩니다. 이 방식은 다음과 같은 장점이 있습니다.
  - **장애 격리**: DC1 언더레이가 재수렴(reconverge)해도 DC2 컨트롤 플레인에는 영향이 없습니다.
  - **루프 방지 경계**: Border Leaf가 EVPN 경로를 도메인 간에 **재생성(re-origination)**하면서 `domain_remote` 표시를 남기므로, DC2에서 배운 경로가 다시 DC2로 되돌아가는 루프가 원천적으로 차단됩니다.
  - **독립적인 주소/VNI 설계**: 두 도메인이 반드시 같은 VLAN ID나 VNI를 쓸 필요가 없습니다. 이 랩에서는 학습 편의상 두 DC가 동일한 VLAN 10/20, 동일한 서브넷을 쓰도록 맞춰 놓았을 뿐입니다(§7 참고).
  - **DCI 구간은 오버레이가 아닌 순수 IP 트랜짓**: `s1-core*`/`s2-core*`는 VXLAN을 전혀 모르는 일반 IP 라우터로, Border Leaf의 Loopback을 서로 도달 가능하게 해주는 역할만 합니다.

<br>

## 2. 전체 토폴로지 (IP 포함)

> 아래 다이어그램은 텍스트(ASCII)로만 그려서 VS Code 기본 미리보기, GitHub, 터미널 어디서든 별도 확장 없이 동일하게 보입니다. 정확한 IP는 다이어그램이 아니라 §3~§8의 표를 기준으로 확인하세요.

**전체 흐름 요약**

```
[s1-host1/2] == s1-leaf1~4 == s1-spine1/2 == s1-brdr1/2  <== EVPN Gateway ==>  s2-brdr1/2 == s2-spine1/2 == s2-leaf1~4 == [s2-host1/2]
                 DC1 도메인 (AS 65000번대)                 |                    |                 DC2 도메인 (AS 65100번대)
                                                            v                    v
                                                     s1-core1/2 == DCI WAN ==> s2-core1/2
                                                       (AS 65501)                (AS 65502)
                                                     순수 IP 언더레이 구간 — VXLAN/EVPN을 전혀 인지하지 않음
```

**DC1 내부 구조** (언더레이 AS 65000)

```
                s1-spine1                                s1-spine2
             AS65000  Lo0 10.1.0.10               AS65000  Lo0 10.1.0.12
                    \                                     /
                     \___  P2P 언더레이 10.255.0.0/22  ___/
                      |  (스파인 2대 - leaf/brdr 6대, 풀메시)  |
        +--------------+--------------+--------------+--------------+--------------+
        |              |              |              |              |              |
   s1-leaf1        s1-leaf2       s1-leaf3       s1-leaf4       s1-brdr1       s1-brdr2
   AS65001         AS65001        AS65002        AS65002        AS65099        AS65099
   Lo0 .14         Lo0 .16        Lo0 .15        Lo0 .17        Lo0 .2         Lo0 .4
   Lo1 .14 <--MLAG--> Lo1 .14     Lo1 .15 <--MLAG--> Lo1 .15    Lo1 .2 <--MLAG--> Lo1 .2
   (LeafPair1, 192.0.0.26/.27)    (LeafPair2, 192.0.0.28/.29)   (BrdrLeafs, 192.0.0.2/.3, EVPN GW)
        |              |              |              |              |
    Po1 trunk      Po1 trunk      Po1 trunk      Po1 trunk       172.16.255.0~.7/31
    10,20 (LACP)   10,20 (LACP)   10,20 (LACP)   10,20 (LACP)    -> DCI 백본 (아래 참고)
        |              |              |              |
     s1-host1 -------- +           s1-host2 -------- +
   10.10.10.11/10.20.20.11       10.10.10.12/10.20.20.12
```

**DCI 백본** (VXLAN을 모르는 순수 IP 트랜짓 — core1 레인 / core2 레인)

```
        core1 레인                                    core2 레인
        ----------                                    ----------
        s1-core1  AS65501                             s1-core2  AS65501
        172.16.255.1  <- s1-brdr1                      172.16.255.3  <- s1-brdr1
        172.16.255.5  <- s1-brdr2                       172.16.255.7  <- s1-brdr2
             |  <---- iBGP PO16 172.17.0.0/31 (DC1 core1<->core2) ---->  |
             |                                                          |
             |  DCI WAN 1.1.1.0/31                DCI WAN 2.2.2.0/31    |
             v                                                          v
        s2-core1  AS65502                             s2-core2  AS65502
        172.16.255.129 <- s2-brdr1                     172.16.255.131 <- s2-brdr1
        172.16.255.133 <- s2-brdr2                      172.16.255.135 <- s2-brdr2
             |  <---- iBGP PO16 172.17.10.0/31 (DC2 core1<->core2) ---->  |
```

**DC2 내부 구조** (언더레이 AS 65100) — DCI 백본과 만나는 Border Leaf를 위쪽에 배치

```
   s2-core1/2 (위 DCI 백본) -> 172.16.255.128~.135/31
        |              |              |              |              |
   s2-brdr1       s2-brdr2       s2-leaf1       s2-leaf2       s2-leaf3       s2-leaf4
   AS65199        AS65199        AS65101        AS65101        AS65102        AS65102
   Lo0 .102       Lo0 .104       Lo0 .114       Lo0 .116       Lo0 .115       Lo0 .117
   Lo1 .102 <--MLAG--> Lo1 .102  Lo1 .114 <--MLAG--> Lo1 .114  Lo1 .115 <--MLAG--> Lo1 .115
   (BrdrLeafs, 192.0.0.202/.203, EVPN GW)  (LeafPair1, 192.0.0.226/.227)  (LeafPair2, 192.0.0.228/.229)
        |                              |              |              |              |
        |                          Po1 trunk      Po1 trunk      Po1 trunk      Po1 trunk
        |                          10,20 (LACP)   10,20 (LACP)   10,20 (LACP)   10,20 (LACP)
        |                              |              |              |              |
        |                           s2-host1 -------- +           s2-host2 -------- +
        |                         10.10.10.21/10.20.20.21        10.10.10.22/10.20.20.22
        |
        |___  P2P 언더레이 10.255.1.0/22 (스파인 2대 - leaf/brdr 6대, 풀메시)  ___
                     \                                     /
             s2-spine1                                s2-spine2
          AS65100  Lo0 10.1.0.110                  AS65100  Lo0 10.1.0.112
```

**범례**: 실선/`+`/`|` = 물리 링크(P2P 언더레이 eBGP), `<--MLAG-->` = MLAG 피어 링크, `<---- iBGP ---->` = 코어 내부 iBGP(PO16), `== DCI WAN ==>` = 코어 간 DCI WAN 링크입니다. Border Leaf(`s1-brdr*`, `s2-brdr*`)와 반대편 Border Leaf 사이의 **EVPN Gateway eBGP EVPN 세션**(§6)은 물리 링크가 아니라 Loopback0끼리 DCI 백본을 거쳐 논리적으로 맺어지는 세션이라 이 그림에는 표시하지 않았습니다.

<br>

## 3. 도메인별 언더레이/오버레이 설계

두 도메인은 `sites/dc1/group_vars/dc1_fabric.yml`과 `sites/dc2/group_vars/dc2_fabric.yml`에 거의 대칭적인 구조로 정의되어 있지만, **AS 대역만큼은 서로 다르게** 잡혀 있습니다.

| 항목 | DC1 (`dc1_fabric.yml`) | DC2 (`dc2_fabric.yml`) |
| --- | --- | --- |
| 언더레이/오버레이 프로토콜 | eBGP / eBGP (`dc1_fabric.yml:4-5`) | eBGP / eBGP (`dc2_fabric.yml:4-5`) |
| Spine AS | 65000 (`dc1_fabric.yml:34`) | 65100 (`dc2_fabric.yml:31`) |
| LeafPair1 AS | 65001 (`dc1_fabric.yml:148`) | 65101 (`dc2_fabric.yml:145`) |
| LeafPair2 AS | 65002 (`dc1_fabric.yml:166`) | 65102 (`dc2_fabric.yml:163`) |
| Border Leaf AS | 65099 (`dc1_fabric.yml:94`) | 65199 (`dc2_fabric.yml:91`) |
| Loopback0 대역 (Router-ID) | `10.1.0.0/24` (`dc1_fabric.yml:35,56`) | `10.1.0.0/24` (`dc2_fabric.yml:32,53`) |
| Loopback1 대역 (VTEP source) | `10.1.1.0/24` (`dc1_fabric.yml:57`) | `10.1.1.0/24` (`dc2_fabric.yml:54`) |
| Uplink P2P 대역 | `10.255.0.0/22` (`dc1_fabric.yml:60`) | `10.255.0.0/22` (`dc2_fabric.yml:57`, 실제 배정은 `10.255.1.0/24`대) |
| MLAG L2 피어 대역 | `192.0.0.0/24` (`dc1_fabric.yml:62`) | `192.0.0.0/24` (`dc2_fabric.yml:59`) |
| MLAG L3(언더레이) 대역 | `192.1.1.0/24` (`dc1_fabric.yml:63`) | `192.1.1.0/24` (`dc2_fabric.yml:60`) |
| MLAG iBGP(VRF A) 대역 | `192.2.2.0/23` (`dc1_fabric_services.yml:11`) | `192.2.2.0/23` (`dc2_fabric_services.yml:11`) |

> Loopback/MLAG 대역 값 자체는 두 파일에 동일하게 적혀 있지만(`10.1.0.0/24` 등), 각 도메인의 스위치는 서로 다른 `id:`(예: DC1 leaf는 14~17, DC2 leaf는 114~117)를 쓰므로 AVD가 풀에서 실제로 배정하는 IP는 겹치지 않습니다. 아래 §4의 실제 배정 결과를 보면 확인할 수 있습니다.

각 스위치의 `id:` 값(`dc1_fabric.yml:44,47,107,124,151,155,169,173` / `dc2_fabric.yml:41,44,104,121,148,152,166,170`)이 Loopback/MLAG 풀에서 실제 옥텟을 결정하는 키입니다. spine의 `uplink_switch_interfaces:`는 leaf/brdr 쪽에서 spine으로 향하는 물리 포트를 지정합니다.

<br>

## 4. 노드별 실제 주소 (빌드 결과)

`make build_dc1` / `make build_dc2`가 실행하는 `arista.avd.eos_designs` + `arista.avd.eos_cli_config_gen`이 §3의 풀/정책을 기반으로 실제 배정한 주소입니다(`sites/dc{n}/intended/structured_configs/*.yml` 기준).

### DC1

| 장비 | Mgmt IP | AS | Loopback0 (Router-ID) | Loopback1 (VTEP) |
| --- | --- | --- | --- | --- |
| s1-spine1 | 192.168.0.10 | 65000 | 10.1.0.10/32 | — |
| s1-spine2 | 192.168.0.11 | 65000 | 10.1.0.12/32 | — |
| s1-leaf1 | 192.168.0.12 | 65001 | 10.1.0.14/32 | 10.1.1.14/32 |
| s1-leaf2 | 192.168.0.13 | 65001 | 10.1.0.16/32 | 10.1.1.14/32 |
| s1-leaf3 | 192.168.0.14 | 65002 | 10.1.0.15/32 | 10.1.1.15/32 |
| s1-leaf4 | 192.168.0.15 | 65002 | 10.1.0.17/32 | 10.1.1.15/32 |
| s1-brdr1 | 192.168.0.100 | 65099 | 10.1.0.2/32 | 10.1.1.2/32 |
| s1-brdr2 | 192.168.0.101 | 65099 | 10.1.0.4/32 | 10.1.1.2/32 |

### DC2

| 장비 | Mgmt IP | AS | Loopback0 (Router-ID) | Loopback1 (VTEP) |
| --- | --- | --- | --- | --- |
| s2-spine1 | 192.168.0.20 | 65100 | 10.1.0.110/32 | — |
| s2-spine2 | 192.168.0.21 | 65100 | 10.1.0.112/32 | — |
| s2-leaf1 | 192.168.0.22 | 65101 | 10.1.0.114/32 | 10.1.1.114/32 |
| s2-leaf2 | 192.168.0.23 | 65101 | 10.1.0.116/32 | 10.1.1.114/32 |
| s2-leaf3 | 192.168.0.24 | 65102 | 10.1.0.115/32 | 10.1.1.115/32 |
| s2-leaf4 | 192.168.0.25 | 65102 | 10.1.0.117/32 | 10.1.1.115/32 |
| s2-brdr1 | 192.168.0.200 | 65199 | 10.1.0.102/32 | 10.1.1.102/32 |
| s2-brdr2 | 192.168.0.201 | 65199 | 10.1.0.104/32 | 10.1.1.102/32 |

같은 leaf pair(`s1-leaf1`/`s1-leaf2`, `s1-brdr1`/`s1-brdr2` 등)는 **Loopback1(VTEP)을 공유**합니다 — MLAG 페어가 EVPN 관점에서 하나의 논리적 VTEP(anycast VTEP)로 동작하기 때문입니다. 반면 Loopback0(BGP Router-ID)는 각자 고유합니다.

<br>

## 5. DCI 백본 — 순수 IP 트랜짓 구간

`s1-core1/2`, `s2-core1/2`는 `eos_designs`/`eos_cli_config_gen`으로 빌드되지 않는 **비-AVD 장비**입니다. 정적 설정은 `sites/dc{n}/dci_configs/*.cfg`에 있고, `make deploy_dc{n}_dci*`로 배포합니다. Border Leaf 쪽 P2P 링크 정의는 `dc1_fabric.yml:180-207` / `dc2_fabric.yml:177-204`의 `core_interfaces.p2p_links`에 있으며, `include_in_underlay_protocol: false`로 설정되어 있어 **이 링크들은 AVD 언더레이 라우팅 프로토콜에 자동으로 포함되지 않습니다.** core 장비는 별도의 정적 BGP 설정으로 직접 관리합니다.

| 링크 | 대역 | AS |
| --- | --- | --- |
| s1-brdr1 ↔ s1-core1 | `172.16.255.0/31` | 65099 ↔ 65501 |
| s1-brdr1 ↔ s1-core2 | `172.16.255.2/31` | 65099 ↔ 65501 |
| s1-brdr2 ↔ s1-core1 | `172.16.255.4/31` | 65099 ↔ 65501 |
| s1-brdr2 ↔ s1-core2 | `172.16.255.6/31` | 65099 ↔ 65501 |
| s1-core1 ↔ s1-core2 (내부 iBGP, PO16) | `172.17.0.0/31` | 65501 (iBGP) |
| **s1-core1 ↔ s2-core1 (DCI WAN)** | `1.1.1.0/31` | 65501 ↔ 65502 |
| **s1-core2 ↔ s2-core2 (DCI WAN)** | `2.2.2.0/31` | 65501 ↔ 65502 |
| s2-core1 ↔ s2-core2 (내부 iBGP, PO16) | `172.17.10.0/31` | 65502 (iBGP) |
| s2-brdr1 ↔ s2-core1 | `172.16.255.128/31` | 65199 ↔ 65502 |
| s2-brdr1 ↔ s2-core2 | `172.16.255.130/31` | 65199 ↔ 65502 |
| s2-brdr2 ↔ s2-core1 | `172.16.255.132/31` | 65199 ↔ 65502 |
| s2-brdr2 ↔ s2-core2 | `172.16.255.134/31` | 65199 ↔ 65502 |

core 장비는 IPv4 유니캐스트(`address-family ipv4`)만 활성화하고 VXLAN/EVPN은 전혀 설정하지 않습니다. 이들이 실제로 라우팅하는 대상은 Border Leaf의 Loopback0/Loopback1뿐이며, 역할은 **DC1의 Border Leaf가 DC2의 Border Leaf Loopback에 IP 레벨로 도달할 수 있게 해주는 것**이 전부입니다. VXLAN 캡슐화와 EVPN 경로 교환은 이 IP 도달성 위에서 Border Leaf끼리 직접 처리합니다(§6).

<br>

## 6. 도메인 간 연동 — EVPN Gateway

Border Leaf 노드 그룹에만 아래 설정이 들어 있습니다(`dc1_fabric.yml:95-104`, DC2도 대칭적으로 `dc2_fabric.yml:92-101`).

```yaml
# dc1_fabric.yml
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
```

이 설정으로 일어나는 일은 세 가지입니다.

1. `s1-brdr1`/`s1-brdr2`가 `s2-brdr1`(10.1.0.102)·`s2-brdr2`(10.1.0.104)의 Loopback0으로 **직접 eBGP EVPN 세션**을 맺습니다(`EVPN-OVERLAY-REMOTE-PEERS` 피어 그룹, `ebgp_multihop 15`). spine·core를 여러 홉 거쳐야 하므로 로컬 피어에 쓰는 `ebgp_multihop 3`보다 훨씬 큰 값을 씁니다. Spine과 core는 이 세션에 전혀 관여하지 않고, 두 Loopback 사이의 IP 패킷을 라우팅해줄 뿐입니다.
2. `evpn_l2.enabled: true`로 Border Leaf가 **EVPN Gateway**로 동작합니다. DC1에서 배운 MAC/IP(Type-2)·IMET(Type-3) 경로를 그대로 전달하는 대신, **자신의 Loopback1(VTEP)을 새 next-hop으로 삼아 다시 생성(re-origination)**해서 DC2로 광고합니다. 그 결과 DC2 leaf가 보는 "원격 VTEP"은 항상 `s1-brdr1`/`s1-brdr2`의 Loopback1(10.1.1.2)이고, DC1의 실제 leaf(`s1-leaf1` 등) VTEP IP는 DC2에 노출되지 않습니다. 두 도메인 사이의 VTEP·캡슐화 세부 사항을 완전히 감춰주는 **stitching(스티칭) 경계**가 만들어지는 셈입니다.
3. `router_bgp.address_family_evpn.peer_groups`에서 `EVPN-OVERLAY-REMOTE-PEERS`가 `domain_remote: true`로 활성화됩니다(구조화된 설정 기준). 이 표시 덕분에 원격 도메인에서 배운 경로에 도메인 정보가 남고, 같은 경로가 다시 원래 도메인으로 되돌아가 루프를 만드는 상황을 막을 수 있습니다.

정리하면 Border Leaf는 언더레이 관점에서는 그냥 자기 도메인의 leaf지만, 오버레이 관점에서는 EVPN 경로의 next-hop을 자신으로 바꿔서 전달하는 게이트웨이 역할을 겸합니다.

<br>

## 7. 테넌트/VXLAN 서비스 설계

`dc1_fabric_services.yml:4-26`에서 정의하며, DC2의 `dc2_fabric_services.yml`도 완전히 동일한 값을 씁니다.

```yaml
tenants:
  - name: ATD_DC
    mac_vrf_vni_base: 10000        # VNI = 10000 + VLAN ID
    vrfs:
      - name: A
        vrf_vni: 50001
        svis:
          - id: 10
            ip_address_virtual: 10.10.10.1/24   # 모든 leaf/brdr에서 동일 (anycast gateway)
          - id: 20
            ip_address_virtual: 10.20.20.1/24
```

| VLAN | VNI (`mac_vrf_vni_base` + id) | 서브넷 | Anycast Gateway |
| --- | --- | --- | --- |
| 10 (`ten`) | 10010 | `10.10.10.0/24` | `10.10.10.1` (DC1·DC2 leaf/brdr 전체 동일) |
| 20 (`twenty`) | 10020 | `10.20.20.0/24` | `10.20.20.1` (DC1·DC2 leaf/brdr 전체 동일) |

| VRF | VNI | RD/RT 기준 |
| --- | --- | --- |
| A | 50001 | 장비별 `Loopback0:VNI` |

> **참고**: DC1·DC2가 같은 값을 쓰는 건 §1에서 언급했듯 두 DC를 "같은 서브넷을 쓰는 하나의 L2 확장망"처럼 보이게 하려는 **의도된 설계**일 뿐, Multi-Domain 아키텍처의 필수 요건은 아닙니다. 실무에서는 도메인별로 VNI/RD를 다르게 가져가고, Border Leaf에서 필요한 서비스만 선택적으로 스티칭하는 것도 얼마든지 가능합니다.

<br>

## 8. 엔드포인트(호스트) 연결

`s{n}-host1/2`는 `eos_designs`가 빌드하지 않는 정적 설정(`sites/dc{n}/host_configs/*.cfg`, `make deploy_dc{n}_host_cvp`)으로 배포하며, leaf pair에 MLAG로 이중 연결됩니다.

| 호스트 | 연결된 Leaf Pair | Vlan10 IP | Vlan20 IP |
| --- | --- | --- | --- |
| s1-host1 | s1-leaf1 / s1-leaf2 | 10.10.10.11/24 | 10.20.20.11/24 |
| s1-host2 | s1-leaf3 / s1-leaf4 | 10.10.10.12/24 | 10.20.20.12/24 |
| s2-host1 | s2-leaf1 / s2-leaf2 | 10.10.10.21/24 | 10.20.20.21/24 |
| s2-host2 | s2-leaf3 / s2-leaf4 | 10.10.10.22/24 | 10.20.20.22/24 |

실제로 `make deploy_dc1_host_cvp`/`make deploy_dc2_host_cvp`를 배포한 뒤 `s1-host1 → s2-host1`, `s1-host2 → s2-host2` 양방향 ping을 Vlan10/Vlan20 모두에서 0% 패킷 손실로 확인했습니다. DC1과 DC2가 서로 다른 언더레이·AS를 쓰는 독립 도메인인데도, EVPN Gateway 스티칭 덕분에 마치 하나의 L2/L3 네트워크처럼 통신되는 것입니다.

> **참고**: 각 호스트의 `vlan10`/`vlan20`/`vlan100`/`vlan200` SVI는 이제 호스트 장비 자체에서 VLAN ID와 동일한 이름의 로컬 VRF(`vrf 10`/`20`/`100`/`200`)에 배치되어 있고, 각 VRF에는 해당 leaf anycast VIP(`10.10.10.1`, `10.20.20.1`, `10.100.100.1`, `10.200.200.1`)를 향하는 기본 경로(`ip route vrf ... 0.0.0.0/0 ...`)가 설정되어 있습니다. 이는 호스트 장비 로컬 라우팅 테이블 구성일 뿐, leaf/fabric 쪽 VRF 설계(VLAN10/20은 여전히 leaf에서 VRF `A`를 공유)와는 별개입니다. 따라서 호스트에서 ping을 테스트할 때는 `ping 10.20.20.21` 처럼 기본 VRF로 실행하면 안 되고, `ping vrf 20 10.20.20.21`처럼 반드시 `vrf` 키워드로 해당 VLAN의 VRF를 지정해야 합니다.

<br>

## 9. 패킷 한 개의 여정 — `s1-host1 → s2-host1` (Vlan10, 10.10.10.11 → 10.10.10.21)

1. **s1-host1**: Vlan10 SVI에서 ARP로 목적지가 같은 서브넷임을 확인하고, 이더넷 프레임을 Port-Channel1(트렁크, VLAN 10)로 전송합니다.
2. **s1-leaf1/s1-leaf2 (MLAG)**: 프레임을 받아 목적지 MAC이 로컬에 없으면 EVPN Type-2(MAC/IP)로 학습해 둔 원격 VTEP을 조회합니다. VXLAN(VNI 10010)으로 캡슐화하고, source는 자신의 Loopback1(10.1.1.14), 목적지 VTEP은 **자신이 배운 원격 next-hop**입니다.
3. **s1-spine1/2**: 언더레이 IP 라우팅만 수행합니다(VXLAN 페이로드는 들여다보지 않음). Loopback1 목적지로 최적 경로를 통해 전달합니다.
4. **s1-brdr1/s1-brdr2 (EVPN Gateway)**: DC1 입장에서는 자신이 VLAN 10의 "원격 VTEP"이었으므로, 여기서 **VXLAN을 종단(de-encap)**한 뒤 DC2로 갈 경로를 조회해 **자신의 Loopback1(10.1.1.2)을 source로 다시 캡슐화(re-encap)**해서 DCI 쪽으로 전달합니다. 이 지점이 두 도메인의 실제 경계입니다.
5. **s1-core1/2 → DCI WAN(1.1.1.0/31 또는 2.2.2.0/31) → s2-core1/2**: 순수 IP 라우팅 구간입니다. VXLAN 헤더는 그대로 통과할 뿐, core는 내용을 전혀 해석하지 않습니다.
6. **s2-brdr1/s2-brdr2 (EVPN Gateway)**: 도착한 VXLAN을 de-encap한 뒤, DC2 도메인 안에서 학습한 경로(Type-2)로 다시 VNI 10010 캡슐화합니다. source는 자신의 Loopback1(10.1.1.102)입니다.
7. **s2-spine1/2**: 언더레이 라우팅만 수행합니다.
8. **s2-leaf1/s2-leaf2 (MLAG)**: VXLAN을 de-encap한 뒤 로컬 VLAN 10으로 브리징합니다.
9. **s2-host1**: 프레임을 받습니다.

같은 서브넷(`10.10.10.0/24`)이지만 실제로는 **VXLAN 캡슐화가 도메인마다 한 번씩, 총 두 번 일어난다**는 점이 Multi-Domain 설계의 핵심입니다. 엔드포인트나 leaf 입장에서는 "하나의 큰 VXLAN"처럼 보이지만, 실제로는 도메인마다 독립된 VTEP 스페이스를 가지고 Border Leaf에서 스티칭되는 구조입니다.

<br>

## 10. ANTA로 배포 상태 검증하기

§8~§9는 사람이 직접 ping으로 확인한 결과였습니다. 이 저장소는 같은 검증을 자동화하는 수단으로 **ANTA**(Arista Network Test Automation)도 함께 포함하고 있습니다.

### ANTA란

ANTA는 EOS 장비의 운영 상태를 자동으로 검증하는 오픈소스 Python 테스트 프레임워크입니다([anta.arista.com](https://anta.arista.com)). AVD는 `arista.avd.anta_runner` 롤로 이를 Ansible과 통합합니다. 이 롤의 가장 큰 특징은, 테스트를 직접 작성하지 않아도 **AVD가 만든 structured config(§4의 출처)를 그대로 읽어서 장비별 테스트 카탈로그를 자동 생성**해준다는 점입니다 — BGP 이웃, 인터페이스 상태, MLAG, VXLAN/VNI 매핑처럼 이 설계에서 실제로 구성한 항목들이 자동으로 테스트 대상이 됩니다. 물론 사용자가 직접 만든 테스트 카탈로그를 추가로 얹는 것도 가능합니다.

### 이 저장소에서 실행되는 위치

- `playbooks/deploy_dc1_eapi.yml`에는 config 배포 뒤에 `arista.avd.anta_runner`를 실행하는 두 번째 play가 이어져 있습니다. 즉 `make deploy_dc1_eapi`를 실행하면 **배포와 검증이 한 번에** 이루어집니다.
- `playbooks/deploy_dc2_eapi.yml`에는 아직 이 검증 play가 없습니다 — DC1에만 구성되어 있고, DC2에 동일하게 추가하는 것은 README에서 언급한 "직접 구현해봐야 할" 부분 중 하나입니다.
- CVP로 배포하는 `deploy_dc{n}_cvp.yml` / `deploy_dc{n}_host_cvp.yml` / `deploy_dc{n}_dci_cvp.yml`에는 ANTA가 포함되어 있지 않습니다. CVP의 change control 성공 여부와 ANTA의 상태 검증은 서로 별개입니다.

### 결과물이 쌓이는 위치

| 경로 | 내용 |
| --- | --- |
| `sites/dc1/anta/avd_catalogs/*.json` | structured config로부터 자동 생성된 장비별 테스트 카탈로그 |
| `sites/dc1/anta/reports/anta_report.json` | 전체 테스트 결과(자동화·CI 파싱용) |
| `sites/dc1/anta/reports/anta_report.csv` | 테스트 결과를 표 형태로(스프레드시트에서 열어보기 좋음) |
| `sites/dc1/anta/reports/anta_report.md` | 사람이 읽기 좋은 요약 리포트 |

### 결과 확인 절차

1. `make deploy_dc1_eapi`를 실행합니다. config 배포 태스크 다음에 "Run ANTA on EOS devices" 태스크가 이어서 실행됩니다.
2. 이 태스크는 **실패나 에러로 판정된 테스트가 하나라도 있으면 자체적으로 실패 처리**됩니다. 콘솔에 출력되는 play recap에서 바로 확인할 수 있으니, 우선 여기서 전체 통과 여부부터 확인하세요.
3. 자세한 내용은 `sites/dc1/anta/reports/anta_report.md`를 엽니다. 다음 세 가지를 순서대로 보면 됩니다.
   - **Summary Totals**: 전체 테스트 중 성공/스킵/실패/에러 개수
   - **Summary Totals Device Under Test**: 장비별 성공/실패 breakdown — 어느 장비에 문제가 있는지 먼저 좁힙니다
   - **Summary Totals Per Category**: BGP/Interfaces/Routing 등 카테고리별 breakdown — 어떤 영역의 문제인지 좁힙니다
   - 이후 **Test Results** 표에서 실패한 개별 테스트를 찾아 `Message(s)` 컬럼을 확인하면, 실제 EOS 출력이나 설정 diff가 함께 기록되어 있어 원인을 바로 알 수 있습니다(예: `VerifyRunningConfigDiffs` 테스트는 running-config와 startup-config의 차이를 그대로 보여줍니다).
4. 특정 장비나 카테고리만 다시 보고 싶다면 `ansible-playbook ... --limit <hostname>`으로 대상을 좁히거나, `anta_runner`의 `avd_catalogs_filters` 변수로 카테고리/테스트를 걸러서 재실행할 수 있습니다.

> 이 저장소에는 이전에 실행된 `sites/dc1/anta/reports/anta_report.md` 예시가 이미 포함되어 있습니다. 다만 이는 특정 시점의 스냅샷이므로, 현재 배포 상태를 확인하려면 `make deploy_dc1_eapi`를 다시 실행해 리포트를 새로 생성하세요.

<br>

## 11. 참고 — 이 설계와 관련 있는 파일

| 파일 | 내용 |
| --- | --- |
| `sites/dc1/group_vars/dc1_fabric.yml`, `sites/dc2/group_vars/dc2_fabric.yml` | 노드 토폴로지, AS, Loopback/MLAG 풀, `evpn_gateway`(§6), `core_interfaces.p2p_links`(§5) |
| `sites/dc1/group_vars/dc1_fabric_services.yml`, `sites/dc2/group_vars/dc2_fabric_services.yml` | 테넌트/VRF/VLAN/VNI (§7) |
| `sites/dc1/group_vars/dc1_fabric_ports.yml`, `sites/dc2/group_vars/dc2_fabric_ports.yml` | leaf가 host 쪽으로 자동 생성하는 포트 설정(§8) |
| `sites/dc{n}/dci_configs/*.cfg` | core 라우터 정적 설정(§5) |
| `sites/dc{n}/host_configs/*.cfg` | host 엔드포인트 정적 설정(§8) |
| `sites/dc{n}/intended/structured_configs/*.yml` | AVD가 실제로 배정한 최종 IP/AS (§4의 출처) |
| `playbooks/deploy_dc1_eapi.yml`, `sites/dc1/anta/` | ANTA 자동 검증 및 결과물(§10) |
