# ANTA PSIRT로 Arista Security Advisory 점검하기

ANTA 1.11.0에 들어 있는 `anta psirt` 명령으로, **지금 실행 중인** 장비들이 Arista Security Advisory(SA)에
해당되는지 확인합니다. 단순히 EOS 버전만 비교하는 것이 아니라, 장비에 `show` 명령을 보내서 취약점이 실제로 동작할
조건(예: SSH가 켜져 있는지, PIM sparse-mode가 설정되어 있는지)까지 함께 판단합니다.

> **[PREVIEW]** `anta psirt`는 ANTA의 프리뷰 기능입니다. 명령어 옵션이나 결과 형식이 예고 없이 바뀔 수 있습니다.

| 구분 | 내용 |
|---|---|
| 대상 | `sites/dc{n}/inventory.yml`에서 **활성화된** EOS 장비 전체 (spine/leaf/border-leaf/core/host, CVP 제외) |
| 장비 영향 | 없음 — `show` 명령만 실행하고 설정은 변경하지 않음 |
| 소요 시간 | DC당 약 10초 (장비 12대 × advisory 57개, ANTA 1.11.0 기준) |
| 결과 파일 | `sites/dc{n}/anta/reports/psirt_report.md`, `psirt_report.csv` |

<br>

## 1. 준비

`anta` CLI를 실행하려면 `[cli]` extra가 함께 설치되어 있어야 합니다 (`setup_env.sh`는 이미 이 형태로 설치합니다).

```bash
python3 -m pip install "anta[cli]==1.11.0"
anta psirt --help
```

`The ANTA command line client could not run because the required dependencies were not installed.` 메시지가
나오면 `[cli]` 없이 `anta`만 설치된 상태입니다. 위 명령으로 다시 설치하세요.

자격 증명은 아래 순서대로 찾으므로, ATD 랩에서는 따로 설정할 필요가 없습니다.

| 항목 | 찾는 순서 |
|---|---|
| 사용자 | `ANTA_USERNAME` → 기본값 `arista` |
| 비밀번호 | `ANTA_PASSWORD` → `LABPASSPHRASE` → `~/.config/code-server/config.yaml`의 `password:` |

<br>

## 2. 실행

```bash
make psirt        # dc1 + dc2
make psirt_dc1    # DC1만
make psirt_dc2    # DC2만
```

`make psirt`가 실행하는 `psirt/run_psirt.py`는 DC마다 아래 순서로 동작합니다.

1. `sites/dc{n}/inventory.yml`을 읽어 ANTA inventory(`sites/dc{n}/anta/psirt_inventory.yml`)를 만듭니다.
   - Lab 단계에 따라 Border Leaf를 주석 처리하거나 해제하면, 점검 대상도 그에 맞게 바뀝니다.
   - `ansible_host`가 없는 장비(`s{n}-core1/2`)는 호스트 이름으로 접속합니다.
2. `anta psirt ... md-report`, `anta psirt ... csv` 명령을 차례로 실행합니다.
3. 결과 중 Affected, Inconclusive, Error만 골라 터미널에 요약해서 출력합니다.

`--ignore-status`를 붙여 실행하므로, 해당되는 advisory가 있어도 `make`는 실패로 끝나지 않습니다. 결과는 요약
출력과 리포트 파일에서 확인하세요.

직접 실행하고 싶다면 아래처럼 입력합니다 (`run_psirt.py`가 먼저 한 번 실행되어 inventory가 만들어진 상태여야 합니다).

```bash
export ANTA_USERNAME=arista ANTA_PASSWORD=$LABPASSPHRASE
INV=sites/dc1/anta/psirt_inventory.yml

anta psirt -i $INV --insecure md-report --md-output /tmp/psirt.md
anta psirt -i $INV --insecure -d s1-leaf1 -t SA147 csv --csv-output /tmp/sa147.csv   # 장비 1대, advisory 1개만
anta psirt -i $INV --insecure --hide success --hide skipped md-report --md-output /tmp/psirt.md
anta psirt -i $INV --dry-run md-report --md-output /tmp/x.md                          # 장비에 접속하지 않고 실행 계획만 확인
```

<br>

## 3. 결과 읽는 법

| 결과 | 의미 | 조치 |
|---|---|---|
| 🛑 Affected | 버전과 동작 조건이 모두 해당됨 | 수정된 EOS로 업그레이드하거나 advisory의 우회 방법(workaround) 적용 |
| ❓ Inconclusive | 버전은 해당되지만, 장비 상태만으로는 실제로 해당되는지 판단할 수 없음 | 결과 메시지의 `Unresolved:` 항목을 advisory 원문과 비교해 직접 판단 |
| 🛡️ Mitigated | 해당되지만 우회 방법이 이미 적용되어 있음 | 업그레이드 계획만 세움 |
| ✅ Not affected | 버전이 해당되지 않거나, 기능이 꺼져 있음 | 없음 |

CSV는 **취약점(CVE) 하나당 한 행**으로 기록되며, 주요 컬럼은 아래와 같습니다.

- `Advisory Result`: SA 단위 판정
- `Vulnerability Result`, `Vulnerability Result Messages`: CVE별 판정과 그 근거 (어떤 패키지 버전이나 기능 때문에 해당되는지)
- `Vulnerability Remediation`: 수정된 릴리스 정보

