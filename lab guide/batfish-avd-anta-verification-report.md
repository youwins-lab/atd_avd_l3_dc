# Batfish 사전 검증 → AVD 배포 → ANTA 검증 → 호스트 통신 확인: 전체 실행 기록

> 이 문서는 **AVD 6.3.0** 시점의 실행 기록입니다. AVD 6.4.0으로 전환한 뒤 같은 절차(Batfish → 배포 → ANTA →
> 호스트 통신)와 Lab 1~6, §7-A 장애 주입 실습을 다시 수행한 결과는
> [`avd-6.4-upgrade-verification.md`](avd-6.4-upgrade-verification.md)에 있습니다.

`lab guide/batfish-preflight-guide.md`에서 만든 사전 검증 절차를 실제 ATD 랩에 그대로 적용하고,
그 뒤 AVD 배포와 ANTA 검증, 호스트 간 통신까지 한 번에 이어서 실행한 기록입니다.
**아래 로그는 모두 실제 실행 결과이며 편집하지 않았습니다**(길이 문제로 일부 구간은 발췌).

- 실행 일자: 2026-08-22
- 대상: dc1(`s1-*`) + dc2(`s2-*`), 총 24대 (spine 4, leaf 8, border-leaf 4, DCI core 4, host 4)
- 랩 상태: `evpn-vxlan-labs.md`의 **Lab 1~6이 모두 적용된 상태**

| 구성요소 | 버전 |
|---|---|
| Batfish 서비스 | `batfish/allinone:latest` (2025.07.07 빌드) — OpenJDK 17.0.20 위에서 직접 실행 |
| pybatfish | 2025.07.07.2423 |
| AVD | 6.3.0 (`pyavd` 6.3.0, `arista.avd` collection 6.3.0) |
| ANTA | 1.8.0 |
| ansible-core | 2.16.14 |
| EOS | 4.36.0.1F (cEOS-lab) |

## 실행 순서와 결과 요약

| # | 단계 | 명령 | 결과 |
|---|---|---|---|
| 1 | AVD 설정 빌드 | `make build_dc1`, `make build_dc2` | 성공 (16대 설정 재생성, failed=0) |
| 2 | **Batfish 사전 검증** | `make preflight` | **PASS 28 / FAIL 0** |
| 3 | AVD 배포 (DC1) | `make deploy_dc1_eapi` | 설정 push 성공, ANTA에서 **BGP 2건 실패** |
| 4 | 원인 조치 | `make deploy_dc1_dci`, `make deploy_dc2_dci` | DCI core 4대 설정 배포 (changed=1) |
| 5 | AVD 배포 (DC2) | `make deploy_dc2_eapi` | 설정 push 성공 |
| 6 | ANTA 재검증 | `make verify_dc1` | 프로토콜 계열 **전항목 통과** (잔여 실패는 랩 환경 요인) |
| 7 | 호스트 간 통신 | `ping vrf <n> <ip>` 32건 | **성공 28건 + 실패 4건**(VRF 격리, 막히는 것이 정상) — 기대와 결과 전부 일치 |
| 8 | 장애 시나리오 (§10) | Edge에 VTEP 블랙홀 주입 → 복구 | Batfish **탐지**, BGP·ANTA **미탐지**, DC 간 통신 100% 손실 |

<br>

## 1. AVD 설정 빌드

```
$ make build_dc1
...
PLAY RECAP *********************************************************************
s1-brdr1                   : ok=4    changed=0    unreachable=0    failed=0
s1-brdr2                   : ok=4    changed=0    unreachable=0    failed=0
s1-leaf1                   : ok=4    changed=0    unreachable=0    failed=0
s1-leaf2                   : ok=4    changed=0    unreachable=0    failed=0
s1-leaf3                   : ok=4    changed=0    unreachable=0    failed=0
s1-leaf4                   : ok=4    changed=0    unreachable=0    failed=0
s1-spine1                  : ok=12   changed=0    unreachable=0    failed=0   skipped=1
s1-spine2                  : ok=4    changed=0    unreachable=0    failed=0

$ make build_dc2
...
s2-spine1                  : ok=12   changed=0    unreachable=0    failed=0   skipped=1
(이하 동일, failed=0)
```

이 시점에 `sites/dc{1,2}/intended/configs/*.cfg` 16개 파일이 최신 상태가 됩니다. 여기까지는
아직 어떤 장비도 건드리지 않았습니다.

<br>

## 2. Batfish 사전 검증 — 배포 전

`make preflight`는 위에서 생성된 16개 AVD 설정에 더해 DCI core 4대(`dci_configs/`)와
호스트 4대(`host_configs/`)의 정적 설정까지 합쳐 **24개 노드짜리 스냅샷**을 만들고 검증합니다.
장비 접속은 일어나지 않습니다.

