#!/usr/bin/env bash
# =============================================================================
# run_scenarios.sh — Voer de 3 testscenario's uit op GitHub Actions
#
# Dit script maakt branches aan met specifieke wijzigingen die de
# AI test-selectie triggeren. Na het pushen draaien zowel de baseline
# (op main via merge) als de AI-optimized (op feature branch) pipelines.
#
# Gebruik:
#   bash scripts/run_scenarios.sh
#
# Voorwaarden:
#   - Je bent in de root van het project
#   - main branch is up-to-date
#   - GitHub remote is geconfigureerd
#
# Gemaakt: 2026-06-09
# =============================================================================

set -euo pipefail

echo "=== Scenario A: Kleine bugfix (1 bestand) ==="
echo "Wijzigt alleen app/services/user_service.py"
echo ""

git checkout main
git pull

# Scenario A: kleine wijziging in user_service.py
git checkout -b scenario/a-bugfix
# Voeg een onschuldige docstring-wijziging toe
sed -i.bak 's/"""Business logic for users."""/"""Business logic for users. (v1.1 — improved validation)"""/' app/services/user_service.py
rm -f app/services/user_service.py.bak
git add app/services/user_service.py
git commit -m "fix: verbeter validatie-foutmelding in user service"
git push -u origin scenario/a-bugfix
echo "✅ Scenario A gepusht — AI-optimized pipeline draait nu"
echo ""

sleep 5

echo "=== Scenario B: Feature-toevoeging (3 bestanden) ==="
echo "Wijzigt products.py, product_service.py, en main.py"
echo ""

git checkout main
git checkout -b scenario/b-feature
# Wijzig 3 bestanden
sed -i.bak 's/"""Product endpoints."""/"""Product endpoints. (v2.0 — added search)"""/' app/routes/products.py
rm -f app/routes/products.py.bak
sed -i.bak 's/"""Business logic for products."""/"""Business logic for products. (v2.0 — search support)"""/' app/services/product_service.py
rm -f app/services/product_service.py.bak
sed -i.bak 's/"""Flask application factory."""/"""Flask application factory. (v2.0)"""/' app/main.py
rm -f app/main.py.bak
git add app/routes/products.py app/services/product_service.py app/main.py
git commit -m "feat: voeg zoekfunctionaliteit toe aan producten"
git push -u origin scenario/b-feature
echo "✅ Scenario B gepusht — AI-optimized pipeline draait nu"
echo ""

sleep 5

echo "=== Scenario C: Breaking change (email validatie verwijderen) ==="
echo "Verwijdert validatie → tests gaan falen → AI diagnose activeert"
echo ""

git checkout main
git checkout -b scenario/c-breaking
# Verwijder email validatie (breekt tests)
sed -i.bak '/if not email or not email.strip():/,/raise ValueError("email is required")/d' app/services/user_service.py
rm -f app/services/user_service.py.bak
git add app/services/user_service.py
git commit -m "refactor: vereenvoudig user creation flow"
git push -u origin scenario/c-breaking
echo "✅ Scenario C gepusht — AI-optimized pipeline draait (met failures + AI diagnose)"
echo ""

echo "=== Nu baseline runs triggeren via merge naar main ==="
echo ""

git checkout main

# Merge scenario A naar main (triggert baseline)
git merge scenario/a-bugfix --no-edit
git push
echo "✅ Scenario A gemerged naar main — baseline pipeline draait"
sleep 3

# Merge scenario B naar main (triggert baseline)
git merge scenario/b-feature --no-edit
git push
echo "✅ Scenario B gemerged naar main — baseline pipeline draait"
sleep 3

echo ""
echo "=== KLAAR ==="
echo "Wacht ~5 minuten tot alle pipelines klaar zijn, dan:"
echo "  python3 scripts/fetch_metrics.py"
echo ""
echo "Scenario C is NIET gemerged naar main (breekt tests)."
echo "Na het verzamelen van data: git branch -D scenario/c-breaking"
