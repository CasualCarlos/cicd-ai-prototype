# AI-Geoptimaliseerde CI/CD Pipeline

<!-- Badges: vervang door je eigen GitHub username na push -->
<!-- ![Baseline CI](https://github.com/<username>/cicd-ai-prototype/actions/workflows/baseline.yml/badge.svg) -->
<!-- ![AI-geoptimaliseerde CI](https://github.com/<username>/cicd-ai-prototype/actions/workflows/ai-optimized.yml/badge.svg) -->

Een prototype dat een CI/CD-pipeline uitbreidt met twee AI-componenten: **predictive test selection** (alleen relevante tests draaien op basis van gewijzigde bestanden) en **AI-gestuurde foutdiagnose** (automatische root-cause analyse bij falende builds als PR-commentaar). Gebouwd als afstudeerproject voor HBO-ICT Secure Software Engineering, Toets 2.

**Resultaat**: gemiddeld 35% kortere push-to-deploy doorlooptijd; time-to-understand van faallogboeken van 8–12 minuten naar ~30 seconden.

---

## Inhoudsopgave

- [Vereisten](#vereisten)
- [Lokaal draaien](#lokaal-draaien)
- [Pipelines vergelijken](#pipelines-vergelijken)
- [Mappenstructuur](#mappenstructuur)
- [Documentatie](#documentatie)

---

## Vereisten

- Python 3.11+
- pip (of een virtual environment zoals `.venv`)
- Git
- GitHub-account met toegang tot GitHub Actions (voor de CI-pipelines)
- Een OpenAI API-sleutel (voor de log-analysecomponent; optioneel voor lokaal draaien)

---

## Lokaal draaien

### 1. Repository klonen

```bash
git clone https://github.com/YOUR_USERNAME/cicd-ai-prototype.git
cd cicd-ai-prototype
```

### 2. Virtual environment aanmaken en afhankelijkheden installeren

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

### 3. Alle tests uitvoeren (baseline)

```bash
pytest tests/ -v --tb=short
```

### 4. AI-testselectie handmatig testen

```bash
# Zorg dat je in de root van de repository staat
# Simuleer een wijziging in user_service.py:
git diff HEAD~1 --name-only   # of pas coverage_map.json aan voor simulatie

python3 ai_component/test_selector.py
# Output: ruimtegescheiden lijst van geselecteerde testpaden
```

### 5. Log-analyser handmatig uitvoeren

Vereist een geldig `results/test-results.xml` (gegenereerd door pytest met `--junitxml`):

```bash
export OPENAI_API_KEY="sk-..."   # Stel je OpenAI API-sleutel in
pytest tests/ --junitxml=results/test-results.xml   # Genereer testresultaten
python3 ai_component/log_analyzer.py results/test-results.xml
# Output: results/ai-diagnosis.md
```

### 6. Coverage-map regenereren na structuurwijzigingen

```bash
pytest tests/ --cov=app --cov-context=test
python3 scripts/generate_coverage_map.py
# Schrijft ai_component/coverage_map.json
```

---

## Pipelines vergelijken

Het prototype bevat twee pipeline-configuraties die naast elkaar meten:

| Pipeline | Bestand | Triggert op | Beschrijving |
|----------|---------|-------------|--------------|
| **Baseline** | `.github/workflows/baseline.yml` | Push naar `main`, alle PRs | Altijd alle 31 tests |
| **AI-geoptimaliseerd** | `.github/workflows/ai-optimized.yml` | Feature-branches (`feature/**`, `fix/**`), PRs | AI-testselectie + diagnose bij failures |

### Meting uitvoeren

1. Maak een feature-branch aan en doe een gerichte wijziging in één servicebestand:
   ```bash
   git checkout -b feature/test-selectie-demo
   # Wijzig bijv. app/services/user_service.py
   git add app/services/user_service.py
   git commit -m "feat: demo AI-testselectie"
   git push origin feature/test-selectie-demo
   ```
2. Bekijk de GitHub Actions UI: beide pipelines draaien; vergelijk de doorlooptijden
3. Metriekdata wordt opgeslagen in `results/metrics.csv` en `results/releases.csv`

---

## Mappenstructuur

```
cicd-ai-prototype/
├── .github/workflows/       # CI/CD workflow-definities
│   ├── baseline.yml         # Config A: altijd alle tests
│   └── ai-optimized.yml     # Config B: AI-selectie + log-analyse
│
├── ai_component/            # AI-logica
│   ├── test_selector.py     # Selecteert relevante tests op basis van git diff
│   ├── log_analyzer.py      # Analyseert pytest-failures met GPT-4o-mini
│   └── coverage_map.json    # Bestand-naar-test mapping (handmatig of gegenereerd)
│
├── app/                     # FastAPI REST-applicatie
│   ├── main.py              # App-entry en routing
│   ├── models.py            # SQLAlchemy modellen
│   ├── routes/              # Endpoint-definities (users, products)
│   └── services/            # Businesslogica (user_service, product_service)
│
├── tests/                   # Geautomatiseerde testsuites
│   ├── unit/                # 16 unit-tests
│   └── integration/         # 15 integratie-tests
│
├── results/                 # Metriekdata en gegenereerde rapporten
│   ├── metrics.csv          # Testtijden per scenario
│   ├── releases.csv         # Push-to-deploy per release
│   └── ai-diagnosis-example.md  # Voorbeeldoutput log-analyser
│
├── scripts/                 # Hulpscripts
│   ├── generate_coverage_map.py  # Genereert coverage_map.json
│   ├── collect_metrics.py        # Vergelijkt coverage-rapporten
│   └── post_pr_comment.py        # Plaatst AI-diagnose als PR-commentaar
│
├── docker/                  # Container-configuratie
├── docs/                    # Projectdocumentatie
└── requirements.txt         # Python-afhankelijkheden
```

---

## Documentatie

| Bestand | Inhoud | Weging |
|---------|--------|--------|
| [`docs/rapport.md`](docs/rapport.md) | **Eindrapport** — volledig geïntegreerd verslag van alle fasen | — |
| [`docs/fase1_analyse.md`](docs/fase1_analyse.md) | Analyse: CI/CD-processen, platformvergelijking, knelpunten, AI-mogelijkheden | 25% |
| [`docs/fase2_ontwerp.md`](docs/fase2_ontwerp.md) | Ontwerp: pipeline-architectuur, AI-componenten, security, KPI's | 30% |
| [`docs/fase3_implementatie.md`](docs/fase3_implementatie.md) | Implementatie: prototype, testscenario's, meetresultaten | 30% |
| [`docs/fase4_reflectie.md`](docs/fase4_reflectie.md) | Reflectie: prestatieanalyse, beperkingen, aanbevelingen, toekomstvisie | 15% |
