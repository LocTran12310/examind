"""Dependency rules of the layered API (architecture-refactor AC-01, ADR-05)."""
import os
import pkgutil
import subprocess

import grimp

import app.modules

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_import_linter_contracts_are_kept():
    r = subprocess.run(["lint-imports"], cwd=HERE, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def _modules() -> list[str]:
    return [m.name for m in pkgutil.iter_modules(app.modules.__path__) if m.ispkg]


def test_modules_talk_through_application_only():
    graph = grimp.build_graph("app")
    bad = []
    for name in _modules():
        mine = f"app.modules.{name}"
        for other in _modules():
            if other == name:
                continue
            for layer in ("domain", "infrastructure", "interface"):
                target = f"app.modules.{other}.{layer}"
                if target not in graph.modules:
                    continue
                for chain in graph.find_shortest_chains(importer=mine, imported=target, as_packages=True):
                    bad.append(" → ".join(chain))
    assert not bad, "import another module's application layer instead:\n" + "\n".join(bad)


def test_every_module_has_the_four_layers():
    for name in _modules():
        base = os.path.join(os.path.dirname(app.modules.__file__), name)
        missing = [layer for layer in ("domain", "application", "infrastructure", "interface") if not os.path.isdir(os.path.join(base, layer))]
        assert not missing, f"{name}: missing {missing}"
