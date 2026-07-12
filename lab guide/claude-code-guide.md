# Claude Code 설치 및 활용 가이드

이 문서는 `README.md`의 STEP #5였던 Claude Code 설치 안내를 분리하고, 이 저장소(AVD 6.3.0 기반 L3LS EVPN-VXLAN 랩)에서 Claude Code를 실제로 어떻게 활용할 수 있는지 실전 프롬프트 예시와 함께 정리한 자료입니다. 설치 자체는 `README.md`의 STEP #1~#4(Python 패키지 설치, 저장소 클론, `LABPASSPHRASE` 설정, 저장소 디렉토리 이동)를 먼저 마친 뒤 진행하세요.

<br>

## 1. 설치

`atd_avd_l3_dc` 저장소 루트로 이동한 터미널에서 아래 명령어로 Claude Code를 설치합니다.

``` bash
curl -fsSL https://claude.ai/install.sh | bash
```

<br>

## 2. 실행 및 기본 사용법

설치가 끝나면 저장소 루트 디렉토리(`atd_avd_l3_dc`)에서 아래 명령어로 실행합니다.

``` bash
claude
```

실행되면 대화형 세션이 시작되며, 이 디렉토리 안의 파일들을 읽고 수정하거나, `make` 명령어와 ansible 플레이북을 대신 실행시키는 등의 작업을 자연어로 요청할 수 있습니다. 세션을 종료하려면 `exit`를 입력하거나 `Ctrl+C`를 두 번 누르면 됩니다.

이 저장소 루트에는 `CLAUDE.md` 파일이 있어, Claude Code가 세션을 시작할 때 자동으로 읽고 이 랩의 구조(AVD 관리 장비 vs 정적 config 장비, `group_vars` 입력과 `intended/` 산출물의 관계, `make` 타겟 목록 등)를 미리 파악합니다. 즉 "`dc1_fabric_services.yml`이 뭐하는 파일이야?" 같은 질문에도 저장소를 처음부터 탐색하지 않고 바로 답할 수 있습니다.

<br>

## 3. AVD 6.3.0 작업에 Claude Code 활용하기 — 실전 예시

아래는 이 저장소의 실제 워크플로우(`group_vars` 수정 → `make build_dc{n}` → diff 확인 → 배포 → ANTA 검증)를 Claude Code로 진행하는 구체적인 프롬프트 예시입니다. 각 예시는 그대로 입력해도 되고, 상황에 맞게 바꿔서 사용해도 됩니다.

### 예시 1 — 새 VLAN 추가 (Lab 1과 동일한 작업을 Claude에게 위임)

`lab guide/evpn-vxlan-labs.md`의 Lab 1은 `dc1_fabric_services.yml`/`dc2_fabric_services.yml`에 VLAN 30/40/50을 직접 추가하는 실습입니다. 동일한 작업을 Claude에게 자연어로 요청할 수 있습니다.

```
dc1과 dc2의 fabric_services.yml에 VLAN 30(name: thirty, subnet 10.30.30.0/24, EVPN)을
기존 VLAN 10/20과 같은 패턴으로 추가해줘. 추가한 다음 make build_dc1, make build_dc2를
실행하고, intended/configs 아래에서 어떤 leaf들의 config가 바뀌었는지 요약해줘.
```

Claude Code는 기존 VLAN 정의 패턴을 읽고 동일한 구조로 새 항목을 추가한 뒤, `make build_dc{n}`을 직접 실행하고 그 결과(diff)를 요약해서 알려줍니다. 실제로 CVP에 배포하기 전에는 항상 결과를 직접 검토하세요.

### 예시 2 — ANTA 리포트 실패 원인 분석

`make deploy_dc1_eapi` / `make deploy_dc2_eapi`는 배포 후 `arista.avd.anta_runner`로 ANTA 검증을 실행하고 `sites/dc{n}/anta/reports/`에 리포트를 남깁니다. 실패한 테스트가 있을 때 원인 파악을 Claude에게 맡길 수 있습니다.

```
sites/dc1/anta/reports/ 아래 가장 최근 리포트를 읽고 실패한 테스트를 나열해줘.
각 실패가 EVPN 피어링 문제인지, MLAG 문제인지, 아니면 다른 원인인지 분류하고,
연관된 group_vars 설정이 있으면 어떤 파일의 어떤 값을 봐야 하는지 알려줘.
```

### 예시 3 — Border Leaf 추가로 DCI 연동 (Lab 2를 단계별로 검증하며 진행)

저장소를 처음 clone하면 dc1/dc2는 각각 독립된 단일 데이터센터 EVPN/VXLAN 패브릭으로만 빌드됩니다. Border Leaf(`s{n}-brdr1`/`s{n}-brdr2`, EVPN Gateway)가 `inventory.yml`, `dc{n}_fabric.yml`의 `BrdrLeafs` 블록과 `core_interfaces` 섹션, 이렇게 세 군데에 걸쳐 주석 처리되어 있기 때문입니다. 세 군데를 빠짐없이 맞춰야 해서 실수하기 쉬우므로, Claude에게 위치를 먼저 찾아 보여주게 한 뒤 사람이 검토하는 방식이 안전합니다.

```
sites/dc1/inventory.yml, sites/dc1/group_vars/dc1_fabric.yml에서 s1-brdr1/s1-brdr2(BrdrLeafs)와
core_interfaces 관련해서 주석 처리된 부분이 어디어디인지 전부 찾아서 보여줘. 세 군데(inventory,
BrdrLeafs node_group, core_interfaces)를 모두 주석 해제해야 하는 이유도 설명해주고, 실제로
수정하기 전에 diff 형태로 먼저 보여줘. dc2도 같은 작업이 필요하다는 것만 언급해줘.
```

이렇게 요청하면 Claude가 실제로 파일을 수정하기 전에 세 군데 변경 위치를 모두 찾아 diff로 제시하도록 유도할 수 있어, 한 군데를 빠뜨려 빌드가 깨지는 실수를 배포 전에 걸러낼 수 있습니다.

### 예시 4 — DCI/host 등 정적 config 장비 변경

`s{n}-core*`, `s{n}-host*`는 AVD가 아니라 `dci_configs/`, `host_configs/`의 손으로 작성한 `.cfg` 파일로 관리됩니다. 이런 파일을 고칠 때도 Claude에게 영향 범위를 먼저 물어보는 것이 유용합니다.

```
sites/dc1/host_configs/s1-host1.cfg에 VLAN 30 관련 SVI와 trunk 허용 VLAN을
추가하려면 어디를 고쳐야 하는지 보여주고, 이 장비가 AVD가 아니라 정적 config로
관리된다는 점을 감안해서 make deploy_dc1_host_cvp 실행 전에 확인해야 할 점을 알려줘.
```

<br>

## 4. 배포 전 확인 원칙

Claude Code는 파일 수정과 `make`/ansible 실행까지 대신할 수 있지만, 이 랩에서는 다음 원칙을 지키는 것을 권장합니다.

- CVP로 배포하기 전에는 항상 `intended/configs/*.cfg` diff와 `documentation/` 변경 사항을 직접 눈으로 확인합니다.
- DC1은 `cv_run_change_control: true`(자동 실행), DC2는 `false`(수동 승인)로 설정되어 있으므로, DC2 배포 후에는 CVP UI에서 change control을 직접 확인·승인해야 합니다.
- `dc1.yml`/`dc2.yml`의 `ansible_password`처럼 실제 자격 증명이 들어간 파일은 Claude에게 커밋/푸시를 맡기기 전에 `git diff`로 내용을 확인하세요.
