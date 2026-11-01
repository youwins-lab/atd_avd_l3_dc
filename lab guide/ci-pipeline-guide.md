# CI 파이프라인 가이드 (GitHub Actions)

> **핵심** — `main`으로 PR을 올리면 GitHub이 자동으로 **빌드 → drift 검사 → Batfish 검증**을 돌린다.
> 랩 장비에는 접속하지 않고, 비밀번호도 쓰지 않는다. 실패한 PR은 배포하면 장애가 나는 변경이다.

```
PR 생성 ──▶ build (AVD 6.4.0 빌드 + drift 검사) ──▶ batfish (preflight + selftest)
              └─ avd-next (최신 AVD로 빌드, 참고용·차단 안 함)
```

## 1. 무엇을 검사하나

| Job | 검사 | 실패하면 |
|---|---|---|
| `AVD build + drift check` | `group_vars`로 다시 빌드한 결과가 커밋된 `intended/`, `documentation/`과 같은가 | 빌드 결과를 커밋하지 않음 → `make build_dc1 build_dc2` 후 함께 커밋 |
| `Batfish preflight` | 공통 검사 11종 + Lab 1~6 검사 (`preflight.py --dc all --labs all`), 자가 진단 7종 | 배포 시 장애가 날 설정 → 리포트의 ✘ 항목 확인 |
| `Next AVD version` | 최신 AVD로 빌드 시 config 변화 | 차단 안 함 (업그레이드 사전 점검용) |

## 2. PR에서 결과 보는 법

PR 하단 **Checks** → `pr-validate` → **Summary**

| 항목 | 내용 |
|---|---|
| 장비 설정 변경 | 장비별 +/- 줄 수 표, 펼치면 config diff 전체 |
| Batfish 리포트 | 검사 항목별 PASS/FAIL 표 + 실패 상세 |
| Artifacts | `intended-configs` (생성 config, diff 패치), `batfish-report` |

## 3. 검증된 테스트 시나리오

실제 PR로 확인한 결과입니다.

| PR | 변경 | build | Batfish | 잡아낸 항목 |
|---|---|---|---|---|
| #1 | CI 추가 (장비 config 변경 없음) | ✔ | ✔ | — |
| #2 | §7-A Null0 정적 경로 | ✔ | ✘ | `VTEP 간 도달성` |
| #3 | ACL 검사 추가 (ACL은 주석 상태) | ✔ | ✔ | — |
| #4 | §7-B DCI ACL에서 VXLAN 줄 누락 | ✔ | ✘ | `VXLAN(UDP 4789) 도달성`, `DCI ACL 정책` |

#2·#4처럼 **build는 통과하는데 Batfish만 실패**하는 것이 정상적인 차단입니다.
문법·빌드는 멀쩡하지만 데이터 평면이 끊기는 변경이기 때문입니다.

## 4. PR 작성 규칙

1. `group_vars` 수정 → `make build_dc1 build_dc2` → **생성 파일까지 함께 커밋**
2. 올리기 전에 로컬에서 같은 검사 가능

```bash
./ci/offline_build.sh               # 빌드 + drift 검사 (CI build job과 동일)
./ci/config_diff_summary.sh main    # main 대비 장비 config 변경 요약
make preflight                      # Batfish 검증 (Batfish 서비스 필요)
```

## 5. 저장소 설정 (관리자 1회)

| 설정 | 위치 | 효과 |
|---|---|---|
| 필수 체크 지정 | Settings → Branches → `main` → *Require status checks*: `AVD build + drift check`, `Batfish preflight` | 검사 실패 PR은 머지 버튼 비활성 |
| Actions 허용 | 저장소를 본인 계정으로 복사한 경우 Actions 탭에서 활성화 | 복사본에서도 CI 동작 |

## 6. 설계 메모

| 항목 | 내용 |
|---|---|
| 보안 | 공개 저장소 → `pull_request` + `contents: read`만 사용, 비밀값 없음. 셀프호스티드 러너는 PR에 절대 연결하지 않음 |
| 오프라인 빌드 | 빌드 플레이북 `gather_facts: false`, vault 파일이 없으면 `offline_build.sh`가 더미를 만들고 끝나면 삭제 |
| Batfish 버전 | `batfish/install_batfish.sh`와 워크플로 `BATFISH_TAG`를 같은 값(`2026.08.27.3685`)으로 함께 변경 |
| pybatfish | 이미지 안 휠은 설치 후 삭제되고 PyPI에도 없음 → 저장소를 컨테이너에 마운트해 **컨테이너 안 pybatfish로 실행** |
| 툴체인 | `ci/requirements.txt` (setup_env.sh와 같은 버전) |

## 7. 다음 단계 (예정)

`main` 머지 → ATD 셀프호스티드 러너 → `atd-lab` 환경 승인 → CVP 배포 → ANTA + ping 매트릭스 자동 검증
