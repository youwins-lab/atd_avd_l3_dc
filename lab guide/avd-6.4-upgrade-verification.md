# AVD 6.3.0 → 6.4.0 전환 검증 기록

이 저장소의 실습 자료는 AVD 6.3.0 기준으로 작성되어 있었습니다. 이 문서는 새로 시작한 ATD 랩에서 **AVD 6.4.0**으로
README의 초기 구축 절차와 `lab guide`의 모든 시나리오를 처음부터 다시 실행하고, 실제 장비에서 결과를 확인한 기록입니다.
이 검증에서 발견한 문서 오류와 환경 문제는 같은 커밋에서 함께 고쳤습니다(아래 "수정한 것" 참고).

| 항목 | 값 |
|---|---|
| 실행일 | 2026-11-01 |
| AVD | `arista.avd` collection 6.4.0, `pyavd` 6.4.0 |
| 함께 설치된 의존성 | `pyavd-utils` 0.0.7 (pyavd 6.4.0이 `==0.0.7`로 고정), `anta` 1.10.0, `arista.cvp` 3.12.0 |
| Ansible | ansible-core 2.16.14 |
| 장비 | cEOS-lab 4.36.0.1F, 24대 (DC별 spine 2 · leaf 4 · border leaf 2 · core 2 · host 2) + CVP |
| Batfish | `batfish/allinone:latest` (2026.08.27 빌드), Temurin JRE 25.0.5 |
| EOS MCP Server | `@aristanetworks/eos-mcp-server` 0.6.1-beta |

<br>

## 결과 요약

| 단계 | 명령 | 결과 |
|---|---|---|
| 환경 설치 | `ansible-galaxy collection install arista.avd:==6.4.0 arista.cvp:==3.12.0`, `pip install "pyavd[ansible-collection]==6.4.0"` | 정상 |
| 빌드 | `make build_dc1`, `make build_dc2` | 16대 모두 성공, 경고 없음. **`intended/configs/*.cfg`와 `structured_configs/*.yml`이 6.3.0 결과와 바이트 단위로 동일** |
| DCI 배포 | `make deploy_dc1_dci`, `make deploy_dc2_dci` | core 4대 반영 |
| 패브릭 배포 | `make deploy_dc1_cvp`, `make deploy_dc2_cvp` | change control 자동 생성·실행, 16대 반영 |
| 호스트 배포 | `make deploy_dc1_host_cvp`, `make deploy_dc2_host_cvp` | host 4대 반영 |
| Lab 1 | VLAN 30/40/50 | leaf 8대 모두 VNI 10030/10040/10050 매핑 확인 |
| Lab 2 | Border Leaf 편입 | brdr ↔ spine EVPN, brdr ↔ core IPv4 eBGP 모두 `Established` |
| Lab 3 | EVPN Gateway | brdr ↔ 원격 brdr EVPN 세션 `Established`, `domain remote`는 brdr 4대에만 존재, cross-DC ping 0% 손실 |
| Lab 4 | New-Tenant, VRF 100/200 | VLAN 100/200 cross-DC ping 0% 손실, VRF 100 → 200 ping은 의도대로 실패, VRF 10 → 20은 leaf를 거쳐 성공 |
| Lab 5 | DCI core CVP 태그 | `-e cv_run_change_control=true`로 배포, CVP에서 core 4대에 `topology_hint_type=core`, `topology_hint_network_type=wan` 확인 |
| Lab 6 | Connectivity Monitor | s1-leaf1/2 → s2-host2, s2-leaf3/4 → s1-host1 모두 `Loopback210`, 손실 0% |
| ANTA | `make verify_dc1`, `make verify_dc2`, `make deploy_dc1_eapi` | DC별 252개 중 **통과 180 / 실패 16 / 스킵 56**. 실패 16건은 모두 cEOS 환경 요인 |
| Batfish | `make preflight`, `make preflight_selftest` | **PASS 28 / FAIL 0**, 자가 진단의 모든 주입 고장 탐지 |
| Batfish §7-A | Edge VTEP 블랙홀 주입 → 배포 → 복구 | 문서와 동일하게 재현 (아래) |
| EOS MCP | `./mcp/install.sh`, `probe`, `mcp/topology.py` | 24/24 응답, LLDP 링크 62개, L3/DCI 링크 BGP 34/34 `Established` |

<br>

## 1. 빌드 — 6.3.0과 차이 없음

AVD 6.4.0으로 다시 빌드한 뒤 `git diff`로 비교하면 **장비 config와 structured config는 하나도 바뀌지 않았고**, 바뀐 것은
`documentation/devices/*.md` 16개 파일뿐입니다. 문서 템플릿의 표시 방식 변경입니다.

- BGP Neighbors 표에 `Maximum-accepted-routes`, `Maximum-advertised-routes` 열이 추가됨
- `Routing Enabled` 값 표기가 `false` → `False`로 통일됨

