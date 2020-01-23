import socketserver
import struct
import random
import threading

state = {}


class MyUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        try:
            data = struct.unpack('!IIHH11sx', data)
            if data[0] != len(data[4]) + 1 or data[1] != 0 or data[2] != 1 or data[4].decode('ascii') != 'hello world':
                socket.close()
                return
            num = random.randint(1, 10)
            len_1 = random.randint(1, 10)
            udp_port = random.randint(40000, 50000)
            secret_a = random.randint(1, 100)
            state[data[3]] = (num, len_1, udp_port, secret_a)
            t1 = threading.Thread(target=stage_2, args=(udp_port,))
            t1.start()
            MESSAGE = struct.pack('!IIHHIIII', 16, data[1], 2, data[3], num, len_1, udp_port, secret_a)
            socket.sendto(MESSAGE, self.client_address)

        except Exception as ex:
            print(type(ex))
            print(ex)
            socket.close()
            return


class MyStageBHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        print(data)
        socket = self.request[1]
        try:
            rand = random.random()
            if rand < 0.5:
                return
            header = struct.unpack('!IIHH', data[:11])
            print(header)
        except:
            socket.close()


def stage_2(port):
    server_2 = socketserver.UDPServer((HOST, port), MyStageBHandler)
    server_2.serve_forever()


if __name__ == "__main__":

    HOST, PORT = "localhost", 12235
    server = socketserver.UDPServer((HOST, PORT), MyUDPHandler)
    server.serve_forever()
