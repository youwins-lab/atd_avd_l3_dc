# CI 파이프라인 가이드 (GitHub Actions)

이 저장소의 변경(주로 `group_vars`)이 **랩에 배포되기 전에** 자동으로 검증되도록 하는 파이프라인이다.
두 단계로 나뉜다.

| 단계 | 워크플로 | 실행 위치 | 트리거 | 랩 접속 |
|---|---|---|---|---|
| 1. PR 검증 | `.github/workflows/pr-validate.yml` | GitHub 호스티드 러너 | `pull_request` → main | 없음 |
| 2. 랩 배포 | (예정) `deploy-lab.yml` | ATD 안 셀프호스티드 러너 | main 머지 + `atd-lab` 환경 승인 | CVP 배포 + ANTA |

> **보안 원칙** — 저장소는 공개다. 따라서 셀프호스티드 러너는 절대 `pull_request`로 돌지 않고,
> 랩 비밀번호/vault 키는 GitHub Secrets에도 저장하지 않는다. 1단계는 비밀값이 전혀 필요 없도록 설계했다.

## 1단계: PR 검증

### Job 구성

| Job | 내용 | PR 차단 |
|---|---|---|
| `build` | AVD 6.4.0 오프라인 빌드 → 커밋된 `intended/`·`documentation/`과 다르면 실패(drift). 장비별 config diff를 Job Summary에 표시 | ✔ |
| `batfish` | `batfish/allinone:2026.08.27.3685` 서비스 컨테이너 + 같은 빌드의 pybatfish로 `preflight.py --dc all --labs all`, `selftest.py` | ✔ |
| `avd-next` | 최신 AVD로 빌드했을 때 config가 바뀌는지 참고용 보고 | ✘ (`continue-on-error`) |

### 오프라인 빌드가 가능한 이유

- `playbooks/build_dc{1,2}.yml`에 `gather_facts: false` — 빌드는 로컬 파일만 만들므로 장비 접속 불필요.
- `ci/offline_build.sh`는 `.vault_pass.txt`, `vault.yml`이 **없을 때만** 더미 값을 만들고 끝나면 지운다.
  로컬 랩의 실제 파일은 건드리지 않는다. 더미 비밀번호는 생성 config에 들어가지 않는다(빌드 결과 0 diff로 확인).

로컬에서도 같은 검사를 돌릴 수 있다.

```bash
./ci/offline_build.sh              # 빌드 + drift 검사
./ci/config_diff_summary.sh main   # main 대비 장비 config 변경 요약(마크다운)
```

### PR 작성 규칙

1. `group_vars`를 고쳤다면 반드시 `make build_dc1 build_dc2`를 실행하고 **생성된 `intended/`, `documentation/`까지 함께 커밋**한다.
   빠뜨리면 `build` job이 "빌드 결과가 커밋된 intended/documentation과 다릅니다"로 실패한다.
2. PR의 Checks → `pr-validate` → Summary에서 장비별 +/- 와 전체 diff, Batfish 리포트를 확인한다.
3. Batfish가 FAIL이면 배포 시 실제 장애가 날 변경이다(예: §7-A Null0 정적 경로). 머지하지 않는다.

### 브랜치 보호(권장)

Settings → Branches → `main` 규칙에서 *Require status checks*로 `AVD build + drift check`,
`Batfish preflight`를 지정하면 검증을 통과하지 못한 PR은 머지 버튼이 막힌다.

### Batfish 버전 고정

`batfish/install_batfish.sh`의 기본 태그와 워크플로의 `BATFISH_TAG`는 같은 값(`2026.08.27.3685`)이다.
올릴 때는 두 곳을 함께 바꾸고, 이미지 안 pybatfish 휠 이름(`PYBATFISH_WHL`)도 맞춘다.
