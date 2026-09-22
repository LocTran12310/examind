---
name: api-endpoint
description: Add or change an API use case or endpoint in a layered module (domain rule → application handler → repository/read model → router), with its tests. Use for any change under apps/api/app/modules.
---

# Add an API endpoint

Read `.ai/architecture.md` and the module you are changing. Copy the shape of an existing use case in the same
module rather than inventing one; `modules/taxonomy` (tags) is the smallest complete example.

## Steps

1. **Name the use case.** A command changes state (`create_tag`, `submit_attempt`), a query answers a question
   (`search_tags`, `class_overview`). One file, one handler class.
2. **Domain first.** Put the rule where it belongs: an entity method (`Tag.change`), a value object, or a pure
   service under `domain/services/`. Invalid input raises `Invalid`/`Conflict`/`NotFound` from
   `app.shared.domain.errors`. If the rule needs data, add a method to the port in `domain/ports.py`.
3. **Application handler.**
   ```python
   @dataclass(frozen=True)
   class CreateTag: group: str; name: str; subject_id: uuid.UUID | None = None

   class CreateTagHandler:
       def __init__(self, tags: TagRepository, subjects: SubjectLookup, uow: UnitOfWork): ...
       def __call__(self, actor: Actor, cmd: CreateTag) -> TagView:
           ...                       # rules through the entity, data through ports
           self.uow.commit()         # commands only
           return tag_view(tag)
   ```
   The handler never imports sqlalchemy, fastapi or another module's internals. Data from another context comes
   from its `application/api.py` through an adapter port.
4. **Infrastructure.** Implement the port: aggregates in `repositories.py`, read-only projections in
   `read_models.py` (SQL Core over the tables in `shared/infrastructure/schema/`). Filter by `org_id` in every query.
5. **Interface.** Pydantic in/out in `schemas.py`, a builder in `deps.py`, a thin route in `router.py`:
   ```python
   @router.post("/tags", response_model=TagOut, status_code=201)
   def create_tag(body: TagIn, actor: Actor = Depends(staff_actor), handle: CreateTagHandler = Depends(deps.create_tag)):
       return TagOut(**vars(handle(actor, CreateTag(body.group, body.name, body.subject_id))))
   ```
   `current_actor` for anyone signed in, `staff_actor` for teachers/admins.
6. **Tests.** A handler test in `tests/unit/test_<module>_handlers.py` with fakes from `tests/unit/fakes.py`
   (happy path, each rule, wrong organisation), plus an HTTP test in `tests/test_<area>_api.py`.

## Before you call it done

```bash
cd apps/api && uv run ruff check . && uv run lint-imports
cd ../.. && ./scripts/verify.sh apps/api/tests/unit apps/api/tests/test_<area>_api.py
```
Then the full suite if you touched anything shared. Update `apps/api/AGENTS.md` only when a rule changed.
