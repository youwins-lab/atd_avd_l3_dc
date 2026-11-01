# Batfish 사전 검증 (Pre-flight) 가이드

`lab guide/evpn-vxlan-labs.md`의 Lab 1~6은 모두 같은 리듬으로 진행됩니다 — `group_vars`를 고치고,
`make build_dc{n}`으로 설정을 만들고, `make deploy_dc{n}_*`로 장비에 밀어넣고, 그다음에야 `show`
명령어나 ANTA로 결과를 확인합니다. 이 흐름의 문제는 **틀렸다는 걸 배포한 뒤에야 안다**는 점입니다.
Border Leaf의 MTU를 한쪽만 9214로 적어 놓았거나, leaf 두 대에 같은 라우터 ID를 준 경우, 장비에
설정이 올라가고 세션이 죽고 나서야 발견됩니다.

이 가이드는 그 사이에 한 단계를 끼워 넣습니다.

```
group_vars 수정
     ↓
make build_dc{n}          ← AVD가 intended/configs/*.cfg 생성
     ↓
make preflight            ← ★ Batfish: 장비를 건드리지 않고 설정만으로 검증
     ↓
make deploy_dc{n}_*       ← 여기서부터 실제 장비에 반영
     ↓
make verify_dc{n}         ← ANTA: 살아있는 장비의 상태 검증
```

> 이 가이드는 `evpn-vxlan-labs.md`와 **병행**하는 별도 문서입니다. Lab 1~6을 순서대로 진행하되,
> 각 랩에서 `make build_dc{n}`을 끝낸 직후 여기 §6의 해당 랩 검사를 돌리면 됩니다.

<br>

## 1. Batfish는 무엇이고, ANTA와 무엇이 다른가

| | **Batfish** | **ANTA** |
|---|---|---|
| 검증 대상 | 설정 파일 (`intended/configs/*.cfg`) | 살아있는 장비의 실제 상태 |
| 실행 시점 | **배포 전** | 배포 후 |
| 장비 접속 | 하지 않음 | eAPI로 접속 |
| 원리 | 설정을 파싱해 라우팅/포워딩 동작을 **시뮬레이션** | `show` 명령 결과를 기대값과 비교 |
| 잡아내는 것 | 설정끼리의 모순 (MTU/AS/IP 불일치, 도달 불가 경로) | 실제 장애 (링크 다운, 세션 끊김, 리소스 부족) |
| 못 잡는 것 | 케이블 오배선, 하드웨어 문제, 배포 누락 | 배포하기 전의 실수 |

둘은 대체 관계가 아니라 **짝**입니다. Batfish는 "이 설정을 그대로 밀어넣으면 논리적으로 성립하는가"를,
ANTA는 "실제로 그렇게 됐는가"를 답합니다. 이 랩에서 실제로 두 도구가 서로 다른 문제를 잡아낸 사례는
`lab guide/batfish-avd-anta-verification-report.md` §5에 기록되어 있습니다.

Batfish는 설정을 **읽기만** 합니다. 장비에 접속하지도, 어떤 설정도 바꾸지도 않으므로 운영 중인
패브릭에 대해서도 안전하게 돌릴 수 있습니다.

<br>

## 2. 설치

### 2-1. ATD 환경의 제약과 이 저장소의 설치 방식

Batfish 공식 배포 방식은 Docker 컨테이너입니다.

```bash
docker run --name batfish -v batfish-data:/data -p 9997:9997 -p 9996:9996 batfish/allinone
```

그런데 **ATD 프로그래머빌리티 IDE 자체가 컨테이너 안**이라 Docker 데몬이 없습니다(`docker` 명령어도,
`/var/run/docker.sock`도 없습니다). 그래서 이 저장소의 `batfish/install_batfish.sh`는 같은
`batfish/allinone` 이미지를 **Docker Registry API로 직접 내려받아 풀어 놓고**, 그 안에 들어 있는
`allinone-bundle.jar`를 호스트의 JVM으로 직접 실행합니다. Batfish 서비스는 순수 Java 프로세스라
컨테이너 격리 없이도 그대로 동작합니다.

정리하면 설치 스크립트가 하는 일은 네 가지입니다.

1. Java 25 JRE(Eclipse Temurin) 설치 — Batfish 실행에 필요. `../batfish-service/jre/`에 내려받습니다.
   2026-08 이후의 `batfish/allinone:latest` jar는 Java 21 이상(class file 65)으로 빌드되어 있어 ATD(Debian 12)의
   apt에 있는 OpenJDK 17로는 실행되지 않고, 이미지에 들어 있는 JRE는 glibc 2.38을 요구해 호스트에서 돌지 않습니다.
   그래서 glibc 의존성이 낮은 Temurin 바이너리를 따로 받고, `batfishctl.sh`가 이 JRE를 우선 사용합니다.
2. `batfish/allinone:latest` 이미지 매니페스트/레이어를 레지스트리에서 내려받아 `rootfs/`에 전개
3. `allinone-bundle.jar` 확보 확인
4. 이미지에 동봉된 `pybatfish` wheel 설치 — **서비스와 클라이언트 버전이 정확히 일치**하게 하려고
   PyPI가 아니라 이미지 안의 wheel을 씁니다

### 2-2. 실행

```bash
cd /home/coder/project/labfiles/atd_avd_l3_dc
make bf_install
```

약 600MB를 내려받으므로 몇 분 걸립니다. 설치물은 저장소 밖 `../batfish-service/`에 놓입니다
(`ansible-avd`/`ansible-cvp` collection과 같은 sibling 위치 규칙).

```
/home/coder/project/labfiles/
├── atd_avd_l3_dc/        <- 이 저장소
│   └── batfish/          <- 검증 도구 (저장소에 포함)
└── batfish-service/      <- Batfish 서비스 실체 (저장소 밖, 재설치 가능)
    ├── jre/bin/java      <- Temurin JRE 25 (batfishctl.sh가 우선 사용)
    ├── rootfs/allinone-bundle.jar
    ├── data/containers/  <- 스냅샷 저장소
    └── logs/
```

정상 종료 시 마지막 줄:

```
pybatfish 2026.08.27.3685

설치 완료. 다음 순서로 진행하세요:
  ./batfish/batfishctl.sh start     # Batfish 서비스 기동
  ./batfish/batfishctl.sh status    # 상태 확인
  make preflight                    # 배포 전 사전 검증
```

> **Docker를 쓸 수 있는 환경이라면** 위 `docker run` 한 줄로 서비스를 띄우고, `pip install pybatfish`만
> 하면 됩니다. 그 경우 `make bf_install`/`bf_start`는 건너뛰고 §4부터 그대로 쓰면 됩니다 — 검증
> 스크립트는 `localhost:9996`에 붙기만 하면 되므로 서비스를 어떻게 띄웠는지는 상관없습니다.

<br>

## 3. 서비스 기동과 설치 확인

### 3-1. 기동

```bash
make bf_start
```

```
running (pid 9159, port 9996)
```

`batfishctl.sh`가 제공하는 명령은 다음과 같습니다.

| 명령 | 설명 |
|---|---|
| `./batfish/batfishctl.sh start` | 서비스 기동 (포트가 응답할 때까지 최대 2분 대기) |
| `./batfish/batfishctl.sh stop` | 정지 |
| `./batfish/batfishctl.sh restart` | 재기동 |
| `./batfish/batfishctl.sh status` | 상태 확인 |
| `./batfish/batfishctl.sh log` | 서비스 로그 실시간 확인 |

`make bf_start` / `make bf_stop` / `make bf_status`도 같은 동작입니다.

> ATD 랩이 재시작되면 서비스 프로세스는 죽지만 `../batfish-service/` 디렉토리는 남습니다.
> 재설치 없이 `make bf_start`만 다시 하면 됩니다. Java까지 사라졌다면 `make bf_install`을 다시
> 실행하세요(이미 받아 놓은 레이어는 재사용합니다).