```
$ make preflight

스냅샷: /home/coder/project/labfiles/atd_avd_l3_dc/batfish/snapshots/dc1-dc2
노드 24개: s1-brdr1, s1-brdr2, s1-core1, s1-core2, s1-host1, s1-host2, s1-leaf1, s1-leaf2, s1-leaf3, s1-leaf4, s1-spine1, s1-spine2, s2-brdr1, s2-brdr2, s2-core1, s2-core2, s2-host1, s2-host2, s2-leaf1, s2-leaf2, s2-leaf3, s2-leaf4, s2-spine1, s2-spine2

[공통 검사]
  [✔] 설정 파싱                                  24개 파일 모두 ARISTA로 파싱, 노드 24개 (경고 61건은 Batfish 미지원 문법으로 확인됨)
  [✔] 미정의 참조                                 존재하지 않는 ACL/route-map/peer-group/prefix-list 참조 없음
  [✔] 중복 IP                                  설계상 공유 주소(anycast GW 7개, MLAG 공유 VTEP 6개) 외 중복 없음
        10.1.1.115: s2-leaf3/s2-leaf4 공유 VTEP
        10.1.1.102: s2-brdr1/s2-brdr2 공유 VTEP
        10.1.1.114: s2-leaf1/s2-leaf2 공유 VTEP
        10.1.1.14: s1-leaf1/s1-leaf2 공유 VTEP
        10.1.1.2: s1-brdr1/s1-brdr2 공유 VTEP
        10.1.1.15: s1-leaf3/s1-leaf4 공유 VTEP
  [✔] 물리 토폴로지                                L1 링크 58개 / L3 인접 628개, 모든 Ethernet 인터페이스의 대향이 확인됨
  [✔] L3 링크 MTU                              IP가 붙은 모든 P2P 링크의 양단 MTU 일치
  [✔] BGP 세션 호환성                             176개 세션 모두 UNIQUE_MATCH (AS/IP/peer-group 정합)
  [✔] BGP 세션 수립(모델)                          176개 세션 모두 ESTABLISHED (언더레이 도달성까지 성립)
  [✔] VTEP 간 도달성                             VTEP 6개 × 출발 노드 12대 = 72개 조합 모두 도달 가능

[Lab 1 시나리오 검사]
  [✔] VLAN 30/40/50 SVI/게이트웨이                leaf 8대 모두 VLAN 30,40,50 SVI 존재, anycast GW/VRF 양 DC 동일
  [✔] VLAN 30/40/50 VXLAN VNI 매핑             VLAN 30->VNI 10030  VLAN 40->VNI 10040  VLAN 50->VNI 10050

[Lab 2 시나리오 검사]
  [✔] Border Leaf 편입                         Border Leaf 4대 렌더링됨: s1-brdr1, s1-brdr2, s2-brdr1, s2-brdr2
  [✔] Border Leaf ↔ DCI core 언더레이            P2P eBGP 8개 세션 수립 (172.16.255.0/24 대역)
  [✔] Border Leaf 로컬 EVPN 오버레이               spine과 EVPN 세션 8개 수립

[Lab 3 시나리오 검사]
  [✔] EVPN Gateway 원격 피어링                    DC 간 EBGP_MULTIHOP EVPN 세션 8개 수립 (Loopback0 10.1.0.x ↔ 10.1.0.1xx)
  [✔] EVPN 경로 재발신 표시                         'domain remote'가 Border Leaf 4대에만 존재: s1-brdr1, s1-brdr2, s2-brdr1, s2-brdr2
  [✔] VTEP 간 언더레이 도달성                        s1-leaf1(10.1.1.14) → s2-leaf1(10.1.1.114) 경로 32개 ACCEPTED
        s1-leaf1 → s1-spine1 → s1-brdr1 → s1-core1 → s2-core1 → s2-brdr1 → s2-spine1 → s2-leaf1

[Lab 4 시나리오 검사]
  [✔] VLAN 100/200 SVI/게이트웨이                 leaf 8대 모두 VLAN 100,200 SVI 존재, anycast GW/VRF 양 DC 동일
  [✔] VLAN 100/200 VXLAN VNI 매핑              VLAN 100->VNI 20100  VLAN 200->VNI 20200
  [✔] 테넌트 VRF 분리                             leaf 8대에 vrf 100 / vrf 200 인스턴스 존재 (VLAN별 전용 VRF)
  [✔] VRF 100/200 격리                         VRF 100 라우팅 테이블에 VLAN 200 대역(10.200.200.0/24) 경로 없음

[Lab 5 시나리오 검사]
  [✔] DCI core 설정 파싱                         core 4대 파싱/라우팅 모델 정상: s1-core1, s1-core2, s2-core1, s2-core2
  [✔] CVP topology 태그 변수                     cv_device_tags 활성: sites/dc1/group_vars/dc1_dci.yml, sites/dc2/group_vars/dc2_dci.yml (태그 자체는 Batfish 검증 대상이 아님 — CVP 메타데이터)

[Lab 6 시나리오 검사]
  [✔] 프로브 소스 Loopback210                     leaf 4대에 VRF A 전용 /32 고유 주소 구성
        s1-leaf1: 10.255.10.14/32 (vrf A)
        s1-leaf2: 10.255.10.16/32 (vrf A)
        s2-leaf3: 10.255.10.115/32 (vrf A)
        s2-leaf4: 10.255.10.117/32 (vrf A)
  [✔] virtual source-nat 짝 맞춤                4대 모두 Loopback210 + source-nat 쌍 구성
  [✔] 프로브 경로 s1-leaf1 → s2-host2             10.255.10.14 → 10.10.10.22 ACCEPTED
        s1-leaf1 → s2-host2
  [✔] 프로브 경로 s1-leaf2 → s2-host2             10.255.10.16 → 10.10.10.22 ACCEPTED
        s1-leaf2 → s2-host2
  [✔] 프로브 경로 s2-leaf3 → s1-host1             10.255.10.115 → 10.10.10.11 ACCEPTED
        s2-leaf3 → s1-host1
  [✔] 프로브 경로 s2-leaf4 → s1-host1             10.255.10.117 → 10.10.10.11 ACCEPTED
        s2-leaf4 → s1-host1

========================================================================
PASS 28 / FAIL 0 / WARN 0 / SKIP 0
리포트: /home/coder/project/labfiles/atd_avd_l3_dc/batfish/reports/preflight_dc1-dc2_20260822_115617.md
========================================================================
```

