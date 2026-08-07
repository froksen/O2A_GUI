import aula.utils as utils_module
import ui.opdater_view as opdater_view_module
import ui.widgets as widgets_module


def _break_git(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise RuntimeError("no git")

    monkeypatch.setattr("git.Repo", _raise)


def test_get_program_version_reads_version_txt_without_git(monkeypatch, tmp_path):
    (tmp_path / "version.txt").write_text("07-02-2026 13:14:15", encoding="utf-8")
    monkeypatch.setattr(
        utils_module, "__file__", str(tmp_path / "aula" / "utils.py")
    )
    _break_git(monkeypatch)

    assert utils_module.get_program_version() == "07-02-2026 13:14:15"


def test_get_program_version_falls_back_to_none_without_git_or_version_file(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        utils_module, "__file__", str(tmp_path / "aula" / "utils.py")
    )
    _break_git(monkeypatch)

    assert utils_module.get_program_version() is None


def test_opdater_view_falls_back_to_ukendt_when_helper_returns_none(monkeypatch):
    monkeypatch.setattr(utils_module, "get_program_version", lambda: None)

    assert opdater_view_module.OpdaterView._get_program_version() == "Ukendt"


def test_version_label_uses_shared_helper(monkeypatch):
    monkeypatch.setattr(utils_module, "get_program_version", lambda: "01-01-2026 00:00")

    assert widgets_module.VersionLabel._get_version() == "01-01-2026 00:00"
