#!/usr/bin/env bash
# Ceragem CIOS — single local dev entry point (foreground servers + diagnostics).
# Usage:
#   bash scripts/dev.sh start [--with-worker]
#   bash scripts/dev.sh stop
#   bash scripts/dev.sh restart [--with-worker]
#   bash scripts/dev.sh status
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=dev_common.sh
source "$ROOT/scripts/dev_common.sh"

usage() {
  cat <<EOF
Ceragem CIOS local dev (v$(read_app_version))

Usage:
  bash scripts/dev.sh start [--with-worker]   Start servers in this Terminal (recommended)
  bash scripts/dev.sh stop                    Stop backend, frontend, and worker
  bash scripts/dev.sh restart [--with-worker] Stop then start (foreground)
  bash scripts/dev.sh status                  Health check and next-step hints

Official macOS launcher: double-click Start CIOS.command
EOF
}

status_line() {
  local state="$1"
  local label="$2"
  shift 2
  printf "  %-5s %-18s %s\n" "[$state]" "$label" "$*"
}

cmd_status() {
  local app_ver listener_b listener_f pg_ok be_ok fe_ok del_route be_ver async_flag
  app_ver="$(read_app_version)"

  echo "Ceragem CIOS — Local Dev Status (v${app_ver})"
  echo ""

  if check_postgres; then
    status_line "OK" "PostgreSQL" "127.0.0.1:5432"
    pg_ok=1
  else
    status_line "FAIL" "PostgreSQL" "not reachable → make postgres-up"
    pg_ok=0
  fi

  listener_b="$(port_listening 8000)"
  listener_f="$(port_listening 3002)"

  if health_backend; then
    be_ver="$(backend_version_live)"
    status_line "OK" "Backend" "http://127.0.0.1:8000 (health up, v${be_ver})"
    be_ok=1
    del_route="$(openapi_has_delete_user)"
    if [ "$del_route" = "yes" ]; then
      status_line "OK" "API routes" "DELETE /admin/users/{email} registered"
    else
      status_line "WARN" "API routes" "stale backend? missing DELETE user → bash scripts/dev.sh restart"
    fi
  elif [ -n "$listener_b" ]; then
    status_line "WARN" "Backend" "port 8000 listening but /health failed → check .dev/logs/backend.log"
    be_ok=0
  else
    status_line "FAIL" "Backend" "down → bash scripts/dev.sh start"
    be_ok=0
  fi

  if health_frontend; then
    status_line "OK" "Frontend" "http://127.0.0.1:3002/login"
    fe_ok=1
  elif [ -n "$listener_f" ]; then
    status_line "WARN" "Frontend" "port 3002 listening but /login failed → check .dev/logs/frontend.log"
    fe_ok=0
  else
    status_line "FAIL" "Frontend" "down → bash scripts/dev.sh start"
    fe_ok=0
  fi

  async_flag="$(read_backend_env UPLOAD_ASYNC false)"
  async_lower="$(printf '%s' "$async_flag" | tr '[:upper:]' '[:lower:]')"
  case "$async_lower" in
    true|1|yes)
      if worker_running; then
        status_line "OK" "Upload worker" "running (UPLOAD_ASYNC=true)"
      else
        status_line "WARN" "Upload worker" "not running → make worker  (or start --with-worker)"
      fi
      ;;
    *)
      status_line "OK" "Upload worker" "not required (UPLOAD_ASYNC=${async_flag:-false})"
      ;;
  esac

  echo ""
  if [ "$pg_ok" = 1 ] && [ "$be_ok" = 1 ] && [ "$fe_ok" = 1 ]; then
    echo "All critical services are up."
    echo "  Login: http://127.0.0.1:3002/login"
    echo "  Admin: http://127.0.0.1:3002/admin/users"
  else
    echo "Some services need attention. Suggested order:"
    [ "$pg_ok" = 0 ] && echo "  1. make postgres-up"
    echo "  2. bash scripts/setup_local.sh   (first-time only)"
    echo "  3. make migrate"
    echo "  4. bash scripts/dev.sh start"
  fi
  echo ""
  echo "Logs: ${LOG_DIR}/"
}

cmd_stop() {
  echo "==> Stopping Ceragem CIOS (backend, frontend, worker)..."
  stop_worker
  stop_all_servers
  echo "Done."
}

cmd_start() {
  local with_worker=0
  for arg in "$@"; do
    case "$arg" in
      --with-worker) with_worker=1 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown option: $arg"; usage; exit 1 ;;
    esac
  done

  echo "==> Stopping any background dev servers..."
  stop_all_servers

  if ! check_postgres; then
    echo "ERROR: PostgreSQL is not running at 127.0.0.1:5432"
    echo "Run: make postgres-up"
    exit 1
  fi

  if [ "$with_worker" = 1 ]; then
    start_worker_background || true
  fi

  exec bash "$ROOT/scripts/dev_foreground.sh"
}

cmd_restart() {
  local args=()
  for arg in "$@"; do args+=("$arg"); done
  cmd_stop
  echo ""
  if [ ${#args[@]} -gt 0 ]; then
    exec bash "$ROOT/scripts/dev.sh" start "${args[@]}"
  else
    exec bash "$ROOT/scripts/dev.sh" start
  fi
}

ACTION="${1:-}"
shift || true

case "$ACTION" in
  start) cmd_start "$@" ;;
  stop) cmd_stop ;;
  restart) cmd_restart "$@" ;;
  status) cmd_status ;;
  ""|-h|--help|help) usage ;;
  *)
    echo "Unknown command: $ACTION"
    usage
    exit 1
    ;;
esac
