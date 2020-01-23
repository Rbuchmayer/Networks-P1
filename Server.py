import socketserver
import struct
import random

state = {}
state['next_to_ack'] = 0


class MyStageAHandler(socketserver.BaseRequestHandler):
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
            MESSAGE = struct.pack('!IIHHIIII', 16, data[1], 2, data[3], num, len_1, udp_port, secret_a)
            socket.sendto(MESSAGE, self.client_address)
            socket.close()

            state['num_packets'] = num
            stage_2(udp_port)

        except Exception as ex:
            print(type(ex))
            print(ex)
            socket.close()
            return


class MyStageBHandler(socketserver.BaseRequestHandler):
    current_packet_id = 0
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        try:
            # decide to acknowledge
            rand = random.random()
            if rand < 0.5:
                header = struct.unpack('!IIHH', data[:12])
                payload_len = header[0]
                psecret = header[1]
                secret_a = state[header[3]][3]
                pad = ''
                for i in range(0, (payload_len - 4) + (4 - (payload_len % 4))):
                    pad += 'x'

                payload_plus_id = struct.unpack('!I' + pad, data[12:])

                if payload_plus_id[0] == state['next_to_ack'] and psecret == secret_a \
                        and len(data[12:]) == header[0] + (4 - (header[0] % 4)):

                    MESSAGE = struct.pack('!IIHHI', 4, psecret, 2, header[3], payload_plus_id[0])
                    socket.sendto(MESSAGE, self.client_address)
                    state['next_to_ack'] = state['next_to_ack'] + 1

                    # check if last packet
                    if state['next_to_ack'] == state['num_packets']:
                        tcp_port = random.randint(40000, 50000)
                        secret_b = random.randint(1, 100)
                        state[header[3]] = (tcp_port, secret_b)

                        # send next stage info
                        MESSAGE = struct.pack('!IIHHII', 8, psecret, 2, header[3], tcp_port, secret_b)
                        socket.sendto(MESSAGE, self.client_address)
                        socket.close()


        except:
            socket.close()


class MyStageCHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        try:
            secret_c = random.randint(1, 100)
            secret_b = random.randint(1, 100)
            student_id = 5
            num_2 = random.randint(1, 10)
            len_2 = random.randint(1, 10)
            c = chr(random.randint(1, 100))
            MESSAGE = struct.pack('!IIHHIIIBxxx', 13, secret_b, 2, student_id, num_2, len_2, secret_c, c)
            socket.sendto(MESSAGE, self.client_address)
        except:
            socket.close()


def stage_2(port):
    server_2 = socketserver.UDPServer((HOST, port), MyStageBHandler)
    server_2.serve_forever()


def stage_3(tcp_port):
    server_3 = socketserver.TCPServer((HOST, tcp_port), MyStageCHandler, bind_and_activate=True)
    server_3.serve_forever()


if __name__ == "__main__":

    HOST, PORT = "localhost", 12235
    server = socketserver.UDPServer((HOST, PORT), MyStageAHandler)
    server.serve_forever()
