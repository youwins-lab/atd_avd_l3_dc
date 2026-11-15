# AVD 6.4.0 → 6.5.0 전환 검증 기록

AVD 6.4.0 기준이던 이 저장소를 **AVD 6.5.0**으로 올리면서, 빌드 결과·사전 검증(Batfish)·실제 장비 상태 검증(ANTA)을
다시 실행해 6.4.0과 비교한 기록입니다. 이번 검증은 **이미 6.4.0으로 Lab 1~6까지 배포되어 있던 랩**에서 진행했으며, 생성된
config가 6.4.0과 완전히 같기 때문에 장비에 다시 배포하지 않았습니다.

| 항목 | 값 |
|---|---|
| 실행일 | 2026-11-15 |
| AVD | `arista.avd` collection 6.5.0, `pyavd` 6.5.0 |
| 함께 설치된 의존성 | `pyavd-utils` **0.0.13** (pyavd 6.5.0이 `==0.0.13`으로 고정), `anta` 1.11.0, `arista.eos` **12.3.0**, `ansible.netcommon` 8.8.0, `arista.cvp` 3.12.0 |
| Ansible | ansible-core 2.16.14 (6.5.0 collection 요구사항: `>=2.16.0,<2.22.0`) |
| 장비 | cEOS-lab 4.36.0.1F, 24대 + CVP (Lab 1~6 배포 상태) |
| Batfish | `batfish/allinone` 2026.08.27 빌드, `pybatfish` 2026.8.27.3685 |

<br>

## 결과 요약

| 단계 | 명령 | 결과 |
|---|---|---|
| 환경 설치 | `ansible-galaxy collection install arista.avd:==6.5.0`, `pip install pyavd==6.5.0 pyavd-utils==0.0.13` | 정상. `arista.eos` 12.3.0과 `ansible.netcommon` 8.8.0이 의존성으로 함께 설치됨 |
| 빌드 | `make build_dc1`, `make build_dc2` | 16대 모두 성공, 경고 없음. **`intended/configs`, `structured_configs`, `documentation` 모두 6.4.0 결과와 바이트 단위로 동일** (모든 렌더링 task `changed=0`) |
| CI drift 검사 | `ci/offline_build.sh`와 같은 조건 | 커밋된 `intended`/`documentation`과 차이 없음 |
| Batfish | `make preflight` | **PASS 29 / FAIL 0 / WARN 0 / SKIP 2** (기준값과 동일) |
| Batfish 자가 진단 | `make preflight_selftest` | 주입한 고장 7개 모두 탐지 |
| ANTA | `make verify_dc1`, `make verify_dc2` (6.5.0 `anta_runner`) | DC별 252개 중 **통과 180 / 실패 16 / 스킵 56 / 오류 0** — 6.4.0과 동일. ANTA 카탈로그(`avd_catalogs/`)도 변경 없음 |
| `arista.eos` 12.3.0 | `eos_command` (`show version`), `deploy_dc1_dci_eapi.yml --check --diff` | 정상 동작, core 2대 `changed=0` |

ANTA 실패 16건은 6.4.0 때와 같은 cEOS 환경 요인입니다.

- `VerifyMemoryUtilization` (8대): 메모리 사용률 약 92%로 기준(75%)을 넘음. 컨테이너 랩이라 메모리가 빠듯함
- `VerifyLoggingErrors` (8대): 부팅 시 생기는 `HARDWARE-0-SYSTEM_IDENTIFICATION_FAILED`(cEOS에서는 정상)와
  BGP 세션이 올라오는 동안 남은 메시지

<br>

## 1. 바뀐 버전 고정

| 항목 | 6.4.0 | 6.5.0 | 비고 |
|---|---|---|---|
| `pyavd-utils` | `==0.0.7` | `==0.0.13` | **pyavd가 정확한 버전으로 고정**하므로 함께 바꾸지 않으면 pip 설치가 실패합니다 |
| `anta` | `>=1.8.0` | `>=1.10.0` | 이 저장소는 이미 1.11.0을 사용 중 |
| `arista.eos` | (별도 요구 없음, 기존 11.0.1 사용) | `>=12.2.0` | collection 설치 시 자동으로 12.3.0이 들어옴 |

