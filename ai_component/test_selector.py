"""
AI Test Selector — op basis van coverage-map heuristiek
=======================================================

Doel
----
Gegeven een `git diff`, bepaal welke testbestanden relevant zijn en geef
alleen die bestanden terug aan pytest. Dit verkort de pipeline-uitvoertijd
aanzienlijk op feature-branches waar maar één module gewijzigd is.

Algoritme
---------
1. Voer `git diff HEAD~1 --name-only` uit om gewijzigde bestanden te vinden.
2. Laad `ai_component/coverage_map.json` (bestand → testlijst mapping).
3. Voor elk gewijzigd bestand:
   a. Als het bestand zelf in tests/ staat → voeg het direct toe.
   b. Als het bestand in de coverage_map staat → voeg de gekoppelde tests toe.
   c. Als het bestand NIET in de coverage_map staat én het is een Python-
      bestand → onbekende afhankelijkheid: fallback naar alle tests.
4. Speciale gevallen die altijd een volledige run vereisen:
   - conftest.py gewijzigd (gedeelde fixtures — alles kan kapot zijn)
   - requirements.txt gewijzigd (afhankelijkheden veranderd)
   - coverage_map.json gewijzigd (de kaart zelf is verouderd)
5. Als er geen Python-bestanden gewijzigd zijn → geen tests nodig (exit 0,
   lege uitvoer), zodat de workflow de pytest-stap kan overslaan.

Exitcodes
----------
0 — Selectie geslaagd; gebruik de uitvoer als pytest-argumenten.
    Uitvoer kan leeg zijn (geen relevante wijzigingen) of een lijst van
    testpaden bevatten.
1 — Onzekerheid; de workflow moet terugvallen op de volledige testsuite.

Gebruik
-------
    python ai_component/test_selector.py
    # Schrijft geselecteerde testpaden naar stdout (ruimtegescheiden)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constanten
# ---------------------------------------------------------------------------

# Pad naar de coverage-map, relatief aan de repo-root
COVERAGE_MAP_PATH = Path("ai_component/coverage_map.json")

# Testdirectory — elk bestand hierin is altijd een testbestand
TESTS_DIR = Path("tests")

# Bestanden die een volledige run vereisen als ze gewijzigd zijn
FULL_RUN_TRIGGERS = {
    "tests/conftest.py",       # Gedeelde pytest-fixtures
    "requirements.txt",        # Afhankelijkheden veranderd
    "ai_component/coverage_map.json",  # De kaart zelf is bijgewerkt
}


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------

def get_changed_files() -> list[str]:
    """
    Voer `git diff HEAD~1 --name-only` uit en retourneer de gewijzigde
    bestanden als lijst van strings.

    Retourneert een lege lijst als git niet beschikbaar is of als er geen
    vorige commit is (bijv. de eerste commit in de repo).
    """
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        # Verwijder lege regels en witruimte
        files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return files
    except subprocess.CalledProcessError as exc:
        # git-commando mislukt (bijv. shallow clone zonder voldoende geschiedenis)
        print(
            f"[WAARSCHUWING] git diff mislukt (exitcode {exc.returncode}): {exc.stderr.strip()}",
            file=sys.stderr,
        )
        return []


def load_coverage_map() -> dict[str, list[str]]:
    """
    Laad coverage_map.json van schijf.

    Gooit FileNotFoundError als het bestand ontbreekt — de aanroeper
    behandelt dit als een fallback-situatie.
    """
    if not COVERAGE_MAP_PATH.exists():
        raise FileNotFoundError(
            f"Coverage map niet gevonden op '{COVERAGE_MAP_PATH}'. "
            "Genereer deze eerst met scripts/generate_coverage_map.py."
        )
    with COVERAGE_MAP_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def collect_all_test_files() -> list[str]:
    """Retourneer alle testbestanden in de tests/ directory (recursief)."""
    return [str(p) for p in sorted(TESTS_DIR.rglob("test_*.py"))]


# ---------------------------------------------------------------------------
# Kernlogica
# ---------------------------------------------------------------------------

def select_tests(
    changed_files: list[str],
    coverage_map: dict[str, list[str]],
) -> tuple[list[str] | None, str]:
    """
    Bepaal welke testbestanden uitgevoerd moeten worden op basis van de
    gewijzigde bestanden en de coverage-map.

    Retourneert een tuple van:
      - list[str] | None: geselecteerde testpaden, of None voor fallback
      - str: leesbare reden voor logging

    Als None wordt teruggegeven, moet de aanroeper terugvallen op alle tests.
    """
    # Bepaal alle beschikbare testbestanden voor tellingsdoeleinden
    all_tests = collect_all_test_files()

    # Filter op alleen Python-bestanden (wijzigingen in bijv. .md of .yml
    # vereisen geen tests)
    python_changes = [f for f in changed_files if f.endswith(".py")]

    # Geen Python-bestanden gewijzigd → sla tests over
    if not changed_files:
        return [], "Geen bestanden gewijzigd; geen tests vereist."
    if not python_changes:
        return (
            [],
            f"Alleen niet-Python bestanden gewijzigd ({changed_files}); geen tests vereist.",
        )

    # Controleer op triggers die altijd een volledige run vereisen
    triggered = [f for f in changed_files if f in FULL_RUN_TRIGGERS]
    if triggered:
        return (
            None,
            f"Volledige testsuite vereist vanwege wijziging in: {triggered}",
        )

    selected: set[str] = set()
    unmapped_files: list[str] = []

    for changed_file in python_changes:
        # Geval 1: gewijzigd bestand is zelf een testbestand
        if changed_file.startswith("tests/") and changed_file.endswith(".py"):
            selected.add(changed_file)
            continue

        # Geval 2: bestand staat in de coverage-map
        if changed_file in coverage_map:
            for test_file in coverage_map[changed_file]:
                selected.add(test_file)
            continue

        # Geval 3: Python-bestand buiten tests/ dat NIET in de map staat
        # → we weten niet welke tests hiervoor gelden → fallback
        unmapped_files.append(changed_file)

    if unmapped_files:
        return (
            None,
            f"Onbekende afhankelijkheden voor: {unmapped_files}. Fallback naar alle tests.",
        )

    # Controleer of de geselecteerde bestanden daadwerkelijk bestaan
    existing = [t for t in selected if Path(t).exists()]
    missing = [t for t in selected if not Path(t).exists()]
    if missing:
        # Verouderde coverage-map → wees voorzichtig en doe fallback
        return (
            None,
            f"Coverage-map verwijst naar niet-bestaande testbestanden: {missing}. Fallback.",
        )

    reason = (
        f"Geselecteerd {len(existing)} van {len(all_tests)} testbestanden "
        f"op basis van wijzigingen in: {python_changes}"
    )
    return sorted(existing), reason


# ---------------------------------------------------------------------------
# Hoofdprogramma
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Hoofdingang van het script.

    Schrijft geselecteerde testpaden (ruimtegescheiden) naar stdout.
    Schrijft voortgangs-/redenberichten naar stderr zodat ze in de
    workflow-logs verschijnen maar de uitvoer van stdout niet vervuilen.

    Exitcodes:
      0 — Selectie geslaagd (gebruik stdout als pytest-argumenten)
      1 — Fallback vereist (voer alle tests uit)
    """
    # Stap 1: laad de coverage-map
    try:
        coverage_map = load_coverage_map()
    except FileNotFoundError as exc:
        print(f"[FOUT] {exc}", file=sys.stderr)
        print("[FOUT] Kan coverage-map niet laden. Terugvallen op alle tests.", file=sys.stderr)
        return 1

    # Stap 2: haal gewijzigde bestanden op via git
    changed_files = get_changed_files()
    print(f"[INFO] Gewijzigde bestanden gevonden: {changed_files}", file=sys.stderr)

    # Stap 3: bepaal de te selecteren tests
    selected, reason = select_tests(changed_files, coverage_map)

    # Stap 4: verwerk het resultaat
    if selected is None:
        # Fallback: de workflow moet alle tests draaien
        print(f"[FALLBACK] {reason}", file=sys.stderr)
        print("", end="")   # Lege stdout zodat de workflow weet: geen selectie
        return 1

    # Schrijf de samenvatting naar stderr (zichtbaar als annotatie in de workflow)
    print(f"[SELECTIE] {reason}", file=sys.stderr)

    if not selected:
        # Geen relevante tests → geef lege string terug (exit 0, sla pytest over)
        print("", end="")
        return 0

    # Schrijf de geselecteerde testpaden als ruimtegescheiden string naar stdout
    # De workflow leest dit via: SELECTED=$(python ai_component/test_selector.py)
    print(" ".join(selected), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
