#!/usr/bin/env bash
# Standardify — Provider key swap script.
#
# Swaps the active LLM provider key in .env with zero code changes.
# Usage:
#   ./scripts/switch_provider_key.sh groq  <GROQ_KEY>
#   ./scripts/switch_provider_key.sh gemini <GEMINI_KEY>
#
# Phase 0 stub: shell skeleton only — implemented alongside Phase 3.2.

set -euo pipefail

PROVIDER="${1:-}"
KEY="${2:-}"

if [[ -z "$PROVIDER" || -z "$KEY" ]]; then
  echo "Usage: $0 <groq|gemini> <API_KEY>" >&2
  exit 1
fi

echo "Switching primary LLM provider to: $PROVIDER"
# Implementation added in Phase 3.2
