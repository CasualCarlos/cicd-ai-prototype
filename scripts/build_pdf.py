#!/usr/bin/env python3
"""
build_pdf.py — Converteer rapport.md naar een professioneel opgemaakte PDF.

Stappen:
1. Pandoc: markdown → HTML met mermaid codeblocks als <pre class="mermaid">
2. Injecteer mermaid.js CDN + academische CSS styling
3. WeasyPrint: HTML → PDF

Gebruik:
    python3 scripts/build_pdf.py

Vereisten:
    pip install weasyprint
    brew install pango pandoc
"""

import re
import subprocess
import sys
from pathlib import Path

DOCS_DIR = Path("docs")
INPUT_MD = DOCS_DIR / "rapport.md"
OUTPUT_HTML = DOCS_DIR / "rapport.html"
OUTPUT_PDF = DOCS_DIR / "rapport.pdf"

# Academische styling
CSS = """
@page {
    size: A4;
    margin: 2.5cm 2.5cm 3cm 2.5cm;
    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #666;
    }
}

body {
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.8;
    color: #1a1a1a;
    text-align: justify;
    hyphens: auto;
}

h1 {
    font-size: 20pt;
    text-align: center;
    margin-top: 0;
    margin-bottom: 0.5em;
    page-break-before: avoid;
}

h2 {
    font-size: 15pt;
    margin-top: 2em;
    border-bottom: 2px solid #333;
    padding-bottom: 4px;
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    margin-top: 1.5em;
    page-break-after: avoid;
}

h4 {
    font-size: 11pt;
    margin-top: 1.2em;
    font-style: italic;
}

/* Voorpagina metadata */
body > p:first-of-type,
body > p:nth-of-type(2),
body > p:nth-of-type(3),
body > p:nth-of-type(4) {
    text-align: center;
    margin: 0.2em 0;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1.2em 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
}

th, td {
    border: 1px solid #666;
    padding: 6px 10px;
    text-align: left;
}

th {
    background: #f0f0f0;
    font-weight: bold;
}

tr:nth-child(even) {
    background: #fafafa;
}

caption, .table-caption {
    font-style: italic;
    margin-top: 0.5em;
    font-size: 9.5pt;
    text-align: center;
}

code {
    background: #f4f4f4;
    padding: 1px 4px;
    font-size: 9pt;
    border-radius: 2px;
    font-family: 'Menlo', 'Consolas', monospace;
}

pre {
    background: #f8f8f8;
    padding: 12px 16px;
    overflow-x: auto;
    font-size: 8.5pt;
    border: 1px solid #ddd;
    border-radius: 4px;
    page-break-inside: avoid;
    line-height: 1.5;
}

pre code {
    background: none;
    padding: 0;
}

blockquote {
    border-left: 3px solid #666;
    margin-left: 0;
    padding-left: 16px;
    color: #444;
    font-style: italic;
}

/* Figuren (mermaid SVGs) */
.mermaid-figure {
    text-align: center;
    margin: 1.5em 0;
    page-break-inside: avoid;
}

.mermaid-figure svg {
    max-width: 100%;
    height: auto;
}

.figure-caption {
    font-style: italic;
    font-size: 9.5pt;
    margin-top: 0.5em;
    color: #444;
}

/* Inhoudsopgave */
nav#TOC {
    page-break-after: always;
    margin-top: 2em;
}

nav#TOC ul {
    list-style: none;
    padding-left: 0;
}

nav#TOC > ul > li {
    margin: 0.6em 0;
    font-weight: bold;
}

nav#TOC > ul > li > ul > li {
    margin: 0.3em 0;
    padding-left: 1.5em;
    font-weight: normal;
}

/* Bronnenlijst */
.references, #bronnenlijst + ul, h2#bronnenlijst ~ p {
    font-size: 10pt;
    line-height: 1.6;
}

/* Horizontale lijn = paginascheiding */
hr {
    border: none;
    page-break-after: always;
}

/* Emoji fix */
.emoji {
    font-style: normal;
}

img {
    max-width: 100%;
    height: auto;
}
"""


def convert_md_to_html():
    """Pandoc: Markdown → HTML5 met TOC en sectienummering."""
    cmd = [
        "pandoc", str(INPUT_MD),
        "-f", "markdown",
        "-t", "html5",
        "--standalone",
        "--toc",
        "--toc-depth=3",
        "--number-sections",
        "-V", "lang=nl",
        "--metadata", "title=",
        "-o", str(OUTPUT_HTML),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Pandoc fout: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"[1/3] Markdown → HTML: {OUTPUT_HTML}")


def inject_styling_and_mermaid():
    """Voeg CSS styling toe en converteer mermaid codeblocks naar SVG placeholders."""
    html = OUTPUT_HTML.read_text(encoding="utf-8")

    # Inject CSS in <head>
    css_tag = f"<style>\n{CSS}\n</style>"
    html = html.replace("</head>", f"{css_tag}\n</head>")

    # Convert mermaid code blocks to styled divs
    # Pandoc renders ```mermaid as <pre><code class="language-mermaid">...</code></pre>
    mermaid_pattern = r'<pre><code class="language-mermaid">(.*?)</code></pre>'

    def mermaid_to_figure(match):
        code = match.group(1)
        # Clean HTML entities
        code = code.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')
        return f'''<div class="mermaid-figure">
<pre style="background: #f0f8ff; border: 1px solid #b0d4f1; border-radius: 8px; padding: 16px; font-size: 8.5pt; text-align: left; white-space: pre-wrap;">
{code.strip()}
</pre>
<p class="figure-caption">Diagram (Mermaid-notatie — render via mermaid.live voor visuele weergave)</p>
</div>'''

    html = re.sub(mermaid_pattern, mermaid_to_figure, html, flags=re.DOTALL)

    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"[2/3] Styling en diagrammen verwerkt")


def html_to_pdf():
    """WeasyPrint: HTML → PDF."""
    try:
        from weasyprint import HTML as WPHTML
    except ImportError:
        print("WeasyPrint niet geïnstalleerd. Run: pip install weasyprint", file=sys.stderr)
        sys.exit(1)

    WPHTML(str(OUTPUT_HTML)).write_pdf(str(OUTPUT_PDF))
    print(f"[3/3] HTML → PDF: {OUTPUT_PDF}")


def main():
    if not INPUT_MD.exists():
        print(f"Bronbestand niet gevonden: {INPUT_MD}", file=sys.stderr)
        sys.exit(1)

    convert_md_to_html()
    inject_styling_and_mermaid()
    html_to_pdf()

    # Tel pagina's
    try:
        from weasyprint import HTML as WPHTML
        doc = WPHTML(str(OUTPUT_HTML)).render()
        print(f"\n✅ Rapport gegenereerd: {len(doc.pages)} pagina's")
        print(f"   PDF: {OUTPUT_PDF}")
        print(f"   HTML: {OUTPUT_HTML}")
    except Exception:
        print(f"\n✅ Rapport gegenereerd")


if __name__ == "__main__":
    main()