### 3-2. 설치가 제대로 됐는지 확인

먼저 클라이언트가 서비스에 붙는지 봅니다.

```bash
python3 -c "
from pybatfish.client.session import Session
bf = Session(host='localhost')
bf.set_network('smoke-test')
print('연결 OK, 네트워크 목록:', bf.list_networks())
"
```

```
연결 OK, 네트워크 목록: ['smoke-test']
```

그다음 실제 설정으로 스냅샷을 만들어 보는 것이 진짜 확인입니다. 공통 검사만 돌려 보세요
(랩 시나리오 검사는 건너뜁니다).

```bash
python3 batfish/preflight.py --labs none
```

```
스냅샷: /home/coder/project/labfiles/atd_avd_l3_dc/batfish/snapshots/dc1-dc2
노드 24개: s1-brdr1, s1-brdr2, s1-core1, s1-core2, s1-host1, s1-host2, s1-leaf1, ...

[공통 검사]
  [✔] 설정 파싱                24개 파일 모두 ARISTA로 파싱, 노드 24개 (경고 61건은 Batfish 미지원 문법으로 확인됨)
  [✔] 미정의 참조               존재하지 않는 ACL/route-map/peer-group/prefix-list 참조 없음
  [✔] 중복 IP                 설계상 공유 주소(anycast GW 7개, MLAG 공유 VTEP 6개) 외 중복 없음
  [✔] 물리 토폴로지              L1 링크 58개 / L3 인접 628개, 모든 Ethernet 인터페이스의 대향이 확인됨
  [✔] L3 링크 MTU             IP가 붙은 모든 P2P 링크의 양단 MTU 일치
  [✔] BGP 세션 호환성            176개 세션 모두 UNIQUE_MATCH (AS/IP/peer-group 정합)
  [✔] BGP 세션 수립(모델)         176개 세션 모두 ESTABLISHED (언더레이 도달성까지 성립)
  [✔] VTEP 간 도달성            VTEP 6개 × 출발 노드 12대 = 72개 조합 모두 도달 가능

========================================================================
PASS 8 / FAIL 0 / WARN 0 / SKIP 0
========================================================================
```

**노드 24개가 모두 잡히고 8개 공통 검사가 PASS**로 나오면 설치·기동이 정상입니다.
여기까지 확인한 뒤에 §6의 시나리오별 검증으로 넘어가세요.

<br>

## 4. 스냅샷이 만들어지는 방식

Batfish는 "스냅샷"(설정 파일 묶음 + 물리 토폴로지) 단위로 동작합니다. `batfish/bf_lib.py`가
저장소의 설정을 모아 스냅샷을 만드는데, 그 과정에서 두 가지 가공이 필요합니다. 검사 결과를
해석하려면 이 두 가지를 알고 있어야 합니다.

### 4-1. 설정 정규화 — 원본은 건드리지 않습니다

이 저장소의 설정 소스는 성격이 다른 세 갈래입니다.

| 소스 | 성격 |
|---|---|
| `sites/dc{n}/intended/configs/*.cfg` | AVD가 만든 **완전한** running-config (spine/leaf/border-leaf) |
| `sites/dc{n}/dci_configs/*.cfg` | 손으로 관리하는 **설정 조각** (DCI core) |
| `sites/dc{n}/host_configs/*.cfg` | 손으로 관리하는 **설정 조각** (서버 엔드포인트) |

뒤의 두 갈래는 `eos_config`로 밀어넣는 조각이라 `hostname` 줄이 없고, 인터페이스도
`interface ethernet1`처럼 소문자로 적혀 있습니다. 그래서 스냅샷을 만들 때 사본에 한해
다음을 보정합니다.

- `hostname <파일명>` 줄이 없으면 추가
- `interface ethernet1` → `interface Ethernet1` 등 EOS 표준 표기로 정규화
- **모든** 설정 파일 맨 앞에 `! device: <hostname> (cEOS-lab, EOS-4.36.0F)` 헤더 추가

마지막 헤더가 특히 중요합니다. EOS `show running-config`의 첫 줄인데, 이게 없으면 Batfish가 설정을
**Cisco IOS로 오탐**해서 `vrf instance A`, `neighbor X peer group Y` 같은 EOS 전용 문법을 전부
파싱하지 못합니다. 실제로 헤더 없이 돌리면 스파인 설정은 통째로 `FAILED`가 나고, 나머지도
파싱 경고가 수백 건 쏟아집니다. 헤더를 붙이면 24개 파일 모두 `ARISTA`로 인식됩니다.

> 이 가공은 **`batfish/snapshots/` 아래 사본에만** 적용됩니다. `sites/` 아래 원본 설정 파일은
> 어떤 경우에도 수정되지 않습니다.

### 4-2. 물리 토폴로지 자동 생성

Batfish에게 "어느 포트가 어느 포트에 물려 있는지"를 알려주지 않으면, IP 서브넷만 보고 L3 인접을
추측합니다. 그러면 실제로는 케이블이 없는 곳도 통한다고 계산해서 결과를 믿을 수 없게 됩니다.

다행히 이 저장소의 설정에는 인터페이스 description에 대향 정보가 전부 들어 있습니다.

```
description P2P_s1-spine1_Ethernet2            <- AVD가 생성 (leaf -> spine)
description MLAG_s1-leaf2_Ethernet1            <- AVD가 생성 (MLAG peer-link)
description SERVER_s1-host1_Ethernet1          <- AVD가 생성 (host-facing)
description P2P_LINK_TO_s1-brdr1_Ethernet4     <- dci_configs 수기 작성
description DCI_P2P_LINK_TO_s2-core1_Ethernet4 <- dci_configs 수기 작성 (DC1 <-> DC2)
description PortChan1_s1-leaf1_Ethernet4       <- host_configs 수기 작성
```

`bf_lib.build_layer1()`이 이 description들을 파싱해 `layer1_topology.json`(58개 링크)을 자동 생성합니다.
description이 없는 링크(`s{n}-core1`↔`s{n}-core2`의 포트채널 멤버 — 설정에 `channel-group 16`만 있고
대향 정보가 없습니다)는 `bf_lib.py`의 `L1_OVERRIDES`에 손으로 적어 둡니다.

> 새 장비나 새 링크를 추가했는데 공통 검사의 **물리 토폴로지** 항목이 "대향 미확인 인터페이스"를
> 경고하면, 그 인터페이스에 위 형식의 description이 없다는 뜻입니다. AVD가 만드는 설정이라면
> description은 자동으로 붙으므로, 보통은 정적 설정 쪽에 description을 추가하거나
> `L1_OVERRIDES`에 한 줄 넣으면 해결됩니다.

<br>

## 5. 공통 검사 11종 — 랩과 무관하게 항상 돌리는 것

`make preflight`는 어떤 랩을 하든 아래 11가지를 먼저 확인합니다.

