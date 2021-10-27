import pytest
import socket
from unittest.mock import patch, Mock


from stupid_http_client import send_http_request, read_responce

def test_send_http_request_using_mocks():
    s = Mock()

    send_http_request(s, 'get', '/')

    s.sendall.assert_called_once_with(b"GET / HTTP/1.1\n\r\n")
    s.shutdown.assert_called_once_with(socket.SHUT_WR)


def test_send_http_request_using_socket_pair():
    s1, s2 = socket.socketpair()

    send_http_request(s1, 'get', '/')

    # В реальности это возможно придётся вынести в отдельный поток чтобы более честно эмулировать сервер
    data = s2.recv(1024) # и не забывать, что recv может прочитать не всё
    assert data == b"GET / HTTP/1.1\n\r\n"

    # cleanup
    s1.close()
    s2.close()


# Testing using real server
@pytest.fixture
def server_address():
    # в реальном коде эти импорты должны быть сверху, в примере они здесь для лаконичности
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import threading
    address = ("127.0.0.1", 8081)
    httpd = HTTPServer(address, SimpleHTTPRequestHandler)
    thread = threading.Thread(target=httpd.serve_forever)
    try:
        thread.start()
        
        # здесь хорошо бы подождать пока сервер действительно запустится ;)

        yield address # отдаём управление коду теста

    finally:
        # прибираемся после теста
        httpd.shutdown()
        thread.join()

def test_send_http_request_using_real_server(server_address):
    s = socket.create_connection(server_address, timeout=5)
    send_http_request(s, 'get', '/')

    data = read_responce(s)
    assert b'200 OK' in data