### 이 단계에서 확인된 것

- **24개 설정 파일 전부 ARISTA로 파싱** — 파싱 경고 61건은 모두 Batfish가 지원하지 않는 EOS 고유
  문법(`rd evpn domain remote`, `monitor connectivity`, `ip address virtual source-nat` 등)으로,
  사전에 분류해 둔 목록과 일치했습니다.
- **BGP 176개 세션 전부 ESTABLISHED (모델상)** — 단순 설정 정합성뿐 아니라, 언더레이 경로를
  계산해 피어 주소에 실제로 패킷이 닿는지까지 확인한 결과입니다. 여기에는 DCI를 넘어가는
  Border Leaf 간 EVPN 멀티홉 세션 8개가 포함됩니다.
- **Lab 1~6 시나리오 20개 항목 전부 PASS** — VLAN 30/40/50과 100/200의 SVI·anycast GW·VNI 매핑이
  양 DC에서 동일하고, VRF 100/200이 격리되어 있으며, Lab 6의 프로브 소스 주소가 leaf마다 고유하고
  감시 대상 호스트까지 경로가 성립함을 배포 전에 확인했습니다.
- **DC 간 VTEP 경로가 의도한 대로 흐름** — `s1-leaf1(10.1.1.14) → s2-leaf1(10.1.1.114)` 경로가
  `s1-spine1 → s1-brdr1 → s1-core1 → s2-core1 → s2-brdr1 → s2-spine1 → s2-leaf1`로 계산되어,
  트래픽이 Border Leaf와 DCI core를 경유한다는 설계 의도가 확인되었습니다(ECMP 조합 32개).

<br>

## 3. AVD 배포 (DC1) — 그리고 사전 검증이 볼 수 없었던 문제

```
$ make deploy_dc1_eapi

TASK [load configuration from file] ********************************************
ok: [s1-spine1]
ok: [s1-spine2]
ok: [s1-leaf1] ... ok: [s1-brdr2]        <- changed=0, 즉 live 설정이 intended와 이미 일치

PLAY [validate states on EOS devices] ******************************************
TASK [arista.avd.anta_runner : Run ANTA] ***************************************
fatal: [s1-spine1 -> localhost]: FAILED! => {"anta_tests_summary": {
    "devices_with_test_failures": ["s1-brdr1", "s1-brdr2", "s1-leaf1", "s1-leaf2",
                                   "s1-leaf3", "s1-leaf4", "s1-spine1", "s1-spine2"],
    "tests_error": 0, "tests_failed": 26, "tests_passed": 170,
    "tests_skipped": 56, "tests_unset": 0, "total_tests": 252}, ...
```

26건 실패 중 **2건이 진짜 문제**였습니다.

```
s1-brdr1 | VerifyBGPPeerSession | ['Peer: 172.16.255.1 VRF: default - Incorrect session state -
                                    Expected: Established Actual: Active',
                                   'Peer: 172.16.255.3 VRF: default - ... Actual: Active']
s1-brdr2 | VerifyBGPPeerSession | ['Peer: 172.16.255.5 ... Actual: Active',
                                   'Peer: 172.16.255.7 ... Actual: Active']
```

Border Leaf → DCI core 방향 eBGP가 `Active`(수립 실패) 상태였습니다. Batfish는 같은 세션을
`ESTABLISHED`로 계산했는데 실제로는 붙지 않은 것입니다. 장비에서 직접 확인한 결과:

```
$ ansible -i sites/dc1/inventory.yml dc1_dci -m arista.eos.eos_command \
    -a "commands='show ip interface brief'"

s1-core1 | SUCCESS =>
    Interface       IP Address           Status     Protocol         MTU
    --------------- -------------------- ---------- ------------- ---------
    Management0     192.168.0.102/24     up         up              1500
```

**DCI core 4대에 Management0 외에 아무 설정도 없었습니다.** ATD 랩이 재시작되면서 `dci_configs/`가
배포되지 않은 상태였던 것입니다(core는 CVP/eos_designs 관리 대상이 아닌 정적 설정 장비라,
`make deploy_dc{n}_dci`를 따로 돌려야 합니다).

> **이것이 Batfish와 ANTA의 역할 분담을 보여주는 사례입니다.** Batfish는 `dci_configs/s1-core1.cfg`
> **파일**을 읽고 "이 설정이면 세션이 붙는다"고 정확히 계산했습니다. 그 설정이 장비에 실제로
> 올라갔는지는 Batfish가 알 수 있는 영역이 아니고, 그건 ANTA가 잡았습니다. 사전 검증은 배포 전
> 실수를 없애 주지만 배포 자체를 대신하지는 않습니다.

<br>

## 4. 원인 조치 — DCI core 설정 배포

```
$ make deploy_dc1_dci
TASK [load configuration from file] ********************************************
changed: [s1-core1]
changed: [s1-core2]
PLAY RECAP *********************************************************************
s1-core1  : ok=2  changed=1  unreachable=0  failed=0
s1-core2  : ok=2  changed=1  unreachable=0  failed=0

$ make deploy_dc2_dci
changed: [s2-core1]
changed: [s2-core2]
s2-core1  : ok=2  changed=1  unreachable=0  failed=0
s2-core2  : ok=2  changed=1  unreachable=0  failed=0
```

배포 직후 Border Leaf에서 세션 상태를 확인하면, Batfish가 예측한 대로 붙습니다.

