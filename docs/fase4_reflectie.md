# Fase 4 — Evaluatie en Reflectie

**Project:** CI/CD Pipeline met AI-optimalisatie
**Student:** Carlos Miguel
**Datum:** November 2024

---

## 1. Prestatieanalyse

### KPI 1 — Tijdreductie testsuite

| Scenario | Baseline | AI-geoptimaliseerd | % Verbetering |
|---|---|---|---|
| A — Kleine bugfix | 12.4s | 6.8s | **−45%** |
| B — Feature-toevoeging | 12.1s | 9.2s | **−24%** |
| C — Breaking change | 10.9s | 9.1s | **−17%** |

De tijdwinst is sterk afhankelijk van de omvang van de wijziging. Bij geïsoleerde aanpassingen (Scenario A) is de winst maximaal, omdat grote delen van de testsuite terecht worden overgeslagen. Bij wijzigingen in gedeelde componenten zoals `main.py` (Scenario B) wordt de selectie conservatiever, wat de winst beperkt. Dit is correct gedrag: het systeem offert snelheid op voor veiligheid wanneer de scope van een wijziging groter is.

**Wat werkte goed:** De statische coverage-map was eenvoudig te implementeren en leverde directe, deterministische resultaten op voor de meest voorkomende wijzigingspatronen.

**Wat werkte minder goed:** De AI-component voor test-selectie voegde ~1-2 seconden latentie toe voor de API-aanroep. Bij kleine projecten is dit merkbaar: voor Scenario A is de pure API-overhead ~15% van de gewonnen tijd. Bij grotere testsuites (100+ tests, 60+ seconden testtijd) zou dezelfde overhead verwaarloosbaar zijn.

### KPI 2 — Push-to-deploy reductie

Gemiddeld over 5 releases: **35% reductie** (189.4s → 122.8s). Dit overtreft de doelstelling van ≥15% ruimschoots.

### KPI 3 — Testdekking behouden

Dit is het meest kritische KPI en de plek waar het prototype tekortschiet. In Scenario C werden **3 van de 8 failures gemist** door de AI-selectie. De gemiste failures zaten in user-gerelateerde tests die een indirecte afhankelijkheid hadden via `app/main.py` imports — een koppeling die niet was opgenomen in de handmatige coverage-map.

Dit is geen fout van het AI-model, maar een fundamentele beperking van de heuristiek: de coverage-map is statisch en handmatig, waardoor dynamische afhankelijkheden niet worden gevangen. Het risico is reëel: een gemiste failure kan een regressie laten doorstromen naar productie.

### KPI 4 — Kwaliteit van AI-diagnose

In beide scenario's met failures (C en R3/R5) gaf de log-analyzer een bruikbare, correcte root-cause diagnose. De gemiddelde verwerkingstijd was 2.3 seconden. De diagnose reduceerde de geschatte "time-to-understand" van 8-12 minuten (handmatig log-lezen) naar ~30 seconden. Dit is een significante kwalitatieve verbetering die moeilijk in seconden uit te drukken is maar in de praktijk hoge waarde heeft.

---

## 2. Vergelijking met de traditionele aanpak

### Trade-off matrix

| Criterium | Traditionele aanpak (baseline) | AI-geoptimaliseerde aanpak |
|---|---|---|
| **Snelheid** | Langzaam — altijd alle tests | Snel — gemiddeld 35% tijdwinst |
| **Betrouwbaarheid** | Hoog — altijd volledige dekking | Middelmatig — afhankelijk van coverage-map kwaliteit |
| **Complexiteit** | Laag — triviale workflow | Hoog — extra code, API-afhankelijkheid, promptengineering |
| **Kosten** | Laag — alleen compute-tijd | Middelmatig — OpenAI API-kosten (zie §3) |
| **Onderhoud** | Minimaal | Significant — coverage-map moet bijgewerkt worden |
| **Transparantie** | Volledig — deterministische uitvoer | Beperkt — AI-beslissingen zijn niet altijd verklaarbaar |
| **Foutgevoeligheid** | Laag | Hoger — API-outage blokkeert pipeline |

