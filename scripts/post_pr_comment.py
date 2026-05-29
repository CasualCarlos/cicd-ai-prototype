"""
PR Comment Poster — plaatst de AI-diagnose als commentaar op de huidige PR.

Leest results/ai-diagnosis.md en post de inhoud via de GitHub REST API als
PR-commentaar. Als er geen PR-context beschikbaar is (bijv. bij een directe
push zonder open PR), wordt de diagnose alleen naar stdout geschreven.

Gebruik:
    python scripts/post_pr_comment.py

Omgevingsvariabelen:
    GITHUB_TOKEN        — vereist voor de GitHub API (meegeleverd door Actions)
    GITHUB_REPOSITORY   — eigenaar/repo, bijv. "gebruiker/repo" (door Actions)
    GITHUB_EVENT_NAME   — "pull_request" of "push" (door Actions)
    GITHUB_EVENT_PATH   — pad naar het event-JSON-bestand (door Actions)

Beveiligingsrichtlijnen:
    - Geen secrets in code; uitsluitend via omgevingsvariabelen
    - Minimale GitHub-tokenrechten: pull-requests: write
    - continue-on-error: true in de workflow — dit script stopt de pipeline nooit
"""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Constanten
# ---------------------------------------------------------------------------

# Bestand met de AI-diagnose, gegenereerd door log_analyzer.py
DIAGNOSIS_FILE = Path("results/ai-diagnosis.md")

# Commentaarheader zichtbaar boven de diagnose in de PR
COMMENT_HEADER = "## 🤖 AI Log Analysis — Failure Diagnosis\n\n"

# GitHub API basis-URL
GITHUB_API_BASE = "https://api.github.com"

# Fallback-diagnose als het diagnosebestand ontbreekt
FALLBACK_DIAGNOSIS = (
    "**AI-diagnose niet beschikbaar** — "
    "het bestand `results/ai-diagnosis.md` ontbreekt. "
    "Controleer de workflow-logs voor meer details."
)


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------

def read_diagnosis() -> str:
    """
    Lees de AI-diagnose uit DIAGNOSIS_FILE.

    Retourneert FALLBACK_DIAGNOSIS als het bestand ontbreekt of leeg is.
    """
    if not DIAGNOSIS_FILE.exists():
        print(
            f"[post_pr_comment] Waarschuwing: {DIAGNOSIS_FILE} niet gevonden.",
            file=sys.stderr,
        )
        return FALLBACK_DIAGNOSIS

    content = DIAGNOSIS_FILE.read_text(encoding="utf-8").strip()
    return content if content else FALLBACK_DIAGNOSIS


def get_pr_number() -> int | None:
    """
    Haal het PR-nummer op uit het GitHub Actions-event JSON-bestand.

    Retourneert None als we niet in een PR-context zitten of als het
    event-bestand niet beschikbaar is.
    """
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    if event_name != "pull_request":
        return None

    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not event_path or not Path(event_path).exists():
        print(
            "[post_pr_comment] GITHUB_EVENT_PATH niet ingesteld of bestand ontbreekt.",
            file=sys.stderr,
        )
        return None

    try:
        with open(event_path, encoding="utf-8") as fh:
            event_data = json.load(fh)
        return event_data.get("pull_request", {}).get("number")
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[post_pr_comment] Kon event-bestand niet lezen: {exc}", file=sys.stderr)
        return None


def post_github_comment(repo: str, pr_number: int, body: str, token: str) -> bool:
    """
    Post een commentaar op een GitHub PR via de REST API.

    Args:
        repo:       "eigenaar/repo" string
        pr_number:  nummer van de PR
        body:       Markdown-tekst van het commentaar
        token:      GitHub-token met pull-requests: write rechten

    Retourneert True bij succes, False bij een fout.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo}/issues/{pr_number}/comments"

    payload = json.dumps({"body": body}).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            # Identificeer het script als user-agent (GitHub raadt dit aan)
            "User-Agent": "cicd-ai-prototype/post_pr_comment",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            status = response.status
            if status == 201:
                print(
                    f"[post_pr_comment] Commentaar geplaatst op PR #{pr_number}.",
                    file=sys.stderr,
                )
                return True
            print(
                f"[post_pr_comment] Onverwachte statuscode: {status}",
                file=sys.stderr,
            )
            return False
    except urllib.error.HTTPError as exc:
        print(
            f"[post_pr_comment] HTTP-fout bij plaatsen commentaar: {exc.code} {exc.reason}",
            file=sys.stderr,
        )
        return False
    except urllib.error.URLError as exc:
        print(
            f"[post_pr_comment] Netwerkfout bij plaatsen commentaar: {exc.reason}",
            file=sys.stderr,
        )
        return False


# ---------------------------------------------------------------------------
# Hoofdfunctie
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Ingangspunt van het script.

    Altijd exitcode 0 — de pipeline mag nooit blokkeren door dit script.
    """
    # --- Lees diagnose ---
    diagnosis = read_diagnosis()
    full_comment = COMMENT_HEADER + diagnosis

    # --- Altijd naar stdout schrijven (zichtbaar in workflow-logs) ---
    print(full_comment)

    # --- GitHub-context controleren ---
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    pr_number = get_pr_number()

    if not token:
        print(
            "[post_pr_comment] GITHUB_TOKEN niet ingesteld — sla PR-commentaar over.",
            file=sys.stderr,
        )
        return 0

    if not repo:
        print(
            "[post_pr_comment] GITHUB_REPOSITORY niet ingesteld — sla PR-commentaar over.",
            file=sys.stderr,
        )
        return 0

    if pr_number is None:
        print(
            "[post_pr_comment] Geen PR-context gevonden "
            "(event_name='%s') — analyse alleen naar stdout." % os.environ.get("GITHUB_EVENT_NAME", "onbekend"),
            file=sys.stderr,
        )
        return 0

    # --- Commentaar op PR plaatsen ---
    post_github_comment(repo, pr_number, full_comment, token)

    return 0


if __name__ == "__main__":
    sys.exit(main())