```
$ ansible -i sites/dc1/inventory.yml s1-brdr1 -m arista.eos.eos_command \
    -a "commands='show ip bgp summary vrf default'"

BGP summary information for VRF default
Router identifier 10.1.0.2, local AS number 65099
  Description              Neighbor     V AS       MsgRcvd MsgSent InQ OutQ Up/Down State  PfxRcd
  s1-spine1_Ethernet7      10.255.0.4   4 65000        148     145   0    0 01:47:38 Estab  7
  s1-spine2_Ethernet7      10.255.0.6   4 65000        146     142   0    0 01:47:38 Estab  7
  s1-core1 VRF Default     172.16.255.1 4 65501          9      14   0    0 00:00:11 Estab  11
  s1-core2 VRF Default     172.16.255.3 4 65501          9      10   0    0 00:00:11 Estab  11
  s1-brdr2_Vlan4093        192.1.1.3    4 65099        139     138   0    0 01:47:37 Estab  21
```

EVPN Gateway(Lab 3)의 DC 간 원격 피어링도 함께 살아났습니다.

```
$ ansible -i sites/dc1/inventory.yml s1-brdr1 -m arista.eos.eos_command \
    -a "commands='show bgp evpn summary'"

BGP summary information for VRF default
Router identifier 10.1.0.2, local AS number 65099
  Description          Neighbor   V AS       MsgRcvd MsgSent InQ OutQ Up/Down State  PfxRcd
  s1-spine1_Loopback0  10.1.0.10  4 65000        292     314   0    0 01:50:01 Estab  92
  s1-spine2_Loopback0  10.1.0.12  4 65000        297     267   0    0 01:50:01 Estab  92
  s2-brdr1             10.1.0.102 4 65199         94      94   0    0 00:02:28 Estab  72
  s2-brdr2             10.1.0.104 4 65199         95      88   0    0 00:02:29 Estab  72
```

`10.1.0.102`/`10.1.0.104`(반대쪽 DC의 Border Leaf) 세션이 `Estab` — Batfish가 사전 검증 단계에서
`EBGP_MULTIHOP EVPN 세션 8개 수립`이라고 계산했던 바로 그 세션들입니다.

<br>

## 5. AVD 배포 (DC2)

```
$ make deploy_dc2_eapi

TASK [load configuration from file] ********************************************
ok: [s2-spine1] ... ok: [s2-brdr2]       <- changed=0

PLAY RECAP *********************************************************************
s2-brdr1 ~ s2-spine2         : ok=2  changed=0  unreachable=0  failed=0
```

<br>

## 6. ANTA 배포 후 검증

DCI core 배포 후 다시 실행한 결과입니다.

```
$ make verify_dc1
TASK [arista.avd.anta_runner : Run ANTA] ***************************************
{"anta_tests_summary": {"devices_with_test_errors": [],
  "tests_error": 0, "tests_failed": 24, "tests_passed": 172,
  "tests_skipped": 56, "tests_unset": 0, "total_tests": 252}}
```

| | DC1 | DC2 |
|---|---|---|
| 전체 테스트 | 252 | 252 |
| 통과 | 172 | 172 |
| 실패 | 24 | 24 |
| 건너뜀 | 56 | 56 |

### 통과한 테스트 (DC1 기준, DC2 동일)

`VerifyAgentLogs`×8; `VerifyBGPPeerSession`×8; `VerifyCoredump`×8; `VerifyIllegalLACP`×6; `VerifyInterfaceDiscards`×8; `VerifyInterfaceErrDisabled`×8; `VerifyInterfaceErrors`×8; `VerifyInterfaceUtilization`×8; `VerifyInterfacesStatus`×8; `VerifyLLDPNeighbors`×8; `VerifyMaintenance`×8; `VerifyMlagConfigSanity`×6; `VerifyMlagInterfaces`×6; `VerifyMlagStatus`×6; `VerifyNTP`×8; `VerifyPortChannels`×6; `VerifyReachability`×8; `VerifyReloadCause`×8; `VerifyRoutingProtocolModel`×8; `VerifyRunningConfigDiffs`×8; `VerifySTPCounters`×8; `VerifyVxlanConfigSanity`×6; `VerifyZeroTouch`×8

프로토콜/설계 검증 계열이 모두 통과했습니다. 특히:

- `VerifyBGPPeerSession` ×8 — 3절에서 실패했던 항목. DCI core 배포 후 전 장비 통과
- `VerifyVxlanConfigSanity` ×6 — VXLAN/VNI 설정 정합성
- `VerifyMlagStatus`/`VerifyMlagInterfaces`/`VerifyMlagConfigSanity` ×6씩 — MLAG 상태
- `VerifyRunningConfigDiffs` ×8 — **장비의 running-config가 AVD intended config와 완전 일치**
- `VerifyInterfacesStatus`/`VerifyLLDPNeighbors` ×8 — 인터페이스/이웃 상태
- `VerifyReachability` ×8 — 관리 도달성

### 남은 실패 24건 — 모두 랩 환경 요인

| 테스트 | 건수 | 실제 메시지 | 성격 |
|---|---|---|---|
| `VerifyFileSystemUtilization` | 8 | `overlay 60G 46G 15G 77% / - Expected: 75% Actual: 77%` | cEOS 컨테이너가 **ATD 호스트의 파일시스템을 공유** — 스위치 디스크가 아님 |
| `VerifyMemoryUtilization` | 8 | `high memory usage - Expected: < 75% Actual: 92.59%` | 동일하게 호스트 메모리를 그대로 보고함 |
| `VerifyLoggingErrors` | 8 | `%HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED: Failed to identify this system` | cEOS-lab에 물리 하드웨어가 없어 부팅 시 항상 남는 로그 |

