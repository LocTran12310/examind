"""Processing config: upload choice > org default > system default (US-04, AC-16, AC-17)."""
from sqlalchemy.orm import Session

from app.deps import OrgScope
from app.models import Organization

SPLIT_MODES = ("rule", "rule_ai", "ai")
OCR_ENGINES = ("auto", "tesseract", "vision")
SYSTEM_DEFAULT = {"split_mode": "rule", "ocr": "auto", "split_models": [], "tag_model": None, "vision_model": None, "threshold": 0.85}


def org_defaults(db: Session, org_id) -> dict:
    org = db.get(Organization, org_id)
    stored = (org.settings or {}).get("ingestion", {}) if org else {}
    return {**SYSTEM_DEFAULT, **{k: v for k, v in stored.items() if k in SYSTEM_DEFAULT}}


def resolve_config(db: Session, scope: OrgScope, override: dict | None) -> dict:
    cfg = org_defaults(db, scope.org_id)
    for k, v in (override or {}).items():
        if k in SYSTEM_DEFAULT and v is not None:
            cfg[k] = v
    if cfg["split_mode"] not in SPLIT_MODES:
        cfg["split_mode"] = "rule"
    if cfg["ocr"] not in OCR_ENGINES:
        cfg["ocr"] = "auto"
    try:
        cfg["threshold"] = min(1.0, max(0.0, float(cfg["threshold"])))
    except (TypeError, ValueError):
        cfg["threshold"] = SYSTEM_DEFAULT["threshold"]
    cfg["split_models"] = [str(m) for m in (cfg.get("split_models") or [])][:3]
    return cfg
