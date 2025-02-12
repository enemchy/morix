import pytest
from unittest.mock import patch
from pathlib import Path
from morix.settings import load_config


def test_load_config_missing_file():
    # Патчим get_config_folder, чтобы вернуть несуществующую директорию
    with patch('morix.settings.get_config_folder', return_value=Path('nonexistent_path')):
        with pytest.raises(FileNotFoundError):
            load_config()
