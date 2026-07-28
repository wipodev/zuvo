import sys
from pathlib import Path
from unittest.mock import patch
from zuvo.utils.paths import get_root_dir, get_locales_dir


class TestGetRootDir:
    """Test suite for resolving the application root directory."""

    def test_development_mode(self, tmp_path, monkeypatch):
        """
        Verify that development mode resolves the root directory based on
        the current working directory (CWD) of the active workspace.
        """
        # Change execution CWD to a controlled temporary directory
        monkeypatch.chdir(tmp_path)

        with patch.object(sys, "frozen", False, create=True):
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            root_dir = get_root_dir()

            assert isinstance(root_dir, Path)
            assert root_dir == tmp_path

    def test_pyinstaller_onefile_mode(self, tmp_path):
        """Verify that PyInstaller executable mode (onefile) uses sys._MEIPASS."""
        mock_meipass = str(tmp_path / "meipass_temp")

        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "_MEIPASS", mock_meipass, create=True):
            
            root_dir = get_root_dir()

            assert isinstance(root_dir, Path)
            assert root_dir == Path(mock_meipass)

    def test_pyinstaller_onedir_mode(self, tmp_path):
        """Verify that Onedir executable mode (without _MEIPASS) uses the executable's directory."""
        mock_exe = str(tmp_path / "dist" / "my_app.exe")

        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "executable", mock_exe):
            
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            root_dir = get_root_dir()

            assert isinstance(root_dir, Path)
            assert root_dir == Path(mock_exe).resolve().parent


class TestGetLocalesDir:
    """Test suite for resolving the locales directory."""

    def test_get_locales_dir_structure(self):
        """Verify that get_locales_dir returns the path concatenated with 'locales'."""
        locales_dir = get_locales_dir()
        
        assert isinstance(locales_dir, Path)
        assert locales_dir.name == "locales"
        assert locales_dir.parent == get_root_dir()