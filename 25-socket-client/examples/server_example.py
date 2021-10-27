import socket

# создаём сокет, AF_INET - ipv4, SOCK_STREM - хотим tcp
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# говорим, что хотим слушать на локальном адресе на порту 8080
s.bind(("127.0.0.1", 8080))
# начинаем слушать на порту и разрешаем до 5 соединений от клиентов в очереди
s.listen(5)

while True:
    # принимаем соединение от очередного клиента
    clientsocket, address = s.accept()
    print(f"New connection from {address}")
    # и пока без многопоточности принимаем данные и возвращаем обратно
    while True:
        chunk = clientsocket.recv(2048)
        # если получили ничего, значит нам больше ничего не пришлют
        if len(chunk) == 0:
            break
        # и посылаем всё, что получили
        clientsocket.sendall(chunk)
    # Не забываем закрыть соединение!
    clientsocket.shutdown(socket.SHUT_RDWR)
    clientsocket.close()

