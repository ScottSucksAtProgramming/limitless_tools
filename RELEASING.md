# Releasing limitless_tools

This guide describes how to cut and publish a release. Ensure CI is green before tagging.

## Prerequisites
- Python 3.11+
- Clean working tree on `main`
- Maintainer access to TestPyPI/PyPI (and Homebrew tap if used)
- Tools installed in your venv:

```
pip install -r requirements-dev.txt
pip install build twine
```

## Versioning
- Follow SemVer.
- Update `pyproject.toml` `version` and `CHANGELOG.md`.
- Prefer Conventional Commits for history; summarize in CHANGELOG.

## Release Steps
1) Ensure quality gates pass locally:

```
ruff check .
mypy .
python -m pytest -q
```

2) Build artifacts (sdist + wheel) and verify:

```
python -m build
python -m twine check dist/*
```

3) Smoke test install in a clean venv:

```
python3 -m venv .venv-release
source .venv-release/bin/activate
pip install dist/*.whl
limitless --help
```

4) Tag and push:

```
git tag vX.Y.Z
git push origin vX.Y.Z
```

5) TestPyPI (first‑time or RCs):

```
python -m twine upload --repository testpypi dist/*
```

6) PyPI (when ready):

```
python -m twine upload dist/*
```

7) Post‑publish
- Update GitHub release notes; link to CHANGELOG entries
- Verify `pipx install limitless-tools` works on a clean machine
- (Optional) Homebrew: evaluate providing a formula using a Python venv with vendored deps

## CI
- CI should run ruff/mypy/pytest on PRs and main. See `.github/workflows/ci.yml` (added separately).

## Notes
- Do not publish secrets. Ensure `.env` and local data are ignored by git.
- Consider releasing to TestPyPI for validation before PyPI.

