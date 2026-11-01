#!/usr/bin/env bash
# 랩 장비에 접속하지 않고 dc1/dc2 AVD 빌드를 돌린 뒤, 결과가 저장소에 커밋된 내용과 같은지 확인한다.
#
#   ./ci/offline_build.sh            # 빌드 + 차이 검사 (차이가 있으면 exit 1)
#   ./ci/offline_build.sh --no-check # 빌드만
#
# CI(GitHub 러너)에는 랩 비밀번호도 vault 키도 없다. 빌드는 비밀번호를 실제로 쓰지 않지만
# ansible.cfg의 vault_password_file과 group_vars의 "{{ vault_ansible_password }}" 참조 때문에
# 둘 다 "존재"는 해야 하므로, 없을 때만 더미 값을 만든다. 로컬 랩에서 이미 만든 실제
# .vault_pass.txt / vault.yml은 절대 덮어쓰지 않는다.
set -euo pipefail
cd "$(dirname "$0")/.."

created=()
if [ ! -e .vault_pass.txt ]; then
  echo "ci-dummy-vault-key" > .vault_pass.txt && created+=(.vault_pass.txt)
fi
for f in sites/dc1/group_vars/dc1/vault.yml sites/dc2/group_vars/dc2/vault.yml; do
  if [ ! -e "$f" ]; then
    echo 'vault_ansible_password: "ci-dummy-not-a-real-password"' > "$f" && created+=("$f")
  fi
done
cleanup() { [ ${#created[@]} -eq 0 ] || rm -f "${created[@]}"; }
trap cleanup EXIT

make build_dc1
make build_dc2

[ "${1:-}" = "--no-check" ] && exit 0

paths=(sites/dc1/intended sites/dc2/intended sites/dc1/documentation sites/dc2/documentation)
changes=$(git status --porcelain -- "${paths[@]}")
if [ -n "$changes" ]; then
  echo
  echo "✘ 빌드 결과가 커밋된 intended/documentation과 다릅니다."
  echo "  group_vars를 고친 뒤 'make build_dc1 build_dc2'를 실행하고 생성된 파일까지 함께 커밋하세요."
  echo "$changes"
  git --no-pager diff --stat -- "${paths[@]}"
  exit 1
fi
echo "✔ 빌드 결과가 커밋된 intended/documentation과 일치합니다."
