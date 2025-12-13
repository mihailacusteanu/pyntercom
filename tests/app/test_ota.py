"""Tests for OTA (Over-The-Air) update system."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.app.ota import OTAServer


def test_ota_server_initialization():
    """Test OTA server initializes with correct defaults."""
    server = OTAServer()

    assert server.port == 8266
    assert server.password == "pyntercom_ota_2024"
    assert server.running == False


def test_ota_server_custom_config():
    """Test OTA server accepts custom configuration."""
    server = OTAServer(port=9999, password="custom_pass")

    assert server.port == 9999
    assert server.password == "custom_pass"


def test_ota_server_stop():
    """Test OTA server stop sets running flag."""
    server = OTAServer()
    server.running = True

    server.stop()

    assert server.running == False


def test_write_file_prevents_path_traversal():
    """Test that _write_file prevents directory traversal attacks."""
    server = OTAServer()

    # Test path traversal attempts
    with pytest.raises(ValueError, match="Invalid file path"):
        server._write_file("../etc/passwd", b"malicious")

    with pytest.raises(ValueError, match="Invalid file path"):
        server._write_file("/etc/passwd", b"malicious")

    with pytest.raises(ValueError, match="Invalid file path"):
        server._write_file("foo/../../etc/passwd", b"malicious")


def test_write_file_creates_directories():
    """Test that _write_file creates necessary directories."""
    server = OTAServer()

    mock_open = MagicMock()
    makedirs_calls = []

    def mock_makedirs(path):
        makedirs_calls.append(path)

    server._makedirs = mock_makedirs

    with patch('builtins.open', mock_open):
        server._write_file("foo/bar/test.py", b"content")

    # Should create parent directories
    assert "foo" in makedirs_calls or "foo/bar" in makedirs_calls

    # Should write file
    mock_open.assert_called_once_with("foo/bar/test.py", 'wb')


def test_send_response():
    """Test HTTP response formatting."""
    server = OTAServer()
    mock_socket = Mock()

    server._send_response(mock_socket, 200, "OK", "Success")

    # Verify send was called
    mock_socket.send.assert_called_once()

    # Verify response format
    sent_data = mock_socket.send.call_args[0][0].decode('utf-8')
    assert "HTTP/1.1 200 OK" in sent_data
    assert "Content-Type: text/plain" in sent_data
    assert "Content-Length: 7" in sent_data  # len("Success") = 7
    assert "Success" in sent_data


def test_send_response_handles_errors():
    """Test that _send_response handles socket errors gracefully."""
    server = OTAServer()
    mock_socket = Mock()
    mock_socket.send.side_effect = Exception("Socket closed")

    # Should not raise exception
    server._send_response(mock_socket, 500, "Error", "Test error")


def test_makedirs_creates_nested_directories():
    """Test that _makedirs creates nested directory structure."""
    server = OTAServer()
    created_dirs = []

    with patch('src.app.ota.os') as mock_os:
        mock_os.mkdir = Mock(side_effect=lambda d: created_dirs.append(d))

        server._makedirs("foo/bar/baz")

        # Should create each level
        assert "foo" in created_dirs
        assert "foo/bar" in created_dirs
        assert "foo/bar/baz" in created_dirs


def test_makedirs_handles_existing_directories():
    """Test that _makedirs handles already-existing directories."""
    server = OTAServer()

    with patch('src.app.ota.os') as mock_os:
        mock_os.mkdir = Mock(side_effect=OSError("Directory exists"))

        # Should not raise exception
        server._makedirs("existing/dir")

        # mkdir should have been called
        assert mock_os.mkdir.called


def test_ota_server_authentication_required():
    """Test that OTA server requires authentication header."""
    server = OTAServer(password="test_pass")
    mock_socket = Mock()

    # Mock socket to return request without auth
    mock_socket.readline.side_effect = [
        b"POST /upload HTTP/1.1\r\n",
        b"Content-Length: 0\r\n",
        b"\r\n"
    ]

    server._handle_client(mock_socket)

    # Should send 401 Unauthorized
    sent_data = mock_socket.send.call_args[0][0].decode('utf-8')
    assert "401" in sent_data or "Unauthorized" in sent_data


def test_ota_server_requires_file_path_header():
    """Test that OTA server requires X-File-Path header."""
    server = OTAServer(password="test_pass")
    mock_socket = Mock()

    # Mock socket to return request with auth but no file path
    mock_socket.readline.side_effect = [
        b"POST /upload HTTP/1.1\r\n",
        b"Authorization: Bearer test_pass\r\n",
        b"Content-Length: 0\r\n",
        b"\r\n"
    ]

    server._handle_client(mock_socket)

    # Should send 400 Bad Request
    sent_data = mock_socket.send.call_args[0][0].decode('utf-8')
    assert "400" in sent_data or "Bad Request" in sent_data


def test_ota_server_rejects_non_post_requests():
    """Test that OTA server only accepts POST requests."""
    server = OTAServer()
    mock_socket = Mock()

    # Mock GET request
    mock_socket.readline.return_value = b"GET / HTTP/1.1\r\n"

    server._handle_client(mock_socket)

    # Should send 405 Method Not Allowed
    sent_data = mock_socket.send.call_args[0][0].decode('utf-8')
    assert "405" in sent_data or "Method Not Allowed" in sent_data
