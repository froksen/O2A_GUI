import shutil
from pathlib import Path
from types import SimpleNamespace


class DummyButton:
    def __init__(self, signal_factory):
        self.clicked = signal_factory()


class LabelSpy:
    def __init__(self):
        self.text = None
        self.hidden = False

    def setText(self, value):
        self.text = value

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False


def build_setup_target(main_module):
    signal_factory = main_module.Signal
    return SimpleNamespace(
        runO2A=DummyButton(signal_factory),
        forcerunO2A=DummyButton(signal_factory),
        settings_button_aula=DummyButton(signal_factory),
        customize_ignore_people_button=DummyButton(signal_factory),
        customize_alias_button=DummyButton(signal_factory),
        start_window_minimized=DummyButton(signal_factory),
        run_program_at_startup=DummyButton(signal_factory),
        on_runO2A_clicked=lambda: None,
        on_forcerunO2A_clicked=lambda: None,
        runUniSetup=lambda: None,
        on_actionIgnore_people_list_triggered=lambda: None,
        on_actionOutlook_Aulanavne_liste_triggered=lambda: None,
        update_hide_on_startup_clicked=lambda *_args, **_kwargs: None,
        on_run_program_at_startup_clicked=lambda *_args, **_kwargs: None,
        program_version_label=LabelSpy(),
    )


def test_version_helper_reads_version_txt_without_git(
    main_module, monkeypatch, tmp_path
):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    shutil.copy2(Path(main_module.__file__), runtime_dir / "main.pyw")
    (runtime_dir / "version.txt").write_text("07-02-2026 13:14:15", encoding="utf-8")

    monkeypatch.setattr(
        main_module.git,
        "Repo",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("no git")),
    )

    assert main_module.get_program_version_text(runtime_dir) == "07-02-2026 13:14:15"


def test_version_helper_returns_none_without_git_or_version_file(
    main_module, monkeypatch, tmp_path
):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    shutil.copy2(Path(main_module.__file__), runtime_dir / "main.pyw")

    monkeypatch.setattr(
        main_module.git,
        "Repo",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("no git")),
    )

    assert main_module.get_program_version_text(runtime_dir) is None


def test_setup_gui_shows_fallback_version_text(main_module, monkeypatch):
    target = build_setup_target(main_module)
    monkeypatch.setattr(
        main_module,
        "get_program_version_text",
        lambda *_args, **_kwargs: "18-03-2026 00:00:00",
    )

    main_module.MainWindow.setup_gui(target)

    assert target.program_version_label.text == "18-03-2026 00:00:00"
    assert target.program_version_label.hidden is False


def test_setup_gui_hides_version_label_without_metadata(main_module, monkeypatch):
    target = build_setup_target(main_module)
    monkeypatch.setattr(
        main_module, "get_program_version_text", lambda *_args, **_kwargs: None
    )

    main_module.MainWindow.setup_gui(target)

    assert target.program_version_label.text is None
    assert target.program_version_label.hidden is True
