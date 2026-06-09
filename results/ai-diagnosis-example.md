# AI Log Analyse — Diagnose Voorbeeld (Scenario C: Breaking Change)

**Gegenereerd door:** `ai_component/log_analyzer.py`
**Model:** GPT-4o-mini
**Tijdstip:** 2024-11-01T11:08:32Z
**Build-run:** `github-actions-run-#42`

---

## Samenvatting

> **5 tests gefaald** in de AI-geselecteerde testsuite na een wijziging in `app/services/product_service.py`.
> De AI-diagnose identificeert een **breaking change in de prijsberekeningslogica** als root cause.
> Aanbeveling: herstel de `calculate_discount()` methode of pas de testassertie aan als het nieuwe gedrag intentioneel is.

---

## Gedetecteerde patronen

### Patroon 1 — AssertionError op verwachte prijs (hoge betrouwbaarheid: 94%)

```
FAILED tests/unit/test_product_service.py::test_calculate_price_with_discount
FAILED tests/unit/test_product_service.py::test_calculate_price_bulk_order
FAILED tests/integration/test_products_api.py::test_get_product_returns_correct_price
```

**Analyse:**
Alle drie de failures hebben dezelfde stacktrace-root:
```
AssertionError: assert 85.0 == 90.0
  in app/services/product_service.py, regel 47, in calculate_discount
```
Dit wijst op een **gewijzigde kortingsformule**. De verwachte waarde is `90.0` (10% korting op 100.0),
maar de functie retourneert nu `85.0` (15% korting). Dit is waarschijnlijk een unintentionele regressie
door het aanpassen van de kortingsdrempel in `DISCOUNT_RATE`.

### Patroon 2 — Database constraint violation (betrouwbaarheid: 87%)

```
FAILED tests/integration/test_products_api.py::test_create_product_negative_price
FAILED tests/integration/test_product_routes.py::test_update_product_price_validation
```

**Analyse:**
```
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) CHECK constraint failed: price >= 0
  in app/routes/products.py, regel 89, in update_product
```
De validatie in `app/routes/products.py` laat nu negatieve prijzen door die de database-constraint
triggert. Dit hangt mogelijk samen met de refactor in `product_service.py` — de `validate_price()`
aanroep is weggevallen bij de herstructurering.

---

## Aanbevolen herstelacties

1. **Onmiddellijk:** Controleer `app/services/product_service.py` regel 23 — `DISCOUNT_RATE` is gewijzigd van `0.10` naar `0.15`. Dit lijkt onbedoeld op basis van de testspecificaties.
2. **Herstel validatie:** Voeg `validate_price()` terug toe in `app/routes/products.py` vóór de database-aanroep (regel 87-89).
3. **Niet blokkeren:** De overige 11 geslaagde tests (inclusief alle user-gerelateerde tests) zijn niet aangetast. Deze wijziging is geïsoleerd tot de product-module.

---

## Niet-gediagnosticeerde failures

Geen. Alle 5 failures zijn verklaard met hoge betrouwbaarheid.

---

## Contextuele waarschuwing

> De AI-diagnose is gebaseerd op patroonherkenning in logtekst en statische code-analyse.
> Verifieer altijd de aanbevelingen handmatig voordat u automatisch rollback of fixes uitvoert.
> Betrouwbaarheidsscores > 80% zijn in de evaluatie consistent correct gebleken, maar zijn geen garantie.

---

*Analyse gegenereerd in 2.3 seconden | OpenAI tokens gebruikt: ~1.240 prompt + ~380 completion*
