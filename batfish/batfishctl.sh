#!/usr/bin/env bash
# Batfish 서비스 기동/정지/상태 확인.
set -uo pipefail

BF_HOME="${BF_HOME:-/home/coder/project/labfiles/batfish-service}"
LOG="$BF_HOME/logs/batfish_service.log"
PORT=9996
# install_batfish.sh가 받아 둔 Java 21+ JRE를 우선 사용 (최신 Batfish jar는 Java 17로 실행 불가)
JAVA="$BF_HOME/jre/bin/java"; [ -x "$JAVA" ] || JAVA=java

status() {
  if pgrep -f allinone-bundle.jar >/dev/null 2>&1; then
    code=$(curl -sS -o /dev/null -w "%{http_code}" "http://localhost:$PORT/" 2>/dev/null)
    # 서비스 루트는 404를 돌려주는 게 정상 — 응답이 온다는 것 자체가 살아있다는 뜻
    if [ "$code" != "000" ]; then
      echo "running (pid $(pgrep -f allinone-bundle.jar | head -1), port $PORT)"
      return 0
    fi
    echo "starting (프로세스는 떠 있으나 아직 포트 응답 없음)"
    return 1
  fi
  echo "stopped"
  return 1
}

case "${1:-status}" in
  start)
    if pgrep -f allinone-bundle.jar >/dev/null 2>&1; then echo "이미 실행 중"; status; exit 0; fi
    test -s "$BF_HOME/rootfs/allinone-bundle.jar" || {
      echo "Batfish가 설치되어 있지 않습니다. ./batfish/install_batfish.sh 를 먼저 실행하세요." >&2; exit 1; }
    mkdir -p "$BF_HOME/logs" "$BF_HOME/data/containers"
    cd "$BF_HOME/rootfs"
    setsid nohup "$JAVA" -XX:-UseCompressedOops -Xmx3g \
      -Dlog4j.configurationFile=log4j2.yaml \
      -cp allinone-bundle.jar org.batfish.allinone.Main \
      -runclient false -loglevel warn \
      -coordinatorargs "-templatedirs questions -containerslocation $BF_HOME/data/containers" \
      > "$LOG" 2>&1 < /dev/null &
    for _ in $(seq 1 60); do sleep 2; status >/dev/null && break; done
    status
    ;;
  stop)
    pkill -f allinone-bundle.jar && echo "정지됨" || echo "실행 중이 아님"
    ;;
  restart) "$0" stop; sleep 3; "$0" start ;;
  status)  status ;;
  log)     tail -f "$LOG" ;;
  *) echo "사용법: $0 {start|stop|restart|status|log}" >&2; exit 2 ;;
esac
