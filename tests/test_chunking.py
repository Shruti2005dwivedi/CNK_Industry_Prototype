import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ingestion import chunk_plain_text

SAMPLE = """CBDT Circular No. 12/2026
Issued by: Income Tax Department
Date of Issue: 15-06-2026

Section 16(4) of the CGST Act provides that a registered person shall not be entitled
to take input tax credit after the prescribed statutory period. """ * 3


def test_chunking_produces_chunks():
    chunks = chunk_plain_text(SAMPLE, source_document="test_circular.txt")
    assert len(chunks) > 0
    assert all(c.source_document == "test_circular.txt" for c in chunks)


def test_metadata_tagging_extracts_section_and_date():
    chunks = chunk_plain_text(SAMPLE, source_document="test_circular.txt")
    found_section = any(c.section_reference != "Unknown" for c in chunks)
    found_date = any(c.date_of_issue != "Unknown" for c in chunks)
    assert found_section, "Expected at least one chunk to tag a Section reference"
    assert found_date, "Expected at least one chunk to tag a date"


def test_chunk_ids_are_unique():
    chunks = chunk_plain_text(SAMPLE, source_document="test_circular.txt")
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


if __name__ == "__main__":
    test_chunking_produces_chunks()
    test_metadata_tagging_extracts_section_and_date()
    test_chunk_ids_are_unique()
    print("All chunking tests passed.")
