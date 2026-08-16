"""Generates sample_circular.pdf from sample_circular_source.txt so the
ingestion pipeline has a real PDF to chew on out of the box.

Usage: python data/sample_docs/make_sample_pdf.py
"""
from pathlib import Path

import fitz  # PyMuPDF

HERE = Path(__file__).resolve().parent
src = (HERE / "sample_circular_source.txt").read_text()
out_path = HERE / "sample_circular.pdf"

doc = fitz.open()
page = doc.new_page()
rect = fitz.Rect(50, 50, 545, 792)
page.insert_textbox(rect, src, fontsize=10, fontname="helv")
doc.save(out_path)
doc.close()
print(f"Wrote {out_path}")