따라서 `group_vars`는 수정 없이 그대로 6.4.0에서 동작하며, 이미 6.3.0으로 배포된 랩에 6.4.0 결과를 다시 배포해도
장비 설정 변경은 없습니다.

<br>

## 2. 랩별 확인 내용

### Lab 3 — 스티칭 경계 (문서 수정 포함)

`s2-leaf1`에서 `s1-host1`(`10.10.10.11`)의 Type-2 경로를 보면, RD와 next-hop이 모두 **DC2 자신의 Border Leaf**입니다.

```
s2-leaf1# show bgp evpn route-type mac-ip 10.10.10.11 detail
BGP routing table entry for mac-ip 001c.73c0.c616 10.10.10.11, Route Distinguisher: 10.1.0.102:10010
  65100 65199 65099 65000 65001
    10.1.1.102 from 10.1.0.112 (10.1.0.112)
```

반대 방향도 대칭입니다. `s1-leaf1`이 보는 `s2-host1`(`10.10.10.21`)의 next-hop은 `10.1.1.2`(`s1-brdr1`/`s1-brdr2`)이고,
DC1 안의 `s1-leaf3`이 보는 `s1-host1` 경로는 원래 RD(`10.1.0.14:10010`)를 그대로 가집니다.

기존 `evpn-vxlan-labs.md` Lab 3의 5단계는 "DC2 leaf의 next-hop은 `10.1.1.2`/`10.1.1.4`(DC1 Border Leaf)"라고 설명하고
있었는데, 실제 동작과 다르고 `batfish-preflight-guide.md` §7-A의 설명과도 맞지 않았습니다. 또 `10.1.1.4`라는 VTEP은 없습니다
(`s1-brdr1`/`s1-brdr2`는 MLAG 페어로 VTEP `10.1.1.2`를 공유). 5단계를 실제 출력 기준으로 고쳤습니다.

### 호스트 통신

| 출발 | 명령 | 결과 | 기대 |
|---|---|---|---|
| s1-host1 | `ping vrf 10 10.10.10.21` | 0% loss | 성공 |
| s1-host2 | `ping vrf 10 10.10.10.22` | 0% loss | 성공 |
| s2-host2 | `ping vrf 10 10.10.10.12` | 0% loss | 성공 |
| s1-host1 | `ping vrf 20 10.20.20.21` | 0% loss | 성공 |
| s1-host1 | `ping vrf 100 10.100.100.21` | 0% loss | 성공 |
| s1-host1 | `ping vrf 200 10.200.200.21` | 0% loss | 성공 |
| s1-host2 | `ping vrf 100 10.100.100.22` / `vrf 200 10.200.200.22` | 0% loss | 성공 |
| s1-host1 | `ping vrf 100 10.100.100.12` (같은 DC, 다른 leaf pair) | 0% loss | 성공 |
| s1-host1 | `ping vrf 10 10.20.20.11` (VLAN10 → VLAN20, leaf VRF A 경유) | 0% loss | 성공 |
| s1-host1 | `ping vrf 100 10.200.200.11` (VRF 100 → 200) | 100% loss | **실패가 정상** |

### Lab 6 — Connectivity Monitor

```
s1-leaf1  10.10.10.22 Loopback210  8.324 ms 0.411 ms  0%
s1-leaf2  10.10.10.22 Loopback210  9.226 ms 0.206 ms  0%
s2-leaf3  10.10.10.11 Loopback210  8.953 ms 0.344 ms  0%
s2-leaf4  10.10.10.11 Loopback210  8.705 ms 0.319 ms  0%
```

<br>

## 3. ANTA — AVD 6.4.0 + ANTA 1.10.0

pyavd 6.4.0은 `anta>=1.8.0`을 요구하므로 별도 고정 없이 설치하면 ANTA 1.10.0이 들어옵니다. `arista.avd.anta_runner`
롤은 그대로 동작했고, 카탈로그(`sites/dc{n}/anta/avd_catalogs/`)도 수정 없이 사용됐습니다.

| 테스트 | 건수 (DC별) | 성격 |
|---|---|---|
| `VerifyMemoryUtilization` | 8 | cEOS가 ATD 호스트 메모리를 그대로 보고 (91~92%) |
| `VerifyLoggingErrors` | 8 | cEOS 부팅 시 항상 남는 `%HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED` |

BGP, 인터페이스, MLAG, VXLAN/VNI 관련 테스트는 모두 통과했습니다. 6.3.0 기록에 있던 `VerifyFileSystemUtilization` 8건은
이번 랩 호스트의 디스크 사용률이 기준(75%) 아래라 나타나지 않았습니다(설정과 무관).

<br>

## 4. Batfish — 설치 문제와 해결

**문제**: `make bf_install` 후 `make bf_start`가 `stopped`로 끝났습니다. 로그는 다음과 같습니다.

