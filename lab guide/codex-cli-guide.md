# Codex CLI 설치 및 활용 가이드

이 문서는 `lab guide/claude-code-guide.md`의 Codex CLI(OpenAI) 버전입니다. Claude Code 대신(또는 함께) OpenAI의 Codex CLI를 이용해 이 저장소(AVD 6.3.0 기반 L3LS EVPN-VXLAN 랩)의 설정 작업을 진행하고 싶은 경우 이 가이드를 참고하세요. 설치 자체는 `README.md`의 STEP #1~#4(Python 패키지 설치, 저장소 클론, `LABPASSPHRASE` 설정, 저장소 디렉토리 이동)를 먼저 마친 뒤 진행하세요.

<br>

## 1. 설치

Codex CLI(`openai/codex`)는 npm 패키지 외에도 GitHub Releases에 플랫폼별 바이너리로 배포됩니다. 이 랩의 ATD IDE 터미널(Linux x86_64, npm 없음)에서 직접 확인한 설치 명령어는 아래와 같습니다. `sudo` 없이 `~/.local/bin`(이미 `PATH`에 포함되어 있음)에 설치합니다.

``` bash
curl -fsSL -o /tmp/codex.tar.gz https://github.com/openai/codex/releases/latest/download/codex-x86_64-unknown-linux-musl.tar.gz
tar -xzf /tmp/codex.tar.gz -C /tmp
chmod +x /tmp/codex-x86_64-unknown-linux-musl
mv /tmp/codex-x86_64-unknown-linux-musl ~/.local/bin/codex
```

설치가 끝나면 버전이 출력되는지 확인합니다.

``` bash
codex --version
```


## 2. 로그인 및 실행

최초 실행 시 ChatGPT 계정으로 로그인하거나 OpenAI API 키를 사용하도록 인증이 필요합니다.

``` bash
codex login --device-auth
```

인증이 끝나면 저장소 루트 디렉토리(`atd_avd_l3_dc`)에서 아래 명령어로 실행합니다.

``` bash
codex
```

<br>

실행되면 대화형 세션이 시작되며, 이 디렉토리 안의 파일을 읽고 수정하거나 `make` 명령어와 ansible 플레이북 실행을 자연어로 요청할 수 있습니다. 세션을 종료하려면 `exit`를 입력하거나 `Ctrl+C`를 두 번 누르면 됩니다. 대화형 세션 없이 한 번의 프롬프트만 비대화식으로 실행하고 싶다면 `codex exec "..."` 형태로도 사용할 수 있습니다.

> **참고 — 저장소 컨텍스트 파일**: Codex CLI는 이 저장소의  `AGENTS.md` 를 세션 시작 시 자동으로 읽어 랩 구조를 파악합니다. 이 저장소 루트에는 `AGENTS.md`가 이미 있으므로 Codex CLI도 세션 시작 시 별도 요청 없이 이를 자동으로 읽습니다.

<br>

## 3. AVD 6.3.0 작업에 Codex CLI 활용하기 — 실전 예시

### 예시 1 — 새 VLAN 추가 (Lab 1과 동일한 작업을 Codex에게 위임)

```
dc1과 dc2의 fabric_services.yml에 VLAN 30(name: thirty, subnet 10.30.30.0/24, EVPN)을
기존 VLAN 10/20과 같은 패턴으로 추가해줘. 추가한 다음 make build_dc1, make build_dc2를
실행하고, intended/configs 아래에서 어떤 leaf들의 config가 바뀌었는지 요약해줘.
```

### 예시 2 — ANTA 리포트 실패 원인 분석

```
sites/dc1/anta/reports/ 아래 가장 최근 리포트를 읽고 실패한 테스트를 나열해줘.
각 실패가 EVPN 피어링 문제인지, MLAG 문제인지, 아니면 다른 원인인지 분류하고,
연관된 group_vars 설정이 있으면 어떤 파일의 어떤 값을 봐야 하는지 알려줘.
```

### 예시 3 — Border Leaf 추가로 DCI 연동 (Lab 2를 단계별로 검증하며 진행)

저장소를 처음 clone하면 dc1/dc2는 각각 독립된 단일 데이터센터 EVPN/VXLAN 패브릭으로만 빌드됩니다. Border Leaf(`s{n}-brdr1`/`s{n}-brdr2`)가 `inventory.yml`, `dc{n}_fabric.yml`의 `BrdrLeafs` 블록과 `core_interfaces` 섹션, 이렇게 세 군데에 걸쳐 주석 처리되어 있기 때문입니다. `BrdrLeafs` 블록 안의 `evpn_gateway` 서브 블록은 별도로 주석 처리되어 있어 Lab 2에서는 건드리지 않습니다(Lab 3에서 다룸).

```
sites/dc1/inventory.yml, sites/dc1/group_vars/dc1_fabric.yml에서 s1-brdr1/s1-brdr2(BrdrLeafs)와
core_interfaces 관련해서 주석 처리된 부분이 어디어디인지 전부 찾아서 보여줘. BrdrLeafs 블록 안에
evpn_gateway라는 서브 블록도 별도로 주석 처리되어 있는데, 이건 Lab 3용이니까 이번엔 건드리지 말라고
알려줘. 세 군데(inventory, BrdrLeafs node_group, core_interfaces)를 모두 주석 해제해야 하는 이유도
설명해주고, 실제로 수정하기 전에 diff 형태로 먼저 보여줘. dc2도 같은 작업이 필요하다는 것만 언급해줘.
```

### 예시 4 — DCI/host 등 정적 config 장비 변경

```
sites/dc1/host_configs/s1-host1.cfg에 VLAN 30 관련 SVI와 trunk 허용 VLAN을
추가하려면 어디를 고쳐야 하는지 보여주고, 이 장비가 AVD가 아니라 정적 config로
관리된다는 점을 감안해서 make deploy_dc1_host_cvp 실행 전에 확인해야 할 점을 알려줘.
```

<br>

## 4. 배포 전 확인 원칙

Codex CLI도 파일 수정과 `make`/ansible 실행을 대신할 수 있지만, 이 랩에서는 다음 원칙을 지키는 것을 권장합니다.

- CVP로 배포하기 전에는 항상 `intended/configs/*.cfg` diff와 `documentation/` 변경 사항을 직접 눈으로 확인합니다.
- DC1은 `cv_run_change_control: true`(자동 실행), DC2는 `false`(수동 승인)로 설정되어 있으므로, DC2 배포 후에는 CVP UI에서 change control을 직접 확인·승인해야 합니다.
- `dc1.yml`/`dc2.yml`의 `ansible_password`처럼 실제 자격 증명이 들어간 파일은 Codex에게 커밋/푸시를 맡기기 전에 `git diff`로 내용을 확인하세요.
- 셸 명령 실행 승인 모드(approval mode)는 기본적으로 매 명령마다 확인을 요구합니다. 이 랩처럼 실제 장비에 배포하는 명령(`make deploy_*`)은 자동 승인 모드로 바꾸기보다 매번 직접 확인하고 승인하는 것을 권장합니다.
