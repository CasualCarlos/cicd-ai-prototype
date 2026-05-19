# AI-Geoptimaliseerde CI/CD Pipeline Prototype

![Build Status](https://github.com/YOUR_USERNAME/cicd-ai-prototype/actions/workflows/baseline.yml/badge.svg)
![AI Build Status](https://github.com/YOUR_USERNAME/cicd-ai-prototype/actions/workflows/ai-optimized.yml/badge.svg)

## Beschrijving

Dit project is een schoolopdracht waarbij een CI/CD-pipeline wordt gebouwd en verbeterd met behulp van AI-technieken. De kern van het prototype bestaat uit twee pijplijnconfiguraties: een **baseline-pipeline** (configuratie A) die altijd alle tests uitvoert, en een **AI-geoptimaliseerde pipeline** (configuratie B) die op basis van de gewijzigde bestanden (`git diff`) intelligente testselectie toepast om onnodige testuitvoering te vermijden. Daarnaast analyseert de AI-component bij mislukte builds automatisch de foutlogs en plaatst een diagnose als PR-commentaar, waardoor de gemiddelde tijd tot foutidentificatie aanzienlijk wordt verkort. Het project is gebouwd met Python 3.11, Flask, pytest en Docker, en draait op GitHub Actions.

---

## Mappenstructuur

```
cicd-ai-prototype/
├── .github/workflows/       # CI/CD workflow definities (baseline + AI)
├── app/                     # Flask-applicatie (routes, services, modellen)
├── tests/                   # Pytest-testsuites (unit + integratie)
├── ai_component/            # AI-logica: testselectie en loganalyse
├── docker/                  # Dockerfiles voor app en AI-component
├── scripts/                 # Hulpscripts: metingen, coverage-map genereren
├── results/                 # CSV-data en gegenereerde grafieken
├── docs/                    # Projectdocumentatie per fase
└── requirements.txt         # Python-afhankelijkheden
```

---

## Hoe uitvoeren

> **Let op**: volledige installatie-instructies worden toegevoegd zodra de applicatie en workflows zijn geïmplementeerd.

### Vereisten

- Docker Desktop
- Python 3.11+
- GitHub-account met toegang tot GitHub Actions

### Lokaal draaien (placeholder)

```bash
# Afhankelijkheden installeren
pip install -r requirements.txt

# Tests uitvoeren
pytest tests/

# AI testselectie handmatig testen
python ai_component/test_selector.py --diff "app/services/user_service.py"
```

### Pijplijnen vergelijken

1. Push een wijziging naar een feature branch om de AI-pipeline te triggeren
2. Merge naar `main` om de baseline-pipeline te triggeren
3. Bekijk timing-resultaten in `results/`

---

## Meting & Resultaten

Meetgegevens worden opgeslagen in `results/baseline_runs.csv` en `results/ai_runs.csv`.  
Grafieken worden gegenereerd via `scripts/collect_metrics.py`.

---

## Documenten

| Bestand | Inhoud |
|---------|--------|
| `docs/fase1_analyse.md` | Probleemanalyse en context |
| `docs/fase2_ontwerp.md` | Architectuurontwerp en beslissingen |
| `docs/fase3_implementatie.md` | Implementatieverslag |
| `docs/fase4_reflectie.md` | Reflectie en evaluatie |