```
java.lang.UnsupportedClassVersionError: org/batfish/allinone/Main has been compiled by a more recent version of
the Java Runtime (class file version 65.0), this version of the Java Runtime only recognizes class file versions up to 61.0
```

`batfish/allinone:latest`가 2026-08 빌드부터 Java 21 이상(class file 65)을 요구하는데, 설치 스크립트는 apt의
`default-jre-headless`(Debian 12 = OpenJDK 17)를 설치하고 있었습니다. 이미지 안에 Java 25가 들어 있지만 Ubuntu 26.04 기반이라
glibc 2.38을 요구해 ATD 호스트(glibc 2.36)에서는 실행되지 않습니다.

**해결**: `install_batfish.sh`가 Eclipse Temurin JRE 25를 `../batfish-service/jre/`에 내려받고, `batfishctl.sh`가 그 JRE를
우선 사용하도록 고쳤습니다. 이후 결과는 기존 문서와 같습니다.

```
[공통 검사]
  [✔] 설정 파싱          24개 파일 모두 ARISTA로 파싱, 노드 24개 (경고 61건은 Batfish 미지원 문법으로 확인됨)
  [✔] 물리 토폴로지        L1 링크 58개 / L3 인접 628개
  [✔] BGP 세션 호환성      176개 세션 모두 UNIQUE_MATCH
  [✔] BGP 세션 수립(모델)   176개 세션 모두 ESTABLISHED
  [✔] VTEP 간 도달성       VTEP 6개 × 출발 노드 12대 = 72개 조합 모두 도달 가능
...
PASS 28 / FAIL 0 / WARN 0 / SKIP 0
```

### §7-A 장애 주입 실습

| 단계 | 결과 |
|---|---|
| `static_routes` 주석 해제 → `make build_dc1` | `ip route 10.1.1.102/32 Null0` 생성 |
| `make preflight` | **PASS 27 / FAIL 1** — `VTEP 간 도달성`만 FAIL. brdr는 `NULL_ROUTED`, leaf는 `NO_ROUTE` |
| `make deploy_dc1_eapi` | ANTA는 장애 전과 같음 (추가 실패는 `VerifyRunningConfigDiffs` 2건뿐) |
| `s1-brdr1# show bgp evpn summary` | s2-brdr1/2 `Estab`, 수신 prefix 51 |
| s1-host1 → s2-host1/s2-host2 (vrf 10, 100) | 100% loss. 로컬 GW `10.10.10.1`은 0% loss |
| 복구 (`group_vars` 원복, build, `no ip route 10.1.1.102/32 Null0`) | `make preflight` PASS 28, 경로가 BGP ECMP(`172.16.255.1`/`.3`)로 복귀, cross-DC ping 0% loss |

<br>

## 5. 수정한 것

| 파일 | 내용 |
|---|---|
| `setup_env.sh`, `README.md`, `CLAUDE.md`, `AGENTS.md` | AVD 6.4.0으로 변경. `pyavd-utils`를 `0.0.7`, `anta`를 `1.10.0`으로 변경 — **`pyavd-utils==0.0.6`을 그대로 두면 pyavd 6.4.0과 충돌해 pip 설치가 실패**합니다 |
| `CLAUDE.md`, `AGENTS.md` | `cv_run_change_control` 설명을 실제 플레이북 값(fabric/host = true, DCI = false)에 맞추고 extra-vars로 덮어쓰는 방법 추가 |
| `lab guide/evpn-vxlan-labs.md` | 버전 표기, Lab 3 5단계(스티칭 next-hop) 실제 출력 기준으로 수정, Lab 5에 CVP UI 없이 change control까지 실행하는 방법 추가 |
| `batfish/install_batfish.sh`, `batfish/batfishctl.sh`, `lab guide/batfish-preflight-guide.md` | Java 25(Temurin) 사용, 문제 해결 항목 추가 |
| `mcp/topology.py`, `lab guide/eos-mcp-server-guide.md` §7-4, `mcp/README.md` | EOS MCP로 주요 정보를 수집해 토폴로지 HTML을 만드는 스크립트와 설명 추가 |
| `lab guide/claude-code-guide.md`, `codex-cli-guide.md` | 버전 표기 |
| `sites/dc{n}/documentation/`, `sites/dc{n}/anta/reports/` | AVD 6.4.0 빌드와 ANTA 1.10.0 실행 결과로 재생성 |

## 이번에 실행하지 않은 것

- `make deploy_dc1_srv6_cvp` — DC1 패브릭을 내리는 파괴적 부록 실습이고 `lab guide`의 시나리오가 아니라 제외했습니다.
- Codex CLI 설치·로그인 (`codex-cli-guide.md`) — OpenAI 계정 로그인이 필요해 제외했습니다. 문서의 AVD 관련 내용은 Claude Code 가이드와 같은 작업이라
  위 Lab 결과로 갈음합니다.
- `git-github-guide.md` — 계정/토큰 절차 안내 문서라 별도로 실행할 시나리오가 없습니다.
