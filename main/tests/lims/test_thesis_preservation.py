"""Verify LIMS additions do not contaminate thesis code paths."""

from pathlib import Path

import pytest


def _find_lims_import_violations(scan_root: Path) -> list[str]:
    """Return lines containing forbidden LIMS imports under a path."""
    violations: list[str] = []

    if not scan_root.exists():
        return violations

    for py_file in scan_root.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for line_number, line in enumerate(content.splitlines(), start=1):
            if "from main.src.lims" in line or "import main.src.lims" in line:
                violations.append(f"{py_file}:{line_number}: {line.strip()}")

    return violations


class TestNoLIMSImportsInThesis:
    """Ensure additive-only migration boundaries are preserved."""

    def test_no_lims_imports_in_core(self) -> None:
        core_dir = Path("main/src/core")
        if not core_dir.exists():
            pytest.skip("main/src/core/ not found")

        violations = _find_lims_import_violations(core_dir)
        assert violations == [], (
            "LIMS imports found in thesis core code:\n"
            + "\n".join(violations)
        )

    def test_no_lims_imports_in_agents(self) -> None:
        agents_dir = Path("main/src/agents")
        if not agents_dir.exists():
            pytest.skip("main/src/agents/ not found")

        violations = _find_lims_import_violations(agents_dir)
        assert violations == [], (
            "LIMS imports found in thesis agents code:\n"
            + "\n".join(violations)
        )

    def test_thesis_docker_compose_untouched(self) -> None:
        compose_path = Path("docker-compose.dev.yml")
        if not compose_path.exists():
            pytest.skip("docker-compose.dev.yml not found")

        content = compose_path.read_text(encoding="utf-8")
        assert "docker-compose.lims.yml" not in content
        assert "chroma_db_lims" not in content