| 검사 | 무엇을 보는가 | 실패하면 |
|---|---|---|
| **설정 파싱** | 24개 파일이 ARISTA로 인식되고 노드가 만들어지는가. Batfish가 이해 못 한 줄 중 **알려진 미지원 문법 목록에 없는 것**이 있는가 | 설정 문법 오류이거나, AVD가 새 기능을 렌더링하기 시작했다는 뜻 |
| **미정의 참조** | 존재하지 않는 ACL/route-map/prefix-list/peer-group을 참조하는 곳이 있는가 | 오타이거나 `group_vars`에서 이름을 잘못 적음 |
| **중복 IP** | 서로 다른 장비가 같은 IP를 들고 있는가. **anycast GW**(`ip address virtual`)와 **MLAG 쌍의 공유 VTEP 주소**는 설계상 정상이므로 제외 | 라우터 ID/Loopback 주소 충돌 — BGP가 안 붙는 대표 원인 |
| **물리 토폴로지** | 모든 Ethernet 인터페이스의 대향이 확인되는가 (§4-2) | description 누락이거나 링크 정의 실수 |
| **L3 링크 MTU** | IP가 붙은 P2P 링크 양단의 MTU가 같은가 | VXLAN 패킷이 조각나거나 OSPF/BGP가 안 붙는 전형적 원인 |
| **BGP 세션 호환성** | 176개 세션의 AS 번호/피어 IP/peer-group 설정이 서로 맞물리는가 (`UNIQUE_MATCH`) | 한쪽에만 네이버를 적었거나 remote-as를 잘못 적음 |
| **BGP 세션 수립(모델)** | 위 세션들이 **언더레이 도달성까지 포함해** 실제로 붙을 수 있는가 (`ESTABLISHED`) | 피어 주소로 가는 경로가 없음 — 링크 shutdown, 언더레이 라우팅 누락 등 |
| **VTEP 간 도달성** | 모든 VXLAN 터널 종단(Loopback1)이 서로 언더레이로 도달 가능한가 (ICMP, 72개 조합) | VXLAN 캡슐화 목적지가 막힘 — **BGP는 멀쩡한데 트래픽만 죽는** 상태 |
| **VXLAN(UDP 4789) 도달성** | 같은 72개 조합을 **실제 VXLAN 패킷(UDP 4789)** 으로 다시 본다 | 경로는 있는데 ACL 등이 UDP 4789만 막음 — **ping까지 되는데 트래픽만 죽는** 상태 (§7-B) |
| **ACL 라인 도달성** | 앞 라인에 가려 절대 매칭되지 않는 ACL 라인(shadowing)이 있는가. ACL이 없으면 SKIP | ACL 순서 실수 — 의도한 허용/차단이 동작하지 않음 |
| **DCI ACL 정책** | Border Leaf의 DCI(core) 방향 인터페이스에 인바운드 ACL이 있으면, 모든 DCI 인터페이스에 빠짐없이 걸렸는지 + 필수 트래픽(ICMP/BGP/BFD multihop/VXLAN) PERMIT, 관리 프로토콜(SSH/Telnet/SNMP) DENY인지. ACL이 없으면 SKIP | 정책 누락/과잉 차단 (§7-B) |

BGP 관련 두 검사의 차이가 중요합니다. **호환성**은 설정 두 개를 나란히 놓고 아귀가 맞는지만 보고,
**수립**은 Batfish가 언더레이 라우팅까지 계산해서 피어 IP에 실제로 패킷이 닿는지를 봅니다.
DCI core 사이 링크를 shutdown하면 호환성은 여전히 PASS지만 수립은 FAIL이 됩니다.

그리고 **VTEP 간 도달성**은 BGP 검사가 전부 통과해도 따로 봐야 합니다. EVPN 피어링은
`Loopback0`(라우터 ID)를 쓰고 VXLAN 캡슐화는 `Loopback1`(VTEP)을 쓰기 때문에, 언더레이에서
VTEP 주소만 막히면 **BGP 세션은 전부 Established인데 호스트 트래픽만 죽습니다**.
`show bgp evpn summary`로는 아무 이상이 보이지 않는 장애이며, §7-A에서 이 상황을 직접 만들어 봅니다.

**VXLAN(UDP 4789) 도달성**을 ICMP 검사와 따로 두는 이유도 같습니다. 경로가 멀쩡해도 중간 ACL이
ICMP와 BGP는 통과시키고 UDP 4789만 막으면, VTEP끼리 ping도 되고 BGP도 붙는데 VXLAN 트래픽만
버려집니다. ICMP로만 보면 PASS가 나오므로 데이터 평면 프로토콜 그대로 한 번 더 봅니다(§7-B).

<br>

## 6. 랩 시나리오별 검증

각 랩에서 `group_vars`를 수정하고 `make build_dc1` / `make build_dc2`를 돌린 **직후**, 배포 전에
해당 랩 번호로 검사를 돌립니다.

```bash
python3 batfish/preflight.py --labs 3        # Lab 3만
python3 batfish/preflight.py --labs 2,3      # Lab 2, 3
make preflight                               # 공통 + Lab 1~6 전체
```

공통 검사 11종은 어떤 경우에도 함께 실행됩니다.

### Lab 1 — VLAN 30/40/50 추가

```bash
make build_dc1 && make build_dc2
python3 batfish/preflight.py --labs 1
```

```
[Lab 1 시나리오 검사]
  [✔] VLAN 30/40/50 SVI/게이트웨이     leaf 8대 모두 VLAN 30,40,50 SVI 존재, anycast GW/VRF 양 DC 동일
  [✔] VLAN 30/40/50 VXLAN VNI 매핑    VLAN 30->VNI 10030  VLAN 40->VNI 10040  VLAN 50->VNI 10050
```

- **SVI/게이트웨이** — leaf 8대(양 DC) 전부에 `Vlan30`/`Vlan40`/`Vlan50`이 있고, VRF가 `A`이며,
  anycast GW IP가 `10.30.30.1`/`10.40.40.1`/`10.50.50.1`로 **양 DC 동일**한지 확인합니다.
  VXLAN 스트레치는 두 DC의 게이트웨이 IP가 같아야 성립하므로, 한쪽 `fabric_services.yml`만 고치고
  다른 쪽을 잊는 실수가 여기서 잡힙니다.
- **VNI 매핑** — `mac_vrf_vni_base: 10000` + VLAN ID 규칙대로 VNI가 붙었는지 확인합니다.
  두 DC의 VNI가 다르면 같은 VLAN이라도 서로 다른 L2 도메인이 됩니다.

### Lab 2 — Border Leaf 편입

```bash
python3 batfish/preflight.py --labs 2
```

```
[Lab 2 시나리오 검사]
  [✔] Border Leaf 편입              Border Leaf 4대 렌더링됨: s1-brdr1, s1-brdr2, s2-brdr1, s2-brdr2
  [✔] Border Leaf ↔ DCI core 언더레이  P2P eBGP 8개 세션 수립 (172.16.255.0/24 대역)
  [✔] Border Leaf 로컬 EVPN 오버레이     spine과 EVPN 세션 8개 수립
```

- **편입** — `inventory.yml`과 `BrdrLeafs` 블록 주석을 풀어야 `s{n}-brdr*.cfg`가 생성됩니다.
  둘 중 하나만 풀면 설정 파일 자체가 안 만들어지므로 여기서 FAIL이 납니다.
- **DCI core 언더레이** — `core_interfaces` 주석을 풀어야 생기는 `172.16.255.x/31` P2P 링크와
  그 위의 eBGP 8개 세션이 **수립 가능한지**까지 봅니다. `core_interfaces`만 잊으면 앞의 두 항목은
  PASS인데 이것만 FAIL이 나서, 세 곳 중 어디를 빠뜨렸는지 바로 알 수 있습니다.
- **로컬 EVPN 오버레이** — Border Leaf가 자기 DC의 spine과 EVPN 세션을 맺는지 확인합니다.
  이 시점에는 반대쪽 DC와의 세션이 **없는 것이 정상**입니다(그게 Lab 3).

### Lab 3 — EVPN Gateway 활성화

```bash
python3 batfish/preflight.py --labs 3
```

```
[Lab 3 시나리오 검사]
  [✔] EVPN Gateway 원격 피어링    DC 간 EBGP_MULTIHOP EVPN 세션 8개 수립 (Loopback0 10.1.0.x ↔ 10.1.0.1xx)
  [✔] EVPN 경로 재발신 표시        'domain remote'가 Border Leaf 4대에만 존재: s1-brdr1, s1-brdr2, s2-brdr1, s2-brdr2
  [✔] VTEP 간 언더레이 도달성       s1-leaf1(10.1.1.14) → s2-leaf1(10.1.1.114) 경로 32개 ACCEPTED
        s1-leaf1 → s1-spine1 → s1-brdr1 → s1-core1 → s2-core1 → s2-brdr1 → s2-spine1 → s2-leaf1
```