세 항목 모두 **cEOS 컨테이너 환경 특성**이지 설정이나 패브릭 상태의 문제가 아닙니다. 실제 하드웨어
스위치에서는 나타나지 않습니다. 건너뛴 56건도 같은 이유입니다(`VerifyEnvironmentCooling`,
`VerifyEnvironmentPower`, `VerifyTemperature`, `VerifyInventory` 등 — 물리 센서가 없어 스킵).

<br>

## 7. 호스트 간 통신 검증

호스트의 VLAN SVI는 각각 이름이 같은 로컬 VRF(`10`/`20`/`100`/`200`)에 있으므로 항상
`ping vrf <n> <ip>` 형태로 실행합니다. 각 호스트 4대에서 8가지 테스트, 총 32건입니다.

**기대**는 이 설계대로라면 통해야 하는지(성공) 막혀야 하는지(실패)를, **결과**는 실제 ping 결과를
가리킵니다. VRF 격리 항목은 막히는 것이 정상이므로 기대·결과가 모두 `실패`일 때 설계대로 동작한 것입니다.

### DC1 → DC2

| 출발 호스트 | 테스트 | VRF → 목적지 | 수신 | 손실 | 기대 | 결과 |
|---|---|---|---|---|---|---|
| `s1-host1` | → s2-host1 VLAN10 (DC간 스트레치) | `vrf 10 -> 10.10.10.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host2` | → s2-host1 VLAN10 (DC간 스트레치) | `vrf 10 -> 10.10.10.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host1` | → s2-host2 VLAN10 (DC간 스트레치) | `vrf 10 -> 10.10.10.22` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host2` | → s2-host2 VLAN10 (DC간 스트레치) | `vrf 10 -> 10.10.10.22` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host1` | → s2-host1 VLAN20 (DC간 스트레치) | `vrf 20 -> 10.20.20.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host2` | → s2-host1 VLAN20 (DC간 스트레치) | `vrf 20 -> 10.20.20.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host1` | → s2-host1 VLAN100 (New-Tenant VRF 100) | `vrf 100 -> 10.100.100.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host2` | → s2-host1 VLAN100 (New-Tenant VRF 100) | `vrf 100 -> 10.100.100.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host1` | → s2-host1 VLAN200 (New-Tenant VRF 200) | `vrf 200 -> 10.200.200.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host2` | → s2-host1 VLAN200 (New-Tenant VRF 200) | `vrf 200 -> 10.200.200.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host1` | → 로컬 anycast GW VLAN10 | `vrf 10 -> 10.10.10.1` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host2` | → 로컬 anycast GW VLAN10 | `vrf 10 -> 10.10.10.1` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host1` | → s2-host1 VLAN20 from VRF10 (leaf VRF A 경유) | `vrf 10 -> 10.20.20.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host2` | → s2-host1 VLAN20 from VRF10 (leaf VRF A 경유) | `vrf 10 -> 10.20.20.21` | 5 received | 0% packet loss | 성공 | 성공 |
| `s1-host1` | → s2-host1 VLAN200 from VRF100 (VRF 격리) | `vrf 100 -> 10.200.200.21` | 0 received | 100% packet loss | 실패 | 실패 |
| `s1-host2` | → s2-host1 VLAN200 from VRF100 (VRF 격리) | `vrf 100 -> 10.200.200.21` | 0 received | 100% packet loss | 실패 | 실패 |

### DC2 → DC1

| 출발 호스트 | 테스트 | VRF → 목적지 | 수신 | 손실 | 기대 | 결과 |
|---|---|---|---|---|---|---|
| `s2-host1` | → s1-host1 VLAN10 (DC간 스트레치) | `vrf 10 -> 10.10.10.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host2` | → s1-host1 VLAN10 (DC간 스트레치) | `vrf 10 -> 10.10.10.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host1` | → s1-host2 VLAN10 (DC간 스트레치) | `vrf 10 -> 10.10.10.12` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host2` | → s1-host2 VLAN10 (DC간 스트레치) | `vrf 10 -> 10.10.10.12` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host1` | → s1-host1 VLAN20 (DC간 스트레치) | `vrf 20 -> 10.20.20.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host2` | → s1-host1 VLAN20 (DC간 스트레치) | `vrf 20 -> 10.20.20.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host1` | → s1-host1 VLAN100 (New-Tenant VRF 100) | `vrf 100 -> 10.100.100.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host2` | → s1-host1 VLAN100 (New-Tenant VRF 100) | `vrf 100 -> 10.100.100.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host1` | → s1-host1 VLAN200 (New-Tenant VRF 200) | `vrf 200 -> 10.200.200.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host2` | → s1-host1 VLAN200 (New-Tenant VRF 200) | `vrf 200 -> 10.200.200.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host1` | → 로컬 anycast GW VLAN10 | `vrf 10 -> 10.10.10.1` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host2` | → 로컬 anycast GW VLAN10 | `vrf 10 -> 10.10.10.1` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host1` | → s1-host1 VLAN20 from VRF10 (leaf VRF A 경유) | `vrf 10 -> 10.20.20.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host2` | → s1-host1 VLAN20 from VRF10 (leaf VRF A 경유) | `vrf 10 -> 10.20.20.11` | 5 received | 0% packet loss | 성공 | 성공 |
| `s2-host1` | → s1-host1 VLAN200 from VRF100 (VRF 격리) | `vrf 100 -> 10.200.200.11` | 0 received | 100% packet loss | 실패 | 실패 |
| `s2-host2` | → s1-host1 VLAN200 from VRF100 (VRF 격리) | `vrf 100 -> 10.200.200.11` | 0 received | 100% packet loss | 실패 | 실패 |

