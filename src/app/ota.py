"""
OTA (Over-The-Air) Update System for ESP8266

This module provides a simple HTTP server for receiving file uploads
via WiFi, enabling remote code updates without USB connection.

Usage:
    from src.app.ota import OTAServer

    # Start OTA server (blocking)
    server = OTAServer(port=8266, password="your_secret_password")
    server.start()

    # Or integrate with MQTT for remote trigger:
    # When MQTT receives "start_ota" message, call server.start()
"""

import socket
import time
import sys
import gc

try:
    import os
    import machine
except ImportError:
    # Mock for testing on non-ESP8266
    os = None
    machine = None


class OTAServer:
    """Simple HTTP server for OTA file uploads."""

    def __init__(self, port: int = 8266, password: str = "pyntercom_ota_2024"):
        """Initialize OTA server.

        Args:
            port: TCP port to listen on (default: 8266)
            password: Password required for uploads (default: pyntercom_ota_2024)
        """
        self.port = port
        self.password = password
        self.running = False

    def start(self, timeout_seconds: int = 300):
        """Start OTA server and listen for uploads.

        Args:
            timeout_seconds: Auto-shutdown after this many seconds of inactivity (default: 5 minutes)
        """
        self.running = True
        print(f"[{time.time()}] 🚀 Starting OTA server on port {self.port}...")
        print(f"[{time.time()}] ⏱️  Server will auto-shutdown after {timeout_seconds}s of inactivity")
        print(f"[{time.time()}] 🔐 Password required for uploads")

        addr = socket.getaddrinfo('0.0.0.0', self.port)[0][-1]
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(addr)
        server_socket.listen(1)
        server_socket.settimeout(5.0)  # 5 second timeout for accept()

        print(f"[{time.time()}] ✅ OTA server listening on 0.0.0.0:{self.port}")

        start_time = time.time()
        last_activity = time.time()

        try:
            while self.running:
                # Check timeout
                if time.time() - last_activity > timeout_seconds:
                    print(f"[{time.time()}] ⏱️  Timeout reached, shutting down OTA server")
                    break

                try:
                    client_socket, client_addr = server_socket.accept()
                    last_activity = time.time()
                    print(f"[{time.time()}] 📡 Connection from {client_addr}")

                    self._handle_client(client_socket)
                    client_socket.close()

                    # Collect garbage after each request
                    gc.collect()

                except OSError as e:
                    # Timeout on accept() - this is normal, just continue
                    if e.args[0] != 110:  # ETIMEDOUT
                        print(f"[{time.time()}] ⚠️  Socket error: {e}")
                    continue

        except KeyboardInterrupt:
            print(f"[{time.time()}] ⚠️  OTA server interrupted by user")
        except Exception as e:
            print(f"[{time.time()}] ❌ OTA server error: {e}")
        finally:
            server_socket.close()
            self.running = False
            print(f"[{time.time()}] 🛑 OTA server stopped")

    def stop(self):
        """Stop the OTA server."""
        self.running = False

    def _handle_client(self, client_socket):
        """Handle a single client connection."""
        try:
            client_socket.settimeout(10.0)  # 10 second timeout for recv

            # Read request line
            request_line = client_socket.readline().decode('utf-8').strip()
            print(f"[{time.time()}] 📨 Request: {request_line}")

            if not request_line.startswith('POST /upload'):
                self._send_response(client_socket, 405, "Method Not Allowed", "Only POST /upload is supported")
                return

            # Read headers
            headers = {}
            while True:
                line = client_socket.readline().decode('utf-8').strip()
                if not line:
                    break
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            # Check authentication
            auth_header = headers.get('authorization', '')
            if not auth_header.startswith('Bearer '):
                self._send_response(client_socket, 401, "Unauthorized", "Missing or invalid authorization")
                return

            provided_password = auth_header[7:]  # Remove "Bearer "
            if provided_password != self.password:
                self._send_response(client_socket, 403, "Forbidden", "Invalid password")
                return

            # Get file path and content length
            file_path = headers.get('x-file-path', '')
            content_length = int(headers.get('content-length', 0))

            if not file_path:
                self._send_response(client_socket, 400, "Bad Request", "Missing X-File-Path header")
                return

            if content_length == 0:
                self._send_response(client_socket, 400, "Bad Request", "Missing or zero Content-Length")
                return

            print(f"[{time.time()}] 📝 Uploading: {file_path} ({content_length} bytes)")

            # Read file content
            content = b''
            remaining = content_length
            while remaining > 0:
                chunk_size = min(remaining, 1024)
                chunk = client_socket.recv(chunk_size)
                if not chunk:
                    break
                content += chunk
                remaining -= len(chunk)

            if len(content) != content_length:
                self._send_response(client_socket, 400, "Bad Request",
                                   f"Content length mismatch: expected {content_length}, got {len(content)}")
                return

            # Write file
            self._write_file(file_path, content)

            self._send_response(client_socket, 200, "OK", f"File uploaded: {file_path}")
            print(f"[{time.time()}] ✅ Successfully uploaded: {file_path}")

        except Exception as e:
            print(f"[{time.time()}] ❌ Error handling client: {e}")
            try:
                self._send_response(client_socket, 500, "Internal Server Error", str(e))
            except:
                pass

    def _send_response(self, client_socket, status_code: int, status_text: str, body: str):
        """Send HTTP response."""
        try:
            response = f"HTTP/1.1 {status_code} {status_text}\r\n"
            response += "Content-Type: text/plain\r\n"
            response += f"Content-Length: {len(body)}\r\n"
            response += "Connection: close\r\n"
            response += "\r\n"
            response += body
            client_socket.send(response.encode('utf-8'))
        except Exception as e:
            print(f"[{time.time()}] ⚠️  Error sending response: {e}")

    def _write_file(self, file_path: str, content: bytes):
        """Write uploaded content to file, creating directories if needed."""
        # Security: prevent path traversal
        if '..' in file_path or file_path.startswith('/'):
            raise ValueError(f"Invalid file path: {file_path}")

        # Create directories if needed
        parts = file_path.split('/')
        if len(parts) > 1:
            dir_path = '/'.join(parts[:-1])
            self._makedirs(dir_path)

        # Write file
        with open(file_path, 'wb') as f:
            f.write(content)

    def _makedirs(self, path: str):
        """Create directory tree recursively."""
        if not path:
            return

        parts = path.split('/')
        current = ''
        for part in parts:
            if not part:
                continue
            current = f"{current}/{part}" if current else part
            try:
                if os:
                    os.mkdir(current)
            except OSError:
                # Directory already exists, continue
                pass


def start_ota_mode(port: int = 8266, password: str = None, timeout: int = 300):
    """Convenience function to start OTA server and optionally restart after.

    Args:
        port: TCP port to listen on
        password: Password for uploads (uses default if None)
        timeout: Auto-shutdown timeout in seconds
    """
    print(f"[{time.time()}] 🔄 Entering OTA update mode...")
    print(f"[{time.time()}] ⚠️  Intercom system paused during OTA")

    if password:
        server = OTAServer(port=port, password=password)
    else:
        server = OTAServer(port=port)

    server.start(timeout_seconds=timeout)

    print(f"[{time.time()}] 🔄 OTA session complete")
    print(f"[{time.time()}] ⚠️  Restarting ESP8266 in 3 seconds...")
    time.sleep(3)

    if machine:
        machine.reset()
    else:
        print("[{time.time()}] (Mock mode: would restart ESP8266 here)")


if __name__ == "__main__":
    # Test mode - run OTA server standalone
    print("Starting OTA server in test mode...")
    start_ota_mode()