이 랩이 Batfish의 가치가 가장 잘 드러나는 지점입니다.

- **원격 피어링** — `evpn_gateway` 주석을 풀면 생기는 DC 간 EVPN 세션이 실제로 붙을 수 있는지
  검증합니다. 이건 **멀티홉** eBGP라서, `10.1.0.2`(s1-brdr1 Loopback0)에서 `10.1.0.102`(s2-brdr1
  Loopback0)까지 DCI를 넘어가는 언더레이 경로가 살아 있어야만 성립합니다. Batfish는 그 경로를
  실제로 계산해서 답을 냅니다 — 배포하지 않고도 "붙을 것"임을 알 수 있습니다.
- **재발신 표시** — `rd evpn domain remote` / `route-target ... domain remote` 설정이 Border Leaf
  **에만** 있는지 봅니다. leaf에 이게 나타나면 `filter.tenants`나 node_group 배치가 잘못된 것입니다.
  (Batfish는 EVPN 재발신 자체를 모델링하지 않으므로 이 항목만 설정 텍스트로 확인합니다.)
- **VTEP 도달성** — DC1 leaf의 VTEP 주소에서 DC2 leaf의 VTEP 주소까지 traceroute를 시뮬레이션합니다.
  결과에 전체 경로(spine → brdr → core → core → brdr → spine → leaf)가 그대로 나오므로, 트래픽이
  의도한 대로 Border Leaf와 DCI를 경유하는지 눈으로 확인할 수 있습니다. 경로가 32개인 것은
  spine 2대 × brdr 2대 × core 2쌍 × 목적지 MLAG 2대의 ECMP 조합입니다.

### Lab 4 — New-Tenant, VLAN별 전용 VRF

```bash
python3 batfish/preflight.py --labs 4
```

```
[Lab 4 시나리오 검사]
  [✔] VLAN 100/200 SVI/게이트웨이    leaf 8대 모두 VLAN 100,200 SVI 존재, anycast GW/VRF 양 DC 동일
  [✔] VLAN 100/200 VXLAN VNI 매핑   VLAN 100->VNI 20100  VLAN 200->VNI 20200
  [✔] 테넌트 VRF 분리               leaf 8대에 vrf 100 / vrf 200 인스턴스 존재 (VLAN별 전용 VRF)
  [✔] VRF 100/200 격리             VRF 100 라우팅 테이블에 VLAN 200 대역(10.200.200.0/24) 경로 없음
```

- **SVI/VNI/VRF 인스턴스** — Lab 1과 같은 검사지만 기대 VRF가 `A`가 아니라 `100`/`200`입니다.
  Lab 4의 핵심 함정 — `fabric_services.yml`의 tenant 주석만 풀고 `fabric.yml`의 `filter.tenants`에
  `New-Tenant`를 추가하지 않으면 **아무 leaf에도 렌더링되지 않는다** — 가 여기서 바로 잡힙니다.
  그 경우 세 항목이 한꺼번에 FAIL로 나옵니다.
- **VRF 격리** — VRF `100`의 라우팅 테이블을 실제로 뽑아서 `10.200.200.0/24` 경로가 새어 들어오지
  않았는지 확인합니다. route-target을 잘못 적어 VRF가 의도치 않게 이어지는 사고를 배포 전에 잡습니다.
  이건 `show`로 확인하려면 배포 후 각 leaf에 들어가야 하는 항목입니다.

### Lab 5 — DCI Core CloudVision 태그

```bash
python3 batfish/preflight.py --labs 5
```

```
[Lab 5 시나리오 검사]
  [✔] DCI core 설정 파싱        core 4대 파싱/라우팅 모델 정상: s1-core1, s1-core2, s2-core1, s2-core2
  [✔] CVP topology 태그 변수     cv_device_tags 활성: sites/dc1/group_vars/dc1_dci.yml, sites/dc2/group_vars/dc2_dci.yml
```

Lab 5는 CVP 메타데이터(태그)만 다루고 장비 설정은 바꾸지 않으므로 **Batfish가 직접 검증할 대상이
아닙니다**. 대신 두 가지를 봅니다.

- core 4대의 설정이 여전히 정상 파싱되는지 (태그 작업 중 설정을 건드리지 않았는지 확인)
- `dc{n}_dci.yml`의 `cv_device_tags`가 주석 해제되어 활성 상태인지 (YAML 직접 확인)

### Lab 6 — Connectivity Monitoring

```bash
python3 batfish/preflight.py --labs 6
```

```
[Lab 6 시나리오 검사]
  [✔] 프로브 소스 Loopback210      leaf 4대에 VRF A 전용 /32 고유 주소 구성
        s1-leaf1: 10.255.10.14/32 (vrf A)
        s1-leaf2: 10.255.10.16/32 (vrf A)
        s2-leaf3: 10.255.10.115/32 (vrf A)
        s2-leaf4: 10.255.10.117/32 (vrf A)
  [✔] virtual source-nat 짝 맞춤   4대 모두 Loopback210 + source-nat 쌍 구성
  [✔] 프로브 경로 s1-leaf1 → s2-host2   10.255.10.14 → 10.10.10.22 ACCEPTED
  [✔] 프로브 경로 s1-leaf2 → s2-host2   10.255.10.16 → 10.10.10.22 ACCEPTED
  [✔] 프로브 경로 s2-leaf3 → s1-host1   10.255.10.115 → 10.10.10.11 ACCEPTED
  [✔] 프로브 경로 s2-leaf4 → s1-host1   10.255.10.117 → 10.10.10.11 ACCEPTED
```

- **Loopback210** — 랩 가이드가 강조하는 두 가지 실수(주소를 leaf마다 다르게 줄 것, VRF는 `A`일 것)를
  그대로 검사합니다. `id` 값을 복사하다 두 leaf에 같은 `/32`를 주면 여기서 FAIL입니다.
- **source-nat 짝 맞춤** — `loopback_interfaces`와 `virtual_source_nat_vrfs`는 항상 짝으로 다녀야
  하는데, 한쪽만 적는 실수가 흔합니다. Loopback210이 있는 장비 집합과 source-nat이 설정된 장비
  집합이 정확히 같은지 비교합니다.
- **프로브 경로** — 각 leaf의 프로브 소스 주소에서 감시 대상 호스트까지 실제로 패킷이 닿는지
  시뮬레이션합니다. 배포 후 `show monitor connectivity`에서 `Packet Loss 0%`가 나올지를
  배포 전에 미리 아는 셈입니다.

<br>

## 7. 검사기 자체를 믿을 수 있는가 — 자가 진단

"전부 PASS"라는 결과는 검사가 아무것도 안 하고 있어도 나옵니다. 그래서 **일부러 고장을 낸 설정에
대해 정말 FAIL이 나는지** 확인하는 자가 진단을 함께 둡니다.

```bash
make preflight_selftest
```

정상 스냅샷을 복제한 뒤 사본에만 일곱 가지 고장을 주입하고, 해당 검사가 FAIL로 바뀌는지 봅니다
(저장소의 원본 설정은 건드리지 않습니다).