`arista.eos`는 `deploy_dc{n}_eapi.yml`, `deploy_dc{n}_dci_eapi.yml`이 직접 호출하는 `arista.eos.eos_config` 모듈의
collection입니다. 메이저 버전이 바뀌었으므로 실제 장비에 `eos_command`와 `eos_config --check`를 실행해 동작을 확인했습니다.

이 저장소에서 버전을 바꾼 파일: `setup_env.sh`, `ci/requirements.txt`, `.github/workflows/pr-validate.yml`,
`README.md`, `CLAUDE.md`, `AGENTS.md`, `lab guide/`의 현재 버전 표기(`ci-pipeline-guide.md`, `claude-code-guide.md`,
`codex-cli-guide.md`, `evpn-vxlan-labs.md`). 과거 시점의 실행 결과를 적은 부분은 그대로 두었습니다.

<br>

## 2. 6.5.0 릴리스 노트 중 이 랩과 관련된 항목

6.5.0 릴리스 노트에는 Breaking Change로 표시된 항목이 없습니다. 동작을 바꾸는 새 옵션은 모두 기본값이 `false`인
opt-in이며, 이 랩은 아무것도 켜지 않았습니다.

- `avd_design_future` (eos_designs): `allow_recursive_profile_inheritance`, `fix_mlag_ibgp_peering_ipv6_pool`,
  `fix_mlag_ibgp_peering_vrfs_address_families`, `fix_virtual_source_nat_address_families`,
  `only_configure_oob_mgmt_vrf_and_ipv4_static_routes_when_used`
- `eos_config_future` (eos_cli_config_gen): `new_bgp_peer_group_cli_order`

이 랩에서 체감할 수 있는 변화는 아래 두 가지입니다.

- **`anta_runner` 로그**: Ansible verbosity를 따르도록 바뀌어, 기본 실행에서는 경고와 오류만 출력됩니다.
  자세한 진행 상황은 `-v` 이상으로 실행해야 보입니다.
- **`cv_deploy`**: 상세 결과에서 CloudVision 비밀번호가 마스킹되고, proxy 환경 변수를 무시합니다.

> `fix_virtual_source_nat_address_families`는 Lab 6(Connectivity Monitor)에서 쓰는 `ip address virtual source-nat`와
> 관련된 옵션입니다. 기본값(`false`)에서는 6.4.0과 출력이 같다는 것을 이번 빌드로 확인했습니다. 켜면 config가 바뀔 수
> 있으므로, 켜기 전에 `make build_dc{n}` 후 `git diff`로 변화를 확인하세요.

<br>

## 3. 이번 검증에서 하지 않은 것

- **장비 재배포 (`make deploy_dc{n}_cvp`, `deploy_dc{n}_eapi`)**: 생성된 config가 6.4.0과 같아 재배포해도 장비 설정
  변경이 없으므로 실행하지 않았습니다. 따라서 6.5.0의 `cv_deploy`(CVP change control 생성·실행)는 실제로 실행해 보지
  않았습니다. 다음에 config를 바꾸는 Lab을 진행할 때 함께 확인됩니다.
- **README 초기 구축부터 다시 하기**: 6.4.0 검증(`avd-6.4-upgrade-verification.md`)과 달리 새 랩에서 처음부터 다시
  구축하지는 않았습니다.

<br>

## 4. 참고 — ATD 재시작 후 `pybatfish`가 사라지는 문제

ATD 랩이 재시작되면 pip로 설치한 패키지가 초기화됩니다. `setup_env.sh`는 pyavd/anta는 다시 설치하지만 `pybatfish`는
설치하지 않으므로, `make preflight`가 `ModuleNotFoundError: No module named 'pybatfish'`로 실패할 수 있습니다.
`../batfish-service/`가 남아 있다면 이미지에 들어 있는 wheel로 다시 설치하면 됩니다 (`make bf_install`을 다시 실행해도 됩니다).

```bash
python3 -m pip install ../batfish-service/rootfs/pybatfish-*.whl
make bf_start
```
