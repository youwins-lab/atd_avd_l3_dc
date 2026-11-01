#!/usr/bin/env bash
# Batfish 설치 스크립트 (ATD 프로그래머빌리티 IDE 환경 전용).
#
# Batfish는 보통 `docker run batfish/allinone` 으로 띄우지만, ATD IDE 자체가 컨테이너 안이라
# Docker 데몬을 쓸 수 없다. 그래서 이 스크립트는 같은 컨테이너 이미지를 레지스트리 API로 직접
# 내려받아 풀어 놓고, 그 안의 allinone-bundle.jar 를 호스트 JVM으로 실행하는 방식을 쓴다.
# (Docker를 쓸 수 있는 환경이라면 README의 대안 절차대로 docker run 을 쓰면 된다.)
set -euo pipefail

BF_HOME="${BF_HOME:-/home/coder/project/labfiles/batfish-service}"
IMAGE="${BF_IMAGE:-batfish/allinone}"
TAG="${BF_TAG:-latest}"

# 최신 batfish/allinone 이미지의 jar는 Java 21 이상으로 빌드되어 있다(class file 65+, 2026-08 빌드 기준).
# ATD(Debian 12)의 apt에는 OpenJDK 17까지만 있고, 이미지에 들어 있는 JRE는 glibc 2.38이 필요해 호스트에서
# 실행되지 않는다. 그래서 glibc 의존성이 낮은 Eclipse Temurin JRE를 $BF_HOME/jre 에 내려받아 쓴다
# (batfishctl.sh가 $BF_HOME/jre/bin/java 를 우선 사용).
JAVA_MAJOR="${BF_JAVA_MAJOR:-25}"
echo "== [1/4] Java ${JAVA_MAJOR} 런타임 설치 (Temurin JRE → $BF_HOME/jre) =="
mkdir -p "$BF_HOME"
if "$BF_HOME/jre/bin/java" -version 2>&1 | grep -q "version \"${JAVA_MAJOR}\."; then
  echo "이미 설치됨: $("$BF_HOME/jre/bin/java" -version 2>&1 | head -1)"
else
  rm -rf "$BF_HOME/jre" && mkdir -p "$BF_HOME/jre"
  curl -fsSL "https://api.adoptium.net/v3/binary/latest/${JAVA_MAJOR}/ga/linux/x64/jre/hotspot/normal/eclipse" \
    | tar -xz -C "$BF_HOME/jre" --strip-components=1
  "$BF_HOME/jre/bin/java" -version 2>&1 | head -1
fi

echo "== [2/4] Batfish 컨테이너 이미지 내려받기 ($IMAGE:$TAG) =="
mkdir -p "$BF_HOME"/{layers,rootfs,logs,data/containers}
cd "$BF_HOME"
TOKEN=$(curl -sS "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${IMAGE}:pull" \
        | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
ACCEPT="application/vnd.docker.distribution.manifest.v2+json,application/vnd.oci.image.manifest.v1+json,application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.index.v1+json"
curl -sS -H "Authorization: Bearer $TOKEN" -H "Accept: $ACCEPT" \
     "https://registry-1.docker.io/v2/${IMAGE}/manifests/${TAG}" > manifest.json
# 멀티아키텍처 이미지면 인덱스가 내려오므로 linux/amd64 매니페스트를 한 번 더 받는다
DIGEST=$(python3 -c "
import json
m = json.load(open('manifest.json'))
for e in m.get('manifests', []):
    p = e.get('platform', {})
    if p.get('os') == 'linux' and p.get('architecture') == 'amd64':
        print(e['digest']); break
")
if [ -n "$DIGEST" ]; then
  curl -sS -H "Authorization: Bearer $TOKEN" -H "Accept: $ACCEPT" \
       "https://registry-1.docker.io/v2/${IMAGE}/manifests/${DIGEST}" > manifest.json
fi

echo "== [3/4] 이미지 레이어 전개 =="
for d in $(python3 -c "import json;[print(l['digest']) for l in json.load(open('manifest.json'))['layers']]"); do
  f="layers/${d#sha256:}.tar.gz"
  [ -s "$f" ] || curl -sSL -H "Authorization: Bearer $TOKEN" \
      "https://registry-1.docker.io/v2/${IMAGE}/blobs/$d" -o "$f"
  tar -xzf "$f" -C rootfs 2>/dev/null || true
done
test -s rootfs/allinone-bundle.jar

echo "== [4/4] pybatfish 설치 (서비스와 같은 버전의 wheel 사용) =="
WHL=$(ls rootfs/pybatfish-*.whl 2>/dev/null | head -1)
if [ -n "$WHL" ]; then
  python3 -m pip install --quiet --upgrade "$WHL"
else
  python3 -m pip install --quiet --upgrade pybatfish
fi
python3 -c "import pybatfish; print('pybatfish', pybatfish.__version__)"

cat <<MSG

설치 완료. 다음 순서로 진행하세요:
  ./batfish/batfishctl.sh start     # Batfish 서비스 기동
  ./batfish/batfishctl.sh status    # 상태 확인
  make preflight                    # 배포 전 사전 검증
MSG
