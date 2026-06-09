# AI-Geoptimaliseerde CI/CD Pipeline

![Baseline CI](https://github.com/CasualCarlos/cicd-ai-prototype/actions/workflows/baseline.yml/badge.svg)
![AI-Optimized CI](https://github.com/CasualCarlos/cicd-ai-prototype/actions/workflows/ai-optimized.yml/badge.svg)

Een prototype dat een CI/CD-pipeline uitbreidt met twee AI-componenten: **predictive test selection** (alleen relevante tests draaien op basis van gewijzigde bestanden) en **AI-gestuurde foutdiagnose** (automatische root-cause analyse bij falende builds als PR-commentaar). Gebouwd voor HBO-ICT Secure Software Engineering, Toets 2.

**Resultaat**: AI-testselectie reduceert het aantal uitgevoerde tests met 48–74% bij gerichte wijzigingen; de log-analyser verkort de foutdiagnosetijd van 5–10 minuten naar ~30 seconden.

---

## Inhoudsopgave

- [Vereisten](#vereisten)
- [Lokaal draaien](#lokaal-draaien)
- [Pipelines vergelijken](#pipelines-vergelijken)
- [Mappenstructuur](#mappenstructuur)
- [Rapport](#rapport)

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
git clone https://github.com/CasualCarlos/cicd-ai-prototype.git
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
# Simuleer een wijziging in user_service.py:
git diff HEAD~1 --name-only

python3 ai_component/test_selector.py
# Output: ruimtegescheiden lijst van geselecteerde testpaden
```

### 5. Log-analyser handmatig uitvoeren

```bash
export OPENAI_API_KEY="sk-..."   # Stel je OpenAI API-sleutel in
pytest tests/ --junitxml=results/test-results.xml   # Genereer testresultaten
python3 ai_component/log_analyzer.py results/test-results.xml
# Output: results/ai-diagnosis.md
```

---

## Pipelines vergelijken

Het prototype bevat twee pipeline-configuraties die naast elkaar meten:

| Pipeline | Bestand | Triggert op | Beschrijving |
|----------|---------|-------------|--------------|
| **Baseline** | `.github/workflows/baseline.yml` | Push naar `main`, alle PRs | Altijd alle 31 tests |
| **AI-geoptimaliseerd** | `.github/workflows/ai-optimized.yml` | Feature-branches (`feature/**`, `fix/**`, `scenario/**`), PRs | AI-testselectie + diagnose bij failures |

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
3. Metriekdata ophalen na afloop: `python3 scripts/fetch_metrics.py`

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
│   └── coverage_map.json    # Bestand-naar-test mapping
│
├── app/                     # Flask REST-applicatie
│   ├── main.py              # App factory en routing
│   ├── database.py          # SQLite database-setup en schema
│   ├── routes/              # Endpoint-definities (users, products)
│   └── services/            # Businesslogica (user_service, product_service)
│
├── tests/                   # Geautomatiseerde testsuites
│   ├── unit/                # 16 unit-tests (2 bestanden)
│   └── integration/         # 15 integratie-tests (2 bestanden)
│
├── results/                 # Meetdata
│   ├── metrics.csv          # Echte GitHub Actions run-data
│   └── ai-diagnosis-example.md  # Voorbeeldoutput log-analyser
│
├── scripts/                 # Hulpscripts
│   ├── fetch_metrics.py     # Haalt run-data op via GitHub API
│   └── post_pr_comment.py   # Plaatst AI-diagnose als PR-commentaar
│
├── docker/                  # Container-configuratie
│   ├── Dockerfile           # Applicatie-container
│   └── docker-compose.yml   # Compose-configuratie
│
├── docs/
│   └── rapport.pdf          # Eindrapport (44 pagina's)
│
├── README.md
└── requirements.txt
```

---

## Rapport

Het eindrapport is beschikbaar als [`docs/rapport.pdf`](docs/rapport.pdf) en bevat:

1. **Analyse** — CI/CD-processen, platformvergelijking, knelpunten, AI-mogelijkheden
2. **Ontwerp** — Pipeline-architectuur, AI-componenten, security, KPI's
3. **Implementatie** — Prototype, testscenario's, meetresultaten met echte GitHub Actions data
4. **Reflectie** — Prestatieanalyse, beperkingen, aanbevelingen, toekomstvisie
