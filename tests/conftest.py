"""The automated suite must remain offline, including the preserved baseline tests."""
import socket
import pytest

@pytest.fixture(autouse=True)
def prohibit_network_connections(monkeypatch):
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def is_loopback(address):
        if not isinstance(address, tuple) or not address:
            return False
        host = address[0]
        return host in {"127.0.0.1", "::1", "localhost"}

    def guarded_connect(sock, address, *args, **kwargs):
        if is_loopback(address):
            return original_connect(sock, address, *args, **kwargs)
        raise AssertionError('Automated tests must use an offline transport or injected provider; outbound sockets are disabled.')

    def guarded_connect_ex(sock, address, *args, **kwargs):
        if is_loopback(address):
            return original_connect_ex(sock, address, *args, **kwargs)
        raise AssertionError('Automated tests must use an offline transport or injected provider; outbound sockets are disabled.')

    monkeypatch.setattr(socket.socket,'connect',guarded_connect)
    monkeypatch.setattr(socket.socket,'connect_ex',guarded_connect_ex)