### 결과 해석

- **DC 간 VXLAN 스트레치가 4개 VLAN 전부에서 동작** — VLAN 10/20(테넌트 `ATD_DC`, VRF `A`)과
  VLAN 100/200(테넌트 `New-Tenant`, VRF `100`/`200`)이 모두 0% 손실로 반대편 DC에 도달합니다.
  Lab 2(Border Leaf) + Lab 3(EVPN Gateway) + Lab 4(New-Tenant)가 함께 성립해야 나오는 결과입니다.
- **VRF 격리가 실제로 동작** — VRF `100`에서 VRF `200` 대역(`10.200.200.x`)으로 보낸 4건은
  100% 손실입니다. 이건 **의도된 실패**로, 사전 검증 단계에서 Batfish가
  "VRF 100 라우팅 테이블에 10.200.200.0/24 경로 없음"이라고 계산했던 것과 정확히 일치합니다.
- **VRF 10 → VLAN 20은 성공** — 호스트에서는 VRF가 분리되어 있지만 leaf 쪽에서는 VLAN 10/20이
  같은 VRF `A`를 공유하므로, leaf를 경유해 도달합니다. VLAN 100/200과 대비되는 지점입니다.

<br>

## 8. Lab 6 — Connectivity Monitor 동작 확인

배포 전 Batfish가 `프로브 경로 s1-leaf1 → s2-host2 : 10.255.10.14 → 10.10.10.22 ACCEPTED`로
계산했던 프로브가, 실제 장비에서도 그대로 동작합니다.

```
$ ansible -i sites/dc1/inventory.yml s1-leaf1 -m arista.eos.eos_command \
    -a "commands='show monitor connectivity'"

VRF: A
Host: s2-host2
Payload size: 56
ICMP ping count: 5
Network statistics:
IP Address  Local Interface Latency   Jitter Packet Loss Probe Error
----------- --------------- ------- -------- ----------- -----------
10.10.10.22 Loopback210     12.2 ms 0.637 ms          0% n/a
```

```
$ ansible -i sites/dc2/inventory.yml s2-leaf3 -m arista.eos.eos_command \
    -a "commands='show monitor connectivity'"

VRF: A
Host: s1-host1
Network statistics:
IP Address  Local Interface   Latency   Jitter Packet Loss Probe Error
----------- --------------- --------- -------- ----------- -----------
10.10.10.11 Loopback210     10.954 ms 0.577 ms          0% n/a
```

`Local Interface`가 `Loopback210`으로 잡혀 있다는 것은 Lab 6에서 만든 leaf 전용 소스 주소와
`virtual_source_nat_vrfs`가 의도대로 동작한다는 뜻이고, 양방향 모두 `Packet Loss 0%`입니다.

<br>

## 9. 검사기 자가 진단

"전부 PASS"가 의미 있으려면 검사기가 실제로 고장을 잡을 수 있어야 합니다. 정상 스냅샷을 복제해
사본에만 고장을 주입하고 확인한 결과입니다(`make preflight_selftest`).

| 주입한 고장 | 결과 |
|---|---|
| Border Leaf에서 원격 EVPN 피어링/`domain remote` 제거 | ✔ Lab 3 두 항목 FAIL — "DC 간 brdr↔brdr EVPN 세션 없음 (evpn_gateway 블록 주석 해제 필요)" |
| DCI 방향 P2P 링크 한쪽 MTU만 9214 → 1500 | ✔ L3 링크 MTU FAIL — 1개 링크 불일치 |
| 서로 다른 leaf에 같은 Loopback0 주소 부여 | ✔ 중복 IP FAIL + 연쇄로 BGP 세션 4개 FAIL |
| DCI core 간 링크 하나 shutdown | ✔ BGP 세션 수립 FAIL 2건 (호환성은 PASS 유지). VTEP 도달성은 여전히 PASS이며 경로 수가 32→16으로 줄어, **이중화가 실제로 동작함**이 확인됨 |


<br>

## 10. 추가 시나리오 — Edge에서 DC 간 통신을 끊고, 누가 잡아내는지 비교

앞의 9절까지가 "정상 상태를 확인한 기록"이라면, 이 절은 **일부러 장애를 만들어 각 도구의 탐지 능력을
비교한 기록**입니다. 실제 랩에 적용했다가 원상 복구까지 마쳤습니다.

### 시나리오 설계

DC 간 통신에서 가장 찾기 어려운 장애는 **제어 평면은 멀쩡한데 데이터 평면만 죽는** 경우입니다.
이 패브릭에서 두 평면은 서로 다른 주소를 씁니다.

| | 쓰는 주소 | 값 |
|---|---|---|
| EVPN 피어링 (제어 평면) | `Loopback0` — 라우터 ID | `10.1.0.2` ↔ `10.1.0.102` |
| VXLAN 캡슐화 (데이터 평면) | `Loopback1` — VTEP | `10.1.1.2` ↔ `10.1.1.102` |

Edge(Border Leaf)를 무대로 삼은 이유는 DC 간 트래픽이 반드시 여기를 지나기 때문입니다. Lab 3의
EVPN Gateway가 경로를 재발신하므로, DC1 leaf가 보는 DC2 호스트의 next-hop은 DC2 leaf가 아니라
**자기 DC의 Border Leaf VTEP**입니다.

```
$ ansible -i sites/dc1/inventory.yml s1-leaf1 -m arista.eos.eos_command \
    -a "commands='show bgp evpn route-type mac-ip vni 10010'"

          Network                        Next Hop     ...  Path
 * >Ec    RD: 10.1.0.2:10010 mac-ip 001c.73c0.c627 10.10.10.22
                                       10.1.1.2      ...  65000 65099 65199 65100 65102 i
```

