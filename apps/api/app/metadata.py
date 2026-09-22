"""The whole schema in one place: every table (app/shared/infrastructure/schema/*) and every module's ORM mapping.
Imported by Alembic (migrations/env.py), the bootstrap and the tests, so the metadata they see is complete."""
import importlib
import pkgutil

import app.modules
from app.shared.infrastructure.db import metadata
import app.shared.infrastructure.schema as schema

for _m in pkgutil.iter_modules(schema.__path__):
    importlib.import_module(f"{schema.__name__}.{_m.name}")
for _m in pkgutil.iter_modules(app.modules.__path__):
    if _m.ispkg:
        importlib.import_module(f"app.modules.{_m.name}.infrastructure.orm")
importlib.import_module("app.worker.queue")  # the job row

__all__ = ["metadata"]
