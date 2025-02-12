import pytest
from unittest.mock import patch
import argparse
import logging
from morix.main import parse_args, handle_command, conversation, open_config_file

# Фикстура для автоматической подмены ввода во всех тестах
@pytest.fixture(autouse=True)
def stub_input(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda prompt='': '')


def test_parse_args_with_path():
    test_args = ["prog", "./data"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.path == "./data"


def test_parse_args_with_contents_flag():
    test_args = ["prog", "--contents", "./data"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.contents is True
        assert args.path == "./data"


def test_parse_args_with_structure_only_flag():
    test_args = ["prog", "--structure-only", "./data"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.structure_only is True
        assert args.path == "./data"


def test_parse_args_with_config_flag():
    test_args = ["prog", "--config"]
    with patch("sys.argv", test_args):
        args = parse_args()
        assert args.config is True


@patch("morix.main.open_config_file")
def test_handle_command_opens_config(mock_open_config_file):
    args = argparse.Namespace(config=True, path="", contents=False, structure_only=False, message=None, verbose=False, wait_enter=False, role="developer")
    handle_command(args)
    mock_open_config_file.assert_called_once()


@pytest.mark.parametrize("log_level", [logging.DEBUG, logging.INFO])
@patch("morix.main.conversation")
def test_handle_command_runs_conversation_without_scan(mock_conversation, log_level, caplog, tmp_path):
    caplog.set_level(log_level)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    args = argparse.Namespace(config=False, path=str(data_dir), contents=False, structure_only=False, message=None, verbose=False, wait_enter=True, role="developer", llm='openai')

    logger = logging.getLogger("morix.conversation")
    logger.setLevel(log_level)
    logger.addHandler(logging.StreamHandler())

    handle_command(args)
    mock_conversation.assert_called_once_with(str(data_dir), False, False, None)
    assert any("Starting work on the project at:" in message.message for message in caplog.records)


@patch("morix.main.conversation")
def test_handle_command_runs_conversation_with_content_scan(mock_conversation, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    args = argparse.Namespace(config=False, path=str(data_dir), contents=True, structure_only=False, message=None, verbose=False, role="developer", wait_enter=True, llm='openai')
    handle_command(args)
    mock_conversation.assert_called_once_with(str(data_dir), True, False, None)


@patch("morix.main.conversation")
def test_handle_command_runs_conversation_with_structure_scan(mock_conversation, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    args = argparse.Namespace(config=False, path=str(data_dir), contents=False, structure_only=True, message=None, verbose=False, role="developer", wait_enter=True, llm='openai')
    handle_command(args)
    mock_conversation.assert_called_once_with(str(data_dir), False, True, None)
