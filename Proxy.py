import threading
import socket
import sys
from urllib.parse import urlparse
import select

if len(sys.argv) < 2:
    print('bad arguments')
    sys.exit()
listen_port = int(sys.argv[1])


def isInt(x):
    try:
        int(x)
        return True
    except ValueError:
        return False


def getHost(headers):
    host = None
    port = None
    for i in range(0, len(headers)):
        header = headers[i].decode('ascii').split()
        header = list(filter(None, header))
        if header[0].lower() == 'host:':
            url = header[1]
            response = urlparse(url)
            host = response.path
            hostportsplit = host.split(':')
            if len(hostportsplit) == 2:
                if isInt(hostportsplit[1]):
                    port = int(hostportsplit[1])
                    host = hostportsplit[0]
                else:
                    port = int(hostportsplit[0])
                    host = hostportsplit[1]

            return host, port
    return host, port


def getContentLength(headers):
    length = 0
    for i in range(0, len(headers)):
        header = headers[i].decode('ascii').split()
        header = list(filter(None, header))
        if header[0].lower() == 'content-length:':
            return int(header[1])
    return length


def filterHeaders(headers):
    new_headers = []
    for header in headers:
        header_string = list(filter(None, header.decode('ascii')))
        if header_string[0].lower() != 'connection:':
            if header_string[0].lower() == 'proxy-connection:':
                header = bytearray('Proxy-connection: close', 'ascii')
            new_headers.append(header)
    new_headers.append(bytearray('Connection: close', 'ascii'))
    return new_headers


def processData(socket, shouldFilter = True):
    data = socket.recv(4000)
    # get all headers
    data_headers = data
    while bytearray("\r\n\r\n", 'ascii') not in data_headers:
        data += socket.recv(4000)
        data_headers = data
    header_end = data.find(bytearray("\r\n\r\n", 'ascii'))
    data_headers = data_headers[:header_end].split(bytearray('\r\n', 'ascii'))
    if shouldFilter:
        data_headers = filterHeaders(data_headers)
    return data, data_headers, data[header_end:]


class myThread(threading.Thread):
    def __init__(self, socket):
        threading.Thread.__init__(self)
        self.socket = socket

    def run(self):
        data, data_headers, body = processData(self.socket, False)

        # first line
        data_first_line = data_headers[0]
        first_line_tokens = data_first_line.split()
        first_line_tokens = list(filter(None, first_line_tokens))

        # get server port and host
        server_host, server_port = getHost(data_headers)
        if server_port is None:
            server_port = urlparse(first_line_tokens[1]).port
        if server_port is None:
            server_port = 80
        print(">>> ", data_first_line.decode('ascii'))
        # handle connect
        if first_line_tokens[0].decode('ascii').upper() == 'CONNECT':
            if server_port is None:
                server_port = 443

            connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                connect_socket.connect((server_host, server_port))
                message = bytearray('HTTP/1.1 200 OK\r\n\r\n', 'ascii')
                self.socket.send(message)
                while True:
                    ready_read, ready_write, in_err = select.select(
                        [self.socket, connect_socket],
                        [],
                        [],
                        10000.0
                    )
                    for sock in ready_read:
                        data = sock.recv(4000)
                        if len(data) == 0:
                            connect_socket.close()
                            self.socket.close()
                            return
                        if sock == self.socket:
                            connect_socket.send(data)
                        else:
                            self.socket.send(data)
            except:
                message = bytearray('HTTP/1.1 502 Bad Gateway\r\n', 'ascii')
                self.socket.send(message)
                self.socket.close()
        else:
            data_headers = filterHeaders(data_headers)
            # print first line, establish tcp connection
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if server_port is None:
                server_port = 80
            server_socket.connect((server_host, server_port))
            # get content length
            content_length = getContentLength(data_headers)

            # send data to server
            tot_recv = len(body)
            server_socket.send(bytearray("\r\n", 'ascii').join(data_headers))
            server_socket.send(body)

            while content_length > tot_recv:
                data = self.socket.recv(4000)
                if len(data) == 0:
                    break
                server_socket.send(data)
                tot_recv += len(data)

            # Response from server
            data, data_headers, body = processData(server_socket)
            content_length = getContentLength(data_headers)
            tot_recv = len(body)
            self.socket.send(bytearray("\r\n", 'ascii').join(data_headers))
            self.socket.send(body)
            while content_length > tot_recv:
                data = server_socket.recv(4000)
                if len(data) == 0:
                    break
                self.socket.send(data)
                tot_recv += len(data)
            server_socket.close()
            self.socket.close()


if __name__ == "__main__":
    listen_host = 'localhost'
    # create socket
    serversocket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((listen_host, listen_port))
    serversocket.listen(5)
    print('Proxy listening on ' + listen_host + ':' + str(listen_port))
    # connect to client
    while True:
        (clientsocket, address) = serversocket.accept()
        thread = myThread(clientsocket)
        thread.start()
