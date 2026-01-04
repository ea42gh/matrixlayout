import jinja2


def test_jinja_loader_fallback_when_packageloader_unavailable(monkeypatch):
    """If PackageLoader fails (common in interop / non-standard installs),
    matrixlayout should still be able to locate templates from disk.

    This test focuses on template discovery, not template rendering.
    Rendering requires a full context, which is validated elsewhere.
    """

    from matrixlayout import jinja_env

    class Boom:
        def __init__(self, *args, **kwargs):
            raise ValueError("simulated PackageLoader failure")

    # Force the fallback path inside matrixlayout.jinja_env._make_loader
    monkeypatch.setattr(jinja_env.jinja2, "PackageLoader", Boom)

    env = jinja_env.make_environment(jinja_env.JinjaConfig(template_dirs=None))

    # Verify the template can be located and its source loaded.
    source, _filename, _uptodate = env.loader.get_source(env, "eigproblem.tex.j2")
    assert "\\begin{tabular}" in source or "tabular" in source
