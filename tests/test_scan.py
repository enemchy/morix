from unittest.mock import patch, mock_open
from morix.scan import (
    get_ignore_patterns_paths,
    read_ignore_file,
    should_ignore,
    is_text_file,
    get_text_files,
    scan,
    get_project_structure,
)


@patch("morix.scan.os.path.exists", return_value=True)
def test_get_ignore_patterns_paths(mock_exists):
    scan_folder = "/test"
    result = get_ignore_patterns_paths(scan_folder)
    assert len(result) > 0


@patch("builtins.open", new_callable=mock_open, read_data="*.pyc\n*.log")
@patch("morix.scan.os.path.exists", return_value=True)
def test_read_ignore_file(mock_exists, mock_open):
    paths = ["/test/.gitignore"]
    patterns = read_ignore_file(paths)
    assert "*.pyc" in patterns
    assert "*.log" in patterns


def test_should_ignore():
    patterns = ["*.py", "*.md"]
    assert should_ignore("test.py", patterns) is True
    assert should_ignore("document.txt", patterns) is False


@patch("builtins.open", new_callable=mock_open, read_data="print('test')")
def test_is_text_file(mock_open):
    filepath = "/test/test.py"
    assert is_text_file(filepath) is True


@patch("os.walk", return_value=[('/test', ('subdir',), ('file1.txt', 'file2.py'))])
@patch("morix.scan.is_text_file", return_value=True)
def test_get_text_files(mock_is_text_file, mock_os_walk):
    root = "/test"
    patterns = []
    result = get_text_files(root, patterns)
    assert len(result) == 2


@patch("morix.scan.get_text_files", return_value=["file1.txt"])
@patch("morix.scan.read_file_content", return_value="Content")
def test_scan(mock_read_file_content, mock_get_text_files):
    scan_folder = "/test"
    result = scan(scan_folder)
    assert "file1.txt" in result


@patch("morix.scan.os.walk", return_value=[('/test', ('dir',), ('file.py',))])
def test_get_project_structure(mock_os_walk):
    scan_folder = "/test"
    result = get_project_structure(scan_folder)
    assert "file.py" in result