| 주입한 고장 | 기대 결과 | 실제 결과 |
|---|---|---|
| Border Leaf에서 원격 EVPN 피어링/`domain remote` 제거 (Lab 3 미적용 상태 재현) | Lab 3 두 항목 FAIL | FAIL — "DC 간 brdr↔brdr EVPN 세션 없음 (evpn_gateway 블록 주석 해제 필요)" |
| DCI 방향 P2P 링크 한쪽 MTU만 9214 → 1500 | L3 링크 MTU FAIL | FAIL — 1개 링크 MTU 불일치 |
| 서로 다른 leaf에 같은 Loopback0 주소 부여 | 중복 IP FAIL | FAIL — 중복 IP 1건, 연쇄로 BGP 세션 4개도 FAIL |
| DCI core 간 링크 shutdown | BGP 세션 수립 FAIL | FAIL — 2개 세션 수립 불가 (호환성은 여전히 PASS) |
| Edge(Border Leaf)에서 원격 VTEP(`10.1.1.102`)을 Null0으로 블랙홀 | VTEP 간 도달성 FAIL | FAIL — 도달 불가 6건. **BGP 세션 수립·EVPN Gateway 피어링은 PASS 유지** |
| DCI ACL(`DCI-EDGE-IN`)에서 VXLAN(UDP 4789) 허용 줄 누락 | VXLAN(UDP 4789) 도달성 + DCI ACL 정책 FAIL | FAIL — UDP 4789 도달 불가 6건, `1000 deny ip any any`에 걸림. **ICMP VTEP 검사·BGP 수립은 PASS 유지** |
| DCI ACL에 `15 deny tcp any any`를 끼워 넣어 BGP 허용 줄을 가림 | ACL 라인 도달성 + DCI ACL 정책 + BGP 세션 수립 FAIL | FAIL — 가려진 라인 2건, BGP 세션 16개 수립 불가, 연쇄로 VTEP 도달성도 FAIL |

마지막 두 케이스는 부수적으로 배울 점이 있습니다.

- **라우터 ID 중복**은 중복 IP 검사뿐 아니라 BGP 세션 호환성/수립까지 연쇄로 FAIL시킵니다 —
  하나의 실수가 여러 검사에 나타나는 것이 정상입니다.
- **DCI core 링크 하나를 죽여도** Lab 3의 "VTEP 간 언더레이 도달성"은 여전히 PASS입니다.
  `s1-core2 ↔ s2-core2` 경로가 살아 있기 때문이고, 이건 이 설계가 **의도한 이중화가 실제로
  동작한다**는 증거입니다(경로 수가 32개에서 16개로 줄어든 것으로 확인됩니다).


<br>

## 7-A. 실습 — Edge에서 통신을 끊어 보고 Batfish가 잡는지 확인

앞의 자가 진단은 스냅샷 사본만 건드립니다. 이번에는 **실제 랩에 장애를 만들어 보고**, 배포 전에
Batfish가 그걸 잡아내는지, 그리고 배포한 뒤 다른 도구들은 그 장애를 보는지 비교합니다.

### 왜 이 시나리오인가

DC 간 통신이 끊기는 방식 중 가장 찾기 어려운 것은 **제어 평면은 멀쩡한데 데이터 평면만 죽는** 경우입니다.
이 패브릭에서 두 평면은 서로 다른 주소를 씁니다.

| | 쓰는 주소 | 이 랩의 값 |
|---|---|---|
| EVPN 피어링 (제어 평면) | `Loopback0` — 라우터 ID | `10.1.0.2` ↔ `10.1.0.102` |
| VXLAN 캡슐화 (데이터 평면) | `Loopback1` — VTEP | `10.1.1.2` ↔ `10.1.1.102` |

그래서 **VTEP 주소로 가는 경로만 막으면** BGP 세션은 전부 `Established`로 남고 경로 교환도 계속되는데
호스트 트래픽만 사라집니다. `show bgp evpn summary`로는 아무 이상이 보이지 않습니다.

Edge(Border Leaf, `s1-brdr1`/`s1-brdr2`)를 무대로 삼는 이유는 **DC 간 트래픽이 반드시 여기를 지나기**
때문입니다. Lab 3의 EVPN Gateway가 경로를 재발신하므로, DC1 leaf가 보는 DC2 호스트의 next-hop은
DC2 leaf가 아니라 자기 DC의 Border Leaf VTEP(`10.1.1.2`)이고, 그 Border Leaf가 다시
`10.1.1.102`(DC2 Border Leaf VTEP)로 캡슐화해 DCI를 건넙니다. 실제 장비에서 확인할 수 있습니다.

```
$ ssh s1-leaf1
s1-leaf1# show bgp evpn route-type mac-ip vni 10010

          Network                        Next Hop     ...  Path
 * >Ec    RD: 10.1.0.2:10010 mac-ip 001c.73c0.c627 10.10.10.22
                                       10.1.1.2      ...  65000 65099 65199 65100 65102 i
```

`10.1.1.2` — DC2 호스트인데 next-hop이 **DC1 자기 쪽 Border Leaf의 VTEP**입니다. 즉 이 한 주소
(`10.1.1.102`)를 Edge에서 막으면 DC1 ↔ DC2 전체가 끊깁니다.

### 1) 장애 주입 — `group_vars`에 잘못된 정적 경로 한 줄

Border Leaf는 AVD가 관리하는 장비이므로, 장비에 직접 손대는 대신 **AVD 입력 파일을 고칩니다**.
실제 현장에서 사고가 나는 방식 그대로입니다. `sites/dc1/group_vars/dc1_fabric.yml`의 `BrdrLeafs`
블록에 이미 주석 처리된 채로 준비되어 있으니 주석만 해제하세요.

```yaml
    - group: BrdrLeafs
      structured_config:
        router_bgp:
          address_family_ipv4:
            networks:
              - prefix: 10.231.0.2/32
              ...
        static_routes:
          - prefix: 10.1.1.102/32
            interface: 'null0'
```

> AVD 6.0.0부터 `destination_address_prefix` 키가 `prefix`로 바뀌었습니다. 예전 표기로 쓰면
> `make build_dc1`이 스키마 검증에서 바로 실패합니다.

```bash
make build_dc1
grep "^ip route" sites/dc1/intended/configs/s1-brdr1.cfg
```

```
ip route 0.0.0.0/0 192.168.0.1
ip route 10.1.1.102/32 Null0        <- 주입된 장애
```

### 2) 배포 전 — Batfish가 잡아냅니다

```bash
make preflight
```

```
[공통 검사]
  [✔] 설정 파싱              24개 파일 모두 ARISTA로 파싱, 노드 24개
  [✔] 중복 IP               설계상 공유 주소 외 중복 없음
  [✔] 물리 토폴로지            L1 링크 58개 / L3 인접 624개
  [✔] L3 링크 MTU           IP가 붙은 모든 P2P 링크의 양단 MTU 일치
  [✔] BGP 세션 호환성          176개 세션 모두 UNIQUE_MATCH
  [✔] BGP 세션 수립(모델)       176개 세션 모두 ESTABLISHED          <- 제어 평면은 멀쩡
  [✘] VTEP 간 도달성          ICMP: VTEP 6개 중 도달 불가 조합 6건 — VXLAN 터널 단절
        s1-brdr1 10.1.1.2  → 10.1.1.102: NULL_ROUTED (s1-brdr1)
        s1-brdr2 10.1.1.2  → 10.1.1.102: NULL_ROUTED (s1-brdr2)
        s1-leaf1 10.1.1.14 → 10.1.1.102: NO_ROUTE (s1-leaf1)
        s1-leaf2 10.1.1.14 → 10.1.1.102: NO_ROUTE (s1-leaf2)
        s1-leaf3 10.1.1.15 → 10.1.1.102: NO_ROUTE (s1-leaf3)
        s1-leaf4 10.1.1.15 → 10.1.1.102: NO_ROUTE (s1-leaf4)
  [✘] VXLAN(UDP 4789) 도달성   UDP 4789: VTEP 6개 중 도달 불가 조합 6건 — 같은 원인
  [-] ACL 라인 도달성          스냅샷에 IP ACL이 없음
  [-] DCI ACL 정책            Border Leaf DCI 방향 인터페이스 8개에 인바운드 ACL 없음

[Lab 3 시나리오 검사]
  [✔] EVPN Gateway 원격 피어링   DC 간 EBGP_MULTIHOP EVPN 세션 8개 수립   <- 여기도 멀쩡
  [✔] VTEP 간 언더레이 도달성      s1-leaf1 → s2-leaf1 경로 32개 ACCEPTED   <- leaf↔leaf는 살아 있음

PASS 27 / FAIL 2 / SKIP 2
```

