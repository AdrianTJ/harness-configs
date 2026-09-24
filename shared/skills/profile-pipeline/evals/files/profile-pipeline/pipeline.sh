#!/usr/bin/env bash
set -o pipefail
cat access.log \
  | grep ' 500' \
  | cut -d' ' -f1 \
  | sort \
  | uniq -c \
  | sort -rn \
  | head -20
