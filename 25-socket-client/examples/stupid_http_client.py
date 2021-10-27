import socket

def send_http_request(s, method, url):
    request = f"{method.upper()} {url} HTTP/1.1\n\r\n"
    s.sendall(request.encode("utf-8"))
    s.shutdown(socket.SHUT_WR)

def read_responce(s):
    buf = []
    while True:
        chunk = s.recv(1024)
        if not chunk:
            break
        buf.append(chunk)
    return b''.join(buf)