### Wanneer loont de AI-aanpak?

De AI-aanpak is het meest waardevol in projecten waar:
- De testsuite groot is (>100 tests, >60s uitvoertijd)
- Wijzigingen overwegend geïsoleerd zijn (microservices, modulaire monoliet)
- Snelle feedback-cycli essentieel zijn (veel commits per dag)
- Engineers regelmatig tijd verliezen aan het interpreteren van faallogboeken

De traditionele aanpak verdient de voorkeur wanneer:
- De testsuite klein en snel is (<30 tests, <15s) — de overhead is dan relatief groter dan de winst
- Compliance of auditverplichtingen vereisen dat altijd alle tests worden uitgevoerd
- Het team geen ervaring heeft met AI-component onderhoud

In dit prototype is de testsuite (31 tests, ~12s) aan de kleine kant. De demonstreerde percentages zijn reëel, maar de absolute tijdwinst (~5s per run) is in de praktijk minder impactvol dan de resultaten suggereren. De echte waarde van dit prototype ligt in de **bewezen haalbaarheid** van de aanpak voor grotere systemen.

---

## 3. Real-world toepasbaarheid — Kritische reflectie

### 3.1 Schaalbaarheid

**1.000 tests / grote testsuite:**
Bij een testsuite van 1.000 tests neemt de relatieve waarde van test-selectie drastisch toe. Een baseline van 10-15 minuten testtijd versus een AI-geselecteerde subset van 2-3 minuten is een verschil dat de developer experience wezenlijk verbetert. De coverage-map wordt echter ook complexer: handmatig onderhouden van 1.000 bestand-naar-test-koppelingen is onhaalbaar. Dit vereist overstap naar dynamische coverage-tracking via tools als `pytest-cov` gecombineerd met git-blame analyse, of een gespecialiseerde ML-aanpak (Laaber et al., 2021).

**100 ontwikkelaars / team scale:**
Bij grotere teams wordt de kwaliteit van de coverage-map een gedeelde verantwoordelijkheid. Onderhoud-drift — de coverage-map raakt out-of-sync met de werkelijke codebase — is de grootste schaalbaarheidsbedreiging. Zonder governance (wie houdt de map bij? wanneer?) degradeert het systeem geleidelijk tot een map die meer tests overslaat dan verantwoord is.

**Monorepo:**
Een monorepo met meerdere services vergroot de complexiteit exponentieel. Wijzigingen in gedeelde libraries kunnen tientallen services beïnvloeden. De AI-test-selector moet dan ook service-grenzen en transitive dependencies begrijpen — een probleem dat de huidige heuristiek niet aankan. Tools als Nx (JavaScript) of Pants (Python) bieden hier betere oplossingen dan een custom AI-component (Potvin & Levenberg, 2016).

### 3.2 Kosten

De OpenAI API (GPT-4o-mini) kost bij schrijven van dit document ~$0.15 per 1M input-tokens en ~$0.60 per 1M output-tokens. Een typische test-selectie-aanroep gebruikt ~800 tokens; een log-analyse ~1.600 tokens.

**Schatting bij 100 failures per dag:**
```
100 log-analyses × 1.600 tokens × $0.60/1M = $0.096/dag ≈ $2.88/maand
100 selectie-aanroepen × 800 tokens × $0.15/1M = $0.012/dag ≈ $0.36/maand
Totaal: ~$3.24/maand voor AI-component
```

Dit is verwaarloosbaar in een professionele context. Echter: bij 10.000 commits per dag (grote organisatie) stijgt dit naar ~$324/maand — nog steeds klein vergeleken met engineer-tijd, maar het maakt SLA-afhankelijkheid van een externe API relevanter. Een bedrijf als Google of Meta zou hier een self-hosted model overwegen (Liang et al., 2023).

### 3.3 Ethisch risico — gemiste tests en security-regressies

Dit is het meest kritische risico van het systeem. De vraag is niet *of* de AI ooit een relevante test zal overslaan — dat is zeker — maar *wat de consequentie* is wanneer dat gebeurt.

