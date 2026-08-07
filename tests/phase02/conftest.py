import importlib.util
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAIN_MODULE_PATH = PROJECT_ROOT / "main.pyw"


@pytest.fixture(scope="session")
def main_module():
    """Loads the real main.pyw as a module.

    main.pyw only builds a window under `if __name__ == "__main__":`, so
    importing it here is side-effect free — it just gives tests access to
    the real MainWindow class (via main.pyw's `from mainwindow import
    MainWindow`) plus main.pyw's own module-level constants
    (INTERNET_ERROR_TITLE, INTERNET_ERROR_MESSAGE, TkLogHandler).
    """
    spec = importlib.util.spec_from_file_location("phase02_main", MAIN_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module
