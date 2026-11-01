#!/usr/bin/env bash
# PR 기준 브랜치 대비 "실제 장비에 들어갈 설정"이 어떻게 바뀌는지 마크다운으로 출력한다.
# group_vars(YAML)가 아니라 렌더링된 config(.cfg) 기준이라 리뷰어가 장비 관점에서 변경을 볼 수 있다.
#
#   ./ci/config_diff_summary.sh origin/main >> "$GITHUB_STEP_SUMMARY"
set -euo pipefail
cd "$(dirname "$0")/.."
base="${1:-origin/main}"
max_lines="${MAX_DIFF_LINES:-400}"

paths=(sites/dc1/intended/configs sites/dc2/intended/configs
       sites/dc1/dci_configs sites/dc2/dci_configs sites/dc1/host_configs sites/dc2/host_configs)
files=$(git diff --name-only "$base"...HEAD -- "${paths[@]}")

echo "## 장비 설정 변경 (기준: \`$base\`)"
echo
if [ -z "$files" ]; then
  echo "장비 설정 변경 없음 — 이 PR은 장비에 배포되는 config를 바꾸지 않습니다."
  exit 0
fi
echo "| 장비 | 추가 | 삭제 |"
echo "|---|---:|---:|"
git diff --numstat "$base"...HEAD -- "${paths[@]}" | while read -r add del f; do
  echo "| \`$(basename "$f" .cfg)\` | +$add | -$del |"
done
echo
echo "<details><summary>config diff 전체 보기</summary>"
echo
echo '```diff'
# head가 먼저 끝나면 git이 SIGPIPE(141)로 종료되므로 pipefail에 걸리지 않게 감싼다
{ git --no-pager diff --no-color "$base"...HEAD -- "${paths[@]}" || true; } | head -n "$max_lines" || true
echo '```'
total=$(git diff "$base"...HEAD -- "${paths[@]}" | wc -l)
if [ "$total" -gt "$max_lines" ]; then
  echo "_(${total}줄 중 ${max_lines}줄만 표시 — 전체는 Artifacts의 config-diff.patch 참고)_"
fi
echo "</details>"
