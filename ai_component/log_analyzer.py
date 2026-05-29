"""
Log Anomaly Detection — AI-component voor CI/CD pipeline.

Analyseert een pytest-logbestand (JUnit XML of tekstuitvoer) bij een mislukte
build en stuurt de inhoud naar OpenAI gpt-4o-mini voor root-cause analyse.

Gebruik:
    python ai_component/log_analyzer.py <log_file_path>

Uitvoer:
    - Markdown-diagnose naar stdout
    - Opgeslagen in results/ai-diagnosis.md

Omgevingsvariabelen:
    OPENAI_API_KEY  — vereist voor de OpenAI API-aanroep
                      (als ontbrekend of ongeldig: fallback naar demo-modus)

Beveiligingsrichtlijnen:
    - Geen secrets in code; alleen via omgevingsvariabelen
    - Pipeline blokkeert nooit door dit script (gebruik continue-on-error: true)
    - Log wordt afgekapt op 2000 tekens om API-kosten te beperken
"""

import os
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Constanten
# ---------------------------------------------------------------------------

# Maximaal aantal tekens van het logbestand dat naar de API wordt gestuurd.
# gpt-4o-mini heeft een ruim contextvenster, maar 2000 tekens bevat de
# relevante foutregels en is goedkoop (~$0.002 per aanroep).
LOG_TRUNCATE_CHARS = 2000

# Uitvoerpad voor de diagnose (relatief aan de projectroot, vanuit CI).
OUTPUT_FILE = Path("results/ai-diagnosis.md")

# Fallback-tekst wanneer de API niet beschikbaar is.
FALLBACK_MESSAGE = (
    "## 🤖 AI Log Analyse\n\n"
    "**AI-analyse niet beschikbaar** — handmatige beoordeling vereist.\n\n"
    "Controleer de workflow-logs voor de volledige foutdetails."
)

# Systeem-prompt die het model instrueert als CI/CD-loganalyst.
SYSTEM_PROMPT = (
    "You are a CI/CD log analyzer. "
    "Given test failure output, identify the root cause and suggest a fix. "
    "Be concise and structured. Respond in Markdown."
)

# Gebruikersprompt met de instructie en het logfragment.
USER_PROMPT_TEMPLATE = textwrap.dedent("""\
    Analyze the following CI/CD test failure log. Identify:
    1. Root cause of the failure
    2. Which specific code change likely caused it
    3. Suggested fix

    Keep your response concise (max 200 words). Format as markdown.

    ---
    {log_content}
    ---
""")


# ---------------------------------------------------------------------------
# Hulpfuncties
# ---------------------------------------------------------------------------

def read_log(log_path: str) -> str:
    """
    Lees het logbestand en retourneer de laatste LOG_TRUNCATE_CHARS tekens.

    We nemen het *einde* van het bestand omdat pytest de foutdetails onderaan
    schrijft (FAILED, AssertionError, traceback).
    """
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"Logbestand niet gevonden: {log_path}")

    content = path.read_text(encoding="utf-8", errors="replace")

    # Afkappen: behoud de laatste LOG_TRUNCATE_CHARS tekens
    if len(content) > LOG_TRUNCATE_CHARS:
        content = "...[afgekapt]...\n" + content[-LOG_TRUNCATE_CHARS:]

    return content


def call_openai_api(log_content: str) -> str:
    """
    Stuur het logfragment naar OpenAI en retourneer de Markdown-diagnose.

    Raises:
        ImportError  — als de openai-package niet geïnstalleerd is
        Exception    — als de API-aanroep mislukt (timeout, rate limit, etc.)
    """
    # Importeer de openai-package pas hier zodat een ontbrekende installatie
    # als een fout wordt afgevangen in de aanroeper, niet bij module-import.
    import openai  # noqa: PLC0415

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is niet ingesteld of leeg. "
            "Stel de omgevingsvariabele in via GitHub Secrets."
        )

    client = openai.OpenAI(api_key=api_key)

    user_prompt = USER_PROMPT_TEMPLATE.format(log_content=log_content)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=400,   # ruim genoeg voor 200 woorden Markdown
        temperature=0.2,  # laag = deterministische, feitelijke output
    )

    return response.choices[0].message.content.strip()