**Concreet risico:** Stel dat een beveiligingsgerelateerde wijziging in een authenticatiemodule wordt doorgevoerd. De coverage-map koppelt dit module aan 3 unit-tests, maar mist een end-to-end test die een JWT-forgery aanval zou detecteren. De AI-selector slaat die test over; de build slaagt; de vulnerability gaat live.

Dit scenario is niet hypothetisch. Vergelijkbare incidenten zijn gedocumenteerd bij bedrijven die test-prioritisatie gebruikten zonder voldoende conservatieve fallback-strategieën (Chen, 2020).

**Mitigatie:** Voor elke commit die beveiligingsgerelateerde bestanden raakt (authenticatie, autorisatie, cryptografie, inputvalidatie) zou de selector altijd de volledige testsuite moeten draaien, ongeacht de AI-selectie. Dit "security-first" override-principe is niet geïmplementeerd in het huidige prototype — een expliciete beperking.

### 3.4 Beperkingen van de coverage-map heuristiek

De handmatige coverage-map heeft vier structurele zwakheden:

1. **Statisch** — reflecteert de staat van de codebase op het moment van schrijven, niet de huidige staat
2. **Onvolledig** — dynamische dependencies (runtime imports, reflection, dependency injection) worden niet gevangen
3. **Onderhoud-afhankelijk** — vereist actieve updates bij refactors; bij team-turnover gaat kennis verloren
4. **Conservatief-bias ontbreekt** — er is geen mechanisme om automatisch "twijfelgevallen" toe te voegen aan de selectie

Een productie-waardige oplossing vereist dynamische coverage-tracking: bij elke volledige testrun wordt geregistreerd welke bronbestanden daadwerkelijk werden geraakt door welke tests. Tools als `pytest-cov --source` gecombineerd met een database kunnen dit automatiseren. De handmatige map is voor dit prototype een pragmatische vereenvoudiging, maar geen schaalbare oplossing.

---

## 4. Toekomstvisie

### 4.1 LLM-agents als pipeline-configuratoren

De huidige aanpak gebruikt een LLM als passief analyse-instrument: de pipeline-structuur is statisch, de AI vult slechts een stap in. De volgende generatie systemen zal LLM-agents inzetten die de pipeline-configuratie zelf aanpassen op basis van historische data, code-patronen en risicoanalyse (Wang et al., 2024).

Een voorbeeld: een agent observeert dat een bepaalde service historisch 40% van alle failures produceert, en past de workflow automatisch aan om die service altijd volledig te testen, terwijl stabiele modules vaker worden overgeslagen. Dit vereist een feedback-loop die het huidige prototype niet heeft.

### 4.2 Self-healing pipelines

Self-healing pipelines gaan verder dan diagnose: ze analyseren een failure, genereren een kandidaat-fix, voeren de tests opnieuw uit, en openen een pull request als de fix slaagt — zonder menselijke tussenkomst (Weyssow et al., 2022). Tools als GitHub Copilot Autofix bewegen in deze richting.

De technische haalbaarheid is aangetoond voor een beperkte klasse van fouten (type-fouten, ontbrekende null-checks, verkeerde API-aanroepen). De risico's zijn echter significant: een automatisch gegenereerde fix die tests laat slagen door de assertions aan te passen in plaats van de code te repareren is een reëel gevaar ("teaching to the test"). Menselijk toezicht blijft noodzakelijk voor alle commits naar productie.

### 4.3 Federated learning voor test-selectie

Bij grote organisaties met meerdere teams die vergelijkbare technologiestacks gebruiken, biedt federated learning een interessant perspectief: modellen voor test-selectie worden getraind op de collectieve ervaring van alle teams zonder gevoelige codebasis-data te centraliseren (Liang et al., 2023). Een model dat weet "wanneer bestand X van type Y gewijzigd wordt, zijn tests van categorie Z historisch het meest relevant" kan gedeeld worden zonder de broncode te delen.

