import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def isolate_cwd():
    orig = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="aniyt_test_") as tmp:
        os.chdir(tmp)
        os.makedirs("data", exist_ok=True)
        yield
    os.chdir(orig)
