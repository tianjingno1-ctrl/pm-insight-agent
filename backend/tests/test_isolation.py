from pathlib import Path

FORBIDDEN_SNIPPETS = (
    "import roundtable",
    "from roundtable",
    "from app import ",
    "import app.py",
    "from app.py",
)


def test_backend_app_has_no_legacy_imports() -> None:
    app_dir = Path(__file__).resolve().parent.parent / "app"
    py_files = list(app_dir.rglob("*.py"))
    assert py_files, "expected backend/app/**/*.py"

    violations: list[str] = []
    for path in py_files:
        text = path.read_text(encoding="utf-8")
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in text:
                violations.append(f"{path.relative_to(app_dir.parent)}: contains {snippet!r}")

    assert not violations, "legacy imports found:\n" + "\n".join(violations)