읽을 거리가 많은 출력입니다.

- **Edge에서는 `NULL_ROUTED`** — 정적 경로가 Null0으로 흘려보내고 있음을 정확히 짚습니다.
- **leaf에서는 `NO_ROUTE`** — Edge가 그 경로를 언더레이로 광고하지 않게 되어, leaf에는 아예 경로가 없습니다.
  하나의 원인이 위치에 따라 다른 증상으로 나타나는 것을 보여줍니다.
- **BGP 검사 세 개는 전부 PASS** — 제어 평면만 보는 검사로는 이 장애를 절대 찾을 수 없습니다.
- **Lab 3의 leaf↔leaf VTEP 검사도 PASS** — `10.1.1.114`(DC2 leaf VTEP)로 가는 경로는 막지 않았기
  때문입니다. 그래서 "대표 경로 하나만 확인"하는 방식으로는 부족하고, **모든 VTEP 조합**을 봐야 합니다.
  공통 검사의 VTEP 도달성이 이 역할을 합니다.

여기서 멈추고 주석을 다시 채우면, 장애는 장비에 닿지도 못하고 끝납니다. 아래는 "만약 그대로 배포했다면"을
확인하려는 경우입니다.

### 3) 배포 후 — 다른 도구들은 이걸 보지 못합니다

```bash
make deploy_dc1_eapi
```

ANTA 결과는 장애가 없을 때와 **똑같습니다**(추가로 뜬 `VerifyRunningConfigDiffs` 2건은 running-config와
startup-config 차이일 뿐, 장애 탐지가 아닙니다).

```
s1-brdr1  VerifyBGPPeerSession      success
s1-brdr1  VerifyVxlanConfigSanity   success
s1-leaf1  VerifyBGPPeerSession      success
s1-leaf1  VerifyVxlanConfigSanity   success
```

EVPN 세션도 정상으로 보입니다.

```
s1-brdr1# show bgp evpn summary
  Description   Neighbor    V AS      MsgRcvd MsgSent Up/Down State  PfxRcd
  s2-brdr1      10.1.0.102  4 65199       319     308 01:50:18 <Estab>  51
  s2-brdr2      10.1.0.104  4 65199       317     303 01:50:19 <Estab>  51
```

그런데 호스트 통신은 전부 끊겨 있습니다.

```
s1-host1 → s2-host1 VLAN10   vrf 10  -> 10.10.10.21    0 received | 100% packet loss
s1-host1 → s2-host2 VLAN10   vrf 10  -> 10.10.10.22    0 received | 100% packet loss
s1-host1 → s2-host1 VLAN20   vrf 20  -> 10.20.20.21    0 received | 100% packet loss
s1-host1 → s2-host1 VLAN100  vrf 100 -> 10.100.100.21  0 received | 100% packet loss
s1-host1 → s2-host1 VLAN200  vrf 200 -> 10.200.200.21  0 received | 100% packet loss
s1-host1 → 로컬 anycast GW    vrf 10  -> 10.10.10.1     5 received | 0% packet loss   <- DC 내부는 정상
```

원인은 Edge의 라우팅 테이블 한 줄입니다.

```
s1-brdr1# show ip route 10.1.1.102
 S        10.1.1.102/32
           directly connected, Null0
```

### 4) 원상 복구

`group_vars`의 주석을 되돌리고 다시 빌드합니다. 다만 `eos_config`는 **없는 줄을 추가할 뿐 남은 줄을
지우지는 않으므로**, 이미 배포했다면 장비에서 정적 경로를 명시적으로 제거해야 합니다.

```bash
# 1) group_vars의 static_routes를 다시 주석 처리
make build_dc1

# 2) 이미 배포했다면 장비에서 직접 제거
ansible -i sites/dc1/inventory.yml s1-brdr1,s1-brdr2 \
  -m arista.eos.eos_config -a "lines='no ip route 10.1.1.102/32 Null0'"

# 3) 확인
make preflight        # PASS 29 / FAIL 0 / SKIP 2
```

```
s1-brdr1# show ip route 10.1.1.102
 B E      10.1.1.102/32 [20/0]
           via 172.16.255.1, Ethernet4
           via 172.16.255.3, Ethernet5
```

BGP가 학습한 ECMP 경로로 돌아오고, 호스트 통신도 모두 0% 손실로 복구됩니다.

### 이 실습이 말하는 것

| 도구 | 이 장애를 잡았는가 |
|---|---|
| **Batfish 사전 검증** (배포 전) | ✔ `VTEP 간 도달성` — 원인 위치(`s1-brdr1` Null0)까지 지목 |
| Batfish의 BGP 검사 | ✘ 176개 세션 전부 정상으로 판정 (실제로도 정상이므로 올바른 판정) |
| ANTA (배포 후) | ✘ BGP·VXLAN 설정 검사 모두 통과 |
| `show bgp evpn summary` | ✘ 세션 `Estab`, 경로 51개 수신 — 이상 없음 |
| 호스트 `ping` | ✔ 100% 손실 — 하지만 **이미 장애가 난 뒤** |

제어 평면만 보는 검사는 이 장애에 대해 원리적으로 침묵합니다. 데이터 평면 경로를 직접 계산해 보는
검사만이 **배포 전에** 잡을 수 있고, 그게 Batfish를 파이프라인에 넣는 이유입니다.

<br>

## 7-B. 실습 — DCI 경계 ACL: ping은 되는데 VXLAN만 막히는 장애

§7-A는 **경로**를 망가뜨렸습니다. 이번에는 경로는 그대로 두고 **ACL**로 같은 종류의 장애를 만듭니다.
현장에서 훨씬 자주 일어나는 유형입니다. 보안팀 요청으로 DCI 경계 ACL을 "꼭 필요한 것만" 남기도록
조이다가 VXLAN 한 줄을 빠뜨리는 식입니다.

### 무엇이 DCI를 건너는가

ACL을 쓰려면 먼저 DCI(core ↔ Border Leaf) 링크를 지나는 트래픽을 전부 알아야 합니다.
이 패브릭에서는 다섯 종류뿐입니다.

| 트래픽 | 프로토콜/포트 | 어디서 어디로 |
|---|---|---|
| 언더레이 eBGP | TCP 179 | Border Leaf ↔ core (`172.16.255.x/31`, single-hop, BFD 없음) |
| EVPN Gateway 피어링 | TCP 179 | `s1-brdr` Loopback0 ↔ `s2-brdr` Loopback0 (`ebgp-multihop 15`) |
| EVPN 피어 BFD | UDP 4784 (multihop BFD) | `EVPN-OVERLAY-REMOTE-PEERS bfd` |
| VXLAN 데이터 평면 | UDP 4789 | `10.1.1.2` ↔ `10.1.1.102` (Border Leaf VTEP 간) |
| 트러블슈팅 | ICMP | — |

DC 간 호스트 트래픽은 전부 VXLAN 안에 캡슐화되어 지나가므로 ACL에 호스트 대역을 적을 필요가 없습니다.

### 1) 정상 정책 적용 — PASS

`sites/dc1/group_vars/dc1_fabric.yml`의 `BrdrLeafs` 블록에서 §7-B 주석 블록 전체를 해제합니다.

