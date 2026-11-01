# EOS MCP Server (읽기 전용)

[aristanetworks/eos-mcp-server](https://github.com/aristanetworks/eos-mcp-server)를 ATD 랩 장비 24대
(s1/s2-spine, leaf, brdr, core, host)에 연결해 Claude Code에서 `show` 명령, facts, 로그, running-config를
조회할 수 있게 한 설정입니다. 설정 변경 기능은 서버 자체에 없습니다 (eAPI, 읽기 전용).

| 파일 | 역할 |
|---|---|
| `install.sh` | Node.js 24(`~/.local/node`) + `@aristanetworks/eos-mcp-server@0.6.1-beta` 설치 |
| `inventory.yml` | 장비/그룹 목록 (`dc1`, `dc2`, `dc1_fabric`, `dc1_leafs`, `dc2_dci`, …). CVP 제외 |
| `eos-mcp-server.yml` | 타임아웃·동시성 등 런타임 설정 |
| `run-eos-mcp.sh` | 실행 래퍼. 랩 비밀번호를 code-server config에서 읽어 `EOS_MCP_PASSWORD`로 주입 (파일에 저장 안 함) |
| `topology.py` | MCP 도구로 24대의 facts/LLDP/IP/BGP/MLAG/VTEP을 수집해 `topology.html`(토폴로지 그림 + 표) 생성. `lab guide/eos-mcp-server-guide.md` §7-4 |

Claude Code 등록은 저장소 루트의 `.mcp.json`(project scope)에 되어 있습니다.

## 사용법

```bash
./mcp/install.sh                          # 랩 세션마다 1회
./mcp/run-eos-mcp.sh probe --target dc1   # eAPI 연결 확인
python3 mcp/topology.py                   # 토폴로지 HTML 생성 → mcp/topology.html
claude                                    # 저장소 루트에서 실행 → 'eos' MCP 서버 승인
```

이후 Claude Code에서 예: "dc1 leaf들의 BGP EVPN 세션 상태 보여줘", "s1-brdr1 running-config의 router bgp 섹션".

## 주의

- 인벤토리는 서버 시작 시 한 번만 읽습니다. 수정 후에는 `/mcp`에서 재연결하세요.
- `show` 단일 명령만 허용 (파이프·리다이렉트 불가), 요청당 최대 5개 명령.
- 랩 계정(`arista`)은 관리자 권한이라 AAA로 읽기 전용이 강제되지는 않습니다.
