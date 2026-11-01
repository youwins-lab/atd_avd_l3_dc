#!/usr/bin/env bash
# ATD가 재시작되면 사라지는 랩 환경 의존성을 한 번에 재설치하는 스크립트.
# Ansible AVD/CVP collection, pyavd/anta 관련 python 패키지, Claude Code CLI를 설치합니다.
set -euo pipefail

AVD_VERSION="6.4.0"
CVP_VERSION="3.12.0"

echo "== [1/3] Ansible Collection 설치 (arista.avd:==${AVD_VERSION}, arista.cvp:==${CVP_VERSION}) =="
ansible-galaxy collection install "arista.avd:==${AVD_VERSION}" "arista.cvp:==${CVP_VERSION}"

echo "== [2/3] Python 패키지 설치 (pyavd, anta, 의존성 패키지) =="
python3 -m pip install --upgrade \
  "pyavd==${AVD_VERSION}" \
  "pyavd-utils==0.0.7" \
  "python-socks[asyncio]>=2.7.2" \
  "anta==1.10.0" \
  "distlib>=0.3.9"

echo "== [3/3] Claude Code CLI 설치 =="
if command -v claude >/dev/null 2>&1; then
  echo "claude 명령어가 이미 존재합니다 ($(command -v claude)). 재설치를 원하면 직접 실행하세요:"
  echo "  curl -fsSL https://claude.ai/install.sh | bash"
else
  curl -fsSL https://claude.ai/install.sh | bash
fi

echo
echo "설치 완료. LABPASSPHRASE 설정과 ansible-vault 암호화는 별도로 진행하세요 (README.md STEP #3 참고):"
echo '  export LABPASSPHRASE=`cat /home/coder/.config/code-server/config.yaml| grep "password:" | awk '"'"'{print $2}'"'"'`'
echo '  openssl rand -base64 24 > .vault_pass.txt && chmod 600 .vault_pass.txt'
echo '  for f in sites/dc1/group_vars/dc1/vault.yml sites/dc2/group_vars/dc2/vault.yml \'
echo '           sites/srv6-dc1/group_vars/dc1_srv6/vault.yml; do'
echo '    ansible-vault encrypt_string \'
echo '      "$LABPASSPHRASE" --name '"'"'vault_ansible_password'"'"' > "$f"'
echo '  done'
