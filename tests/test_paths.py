import sys
from pathlib import Path
from zuvo.utils.paths import get_root_dir, to_pkg_path


class TestGetRootDir:
    """Test suite for resolving the application root directory."""


    def test_override_path_with_path_object(self, tmp_path):
        """Verify that passing a Path object as override_path returns its resolved Path."""
        custom_dir = tmp_path / "custom_folder"
        custom_dir.mkdir()

        root_dir = get_root_dir(override_path=custom_dir)

        assert isinstance(root_dir, Path)
        assert root_dir == custom_dir.resolve()

    def test_override_path_with_string(self, tmp_path):
        """Verify that passing a string path as override_path returns a resolved Path object."""
        custom_dir = tmp_path / "custom_folder"
        custom_dir.mkdir()

        root_dir = get_root_dir(override_path=str(custom_dir))

        assert isinstance(root_dir, Path)
        assert root_dir == custom_dir.resolve()


    def test_development_mode(self, tmp_path, monkeypatch):
        """
        Verify that development mode resolves the root directory based on
        the current working directory (CWD) of the active workspace.
        """
        monkeypatch.chdir(tmp_path)
        monkeypatch.delattr(sys, "frozen", raising=False)
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)

        root_dir = get_root_dir()

        assert isinstance(root_dir, Path)
        assert root_dir == tmp_path.resolve()

    def test_pyinstaller_onefile_mode(self, tmp_path, monkeypatch):
        """Verify that PyInstaller executable mode (onefile) uses sys._MEIPASS."""
        mock_meipass = tmp_path / "meipass_temp"

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(mock_meipass), raising=False)

        root_dir = get_root_dir()

        assert isinstance(root_dir, Path)
        assert root_dir == mock_meipass

    def test_pyinstaller_onedir_mode(self, tmp_path, monkeypatch):
        """Verify that Onedir executable mode (without _MEIPASS) uses the executable's directory."""
        mock_exe = tmp_path / "dist" / "my_app.exe"

        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)
        monkeypatch.setattr(sys, "executable", str(mock_exe), raising=False)

        root_dir = get_root_dir()

        assert isinstance(root_dir, Path)
        assert root_dir == mock_exe.resolve().parent

    def test_default_execution_returns_valid_existing_path(self):
        """
        Smoke test: Verify that executing get_root_dir() without arguments 
        in a real environment returns an existing absolute Path directory.
        """
        root_dir = get_root_dir()

        assert isinstance(root_dir, Path)
        assert root_dir.is_absolute()
        assert root_dir.exists()
        assert root_dir.is_dir()
        assert root_dir == Path.cwd().resolve()

    def test_to_pkg_path_conversion(self):
            """Verify converting filesystem paths to Python package paths."""
            assert to_pkg_path("src/app/commands") == "app.commands"
            assert to_pkg_path("src\\app\\commands") == "app.commands"