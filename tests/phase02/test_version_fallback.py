import ui.opdater_view as opdater_view_module


def _break_git(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise RuntimeError("no git")

    monkeypatch.setattr("git.Repo", _raise)


def test_get_program_version_reads_version_txt_without_git(monkeypatch, tmp_path):
    (tmp_path / "version.txt").write_text("07-02-2026 13:14:15", encoding="utf-8")
    monkeypatch.setattr(
        opdater_view_module, "__file__", str(tmp_path / "ui" / "opdater_view.py")
    )
    _break_git(monkeypatch)

    assert (
        opdater_view_module.OpdaterView._get_program_version() == "07-02-2026 13:14:15"
    )


def test_get_program_version_falls_back_to_ukendt_without_git_or_version_file(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        opdater_view_module, "__file__", str(tmp_path / "ui" / "opdater_view.py")
    )
    _break_git(monkeypatch)

    assert opdater_view_module.OpdaterView._get_program_version() == "Ukendt"