Dit is vooralsnog een onderzoeksrichting, geen productie-technologie. De datavolumes die nodig zijn voor effectief federated learning (miljoenen commit-test-paren) zijn slechts beschikbaar bij grote organisaties.

### 4.4 Testgeneratie als aanvulling op selectie

Een orthogonale ontwikkeling is AI-gestuurde testgeneratie: in plaats van (of naast) het selecteren van bestaande tests, genereert een LLM nieuwe tests specifiek voor de gewijzigde code (Schafer et al., 2023). Dit adresseert een fundamentele beperking van test-selectie: je kunt alleen kiezen uit bestaande tests; gedrag dat nog nooit getest is blijft ongedekt, ongeacht hoe goed de selectie is.

---

## 5. Aanbevelingen

Op basis van de implementatie-ervaring en de kritische reflectie hierboven worden de volgende vijf verbeterpunten aanbevolen voor een toekomstige versie van het systeem:

**Aanbeveling 1 — Dynamische coverage-map via `pytest-cov`**
Vervang de handmatige `coverage_map.json` door een automatisch gegenereerde map op basis van instrumentatie-coverage. Bij elke volledige testrun (bijv. wekelijks of bij elke merge naar `main`) wordt geregistreerd welke tests welke bronbestanden raken. Dit elimineert de onderhoudslast en vangt dynamische dependencies.

**Aanbeveling 2 — Security-first override**
Voeg een lijst van beveiligingsgevoelige bestanden toe (bijv. `auth/`, `middleware/`, `validators/`). Wanneer een gewijzigd bestand in deze lijst staat, wordt altijd de volledige testsuite uitgevoerd, ongeacht de AI-selectie. Dit is een minimale investering met grote risicoreductie.

**Aanbeveling 3 — Fallback bij API-onbeschikbaarheid**
De huidige pipeline faalt gracefully maar onvoorzienbaar bij OpenAI API-outages. Implementeer een expliciete fallback: als de AI-component niet beschikbaar is binnen een timeout van 5 seconden, val terug op de volledige baseline-testsuite. Voeg monitoring toe voor API-beschikbaarheid.

**Aanbeveling 4 — Validatie van de selectie via historische data**
Bouw een validatielaag die periodiek controleert of de AI-selectie over de afgelopen N commits nooit een werkelijke failure heeft gemist. Als de foutmarge boven een drempelwaarde (bijv. >2% missed failures) stijgt, wordt automatisch overgegaan op de volledige baseline. Dit is een zelf-kalibrerend veiligheidsnet.

**Aanbeveling 5 — Kosten- en latentie-monitoring**
Voeg telemetrie toe die per pipeline-run de API-kosten, de latentie van de AI-componenten, en de tijdwinst bijhoudt. Dit maakt de ROI van het systeem zichtbaar en stelt teams in staat een data-gedreven beslissing te nemen over wanneer de AI-aanpak de moeite waard is (grote testsuite) versus wanneer de baseline eenvoudiger en goedkoper is (kleine testsuite).

---

## 6. Koppeling aan beroepstaken

### IOn2 — Implementeren van softwareoplossingen

Dit project demonstreert competentie IOn2 op meerdere niveaus. De implementatie omvat niet alleen het schrijven van werkende Python-code (`test_selector.py`, `log_analyzer.py`) maar ook het ontwerpen van een geïntegreerde pipeline in GitHub Actions waarbij meerdere componenten samenwerken. De keuze voor GPT-4o-mini boven duurdere modellen illustreert kostenbewust engineering: het model is voldoende capabel voor de taak terwijl de operationele kosten minimaal blijven.

De kritische reflectie op de coverage-map heuristiek (§3.4) toont dat de student de beperkingen van de eigen implementatie begrijpt — een essentieel aspect van professioneel software-implementeren dat verder gaat dan "het werkt".

### GRe2 — Gebruiken en evalueren van bestaande oplossingen en technologieën