<br>

## 4. 이 랩의 실측 결과 (2026-11-15, ANTA 1.11.0, cEOS-lab `4.36.0.1F` engineering build, 24대)

점검할 수 있는 advisory 목록은 ANTA 버전에 따라 달라집니다. 같은 날 같은 장비를 ANTA 1.10.0과 1.11.0으로 각각 점검한
결과는 아래와 같습니다.

| ANTA | 점검한 advisory | 🛑 Affected | ❓ Inconclusive |
|---|---|---|---|
| 1.10.0 (2026-09-10) | 35개 (SA0117~SA0178) | 3개 | 1개 |
| 1.11.0 (2026-11-10) | 57개 (+SA0201, SA0205~SA0225) | **8개** | 1개 |

ANTA 1.11.0 결과:

| SA | 심각도 | 결과 | 원인 | 수정 버전 |
|---|---|---|---|---|
| SA0147 | Critical | 🛑 24/24 | OpenSSH 9.9p1 (client 3건, sshd 1건 — SSH 활성화) | CVE-2026-60002: 4.35.6M 이상. 나머지: 아직 수정 버전 없음 |
| SA0201 🆕 | Critical | 🛑 24/24 | EOS trust store + TerminAttr `v1.44.0`이 손상된 CA 인증서를 신뢰할 수 있음 | 4.36.3.2M / 4.37.0F 이상 **+ TerminAttr 업그레이드** |
| SA0208 🆕 | Critical | 🛑 20/24 | BGP + `service routing protocols model multi-agent` — 조작된 패킷으로 BGP agent 크래시 | 4.36.3M / 4.37.0F 이상 |
| SA0162 | Critical | ❓ 24/24 | gNSI Certz/Bootz. 버전은 해당되지만 초기 Bootz CertzProfile 인증서는 지난 상태라 확인 불가 | 4.36.1F 이상 |
| SA0207 🆕 | High | 🛑 20/24 | BGP + multi-agent — 조작된 메시지로 BGP 세션이 반복적으로 리셋됨 | 4.36.3M / 4.37.0F 이상 |
| SA0218 🆕 | High | 🛑 24/24 | eAPI + management HTTP default services 활성화 — 스위치 파일 시스템의 파일이 노출될 수 있음 | 4.36.3.2M / 4.37.0F 이상 |
| SA0152 | Medium | 🛑 24/24 | AAA login 인증 + 비밀번호 기반 SSH/Telnet 서비스 활성화 | 4.36.1F 이상 |
| SA0153 🆕 | Medium | 🛑 24/24 | 특수 agent trace를 켜면 개인 키·비밀번호가 로그에 평문으로 남을 수 있음 (1.11.0에서 판정 로직 수정) | 4.36.2F 이상 + trace를 켰던 적이 있다면 로그 정리 |
| SA0159 | Medium | 🛑 24/24 | IGMP snooping agent (버전 조건만으로 해당) | 4.36.2F 이상 |
| 나머지 48개 | — | ✅ 24/24 | — | — |

🆕는 1.10.0에서는 점검되지 않았거나 Not affected로 나왔던 항목입니다.

**SA0207/SA0208이 20/24인 이유:** `s{n}-host1/2`는 BGP를 실행하지 않아 Not affected입니다. 반대로 spine, leaf,
border-leaf, core는 모두 BGP를 multi-agent 모델로 실행하므로 해당됩니다. 같은 EOS 이미지를 쓰더라도 **기능 설정에 따라
결과가 갈리는** 예시입니다.

**업그레이드 기준:** 1.10.0 기준으로는 4.36.2F 이상이면 충분했지만, 1.11.0에서는 **EOS 4.36.3.2M 이상(또는 4.37.0F
이상)으로 올리고 TerminAttr도 함께 업그레이드**해야 SA0201, SA0218까지 해결됩니다. 이렇게 하면 SA0147만 남으며,
SA0147은 수정 버전이 나올 때까지 장비에서 신뢰할 수 없는 서버로 SSH/SCP/SFTP 접속을 하지 않는 것으로 대응합니다.

> **ANTA를 업그레이드하면 다시 점검하세요.** 장비와 설정이 그대로여도, 새로 공개된 advisory가 추가되거나 기존 판정
> 로직이 수정되면서 결과가 달라집니다. 위 표처럼 Affected 3개 → 8개로 늘어날 수 있습니다. ANTA 릴리스 정보는
> <https://github.com/aristanetworks/anta/releases>에서 확인할 수 있습니다.

<br>

## 5. 다른 검증 단계와의 관계

| 단계 | 도구 | 보는 대상 |
|---|---|---|
| 배포 전 | `make preflight` (Batfish) | intended config의 논리 오류 |
| 배포 후 | `make verify_dc{n}` (ANTA NRFU) | 패브릭 상태 (BGP, EVPN, MLAG, 인터페이스) |
| 수시 / 정기 | `make psirt` (ANTA PSIRT) | 실행 중인 EOS의 보안 취약점 해당 여부 |

PSIRT 점검은 설정을 바꾸지 않기 때문에, 위의 Lab 순서와 상관없이 언제든 실행할 수 있습니다. 결과를 바꾸는 것은
EOS 버전 업그레이드나 관련 기능의 활성화/비활성화이므로, 이런 작업 전후에 다시 실행해 비교하면 됩니다.