```yaml
        ip_access_lists:
          - name: DCI-EDGE-IN
            counters_per_entry: true
            entries:
              - {sequence: 10, action: permit, protocol: icmp, source: any, destination: any}
              - {sequence: 20, action: permit, protocol: tcp, source: any, destination: any, destination_ports_match: eq, destination_ports: [bgp]}
              - {sequence: 30, action: permit, protocol: tcp, source: any, source_ports_match: eq, source_ports: [bgp], destination: any}
              - {sequence: 40, action: permit, protocol: udp, source: any, destination: any, destination_ports_match: eq, destination_ports: ["4784"]}
              - {sequence: 50, action: permit, protocol: udp, source: any, destination: any, destination_ports_match: eq, destination_ports: ["4789"]}
              - {sequence: 1000, action: deny, protocol: ip, source: any, destination: any}
        ethernet_interfaces:
          - {name: Ethernet4, access_group_in: DCI-EDGE-IN}
          - {name: Ethernet5, access_group_in: DCI-EDGE-IN}
```

> `core_interfaces.p2p_links`에는 ACL 키가 없어서 `structured_config`로 넣습니다.
> `ethernet_interfaces`는 이름 기준으로 AVD가 만든 인터페이스 설정에 **병합**되므로 `ip access-group`
> 한 줄만 추가됩니다. 마지막 deny에 `log`를 붙이면 cEOS가 "data-plane에서 지원하지 않는 옵션"
> 경고를 내므로 빼 두었습니다.

```bash
make build_dc1 && make preflight
```

```
  [✔] BGP 세션 수립(모델)       176개 세션 모두 ESTABLISHED
  [✔] VTEP 간 도달성           ICMP: VTEP 6개 × 출발 노드 12대 = 72개 조합 모두 도달 가능
  [✔] VXLAN(UDP 4789) 도달성   UDP 4789: VTEP 6개 × 출발 노드 12대 = 72개 조합 모두 도달 가능
  [✔] ACL 라인 도달성          IP ACL 2개(장비별)의 모든 라인이 매칭 가능
  [✔] DCI ACL 정책            4개 인터페이스에 'DCI-EDGE-IN' 적용, 필수 허용 5종 PERMIT / 관리 프로토콜 3종 DENY 확인
```

배포(`make deploy_dc1_cvp`)한 뒤 장비에서 카운터를 보면 위 표의 트래픽이 실제로 각 줄에 매칭됩니다.
cEOS도 인바운드 ACL을 실제로 적용합니다.

```
s1-brdr1# show ip access-lists DCI-EDGE-IN
IP Access List DCI-EDGE-IN
        counters per-entry
        10 permit icmp any any
        20 permit tcp any any eq bgp [match 19 packets, 0:00:01 ago]
        30 permit tcp any eq bgp any [match 7 packets, 0:00:20 ago]
        40 permit udp any any eq multihop-bfd [match 1315 packets, 0:00:01 ago]
        50 permit udp any any eq 4789 [match 692 packets, 0:00:01 ago]
        1000 deny ip any any
        Configured on Ingress: Et4-5
        Active on     Ingress: Et4-5
```

호스트 간 cross-DC ping(`ping vrf 10/20/100/200`, 4대 × 4 VRF = 16건)도 전부 성공합니다.

### 2) 장애 주입 — seq 50 한 줄만 주석

```yaml
              - {sequence: 40, ...  destination_ports: ["4784"]}
              # - {sequence: 50, ... destination_ports: ["4789"]}     <- VXLAN 허용 줄 누락
```

```bash
make build_dc1 && make preflight
```

```
  [✔] BGP 세션 수립(모델)       176개 세션 모두 ESTABLISHED                         <- 제어 평면 정상
  [✔] VTEP 간 도달성           ICMP: VTEP 6개 × 출발 노드 12대 = 72개 조합 모두 도달 가능 <- ping도 정상
  [✘] VXLAN(UDP 4789) 도달성   UDP 4789: VTEP 6개 중 도달 불가 조합 6건 — VXLAN 터널 단절
  [✔] ACL 라인 도달성          IP ACL 2개(장비별)의 모든 라인이 매칭 가능
  [✘] DCI ACL 정책            4개 인터페이스 중 정책 위반 2건
        s1-brdr1 DCI-EDGE-IN: VXLAN (UDP 4789) 기대 PERMIT / 실제 DENY (1000 deny ip any any)
        s1-brdr2 DCI-EDGE-IN: VXLAN (UDP 4789) 기대 PERMIT / 실제 DENY (1000 deny ip any any)

PASS 9 / FAIL 2          (--labs none 기준)
```

**ICMP로 보는 VTEP 검사는 PASS**입니다. 이 검사만 있었다면 놓쳤을 장애이고, 그래서 UDP 4789 검사를
따로 둡니다. DCI ACL 정책 검사는 어느 장비의 어느 줄(`1000 deny`)에 걸리는지까지 알려 줍니다.

### 3) 배포 후 — 실제 랩에서도 예측과 똑같이 동작합니다

검증용으로 이 상태를 실제로 배포해 보면(ATD, cEOS 4.36.0.1F에서 확인):

```
s1-brdr1# show bgp evpn summary
  s2-brdr1    10.1.0.102 4 65199   ...  00:58:04 Estab   72  72  120     <- EVPN 세션 정상

s1-brdr1# ping 10.1.1.102 source Loopback1
3 packets transmitted, 3 received, 0% packet loss                       <- VTEP 간 ping 정상

s1-brdr1# show ip access-lists DCI-EDGE-IN
        40 permit udp any any eq multihop-bfd [match 4214 packets, ...]
        1000 deny ip any any [match 128 packets, 0:00:00 ago]          <- VXLAN이 여기서 버려짐

s1-host1 vrf 10  -> 10.10.10.21    0 received                           <- cross-DC 16건 전부 실패
```

`show bgp evpn summary`, VTEP ping, ANTA의 BGP 검사로는 보이지 않고, `1000 deny` 카운터가
올라가는 것을 직접 봐야만 원인을 알 수 있습니다. Batfish는 이것을 **배포 전에** 잡았습니다.

### 4) 원상 복구

블록 전체를 다시 주석 처리하고 빌드·배포합니다. CloudVision 배포(`make deploy_dc1_cvp`)는 설정 전체를
교체하므로 ACL과 `ip access-group`이 장비에서 함께 지워집니다(`eos_config`로 배포했다면
`no ip access-list DCI-EDGE-IN`과 인터페이스별 `no ip access-group DCI-EDGE-IN in`을 직접 넣어야 합니다).

```bash
make build_dc1 && make preflight      # PASS 29 / FAIL 0 / SKIP 2 (ACL 검사 두 개는 SKIP)
make deploy_dc1_cvp
```

### 참고 — 또 하나의 ACL 실수: 라인 순서

`make preflight_selftest`의 7번째 케이스는 정상 ACL의 seq 15에 `deny tcp any any`를 끼워 넣습니다.
문법상 정상이라 장비는 그대로 받아들이지만 뒤의 BGP 허용 줄 두 개가 절대 매칭되지 않습니다.

```
  [✘] ACL 라인 도달성     절대 매칭되지 않는 ACL 라인 2건 (앞 라인에 가려짐)
  [✘] BGP 세션 수립(모델)  16/176 세션이 수립 불가
  [✘] DCI ACL 정책       BGP 접속 (dst TCP 179) 기대 PERMIT / 실제 DENY (15 deny tcp any any)
```

이번에는 BGP가 죽으므로 언더레이 경로가 빠지고, 연쇄로 VTEP 도달성까지 FAIL이 됩니다.
**ACL 라인 도달성**은 이런 순서 실수를 원인 그대로(어느 줄이 어느 줄을 가렸는지) 짚어 줍니다.

### 이 실습이 말하는 것

