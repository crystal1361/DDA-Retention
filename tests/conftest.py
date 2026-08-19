"""
conftest.py

Shared pytest fixtures/helpers for this project's test suite.

WHY load_module() EXISTS:
Every analysis script in src/ is named like "01_generate_data.py" so a
human reading the repo can tell the pipeline's run order at a glance
(see README.md's Reproduce section). That's a good property for a
demo/interview project -- but it has one real cost: a filename starting
with a digit is not a legal Python identifier, so the normal
`import generate_data` statement has no equivalent for these files --
`import 01_generate_data` is a SyntaxError, full stop. This helper loads
a script BY FILE PATH instead of by import name (importlib.util's
spec-from-file-location machinery), which sidesteps the identifier
restriction entirely and is the standard way to unit-test scripts that
are deliberately number-prefixed for readability.
"""

import importlib.util
import os
import sys

import pytest

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, os.path.abspath(SRC_DIR))  # so `import config` etc. work from within loaded modules


def load_module(filename, module_name=None):
    """Load src/<filename> as an importable module object, e.g.
    `m = load_module("06_optimization.py"); m.run_optimization(...)`.

    module_name defaults to the filename with the extension stripped
    (still not underscore-prefixed cleanly, but unique and fine as a
    sys.modules key -- nothing else needs to `import` it by that name).
    """
    path = os.path.join(SRC_DIR, filename)
    if module_name is None:
        module_name = filename.replace(".py", "").replace("-", "_")
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def rng():
    """A fresh, deterministically-seeded Generator for tests that need
    their own small amount of randomness (e.g. building synthetic
    fixtures) -- independent of the pipeline's own SEED so a change to
    config.SEED can never silently change what a test's fixture data
    looks like."""
    import numpy as np
    return np.random.default_rng(12345)
