#!/usr/bin/env bash
# Helpers for converting SQLAlchemy DATABASE_URL values to libpq / pg_dump URIs.

is_postgres_url() {
  echo "$1" | grep -qE '^postgresql(\+[^:/]+)?://'
}

is_sqlite_url() {
  echo "$1" | grep -qE '^sqlite:'
}

# postgresql+psycopg2://user:pass@host:5432/db -> postgresql://user:pass@host:5432/db
to_pg_uri() {
  local url="${1:?DATABASE_URL required}"
  echo "$url" | sed -E 's|^postgresql(\+[^:/]+)?://|postgresql://|'
}

resolve_sqlite_path() {
  local url="${1:?DATABASE_URL required}"
  local backend_root="${2:?backend root required}"
  local path
  path="$(echo "$url" | sed -E 's|^sqlite:///+||')"
  if [ "${path#/}" = "$path" ]; then
    echo "$backend_root/$path"
  else
    echo "$path"
  fi
}
