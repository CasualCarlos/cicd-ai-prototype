#!/usr/bin/env bash
# =============================================================================
# collect_metrics.sh — Metriek-verzamelaar voor CI/CD vergelijkingsonderzoek
#
# Gebruik:
#   bash scripts/collect_metrics.sh <label> <duration_seconds> \
#       <tests_run> <tests_passed> <tests_failed>
#
# Voorbeeld:
#   bash scripts/collect_metrics.sh baseline 72 31 31 0
#   bash scripts/collect_metrics.sh ai-optimized 34 8 8 0
#
# Het script voegt één rij toe aan results/metrics.csv met de kolommen:
#   timestamp, label, duration_seconds, tests_run, tests_passed, tests_failed
#
# Als het CSV-bestand nog niet bestaat wordt het aangemaakt inclusief
# kolomkoppen. Zo kan het bestand direct worden ingelezen door pandas of
# een spreadsheet voor verdere analyse.
#
# Gemaakt: 2026-06-02
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Argumenten valideren
# ---------------------------------------------------------------------------

if [ "$#" -lt 5 ]; then
  echo "Gebruik: $0 <label> <duration_seconds> <tests_run> <tests_passed> <tests_failed>" >&2
  echo "Voorbeeld: $0 baseline 72 31 31 0" >&2
  exit 1
fi

LABEL="$1"
DURATION_SECONDS="$2"
TESTS_RUN="$3"
TESTS_PASSED="$4"
TESTS_FAILED="$5"

# ---------------------------------------------------------------------------
# Resultatenmap aanmaken als die nog niet bestaat
# ---------------------------------------------------------------------------

RESULTS_DIR="results"
mkdir -p "${RESULTS_DIR}"

CSV_FILE="${RESULTS_DIR}/metrics.csv"

# ---------------------------------------------------------------------------
# Kolomkoppen schrijven als het bestand nog niet bestaat
# ---------------------------------------------------------------------------

if [ ! -f "${CSV_FILE}" ]; then
  echo "timestamp,label,duration_seconds,tests_run,tests_passed,tests_failed" > "${CSV_FILE}"
  echo "[INFO] Nieuw metrics-bestand aangemaakt: ${CSV_FILE}"
fi

# ---------------------------------------------------------------------------
# Tijdstempel ophalen in ISO 8601-formaat (UTC) voor consistente sortering
# ---------------------------------------------------------------------------

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Nieuwe rij toevoegen aan het CSV-bestand
# ---------------------------------------------------------------------------

echo "${TIMESTAMP},${LABEL},${DURATION_SECONDS},${TESTS_RUN},${TESTS_PASSED},${TESTS_FAILED}" >> "${CSV_FILE}"

echo "[OK] Metriek toegevoegd aan ${CSV_FILE}:"
echo "     timestamp=${TIMESTAMP}, label=${LABEL}, duration=${DURATION_SECONDS}s, \
tests_run=${TESTS_RUN}, passed=${TESTS_PASSED}, failed=${TESTS_FAILED}"