`10.10.10.22`는 DC2의 `s2-host2`인데 next-hop이 `10.1.1.2`(DC1 Border Leaf VTEP)입니다.
그 Border Leaf가 다시 `10.1.1.102`(DC2 Border Leaf VTEP)로 캡슐화해 DCI를 건넙니다.
따라서 **Edge에서 `10.1.1.102` 한 주소만 막으면** DC1 ↔ DC2 전체가 끊깁니다.

### 장애 주입 — `group_vars` 한 줄

Border Leaf는 AVD 관리 장비이므로 장비를 직접 건드리지 않고 AVD 입력을 수정했습니다
(`sites/dc1/group_vars/dc1_fabric.yml`의 `BrdrLeafs` 블록, 평소에는 주석 상태로 준비되어 있음).

```yaml
      structured_config:
        static_routes:
          - prefix: 10.1.1.102/32
            interface: 'null0'
```

```
$ make build_dc1
$ grep "^ip route" sites/dc1/intended/configs/s1-brdr1.cfg
ip route 0.0.0.0/0 192.168.0.1
ip route 10.1.1.102/32 Null0
```

> AVD 6.0.0부터 `destination_address_prefix`가 `prefix`로 바뀌어, 예전 키로 쓰면 `make build_dc1`이
> 스키마 검증 단계에서 바로 실패합니다 — 실제로 이 시나리오를 만들면서 겪은 오류입니다.

### 배포 전 — Batfish 결과

```
$ make preflight

[공통 검사]
  [✔] BGP 세션 호환성          176개 세션 모두 UNIQUE_MATCH
  [✔] BGP 세션 수립(모델)       176개 세션 모두 ESTABLISHED            <- 제어 평면은 멀쩡
  [✘] VTEP 간 도달성          VTEP 6개 중 도달 불가 조합 6건 — VXLAN 터널 단절
        s1-brdr1 10.1.1.2  → 10.1.1.102: NULL_ROUTED (s1-brdr1)
        s1-brdr2 10.1.1.2  → 10.1.1.102: NULL_ROUTED (s1-brdr2)
        s1-leaf1 10.1.1.14 → 10.1.1.102: NO_ROUTE (s1-leaf1)
        s1-leaf2 10.1.1.14 → 10.1.1.102: NO_ROUTE (s1-leaf2)
        s1-leaf3 10.1.1.15 → 10.1.1.102: NO_ROUTE (s1-leaf3)
        s1-leaf4 10.1.1.15 → 10.1.1.102: NO_ROUTE (s1-leaf4)

[Lab 3 시나리오 검사]
  [✔] EVPN Gateway 원격 피어링   DC 간 EBGP_MULTIHOP EVPN 세션 8개 수립   <- 여기도 멀쩡
  [✔] VTEP 간 언더레이 도달성      s1-leaf1 → s2-leaf1 경로 32개 ACCEPTED   <- leaf↔leaf는 살아 있음

PASS 27 / FAIL 1 / WARN 0 / SKIP 0
```

- **Edge에서는 `NULL_ROUTED`, leaf에서는 `NO_ROUTE`** — 하나의 원인이 위치에 따라 다른 증상으로
  나타납니다. Edge는 정적 경로가 Null0으로 흘려보내고, leaf는 Edge가 그 경로를 더 이상 언더레이로
  광고하지 않아 아예 경로가 없습니다.
- **BGP 검사 세 개는 전부 통과** — 실제로도 세션은 정상이므로 올바른 판정입니다. 제어 평면만 보는
  검사로는 원리적으로 찾을 수 없는 장애라는 뜻입니다.
- **Lab 3의 leaf↔leaf VTEP 검사도 통과** — `10.1.1.114`(DC2 leaf VTEP)로 가는 경로는 막지 않았기
  때문입니다. 대표 경로 하나만 확인하는 방식으로는 부족하고 **모든 VTEP 조합**을 봐야 한다는 것이
  이 시나리오를 만들면서 확인된 부분이고, 공통 검사에 `VTEP 간 도달성`을 추가한 이유입니다.

### 배포 후 — 다른 도구들의 반응

그대로 배포했을 때 무슨 일이 벌어지는지까지 확인했습니다.

```
$ make deploy_dc1_eapi
changed: [s1-brdr1]
changed: [s1-brdr2]

{"anta_tests_summary": {"tests_failed": 26, "tests_passed": 170, "tests_skipped": 56, "total_tests": 252}}
```

ANTA 실패 건수는 정상일 때(24건)보다 2건 늘었는데, 늘어난 것은 `VerifyRunningConfigDiffs`
— running-config와 startup-config의 차이일 뿐 장애 탐지가 아닙니다.

```
s1-brdr1 -> ['--- flash:/startup-config
             +++ system:/running-config
              ip route 0.0.0.0/0 192.168.0.1
             +ip route 10.1.1.102/32 Null0']
```

프로토콜 검사는 전부 통과합니다.

```
s1-brdr1  VerifyBGPPeerSession      success
s1-brdr1  VerifyVxlanConfigSanity   success
s1-leaf1  VerifyBGPPeerSession      success
s1-leaf1  VerifyVxlanConfigSanity   success
```

EVPN 세션도 정상으로 보입니다 — 경로도 51개씩 주고받고 있습니다.

