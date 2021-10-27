import socket

# создаём сокет, AF_INET - ipv4, SOCK_STREM - хотим tcp
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# устанавливаем соединение
s.connect(("127.0.0.1", 8080))
# посылаем данные
sent = s.send("message".encode("utf-8"))
# и говорим, что ничего больше не будем посылать
s.shutdown(socket.SHUT_WR)
# принимаем данные
data = s.recv(1024)
print(f"Recieved: {data}")
# и закрываем socket
s.close()
