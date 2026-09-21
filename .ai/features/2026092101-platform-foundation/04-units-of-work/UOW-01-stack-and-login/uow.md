---
id: UOW-01
slug: stack-and-login
title: Stack runs and users log in with org code
demoable: true
duration: 2d
depends_on: []
requirements: [US-01, US-02, US-03]
verifies: [AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09]
risk: high
status: todo
rollback: revert the merge commit; migrations have downgrade()
---

# UOW-01 — Stack runs and users log in with org code

## Demo script
1. cp .env.example .env && docker compose up -d --build
2. Open http://localhost:8088/api/health → status ok, db ok, storage ok
3. Open http://localhost:8088/login, enter org `system`, `admin`, `admin12345` → forced to /change-password
4. Set a new password → land on the super admin home
5. Log out, log in with a wrong password → generic error; reload /login → org field prefilled

## In scope
- Compose stack, Dockerfiles, Caddy
- API skeleton, config, DB, errors, health
- Alembic base schema (organizations, users, refresh_tokens, audit_logs), seed
- Auth service + routes, lockout, refresh rotation, forced password change
- Next.js scaffold, API client, login + change-password pages, role home

## Not in scope
- Org CRUD (UOW-02)
- User management (UOW-03)

## Risks
| Risk | Mitigation |
| --- | --- |
| argon2 slow on ARM | tune time_cost; measured in T-01-04 |

## Definition of done
- [ ] All of AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09 pass
- [ ] Images build on arm64
- [ ] No token or password in logs
- [ ] Demo script executed end to end
- [ ] Demoed and accepted at gate G4
