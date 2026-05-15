"""Package import surface smoke test.

Asserts that `import floodwatch_ph` succeeds and exposes a __version__ string.
This mirrors the CI model job's smoke test:
    python -c "import floodwatch_ph; print('floodwatch_ph', floodwatch_ph.__version__)"
"""

from __future__ import annotations


def test_package_importable():
    import floodwatch_ph  # noqa: F401


def test_version_present():
    import floodwatch_ph
    assert hasattr(floodwatch_ph, "__version__"), (
        "floodwatch_ph must expose __version__"
    )


def test_version_is_string():
    import floodwatch_ph
    assert isinstance(floodwatch_ph.__version__, str), (
        f"__version__ must be a str, got {type(floodwatch_ph.__version__)}"
    )


def test_version_nonempty():
    import floodwatch_ph
    assert floodwatch_ph.__version__.strip(), "__version__ must not be empty"
