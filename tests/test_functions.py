import pytest
import os
import json
import subprocess
from unittest.mock import MagicMock, patch
from morix.run_functions import process_tool_calls
from morix.settings import config




@pytest.fixture
def dummy_project_path(tmp_path):
    # Создаем временную папку для тестов.
    return str(tmp_path)

def test_crud_files_create(dummy_project_path):
    arguments = {
        "files": [
            {"filename": "test.txt", "content": "Hello, World!", "operation": "create"}
        ]
    }

    # Устанавливаем правильное значение для function.name.
    tool_call = {
        'name': 'crud_files',
        'args': arguments,
        'id': 1
    }
    assistant_message = MagicMock(tool_calls=[tool_call])
    messages = []

    process_tool_calls(messages, assistant_message, dummy_project_path)

    filepath = os.path.join(dummy_project_path, "test.txt")

    assert os.path.isfile(filepath)
    with open(filepath, "r", encoding="utf-8") as file:
        assert file.read() == "Hello, World!"

    assert any("test.txt: created" in msg['content'] for msg in messages)

def test_crud_files_delete(dummy_project_path):
    filepath = os.path.join(dummy_project_path, "test.txt")

    with open(filepath, "w", encoding="utf-8") as file:
        file.write("Delete me")

    arguments = {
        "files": [
            {"filename": "test.txt", "operation": "delete"}
        ]
    }

    # Устанавливаем правильное значение для function.name.
    tool_call = {
        'name': 'crud_files',
        'args': arguments,
        'id': 1
    }
    assistant_message = MagicMock(tool_calls=[tool_call])
    messages = []

    process_tool_calls(messages, assistant_message, dummy_project_path)

    assert not os.path.isfile(filepath)
    assert any("test.txt: deleted" in msg['content'] for msg in messages)

def test_crud_files_read_missing_file(dummy_project_path):
    arguments = {
        "files": [
            {"filename": "missing.txt", "operation": "read"}
        ]
    }

    # Устанавливаем правильное значение для function.name.
    tool_call = {
        'name': 'crud_files',
        'args': arguments,
        'id': 1
    }
    assistant_message = MagicMock(tool_calls=[tool_call])
    messages = []

    process_tool_calls(messages, assistant_message, dummy_project_path)

    assert any("missing.txt: " in msg['content'] for msg in messages)  # Ожидается пустое содержимое в результате.

def test_crud_files_invoke_read_function(dummy_project_path):
    filepath = os.path.join(dummy_project_path, "read.txt")

    with open(filepath, "w", encoding="utf-8") as file:
        file.write("File content")

    arguments = {
        "files": [
            {"filename": "read.txt", "operation": "read"}
        ]
    }

    # Устанавливаем правильное значение для function.name.
    tool_call = {
        'name': 'crud_files',
        'args': arguments,
        'id': 1
    }
    assistant_message = MagicMock(tool_calls=[tool_call])
    messages = []

    process_tool_calls(messages, assistant_message, dummy_project_path)

    # Проверяем, действительно ли было прочтено содержимое файла.
    assert any("File content" in m['content'] for m in messages)


def test_process_tool_calls_with_command(dummy_project_path):
    config.console_commands.allow_run = True
    messages = []
    tool_call = {
        'name': 'run_console_command',
        'args': {'command': 'echo test', 'timeout': 5},
        'id': 1
    }

    assistant_message = MagicMock(tool_calls=[tool_call])

    with patch('subprocess.Popen') as mock_popen:
        process_mock = MagicMock()
        process_mock.configure_mock(
            stdout=iter(['test\n']),
            wait=MagicMock(return_value=None),
            returncode=0
        )

        # Correctly handle the context manager
        mock_popen.return_value.__enter__.return_value = process_mock

        process_tool_calls(messages, assistant_message, dummy_project_path)

    actual_content = ''.join(msg['content'] for msg in messages)
    assert "test" in actual_content

def test_process_tool_calls_with_task_status(dummy_project_path):
    messages = []
    tool_call = {
        'name': 'task_status',
        'args': {'status': 'Completed'},
        'id': 1
    }

    assistant_message = MagicMock(tool_calls=[tool_call])

    process_tool_calls(messages, assistant_message, dummy_project_path)

    # Правильное утверждение, чтобы проверить наличие 'Completed' вместо 'ok', поскольку 'ok' в результате отсутствует.
    assert any("Completed" == m['content'] for m in messages)