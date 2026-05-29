#!/usr/bin/env python3
"""
fetch_metrics.py — Haal echte pipeline-metrieken op via de GitHub Actions API.

Raadpleegt de workflow runs van zowel 'baseline' als 'ai-optimized' pipelines
en schrijft de resultaten naar results/metrics.csv.

Gebruik:
    python3 scripts/fetch_metrics.py

Omgevingsvariabelen:
    GITHUB_TOKEN  — Personal Access Token (of laat leeg voor publieke repos)

Gemaakt: 2026-06-09
"""

import csv
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuratie
# ---------------------------------------------------------------------------

REPO = "CasualCarlos/cicd-ai-prototype"
API_BASE = f"https://api.github.com/repos/{REPO}/actions"
OUTPUT_FILE = Path("results/metrics.csv")
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Token is optioneel voor publieke repos (maar verhoogt rate limit)
TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_get(url: str) -> dict:
    """Doe een GET request naar de GitHub API."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def get_workflow_runs(workflow_filename: str, limit: int = 20) -> list:
    """Haal de laatste N runs op voor een specifieke workflow."""
    url = f"{API_BASE}/workflows/{workflow_filename}/runs?per_page={limit}&status=completed"
    data = api_get(url)
    return data.get("workflow_runs", [])


def get_run_jobs(run_id: int) -> list:
    """Haal de jobs op voor een specifieke run."""
    url = f"{API_BASE}/runs/{run_id}/jobs"
    data = api_get(url)
    return data.get("jobs", [])


def calculate_duration(run: dict) -> int:
    """Bereken de duur in seconden van een workflow run."""
    start = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
    return int((end - start).total_seconds())


# ---------------------------------------------------------------------------
# Hoofdlogica
# ---------------------------------------------------------------------------

def collect_metrics():
    """Verzamel metrieken van alle workflow runs en schrijf naar CSV."""
    rows = []

    for workflow_file, label in [("baseline.yml", "baseline"), ("ai-optimized.yml", "ai-optimized")]:
        print(f"[INFO] Ophalen van runs voor {workflow_file}...")
        runs = get_workflow_runs(workflow_file)
        print(f"       {len(runs)} voltooide runs gevonden.")

        for run in runs:
            duration = calculate_duration(run)
            conclusion = run.get("conclusion", "unknown")

            # Haal test-aantallen op uit de jobs (als beschikbaar)
            jobs = get_run_jobs(run["id"])
            tests_info = {"run": 0, "passed": 0, "failed": 0}

            # Probeer test-resultaten te achterhalen uit de job-stappen
            for job in jobs:
                for step in job.get("steps", []):
                    if "test" in step.get("name", "").lower() and step.get("conclusion") == "failure":
                        tests_info["failed"] += 1

            rows.append({
                "timestamp": run["run_started_at"],
                "workflow": label,
                "run_number": run["run_number"],
                "duration_seconds": duration,
                "conclusion": conclusion,
                "branch": run.get("head_branch", "unknown"),
                "commit_sha": run.get("head_sha", "")[:7],
            })

    # Sorteer op timestamp
    rows.sort(key=lambda r: r["timestamp"])

    # Schrijf CSV
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "workflow", "run_number", "duration_seconds",
            "conclusion", "branch", "commit_sha"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[OK] {len(rows)} metrieken geschreven naar {OUTPUT_FILE}")
    print(f"     Baseline runs: {sum(1 for r in rows if r['workflow'] == 'baseline')}")
    print(f"     AI-optimized runs: {sum(1 for r in rows if r['workflow'] == 'ai-optimized')}")


if __name__ == "__main__":
    try:
        collect_metrics()
    except urllib.error.HTTPError as e:
        print(f"[FOUT] GitHub API fout: {e.code} {e.reason}", file=sys.stderr)
        if e.code == 403:
            print("       Rate limit bereikt. Stel GITHUB_TOKEN in.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[FOUT] {e}", file=sys.stderr)
        sys.exit(1)