def save_diagnosis(diagnosis: str) -> None:
    """Schrijf de diagnose naar OUTPUT_FILE (maakt de map aan indien nodig)."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(diagnosis, encoding="utf-8")
    print(f"[log_analyzer] Diagnose opgeslagen in: {OUTPUT_FILE}", file=sys.stderr)


def generate_demo_diagnosis(log_content: str) -> str:
    """
    Genereer een demonstratie-diagnose op basis van het logbestand.

    Wordt gebruikt als de OpenAI API niet beschikbaar is (geen API-key).
    Analyseert het logbestand met eenvoudige patroonherkenning om een
    realistische voorbeelduitvoer te produceren.
    """
    header = "## 🤖 AI Log Analyse — Faaldiagnose (demo-modus)\n\n"
    header += "> *Opmerking: Deze analyse is gegenereerd in demo-modus "
    header += "(zonder OpenAI API). In productie wordt gpt-4o-mini gebruikt.*\n\n"

    # Eenvoudige patroonherkenning in de logs
    lines = log_content.split("\n")
    failed_tests = [l for l in lines if "FAILED" in l or "AssertionError" in l]
    error_lines = [l for l in lines if "Error" in l or "Exception" in l]

    diagnosis = "### Gedetecteerde patronen\n\n"

    if failed_tests:
        diagnosis += f"**Falende tests gevonden**: {len(failed_tests)}\n\n"
        for t in failed_tests[:3]:
            diagnosis += f"- `{t.strip()}`\n"
        diagnosis += "\n"

    if error_lines:
        diagnosis += f"**Foutmeldingen**: {len(error_lines)}\n\n"
        for e in error_lines[:3]:
            diagnosis += f"- `{e.strip()}`\n"
        diagnosis += "\n"

    diagnosis += "### Mogelijke oorzaak\n\n"
    diagnosis += "Op basis van de foutpatronen lijkt er een regressie te zijn "
    diagnosis += "in de business-logica. Controleer recente wijzigingen in de "
    diagnosis += "service-laag.\n\n"
    diagnosis += "### Aanbevolen actie\n\n"
    diagnosis += "1. Bekijk de `git diff` van de laatste commit\n"
    diagnosis += "2. Controleer de inputvalidatie in de betreffende service\n"
    diagnosis += "3. Draai de falende tests lokaal met `pytest -x -v`\n"

    return header + diagnosis


# ---------------------------------------------------------------------------
# Hoofdfunctie
# ---------------------------------------------------------------------------

def main() -> int:
    """
    Ingangspunt van het script.

    Retourneert exitcode 0 (altijd) — de pipeline mag nooit blokkeren door
    dit script. Fouten worden als fallback-bericht afgehandeld.
    """
    if len(sys.argv) < 2:
        print(
            "Gebruik: python ai_component/log_analyzer.py <log_file_path>",
            file=sys.stderr,
        )
        # Schrijf fallback zodat post_pr_comment.py altijd iets te posten heeft
        save_diagnosis(FALLBACK_MESSAGE)
        print(FALLBACK_MESSAGE)
        return 0

    log_path = sys.argv[1]

    # --- Stap 1: logbestand inlezen ---
    try:
        log_content = read_log(log_path)
    except FileNotFoundError as exc:
        print(f"[log_analyzer] Waarschuwing: {exc}", file=sys.stderr)
        save_diagnosis(FALLBACK_MESSAGE)
        print(FALLBACK_MESSAGE)
        return 0

    # --- Stap 2: OpenAI API aanroepen ---
    try:
        diagnosis = call_openai_api(log_content)
        header = "## 🤖 AI Log Analyse — Faaldiagnose\n\n"
        full_output = header + diagnosis
    except (ValueError, ImportError) as exc:
        # Configuratiefout: API-sleutel ontbreekt of pakket niet geïnstalleerd
        # → Gebruik demo-modus met voorbeeldanalyse
        print(f"[log_analyzer] Configuratiefout: {exc}", file=sys.stderr)
        print("[log_analyzer] Demo-modus actief: voorbeelddiagnose wordt gebruikt.", file=sys.stderr)
        full_output = generate_demo_diagnosis(log_content)
    except Exception as exc:  # noqa: BLE001  (bewust breed: API-fouten variëren)
        # Tijdelijk API-probleem (timeout, rate limit, network error)
        print(f"[log_analyzer] API-fout: {exc}", file=sys.stderr)
        full_output = generate_demo_diagnosis(log_content)

    # --- Stap 3: uitvoer opslaan en naar stdout schrijven ---
    save_diagnosis(full_output)
    print(full_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
