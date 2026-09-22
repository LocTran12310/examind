"""In-memory ports shared by the handler unit tests (no database)."""


class FakeUow:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1

    def flush(self):
        pass

    def rollback(self):
        self.rollbacks = getattr(self, "rollbacks", 0) + 1


class FakeAudit:
    def __init__(self):
        self.entries = []

    def record(self, actor, org_id, action, target_type, target_id=None, **data):
        self.entries.append((action, target_id, data))

    def actions(self):
        return [a for a, _, _ in self.entries]
