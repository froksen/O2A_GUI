from pathlib import Path

import git

from ui.opdater_view import OpdaterView

# Denne test-suite testede tidligere main.pyw's get_program_version_text()
# og MainWindow.setup_gui()'s program_version_label — begge Qt-koncepter,
# der ikke findes længere. Versionsvisningen sidder i dag i
# OpdaterView._get_program_version() (ui/opdater_view.py): git-commit-dato,
# med fallback til version.txt, med fallback til teksten "Ukendt" (aldrig
# None, så der er ikke længere noget label at skjule/vise betinget af).


def test_program_version_falls_back_to_version_txt_without_git(monkeypatch):
    monkeypatch.setattr(
        git, "Repo", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("no git")))

    expected = Path("version.txt").read_text(encoding="utf-8").strip() or "Ukendt"

    assert OpdaterView._get_program_version() == expected


def test_program_version_falls_back_to_ukendt_without_git_or_version_file(monkeypatch):
    monkeypatch.setattr(
        git, "Repo", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("no git")))

    real_is_file = Path.is_file

    def fake_is_file(self):
        if self.name == "version.txt":
            return False
        return real_is_file(self)

    monkeypatch.setattr(Path, "is_file", fake_is_file)

    assert OpdaterView._get_program_version() == "Ukendt"
