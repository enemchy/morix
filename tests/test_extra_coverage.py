import time
import yaml
from unittest.mock import patch, MagicMock

from morix.helpers import DotSpinner, reset_terminal, get_string_size_kb, tokens_from_message
from morix.complection import chat_completion_request
from morix.keys import bindings

mock_llm = MagicMock()
mock_llm.name = "dummy_model"
mock_llm.base_url = "http://dummy.url"
mock_llm.token = "dummy_token"


def test_chat_completion_request():
    # Создаем фиктивную реализацию ChatOpenAI
    class DummyChat:
        def __init__(self, *args, **kwargs):
            pass
        def bind_tools(self, functions):
            return self
        def invoke(self, messages):
            class DummyResponse:
                response_metadata = {'finish_reason': 'stop', 'token_usage': {'total_tokens': 100}}
                content = '{"thoughts": "dummy", "response": "test", "tool_args": {}}'
            return DummyResponse()

    with patch('morix.complection.ChatOpenAI', new=DummyChat), \
            patch('morix.config.llm', new=mock_llm):

        messages = [{"role": "system", "content": "dummy"}]
        response = chat_completion_request(messages)

        assert response.response_metadata['finish_reason'] == 'stop'
        assert '"response": "test"' in response.content



def test_dotspinner_and_reset_terminal():
    spinner = DotSpinner()
    spinner.start()
    time.sleep(0.5)
    spinner.stop()
    with patch('subprocess.run') as mock_run:
        reset_terminal()
        mock_run.assert_called_once_with(['stty', 'sane'])


def test_keys_bindings_not_empty():
    # Проверяем, что в bindings зарегистрированы клавиши
    b = bindings.get_bindings()
    assert len(b) > 0


def test_get_string_size_kb_valid():
    size = get_string_size_kb("Hello")
    assert size > 0


def test_tokens_from_message():
    # Создаем фиктивное кодирование: для любой строки возвращаем ее длину как список символов
    dummy_encoding = MagicMock()
    dummy_encoding.encode.side_effect = lambda x, **kwargs: list(x)
    with patch('morix.helpers.tiktoken.encoding_for_model', side_effect=KeyError), \
            patch('morix.helpers.tiktoken.get_encoding', return_value=dummy_encoding),\
            patch('morix.config.llm', new=mock_llm):
        tokens = tokens_from_message({"role": "user", "content": "test"})
        # Ожидаем, что количество токенов больше 0
        assert tokens > 0


def test_load_yaml_file(tmp_path):
    from morix.settings import load_yaml_file
    test_file = tmp_path / "test.yml"
    test_data = {"key": "value"}
    test_file.write_text(yaml.dump(test_data))
    loaded = load_yaml_file(test_file)
    assert loaded == test_data
