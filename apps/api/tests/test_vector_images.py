"""WMF/EMF → PNG (official-exam-ingestion AC-03)."""
from pathlib import Path

import pytest

from app.shared.domain.images import sniff
from app.modules.ingestion.infrastructure.adapters import vector_images
from app.modules.ingestion.infrastructure.image_store import document_store
from tests.factories import make_org

FIX = Path(__file__).parent / "fixtures" / "vector"
needs_soffice = pytest.mark.skipif(vector_images.soffice() is None, reason="LibreOffice not installed")


def test_kind_from_magic_bytes():
    assert vector_images.kind((FIX / "figure.wmf").read_bytes()) == "wmf"
    assert vector_images.kind((FIX / "figure.emf").read_bytes()) == "emf"
    assert vector_images.kind(b"\x89PNG\r\n\x1a\n") is None


@needs_soffice
@pytest.mark.parametrize("name", ["figure.wmf", "figure.emf"])
def test_metafile_becomes_trimmed_png(name):
    png = vector_images.to_png((FIX / name).read_bytes())
    mime, w, h = sniff(png)
    assert mime == "image/png"
    assert 20 < w < 1400 and 10 < h < 1400  # trimmed, not an A4 page


def test_without_libreoffice_the_old_warning_path_is_used(db, monkeypatch):
    org = make_org(db)
    monkeypatch.setattr(vector_images, "soffice", lambda: None)
    warnings, stats = [], {}
    store = document_store(db, org.id, None, warnings, stats)
    assert store((FIX / "figure.emf").read_bytes()) is None
    assert warnings and stats == {"vector_failed": 1}


@needs_soffice
def test_document_store_saves_png(db):
    org = make_org(db)
    warnings, stats = [], {}
    asset_id = document_store(db, org.id, None, warnings, stats)((FIX / "figure.emf").read_bytes())
    assert asset_id and not warnings and stats == {"vector_images": 1}