| 확인 방법 | VXLAN 줄 누락을 잡았는가 |
|---|---|
| Batfish `VXLAN(UDP 4789) 도달성` / `DCI ACL 정책` (배포 전) | ✔ 원인 장비·ACL 줄까지 지목 |
| Batfish `VTEP 간 도달성` (ICMP) | ✘ PASS — ICMP는 허용되므로 |
| `show bgp evpn summary` / ANTA BGP 검사 | ✘ 세션 `Estab` |
| VTEP 간 `ping` | ✘ 성공 |
| 호스트 `ping` | ✔ 100% 손실 — **이미 장애가 난 뒤** |

같은 "도달성" 검사라도 **어떤 프로토콜로 보느냐**에 따라 결과가 달라집니다. ACL이 있는 경로는
실제로 흐를 트래픽의 프로토콜/포트 그대로 검증해야 합니다.

<br>

## 8. 랩 진행 순서에 끼워 넣기

Lab 1~6 어디서든 아래 순서를 따르면 됩니다.

```bash
# 0) 최초 1회 (또는 ATD 랩 재시작 후)
make bf_install          # 재시작 후에는 보통 bf_start만 하면 됩니다
make bf_start

# 1) group_vars 수정 후
make build_dc1
make build_dc2

# 2) 배포 전 검증  ★
python3 batfish/preflight.py --labs <랩번호>
#    FAIL이 있으면 group_vars로 돌아가 고치고 1)부터 다시

# 3) 배포
make deploy_dc1_cvp && make deploy_dc2_cvp     # 또는 _eapi

# 4) 배포 후 검증
make verify_dc1 && make verify_dc2             # ANTA
#    호스트 간 실제 통신 확인 (ping vrf <n> <ip>)
```

검사 결과는 콘솔 출력 외에 `batfish/reports/preflight_<대상>_<타임스탬프>.md`로도 남습니다
(표 형식 요약 + 항목별 상세). 이 디렉토리와 `batfish/snapshots/`는 매번 다시 생성되는 산출물이라
`.gitignore`에 들어 있습니다.

<br>

## 9. Batfish가 보지 못하는 것

사전 검증을 신뢰하려면 한계도 정확히 알아야 합니다. 이 랩 환경에서 확인된 것들입니다.

- **배포됐는지 여부** — Batfish는 `intended/configs/`를 읽습니다. 그 설정이 실제 장비에 올라갔는지는
  모릅니다. 실제로 이 저장소에서 pre-flight는 전부 PASS였지만 DCI core 4대에 설정이 배포되어 있지
  않아 ANTA가 BGP 실패를 잡아낸 사례가 있습니다
  (`lab guide/batfish-avd-anta-verification-report.md` §5).
- **EVPN 컨트롤 플레인의 세부 동작** — BGP EVPN 세션이 붙을지는 계산하지만, Type-2/Type-5 경로가
  어떻게 전파되고 Border Leaf가 어떻게 재발신하는지는 모델링하지 않습니다. `domain remote` 관련
  설정은 텍스트 존재 여부로만 확인합니다.
- **VXLAN 데이터 플레인의 정확한 경로** — VNI/flood-list는 읽지만, 같은 서브넷 안의 호스트 간
  통신(예: `s1-host1` → `s2-host1`, 둘 다 `10.10.10.0/24`)은 L2로 취급해 곧바로 도달한다고
  판정합니다. 그래서 **호스트 간 traceroute를 그대로 믿으면 안 됩니다** — §7-A에서 실제로 통신이
  완전히 끊긴 상태에서도 Lab 6의 프로브 경로 검사는 `ACCEPTED`로 나왔습니다.
  대신 그 통신이 성립하기 위한 전제(**VTEP 간 도달성**, VNI 일치, EVPN 세션)를 각각 검증하는 쪽으로
  우회했고, §7-A의 장애를 잡아낸 것도 호스트 경로가 아니라 VTEP 도달성 검사입니다. 최종 확인은
  배포 후 실제 `ping`으로 해야 한다는 점은 그대로입니다.
- **`monitor connectivity`, `ip address virtual source-nat` 등 EOS 고유 기능** — 문법을 파싱하지
  못합니다(§5의 "알려진 미지원 문법"). 그래서 Lab 6 검사는 Loopback 주소와 경로 도달성처럼
  Batfish가 다룰 수 있는 부분으로 우회해 확인합니다.
- **물리 계층** — 케이블 오배선, 트랜시버 불량, 링크 플랩은 알 수 없습니다. §4-2의 토폴로지는
  description을 근거로 만든 "설정상의 의도"이지 실제 배선이 아닙니다.

<br>

## 10. 문제 해결

**`make bf_start` 후 `stopped`가 나옵니다**
`../batfish-service/logs/batfish_service.log`를 확인하세요. `UnsupportedClassVersionError ... class file version 65.0`
이면 Java가 너무 오래된 것입니다(OpenJDK 17로 최신 jar를 실행한 경우). `make bf_install`을 다시 실행하면
`../batfish-service/jre/`에 Java 25를 받아 두고, `batfishctl.sh`가 그것을 사용합니다. `NoSuchFileException: allinone-bundle.jar`이면
설치가 덜 된 것이니 `make bf_install`을 다시 실행합니다. 메모리 부족(`OutOfMemoryError`)이면
`batfishctl.sh`의 `-Xmx3g`를 낮춰 보세요.

**검사가 `Work terminated abnormally`로 죽습니다**
서비스가 재시작됐거나 스냅샷 경로가 바뀐 경우입니다. `make bf_stop && make bf_start` 후 다시 실행하세요.

**"설정 파싱"이 WARN으로 "미분류 경고"를 보고합니다**
AVD 버전을 올렸거나 새 기능을 켜서 Batfish가 모르는 설정 줄이 생겼다는 뜻입니다. 경고에 찍힌 줄을
보고 문제가 없는 문법이면 `batfish/preflight.py`의 `KNOWN_UNSUPPORTED` 목록에 패턴을 추가하세요.

**"물리 토폴로지"가 대향 미확인 인터페이스를 경고합니다**
§4-2를 참고해 해당 인터페이스에 `..._<대향장비>_<대향인터페이스>` 형식 description을 넣거나
`bf_lib.py`의 `L1_OVERRIDES`에 링크를 추가하세요.

**BGP 세션 수립이 FAIL인데 실제 장비에서는 잘 붙습니다**
Batfish가 언더레이 경로를 계산하지 못한 것이므로, 대개 토폴로지가 불완전합니다(위 항목 참고).
반대로 **Batfish는 PASS인데 실제로 안 붙는다면** 배포 누락이나 물리 장애를 의심하세요 — 그게
ANTA가 담당하는 영역입니다.

<br>

## 부록 — 저장소에 추가된 파일

| 경로 | 역할 |
|---|---|
| `batfish/install_batfish.sh` | JRE + Batfish 서비스 + pybatfish 설치 (`make bf_install`) |
| `batfish/batfishctl.sh` | 서비스 start/stop/restart/status/log (`make bf_start` 등) |
| `batfish/bf_lib.py` | 스냅샷 빌더 — 설정 정규화, `layer1_topology.json` 자동 생성, anycast/MLAG 정보 추출 |
| `batfish/preflight.py` | 검증 본체 — 공통 검사 11종 + Lab 1~6 시나리오 검사, 마크다운 리포트 생성 |
| `batfish/selftest.py` | 검사기 자가 진단 7종 (`make preflight_selftest`) |
| `sites/dc1/group_vars/dc1_fabric.yml` | `BrdrLeafs`에 §7-A 실습용 `static_routes` 블록과 §7-B 실습용 `DCI-EDGE-IN` ACL 블록이 주석 상태로 준비되어 있음 |
| `batfish/snapshots/` | 생성된 스냅샷 (gitignore) |
| `batfish/reports/` | 검증 리포트 (gitignore) |

Makefile 타깃: `bf_install` `bf_start` `bf_stop` `bf_status` `preflight` `preflight_dc1` `preflight_dc2` `preflight_selftest`
