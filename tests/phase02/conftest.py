import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def mainwindow_module():
    """Det virkelige mainwindow.py — ingen stub nødvendig. Alle
    afhængigheder (pywin32, winshell, keyring) er reelle, installerede
    pakker i dette udviklingsmiljø (se Requirements.txt), så modulet kan
    importeres direkte i stedet for at blive stubbet ud, sådan som denne
    fixture gjorde tilbage da UI'et var Qt-baseret."""
    import mainwindow
    return mainwindow
