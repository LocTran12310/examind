---
feature: architecture-refactor
stories: 4
acceptance_criteria: 8
---

# Requirements

## US-01 — Layered API modules
**Priority:** must

**AC-01** — Dependency rule enforced
```gherkin
Given the API package
When `lint-imports` runs
Then every module keeps interface → application → domain, infrastructure depends only inward, domain imports no sqlalchemy/fastapi/pydantic/boto3, modules use only another module's application layer, and shared never imports modules
```

**AC-02** — Search contract
```gherkin
Given a list resource
When the client posts {page, limit, q, sort, filters} to /<resource>/search with string (* = + - !), compare (= < <= > >=), date-range or enum filters
Then the answer is {data, total, page, limit}, the old GET list is gone, and an unknown field or operator answers 422 bad_filter
```

**AC-03** — Error shape
```gherkin
Given any failing request
When the API answers
Then the body is {code, message, details: {fields?, requestId}} and the X-Request-Id header matches details.requestId
```

## US-02 — Query-driven web client
**Priority:** must

**AC-04** — One data path
```gherkin
Given the web source
When lint runs
Then only services/ call the http client, only hooks/react-query use React Query, routes hold no data logic, and useApi / reloadKey no longer exist
```

**AC-05** — Cache and invalidation
```gherkin
Given a list and a form
When a record is created, edited or deleted, or the organisation is switched
Then the affected queries refetch without a manual reload, and switching organisation clears the cache without a full page reload
```

## US-03 — Same behaviour
**Priority:** must

**AC-06** — No regression
```gherkin
Given the refactored code
When the API suite, the official golden set and the web suite run and each page is walked in the browser
Then they pass with the same results as before the refactor
```

## US-04 — Documented structure
**Priority:** should

**AC-07** — Architecture map
```gherkin
Given .ai/architecture.md
When a developer adds a feature
Then it names every folder, the file-naming rules and the dependency rules for web and API
```

**AC-08** — Own conventions
```gherkin
Given docs, ADRs, code comments and commit messages written from now on
When they are searched for names of other projects
Then nothing is found; the conventions read as Examind's own
```
