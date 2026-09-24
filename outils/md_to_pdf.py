#!/usr/bin/env python3
"""Convertit un document Markdown en PDF (A4) — pipeline : markdown → HTML → PDF.

Moteurs essayés dans l'ordre :
  1. weasyprint  (si les libs système pango sont présentes — meilleur rendu)
  2. xhtml2pdf   (100 % Python, aucune dépendance système — mode dégradé)

Usage :
    /tmp/opencode/venv/bin/python outils/md_to_pdf.py <fichier.md> [fichier2.md ...]

Dépendances (dans le venv) : markdown ; weasyprint OU xhtml2pdf.
Sortie : même nom que l'entrée, extension .pdf, à côté du .md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import markdown

CSS = """
@page {
  size: A4;
  margin: 2cm 1.8cm;
}
body { font-family: Helvetica, "DejaVu Sans", sans-serif; font-size: 10pt;
       line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 17pt; color: #0b3d6e; border-bottom: 2px solid #0b3d6e;
     padding-bottom: 4px; margin-top: 0; }
h2 { font-size: 13.5pt; color: #0b3d6e; border-bottom: 1px solid #c9d8e8;
     padding-bottom: 2px; }
h3 { font-size: 11.5pt; color: #14508c; }
h4 { font-size: 10.5pt; color: #14508c; }
p { margin: 6px 0; }
ul, ol { margin: 6px 0 6px 18px; padding-left: 8px; }
li { margin: 2px 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 8.6pt; }
th { background: #0b3d6e; color: #ffffff; padding: 4px 6px; text-align: left; }
td { border: 0.5px solid #b8c4d2; padding: 3px 6px; vertical-align: top; }
code { font-family: "Courier", "DejaVu Sans Mono", monospace; font-size: 8.4pt;
       background: #eef2f6; padding: 0 3px; }
pre { background: #f4f6f9; border: 0.5px solid #ccd6e0; padding: 8px;
      font-family: "Courier", "DejaVu Sans Mono", monospace; font-size: 8pt;
      white-space: pre-wrap; word-wrap: break-word; }
blockquote { border-left: 3px solid #0b3d6e; margin: 6px 0; padding: 2px 10px;
             color: #444444; background: #f4f7fb; }
strong { color: #0b2d4e; }
hr { border: none; border-top: 1px solid #ccd6e0; margin: 14px 0; }
a { color: #0b3d6e; text-decoration: none; }
"""


def _html(md_path: Path) -> str:
    body = markdown.markdown(
        md_path.read_text(encoding="utf-8"),
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )
    return f"<!DOCTYPE html><html lang='fr'><head><meta charset='utf-8'>" \
           f"<style>{CSS}</style></head><body>{body}</body></html>"


def _try_weasyprint(html: str, pdf_path: Path) -> bool:
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(str(pdf_path))
        return True
    except Exception as exc:  # libs pango manquantes ou autre
        print(f"  ! weasyprint indisponible ({exc.__class__.__name__}) → xhtml2pdf")
        return False


def convert(md_path: Path, pdf_path: Path) -> None:
    html = _html(md_path)
    if not _try_weasyprint(html, pdf_path):
        from xhtml2pdf import pisa
        with open(pdf_path, "wb") as out:
            pisa.CreatePDF(html, dest=out, encoding="utf-8")
    print(f"ok  {pdf_path.name}  ({pdf_path.stat().st_size // 1024} Ko)")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    for arg in argv[1:]:
        src = Path(arg)
        if not src.exists():
            print(f"absent : {src}")
            continue
        convert(src, src.with_suffix(".pdf"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))