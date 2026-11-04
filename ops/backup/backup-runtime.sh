#!/usr/bin/env bash
set -euo pipefail
SRC="${HOME}/services/combo-paper/runtime"; DST="${HOME}/backups"; mkdir -p "$DST"
tar czf "$DST/runtime-$(date +%Y%m%d-%H%M).tgz" -C "$(dirname "$SRC")" "$(basename "$SRC")"
find "$DST" -name 'runtime-*.tgz' -mtime +14 -delete
