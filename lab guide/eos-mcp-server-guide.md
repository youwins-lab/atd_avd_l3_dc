# EOS MCP Server 가이드 — Claude Code로 랩 장비 상태 조회하기

`lab guide/evpn-vxlan-labs.md`의 랩을 진행하다 보면 배포 후 확인 단계에서 같은 일을 반복하게 됩니다 —
장비마다 SSH로 들어가 `show bgp evpn summary`, `show vxlan vtep`, `show mlag`를 치고, 결과를 눈으로
비교합니다. 24대 장비를 상대로 이 작업을 하면 시간이 꽤 걸립니다.

[EOS MCP Server](https://github.com/aristanetworks/eos-mcp-server)는 Arista가 공개한
**읽기 전용** MCP(Model Context Protocol) 서버입니다. Claude Code 같은 AI 에이전트가 eAPI로 장비에
직접 `show` 명령을 실행하고, 그 결과를 해석해 답하도록 해 줍니다.

```
사용자: "dc1 leaf들 EVPN 세션 다 올라왔어?"
   ↓
Claude Code  ──(MCP, stdio)──▶  eos-mcp-server  ──(eAPI, HTTPS)──▶  s1-leaf1 ~ s1-leaf4
   ↓
"4대 모두 spine 2대와 Established, s1-leaf3만 수신 prefix가 0개입니다 …"
```

> 이 가이드는 `claude-code-guide.md`로 Claude Code를 이미 설치했다는 전제로 진행합니다.
> 이 서버는 **베타**이며 Arista TAC 지원 대상이 아닙니다.

<br>

## 1. 무엇을 할 수 있고, 무엇을 할 수 없나

서버가 제공하는 도구는 7개이고, 모두 조회용입니다.

| 도구 | 하는 일 |
|---|---|
| `eos_get_server_info` | 서버 버전, 제한값, TLS 설정, 인벤토리 요약 |
| `eos_list_inventory` | 인벤토리의 장비와 그룹 목록 |
| `eos_probe_devices` | 장비에 무해한 명령을 보내 eAPI 접속 가능 여부 확인 |
| `eos_run_show` | `show` 명령 실행 (요청당 최대 5개, JSON 또는 텍스트 출력) |
| `eos_show_logging` | 심각도(severity) 기준으로 로그 조회 |
| `eos_get_facts` | `show version` 기반 기본 정보 (모델, EOS 버전, 시리얼 등) |
| `eos_get_running_config` | running-config 조회 (`router bgp` 같은 섹션 단위도 가능) |

**할 수 없는 것**

- 설정 변경. `configure`, `write`, `clear`, `reload` 같은 명령은 서버 차원에서 거부됩니다.
  설정 변경은 지금처럼 `group_vars` 수정 → `make build_dc{n}` → `make deploy_dc{n}_*`로만 합니다.
- 파이프(`| include`, `| json`), 리다이렉트, 여러 줄 명령. `show` 한 줄 단위로만 실행됩니다.
- CVP 조회. 대상은 EOS 장비뿐입니다.

ANTA·Batfish와 비교하면 다음과 같습니다.

| | **Batfish** | **ANTA** | **EOS MCP Server** |
|---|---|---|---|
| 대상 | 설정 파일 | 실제 장비 | 실제 장비 |
| 방식 | 시뮬레이션 | 정해진 테스트 카탈로그 | 자연어 질문 → 필요한 `show` 명령을 AI가 골라 실행 |
| 강점 | 배포 전 검증 | 반복 가능한 합격/불합격 판정 | 즉석 조사, 원인 추적, 여러 장비 결과 비교·요약 |

MCP는 ANTA를 대체하지 않습니다. 합격 기준은 여전히 `make verify_dc{n}`이고, MCP는 "왜 실패했지?"를
파고들 때 쓰는 도구입니다.

<br>

## 2. 저장소에 준비된 파일

설정 파일은 모두 `mcp/` 디렉터리에 있습니다.

| 파일 | 역할 |
|---|---|
| `mcp/install.sh` | Node.js 24를 `~/.local/node`에 설치하고, `@aristanetworks/eos-mcp-server@0.6.1-beta`를 설치 |
| `mcp/inventory.yml` | 장비 24대와 그룹 15개. CVP는 제외 |
| `mcp/eos-mcp-server.yml` | 타임아웃, 동시 접속 수 등 런타임 설정 |
| `mcp/run-eos-mcp.sh` | 실행 래퍼. 랩 비밀번호를 읽어 환경변수로 넣고 서버를 띄움 |
| `mcp/topology.py` | MCP 도구로 24대의 주요 정보를 수집해 토폴로지를 HTML 한 장(`mcp/topology.html`)으로 그림 (§7-4) |
| `.mcp.json` (저장소 루트) | Claude Code에 `eos` 서버를 등록하는 프로젝트 설정 |

<br>

## 3. 설치

### 3-1. ATD 환경의 제약

EOS MCP Server는 Node.js 24 이상이 필요한데, ATD 프로그래머빌리티 IDE에는 Node.js가 설치되어 있지
않습니다(`node: command not found`). 시스템 패키지 관리자 대신 `nodejs.org`의 공식 바이너리를 홈
디렉터리(`~/.local/node`)에 풀어 쓰므로 `sudo`가 필요 없습니다.

### 3-2. 설치 실행

ATD 랩 세션을 새로 시작할 때마다 한 번 실행합니다. 저장소 루트에서 실행하세요.

```bash
./mcp/install.sh
```

마지막에 인벤토리 검증 결과가 나오면 설치가 끝난 것입니다.

```
Inventory valid: inventory.yml
Schema: simplified-yaml
Hosts: 24
Groups: 15
```

수동으로 설치하고 싶다면 `install.sh`가 하는 일은 다음과 같습니다.

```bash
V=$(curl -s https://nodejs.org/dist/index.json | python3 -c \
  "import json,sys; print(next(r['version'] for r in json.load(sys.stdin) if r['version'].startswith('v24.')))")
mkdir -p ~/.local/node
curl -sL https://nodejs.org/dist/$V/node-$V-linux-x64.tar.xz | tar -xJ -C ~/.local/node --strip-components=1
export PATH=~/.local/node/bin:$PATH
npm install -g @aristanetworks/eos-mcp-server@0.6.1-beta
```

<br>

## 4. 인벤토리와 비밀번호

### 4-1. 인벤토리

`mcp/inventory.yml`은 `sites/dc{1,2}/inventory.yml`과 같은 장비를 담고 있지만 **형식이 다릅니다**.
EOS MCP Server는 Ansible 인벤토리를 그대로 읽지 않고, 자체 "simplified" 형식을 씁니다.

```yaml
version: 1
vars:
  ansible_user: arista
  ansible_network_os: eos          # 이 값이 있어야 EOS 대상으로 인정됨
  mcp_password_env: EOS_MCP_PASSWORD
  mcp_validate_certs: false        # 랩 장비는 자체 서명 인증서

hosts:
  s1-spine1:
    ansible_host: 192.168.0.10
  ...

groups:
  dc1:        { hosts: [...] }     # DC1 전체 12대
  dc1_fabric: { hosts: [...] }     # spine + leaf + brdr
  dc1_spines / dc1_leafs / dc1_brdrs / dc1_dci / dc1_hosts
  dc2 ...                          # DC2도 같은 구조
```

질문할 때는 IP가 아니라 **장비 이름이나 그룹 이름**으로 대상을 지정합니다. 예를 들어 "dc2_leafs의
MLAG 상태"라고 하면 `s2-leaf1`~`s2-leaf4` 4대에 동시에 조회합니다.

> Ansible 인벤토리에서는 `s{n}-core1/2`의 `ansible_host`가 비어 있고 DNS로 찾지만, 여기서는
> `192.168.0.102/103`, `192.168.0.202/203`을 직접 적었습니다.

### 4-2. 비밀번호를 파일에 쓰지 않는 이유

랩 비밀번호는 ATD 세션마다 바뀌고, 저장소에 커밋되면 안 됩니다(Ansible 쪽은 같은 이유로
`vault.yml`을 씁니다 — `CLAUDE.md` 참고). 그래서 인벤토리에는 비밀번호 대신 **환경변수 이름**
(`EOS_MCP_PASSWORD`)만 적고, `mcp/run-eos-mcp.sh`가 서버를 띄울 때마다 code-server 설정
파일에서 비밀번호를 읽어 그 환경변수에 넣습니다.

```bash
EOS_MCP_PASSWORD="$(awk '/^password:/ {print $2}' /home/coder/.config/code-server/config.yaml)"
```

`EOS_MCP_PASSWORD`가 이미 설정되어 있으면 그 값을 그대로 씁니다.

<br>

## 5. 설치 확인 — Claude Code 없이 먼저

Claude Code에 연결하기 전에 래퍼 스크립트로 직접 접속을 확인합니다.

```bash
./mcp/run-eos-mcp.sh probe --target dc1
./mcp/run-eos-mcp.sh probe --target dc2
```

정상이라면 장비마다 `success`가 나옵니다.

```
Probe target: dc1
Devices: 12/12 succeeded
- s1-brdr1: success
- s1-brdr2: success
- s1-core1: success
...
```

`failed`가 나오는 장비가 있다면 §8 문제 해결을 보세요. 이 단계가 통과하지 않으면 Claude Code에서도
동작하지 않습니다.

<br>

## 6. Claude Code에 연결

### 6-1. 등록 (이미 되어 있음)

저장소 루트의 `.mcp.json`에 다음 내용이 이미 들어 있습니다.

```json
{
  "mcpServers": {
    "eos": {
      "type": "stdio",
      "command": "./mcp/run-eos-mcp.sh",
      "args": ["serve"],
      "env": {}
    }
  }
}
```

새로 등록하는 경우에는 아래 명령을 실행하면 같은 파일이 만들어집니다.

```bash
claude mcp add -s project eos -- ./mcp/run-eos-mcp.sh serve
```

> `command`가 상대 경로이므로 Claude Code는 **반드시 저장소 루트에서** 실행해야 합니다.

### 6-2. 승인과 연결 확인

```bash
cd /home/coder/project/labfiles/atd_avd_l3_dc
claude
```

처음 실행하면 "이 프로젝트의 MCP 서버 `eos`를 사용할까요?"라는 확인 창이 뜹니다. 승인하세요.
Claude Code 안에서 `/mcp`를 입력하면 `eos` 서버가 `connected`로 보여야 합니다.

```bash
claude mcp list
# eos: ./mcp/run-eos-mcp.sh serve - ✓ Connected
```

> Claude Code가 이미 실행 중일 때 `.mcp.json`을 추가했다면, 종료 후 다시 실행해야 도구가 로드됩니다.

<br>

## 7. 사용 예시

Claude Code에 자연어로 묻기만 하면 됩니다. 어떤 `show` 명령을 쓸지, 어떤 장비에 보낼지는 Claude가
고릅니다. 처음 도구를 쓸 때 권한 확인 창이 뜨면 허용하세요.

### 7-1. 기본 확인

```
dc1, dc2 전체 장비의 모델과 EOS 버전을 표로 정리해줘
```

```
s1-leaf1의 running-config 중 router bgp 섹션만 보여줘
```

### 7-2. 랩별 배포 후 점검

`evpn-vxlan-labs.md`의 각 랩에서 `make deploy_dc{n}_*`를 끝낸 뒤, `make verify_dc{n}`과 함께 쓰면
좋은 질문들입니다.

| 랩 | 질문 예시 |
|---|---|
| 초기 배포 | `dc1_fabric 장비들의 BGP underlay/EVPN overlay 세션이 모두 Established인지 확인해줘` |
| 초기 배포 | `dc1_leafs의 MLAG 상태와 port-channel 상태를 요약해줘` |
| Lab 1 (VLAN 30/40/50) | `dc1_leafs와 dc2_leafs에 VLAN 30, 40, 50과 VNI 매핑이 생겼는지 확인해줘` |
| Lab 2 (Border Leaf) | `s1-brdr1, s1-brdr2와 s1-core1, s1-core2 사이 P2P 링크와 BGP 세션 상태 보여줘` |
| Lab 3 (EVPN Gateway) | `s1-brdr1에서 s2 쪽 border leaf와 EVPN gateway 세션이 올라왔고, DC2의 MAC/IP 경로를 받고 있는지 확인해줘` |
| Lab 3 | `s1-leaf1의 VXLAN VTEP 목록에 DC2 VTEP이 보이는지 확인해줘` |
| Lab 4 (New-Tenant) | `dc2_leafs에 VRF 100, 200이 생겼고 VLAN 100/200 SVI가 각각 해당 VRF에 있는지 확인해줘` |
| Lab 6 (Connectivity Monitor) | `s1-leaf1과 s1-leaf2의 monitor connectivity 결과를 보여줘` |

### 7-3. 문제 추적

MCP가 가장 쓸모 있는 곳은 "뭔가 안 되는데 어디서 막혔는지 모를 때"입니다.

```
s1-host1에서 s2-host1으로 ping이 안 돼. dc1 leaf → border leaf → core → dc2 순서로
EVPN 경로, VXLAN VTEP, 라우팅 테이블을 따라가면서 어디서 끊기는지 찾아줘.
```

```
make verify_dc1에서 실패한 테스트가 sites/dc1/anta/reports/에 있어.
리포트를 읽고, 실패한 장비에 접속해서 원인을 확인해줘.
```

```
dc2 전체 장비의 최근 warnings 이상 로그를 모아서 장비별로 요약해줘
```

Claude Code는 이 저장소의 파일(`group_vars`, `intended/configs/*.cfg`)도 읽을 수 있으므로,
**의도한 설정과 실제 장비 상태를 비교**하는 질문도 가능합니다.

```
sites/dc1/intended/configs/s1-brdr1.cfg와 s1-brdr1의 실제 running-config를 비교해서
배포되지 않은 줄이 있는지 알려줘
```

> 이 비교는 `batfish-avd-anta-verification-report.md`에 기록된 "Batfish는 모두 통과했지만 DCI core가
> 실제로는 설정되지 않았던" 경우 같은 배포 누락을 찾는 데 유용합니다.

### 7-4. 주요 정보로 토폴로지 그리기 — HTML 한 장

> **핵심** — `python3 mcp/topology.py` 한 줄로 24대의 연결·인터페이스·BGP·VXLAN 상태를 그림 한 장으로 본다.
> Claude Code와 같은 `eos-mcp-server`(읽기 전용)만 호출하므로 장비 설정은 바뀌지 않는다.

```bash
python3 mcp/topology.py                                 # 수집 + mcp/topology.html 생성 (약 2초)
python3 mcp/topology.py --targets dc1                   # DC1만
python3 mcp/topology.py --from-json mcp/topology.json   # 재수집 없이 그림만 다시
```

생성된 `mcp/topology.html`은 IDE에서 우클릭 → **Open Preview**(또는 브라우저)로 엽니다.

**그림 구성**

```
 DC1 (spine / leaf·border leaf / host)  │  DCI·CORE  │  DC2
                                         │ s1-core1 ━━ DCI ━━ s2-core1
                                         │   ┆Po16          ┆Po16
                                         │ s1-core2 ━━ DCI ━━ s2-core2
```

| 표시 | 의미 |
|---|---|
| 박스 가장자리의 `Et4` 포트 배지 | 그 장비의 인터페이스. 선은 배지에서 출발하고 배지 테두리 색 = 선 색 (Et=Ethernet) |
| 초록 실선 | L3 P2P, BGP Established |
| **굵은 보라 선 + 중앙 라벨** | DCI(core↔core) — `DCI · 1.1.1.0/31 ↔ .1`, `eBGP up` |
| 회색 점선 + `Po1000` | MLAG peer-link / core 간 Po16 / host 포트채널 멤버 |
| 빨간 점선, 빨간 테두리 | 인터페이스 down 또는 BGP down |
| 주황 곡선 (토글) | VXLAN 터널 (`show vxlan vtep`, MLAG 쌍은 하나로 묶음) |

**조작**

| 기능 | 방법 |
|---|---|
| 장비 상세 (인터페이스·IP·Po·상태·상대 장비·BGP) | 장비 클릭 → 연결만 강조 + 아래 상세 표 |
| 표시 켜기/끄기 | `L3 링크 IP` · `VXLAN 터널` |
| 크기 | `화면 맞춤` / `원본 크기` |

그림 아래에 **DCI·core 연결 표**, **VXLAN 터널 표**, 장비 요약, LLDP 링크 전체 목록이 있습니다.

**수집 항목**

| MCP 호출 | 쓰는 곳 |
|---|---|
| `eos_get_facts` | 모델, EOS 버전 |
| `show lldp neighbors` | 물리 링크와 양 끝 인터페이스 |
| `show ip interface brief` | 링크 IP, Loopback0/1 |
| `show interfaces status` | 인터페이스 up/down, description |
| `show port-channel` | 포트채널 멤버 (`Po` 라벨) |
| `show bgp summary` | ASN, 링크별 BGP 상태 |
| `show mlag`, `show vxlan vtep` | MLAG 상태, VXLAN 터널 |

**실행 결과 (AVD 6.4.0, Lab 1~6 배포 상태)**

| 항목 | 결과 |
|---|---|
| 응답 장비 / 링크 up | 24/24 · 62/62 |
| L3 링크 BGP / DCI eBGP | 32/32 · 2/2 |
| VXLAN 터널 | 7개 — DC 간 터널은 **border leaf 사이 1개뿐** (EVPN Gateway 재발신 때문에 leaf는 원격 DC VTEP과 직접 터널을 맺지 않음) |

**Claude Code에 시키기**

```
python3 mcp/topology.py를 실행해서 토폴로지 HTML을 만들고, down된 링크나 BGP 세션이 있으면 알려줘
```

> `mcp/topology.html`, `mcp/topology.json`은 실행마다 다시 만들어지는 산출물이라 `.gitignore`에 있습니다.

<br>

## 8. 문제 해결

| 증상 | 원인과 조치 |
|---|---|
| `eos-mcp-server: command not found` / `node: command not found` | ATD 세션이 재시작되어 `~/.local/node`가 사라짐. `./mcp/install.sh` 다시 실행 |
| `/mcp`에 `eos`가 없음 | 저장소 루트가 아닌 곳에서 `claude`를 실행했거나, 승인 창을 거절함. 루트에서 다시 실행하고 승인 |
| `eos`가 `failed`로 표시됨 | 터미널에서 `./mcp/run-eos-mcp.sh validate-inventory` 실행 후 오류 메시지 확인 |
| probe에서 인증 실패 | 비밀번호가 바뀌었는데 셸에 이전 `EOS_MCP_PASSWORD`가 남아 있음. `unset EOS_MCP_PASSWORD` 후 다시 실행 |
| probe에서 timeout | 장비가 아직 부팅 중이거나 eAPI(`management api http-commands`)가 꺼져 있음. 장비에서 `show management api http-commands` 확인 |
| `BGP inactive` 오류 | 장비에 패브릭 설정이 아직 배포되지 않은 상태. README의 초기 설정 빌드·배포 절차(`make build_dc{n}` → `make deploy_dc{n}_cvp`)를 먼저 진행 |
| `inventory` 수정이 반영되지 않음 | 인벤토리는 서버 시작 시 한 번만 읽음. Claude Code에서 `/mcp` → `eos` → reconnect |
| 응답 크기 초과 오류 | 대상 장비를 줄이거나(`dc1` → `dc1_leafs`), `show running-config` 대신 섹션을 지정 |
| `\| include`가 들어간 명령이 거부됨 | 정상 동작. 파이프 없이 실행하고 필터링은 Claude에게 맡김 |

<br>

## 9. 보안상 주의

- 서버는 읽기 전용이지만, 랩 계정 `arista`는 **관리자 권한**이라 장비 쪽에서 읽기 전용이 강제되지는
  않습니다. 운영 환경에서는 AAA로 `show` 명령만 허용된 별도 계정을 만들어 쓰세요.
- 프로젝트 문서에 따르면 AI 에이전트가 MCP의 제약을 피해 SSH 같은 다른 경로로 설정을 바꾸려 한 사례가
  있습니다. Claude Code가 `ssh`나 `ansible-playbook` 실행 권한을 요청하면 내용을 확인한 뒤 승인하세요.
- `mcp_validate_certs: false`는 자체 서명 인증서를 쓰는 랩이라서 넣은 설정입니다. 운영 환경에서는
  `caFile`로 CA를 지정하세요.
