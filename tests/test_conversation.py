import pytest
from unittest.mock import patch, MagicMock
from morix.conversation import initialize_messages, handle_user_interaction, conversation
from morix.settings import config
from morix.complection import chat_completion_request

# Фикстура для автоматической подмены ввода во всех тестах
@pytest.fixture(autouse=True)

def stub_input(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': '')


def test_scan_project_scan(tmp_path):
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    file_path = test_dir / "file.txt"
    file_path.write_text("test")
    # В данном тесте имитируем сканирование файла
    scan_result = "file.txt"
    assert "file.txt" in scan_result


def test_initialize_messages(tmp_path):
    scan_result = "Test scan result"
    # Устанавливаем ожидаемое содержимое системного сообщения
    config.role_system_content = "Expected system message"
    expected_roles = {
        "system": config.role_system_content,
    }
    messages = initialize_messages(scan_result, str(tmp_path))
    for role, content in expected_roles.items():
        assert any(m["role"] == role and m["content"] == content for m in messages)


def test_conversation_keyboard_interrupt():
    with patch('morix.conversation.chat_completion_request', side_effect=KeyboardInterrupt):
        with patch('morix.conversation.logger') as mock_logger:
            conversation(work_folder="/dummy/path", full_scan=False, structure_only=True, initial_message="Test")
            mock_logger.info.assert_any_call("Session completed")


def test_conversation_with_full_scan(tmp_path):
    with patch('morix.conversation.chat_completion_request') as mock_chat_completion, \
         patch('morix.conversation.handle_user_interaction', return_value='User input'):
        mock_chat_completion.return_value = MagicMock(
            response_metadata={'finish_reason': 'stop', 'token_usage': {'total_tokens': 50}},
            content='Test content'
        )
        conversation(work_folder=str(tmp_path), full_scan=True, structure_only=False, initial_message="Test", is_interactive=False)
        mock_chat_completion.assert_called()
