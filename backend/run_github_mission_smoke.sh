#!/usr/bin/env bash
# Run the real GitHub App check against disposable local services.
set -euo pipefail
umask 077

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
mode=${1:-assessment}
if [[ "$mode" != assessment && "$mode" != --publication ]]; then
  echo 'Usage: run_github_mission_smoke.sh [--publication]'
  exit 1
fi
if [[ "$(uname -s)" != Linux ]]; then
  echo 'Run this in Linux or WSL with Docker integration enabled.'
  exit 1
fi
engine=(docker --host unix:///var/run/docker.sock)
if ! "${engine[@]}" info >/dev/null 2>&1; then
  echo 'Start Docker and make its local socket available to this Linux environment.'
  exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12 or later is required"'

run_dir=$(mktemp -d)
run_id=${run_dir##*.}
mongo="havosec-smoke-mongo-$run_id"
temporal="havosec-smoke-temporal-$run_id"
mongo_id=''
temporal_id=''
cleanup() {
  if [[ -n "$mongo_id" ]]; then "${engine[@]}" rm -f -v "$mongo_id" >/dev/null 2>&1 || true; fi
  if [[ -n "$temporal_id" ]]; then "${engine[@]}" rm -f -v "$temporal_id" >/dev/null 2>&1 || true; fi
  rm -rf -- "$run_dir"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

python3 -m venv "$run_dir/venv"
py="$run_dir/venv/bin/python"
"$py" -m pip install --quiet -r requirements.txt -r requirements-missions.txt

key_path=$("$py" -c 'import os; from dotenv import dotenv_values; print(os.environ.get("GITHUB_APP_PRIVATE_KEY_PATH") or dotenv_values(".env").get("GITHUB_APP_PRIVATE_KEY_PATH") or "")')
if [[ "$key_path" =~ ^[a-zA-Z]: ]] && command -v wslpath >/dev/null; then
  key_path=$(wslpath -u "$key_path")
fi
if [[ -z "$key_path" || ! -f "$key_path" || ! -r "$key_path" ]]; then
  echo 'The GitHub App key path must point to a readable local file.'
  exit 1
fi
export GITHUB_APP_PRIVATE_KEY_PATH="$key_path"

mongo_id=$("${engine[@]}" run -d --name "$mongo" -p 127.0.0.1:27249:27249 \
  mongo:7 --port 27249 --replSet havosec_smoke --bind_ip_all)
"${engine[@]}" pull semgrep/semgrep:1.176.0

wait_ready() {
  for attempt in {1..30}; do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep 2
  done
  echo 'A local test service did not become ready.'
  return 1
}

mongo_shell=("${engine[@]}" exec "$mongo_id" mongosh --quiet 'mongodb://127.0.0.1:27249/?directConnection=true')
wait_ready "${mongo_shell[@]}" --eval 'db.adminCommand({ping: 1})'
"${mongo_shell[@]}" --eval 'rs.initiate({_id:"havosec_smoke",members:[{_id:0,host:"127.0.0.1:27249"}]})'
wait_ready "${mongo_shell[@]}" --eval 'quit(db.hello().isWritablePrimary ? 0 : 1)'
export MISSION_TEST_MONGO_URL='mongodb://127.0.0.1:27249/?replicaSet=havosec_smoke'
export MONGO_URL="$MISSION_TEST_MONGO_URL"
export DB_NAME=havosec_smoke

if [[ "$mode" == --publication ]]; then
  "$py" verify_tile_studio_publication.py
  exit
fi

temporal_id=$("${engine[@]}" run -d --name "$temporal" -p 127.0.0.1:7239:7233 \
  temporalio/temporal:latest server start-dev --ip 0.0.0.0)
wait_ready "${engine[@]}" exec "$temporal_id" temporal operator cluster health
export MISSION_TEST_TEMPORAL_ADDRESS='127.0.0.1:7239'
export MISSION_TEST_USE_GITHUB_APP=1
export MISSION_TEST_GITHUB_PILOT='KathanGoda26/Tile_Studio,1430214091'
export MISSION_TEST_GITHUB_REPORT="${MISSION_TEST_GITHUB_REPORT:-${TMPDIR:-/tmp}/havosec-tile-studio-$run_id.json}"

"$py" -c 'import temporalio'
"$py" -m pytest -q -s tests/test_mission_orchestration.py::test_temporal_scans_authorized_github_snapshot
echo "Report: $MISSION_TEST_GITHUB_REPORT"