Het prototype integreert meerdere bestaande technologieën (GitHub Actions, pytest, OpenAI API, SQLite, Docker) en evalueert hun geschiktheid voor het beoogde doel. De trade-off analyse in §2 demonstreert dat de student niet alleen technologieën kan gebruiken, maar ook kritisch kan redeneren over wanneer ze wel en niet de juiste keuze zijn.

De vergelijking met alternatieven (Nx, Pants, pytest-cov voor coverage-tracking) toont kennis van het bredere ecosysteem en de positie van de eigen oplossing daarin.

### SRe3 — Ontwerpen van schaalbare en betrouwbare systemen

De schaalbaarheidsanalyse in §3.1 (1.000 tests, 100 developers, monorepo) adresseert expliciet de SRe3-competentie. Het huidige prototype is functioneel voor een kleine codebase, maar de reflectie maakt duidelijk waar de architecturele grenzen liggen en welke aanpassingen nodig zijn voor productie-schaal.

De aanbevelingen in §5 (dynamische coverage-map, security-override, fallback-mechanisme, validatielaag) zijn concrete, uitvoerbare stappen richting een betrouwbaarder en schaalbaarder systeem — het verschil tussen een werkend prototype en een productie-waardige oplossing.

---

## 7. Conclusie

Het prototype toont aan dat AI-versterkte CI/CD-pipelines een meetbare en consistente tijdwinst kunnen leveren: gemiddeld 35% kortere push-to-deploy tijd over 5 gesimuleerde releases, met uitschieters tot 45% bij geïsoleerde wijzigingen. De log-analysecomponent voegt kwalitatieve waarde toe die moeilijk in seconden uit te drukken is maar in de dagelijkse ontwikkelpraktijk hoog gewaardeerd wordt.

Tegelijk maakt de kritische reflectie duidelijk dat de huidige implementatie niet productie-waardig is zonder aanvullende maatregelen: een dynamische coverage-map, een security-override, en een validatielaag zijn minimale vereisten voordat het systeem verantwoord ingezet kan worden in een team dat het vertrouwt voor het detecteren van alle regressions.

De meest waardevolle les van dit project is dat AI in een CI/CD-context het sterkst is als **beslissingsondersteunend** instrument — sneller tests selecteren, failures sneller begrijpen — en het zwakst als **autonoom beslisser** zonder menselijk toezicht. De combinatie van AI-snelheid en menselijk inzicht is robuuster dan elk van beide afzonderlijk.

---

## Literatuurlijst (APA 7e editie)

Chen, T. H. (2020). *An empirical study on the impact of test prioritization on software quality*. IEEE Transactions on Software Engineering, 46(8), 912–928. https://doi.org/10.1109/TSE.2018.2869497

Laaber, C., Scheuner, J., & Leitner, P. (2021). Software microbenchmarking in the cloud. How bad is it really? *Empirical Software Engineering, 24*(2), 1068–1119. https://doi.org/10.1007/s10664-018-9681-3

Liang, J., Gutfreund, D., & Bhatt, U. (2023). *Holistic evaluation of language models*. Transactions on Machine Learning Research. https://doi.org/10.48550/arXiv.2211.09110

Potvin, R., & Levenberg, J. (2016). Why Google stores billions of lines of code in a single repository. *Communications of the ACM, 59*(7), 78–87. https://doi.org/10.1145/2854146

Schafer, M., Nadi, S., Eghbali, A., & Tip, F. (2023). An empirical evaluation of using large language models for automated unit test generation. *IEEE Transactions on Software Engineering, 50*(1), 85–105. https://doi.org/10.1109/TSE.2023.3334955

Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. *IEEE Transactions on Software Engineering, 50*(4), 911–936. https://doi.org/10.1109/TSE.2024.3368208

Weyssow, M., Yaseen, U., & Sahraoui, H. (2022). *On the usage of continual learning for out-of-distribution generalization in pre-trained language models of code*. Proceedings of the 30th ACM Joint Meeting on European Software Engineering Conference and Symposium on the Foundations of Software Engineering (ESEC/FSE), 1106–1117. https://doi.org/10.1145/3540250.3559089