```
$ ansible -i sites/dc1/inventory.yml s1-brdr1 -m arista.eos.eos_command \
    -a "commands='show bgp evpn summary'"

  Description   Neighbor    V AS      MsgRcvd MsgSent Up/Down State  PfxRcd
  s2-brdr1      10.1.0.102  4 65199       319     308 01:50:18 Estab   51
  s2-brdr2      10.1.0.104  4 65199       317     303 01:50:19 Estab   51
```

그런데 호스트 통신은 전부 끊겨 있습니다.

| 테스트 | VRF → 목적지 | 수신 | 손실 |
|---|---|---|---|
| → s2-host1 VLAN10 | `vrf 10 -> 10.10.10.21` | 0 received | 100% packet loss |
| → s2-host2 VLAN10 | `vrf 10 -> 10.10.10.22` | 0 received | 100% packet loss |
| → s2-host1 VLAN20 | `vrf 20 -> 10.20.20.21` | 0 received | 100% packet loss |
| → s2-host1 VLAN100 | `vrf 100 -> 10.100.100.21` | 0 received | 100% packet loss |
| → s2-host1 VLAN200 | `vrf 200 -> 10.200.200.21` | 0 received | 100% packet loss |
| → 로컬 anycast GW | `vrf 10 -> 10.10.10.1` | 5 received | **0% packet loss** |

마지막 줄이 중요합니다 — DC **내부** 통신은 멀쩡하고 DC **간** 통신만 죽었습니다. 원인은 Edge의
라우팅 테이블 한 줄입니다.

```
s1-brdr1# show ip route 10.1.1.102
 S        10.1.1.102/32
           directly connected, Null0
```

### 원상 복구

`group_vars`의 주석을 되돌려 재빌드하고, 이미 배포된 장비에서는 정적 경로를 명시적으로 제거했습니다
— `eos_config`는 없는 줄을 추가할 뿐 남은 줄을 지우지 않기 때문입니다.

```
$ ansible -i sites/dc1/inventory.yml s1-brdr1,s1-brdr2 \
    -m arista.eos.eos_config -a "lines='no ip route 10.1.1.102/32 Null0'"
s1-brdr1 | CHANGED
s1-brdr2 | CHANGED

s1-brdr1# show ip route 10.1.1.102
 B E      10.1.1.102/32 [20/0]
           via 172.16.255.1, Ethernet4
           via 172.16.255.3, Ethernet5
```

BGP가 학습한 ECMP 경로로 돌아왔고, 호스트 통신 32건도 7절과 동일하게 복구되었습니다
(성공 28건 0% 손실 + VRF 격리 4건 100% 손실).

### 도구별 탐지 결과

| 도구 | 시점 | 탐지 |
|---|---|---|
| **Batfish `VTEP 간 도달성`** | 배포 전 | **탐지** — 원인 위치(`s1-brdr1` Null0)까지 지목 |
| Batfish BGP 검사 (호환성/수립) | 배포 전 | 미탐지 — 176개 세션 전부 정상 판정 (실제로도 정상) |
| Batfish Lab 3 leaf↔leaf VTEP 경로 | 배포 전 | 미탐지 — 막지 않은 경로만 확인했기 때문 |
| ANTA `VerifyBGPPeerSession` | 배포 후 | 미탐지 — 통과 |
| ANTA `VerifyVxlanConfigSanity` | 배포 후 | 미탐지 — 통과 |
| `show bgp evpn summary` | 배포 후 | 미탐지 — `Estab`, 경로 51개 수신 |
| 호스트 `ping` | 배포 후 | 탐지 — 100% 손실. 다만 **이미 장애가 난 뒤** |

제어 평면만 보는 검사는 이 장애에 대해 원리적으로 침묵합니다. 데이터 평면 경로를 직접 계산하는
검사만이 배포 전에 잡을 수 있고, 그것이 Batfish를 파이프라인에 넣는 이유입니다.

<br>

## 11. 결론

1. **사전 검증은 실효가 있습니다.** 배포 전에 24대 설정을 통째로 시뮬레이션해 BGP 176개 세션의
   수립 가능성, DC 간 VTEP 경로, VRF 격리, MTU 정합, 중복 IP를 전부 확인했고, 결과는 배포 후
   ANTA·실제 ping과 일치했습니다.
2. **사전 검증이 배포 확인을 대체하지는 않습니다.** DCI core 4대가 실제로는 배포되지 않은 상태였고,
   이건 설정 파일만 보는 Batfish로는 원리적으로 알 수 없는 문제였습니다(ANTA가 잡음).
3. **두 도구의 판정이 서로를 검증합니다.** Batfish가 "VRF 100에는 10.200.200.0/24 경로가 없다"고
   계산한 것과 실제 ping이 100% 손실인 것, Batfish가 "프로브 경로 ACCEPTED"라고 한 것과
   `show monitor connectivity`가 `0% loss`인 것이 각각 맞아떨어졌습니다.
4. **랩 환경 요인은 분리해서 봐야 합니다.** ANTA 실패 24건은 전부 cEOS 컨테이너 특성
   (호스트 파일시스템/메모리 공유, 물리 하드웨어 부재)이며 패브릭 상태와 무관합니다.
5. **제어 평면 검사만으로는 부족합니다.** §10에서 Edge에 VTEP 블랙홀을 넣자 BGP·EVPN 세션과 ANTA는
   모두 정상을 보고했지만 DC 간 통신은 완전히 끊겼습니다. 데이터 평면 경로를 직접 계산하는
   `VTEP 간 도달성` 검사만이 배포 전에 이를 잡아냈습니다.

관련 문서: [Batfish 사전 검증 가이드](batfish-preflight-guide.md) · [EVPN VXLAN 랩](evpn-vxlan-labs.md)
