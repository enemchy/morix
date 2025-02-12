import os
import pytest
import tiktoken
from unittest.mock import patch, mock_open, MagicMock
from morix.helpers import (
    get_string_size_kb, 
    save_response_to_file, 
    read_file_content, 
    tokens_from_messages
)


def test_get_string_size_kb():
    string = "12345"
    size_kb = get_string_size_kb(string)
    assert size_kb == pytest.approx(0.0048828125, rel=1e-9)


@patch('os.path.join', side_effect=lambda *args: "/".join(args))
@patch('os.listdir', return_value=[])
def test_save_response_to_file(mock_listdir, mock_join, tmpdir):
    temp_dir = tmpdir.mkdir("sub")
    file_path = str(temp_dir.join('response_1.md'))
    with patch('builtins.open', mock_open()) as mock_file:
        save_response_to_file('sample response', str(temp_dir))
        mock_file.assert_called_once_with(file_path, 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with('sample response')


@patch('builtins.open', new_callable=mock_open, read_data='file content')
def test_read_file_content(mock_open):
    result = read_file_content('/fakepath/file.txt')
    assert result == 'file content'

    mock_open.side_effect = IOError("File not found")
    result = read_file_content('/nonexistent/file.txt')
    assert result == ""


# @patch('morix.helpers.tiktoken.encoding_for_model')
# @patch('morix.helpers.tiktoken.get_encoding')
# def test_num_tousend_tokens_from_messages(mock_get_encoding, mock_encoding_for_model, caplog):
#     mock_encoding = MagicMock()
#     mock_encoding.encode.return_value = [1, 2, 3]
#     mock_encoding_for_model.side_effect = KeyError
#     mock_get_encoding.return_value = mock_encoding

#     messages = [{'content': 'Hello'}, {'role': 'user', 'content': 'world'}]
    
#     tokens_from_messages(messages)
#     assert "Model not found. Using cl100k_base encoding." in caplog.text
