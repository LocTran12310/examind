#!/usr/bin/env python3
"""Write UoW + ticket files for an AI-DLC feature from a compact Python spec.

Usage: python3 scripts/gen_plan.py <feature_dir> <spec.py>
The spec module defines UOWS = [dict(...)] and TICKETS = [dict(...)].
`blocks` is derived from `depends_on`, so the two can never disagree.
"""
import importlib.util
import os
import sys


def fm_list(items):
    return "[" + ", ".join(items) + "]"


def main(feature_dir, spec_path):
    spec = importlib.util.spec_from_file_location("spec", spec_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    blocks = {t["id"]: [] for t in mod.TICKETS}
    for t in mod.TICKETS:
        for d in t.get("depends_on", []):
            blocks.setdefault(d, []).append(t["id"])
    uow_dirs = {}
    for u in mod.UOWS:
        d = os.path.join(feature_dir, "04-units-of-work", f"{u['id']}-{u['slug']}")
        os.makedirs(os.path.join(d, "tickets"), exist_ok=True)
        uow_dirs[u["id"]] = d
        verifies = sorted({ac for t in mod.TICKETS if t["uow"] == u["id"] for ac in t["verifies"]})
        body = [
            "---",
            f"id: {u['id']}",
            f"slug: {u['slug']}",
            f"title: {u['title']}",
            "demoable: true",
            f"duration: {u.get('duration', '2d')}",
            f"depends_on: {fm_list(u.get('depends_on', []))}",
            f"requirements: {fm_list(u['requirements'])}",
            f"verifies: {fm_list(verifies)}",
            f"risk: {u.get('risk', 'medium')}",
            f"status: {u.get('status', 'todo')}",
            f"rollback: {u.get('rollback', 'revert the merge commit; migrations have downgrade()')}",
            "---",
            "",
            f"# {u['id']} — {u['title']}",
            "",
            "## Demo script",
            *[f"{i}. {s}" for i, s in enumerate(u["demo"], 1)],
            "",
            "## In scope",
            *[f"- {s}" for s in u["in_scope"]],
            "",
            "## Not in scope",
            *[f"- {s}" for s in u.get("not_in_scope", ["See other UoWs"])],
            "",
            "## Risks",
            "| Risk | Mitigation |",
            "| --- | --- |",
            *[f"| {r} | {m} |" for r, m in u.get("risks", [("None significant", "—")])],
            "",
            "## Definition of done",
            *[f"- [{'x' if u.get('dod_done') else ' '}] {s}" for s in
              [f"All of {', '.join(verifies)} pass"] + u.get("dod", []) +
              ["Demo script executed end to end", "Demoed and accepted at gate G4"]],
            "",
        ]
        with open(os.path.join(d, "uow.md"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(body))
    for t in mod.TICKETS:
        path = os.path.join(uow_dirs[t["uow"]], "tickets", f"{t['id']}.md")
        status = t.get("status", "todo")
        if os.path.exists(path):  # never clobber controller-managed status
            for line in open(path, encoding="utf-8"):
                if line.startswith("status:"):
                    status = line.split(":", 1)[1].strip()
                    break
        lines = [
            "---",
            f"id: {t['id']}",
            f"uow: {t['uow']}",
            f"title: {t['title']}",
            f"layer: {t['layer']}",
            f"type: {t.get('type', 'feature')}",
            f"estimate: {t['estimate']}",
            f"status: {status}",
            f"depends_on: {fm_list(t.get('depends_on', []))}",
            f"blocks: {fm_list(sorted(blocks.get(t['id'], [])))}",
            f"verifies: {fm_list(t['verifies'])}",
            "tests:",
            *[f"  - {x}" for x in t.get("tests", [])],
            "touches:",
            *[f"  - {x}   # new" for x in t["touches"]],
            f"assumptions: {fm_list(t.get('assumptions', []))}",
            "---",
            "",
            f"# {t['id']} — {t['title']}",
            "",
            "## Context",
            t["context"],
            "",
            "## Implementation notes",
            *[f"- {s}" for s in t.get("notes", [])],
            "",
            "## Done when",
            *[f"- [ ] {s}" for s in t["done_when"]],
            "",
        ]
        if not os.path.exists(path) or t.get("overwrite", True):
            old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            new = "\n".join(lines)
            if old and "- [x]" in old:
                # keep ticked boxes ticked
                for s in t["done_when"]:
                    if f"- [x] {s}" in old:
                        new = new.replace(f"- [ ] {s}", f"- [x] {s}")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(new)
    print(f"wrote {len(mod.UOWS)} UoWs, {len(mod.TICKETS)} tickets")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
