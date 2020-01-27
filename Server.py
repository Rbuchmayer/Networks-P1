import socketserver
import struct
import random
import threading

state = {}
tcp_to_id = {}


class MyStageAHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        try:
            socket.settimeout(3)
            data = struct.unpack('!IIHH11sx', data)
            if data[0] != len(data[4]) + 1 or data[1] != 0 or data[2] != 1 or data[4].decode('ascii') != 'hello world':
                socket.close()
                return
            num = random.randint(20, 30)
            len_1 = random.randint(1, 10)
            udp_port = random.randint(40000, 50000)
            secret_a = random.randint(1, 100)
            state[data[3]] = {'num_1' : num, 'len_1' : len_1, 'udp_port' : udp_port, 'secret_a' : secret_a, 'expected_packet' : 0}
            MESSAGE = struct.pack('!IIHHIIII', 16, data[1], 2, data[3], num, len_1, udp_port, secret_a)
            socket.sendto(MESSAGE, self.client_address)
            stage_2(udp_port)

        except Exception as ex:
            socket.close()
            return


class MyStageBHandler(socketserver.BaseRequestHandler):


    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        try:
            socket.settimeout(3)
            # decide to acknowledge
            rand = random.random()
            if rand < 0.5:
                header = struct.unpack('!IIHH', data[:12])
                payload_len = header[0]
                psecret = header[1]
                secret_a = state[header[3]]['secret_a']
                pad = ''

                for i in range(0, (payload_len - 4) + (4 - (payload_len % 4))):
                    pad += 'x'

                payload_plus_id = struct.unpack('!I' + pad, data[12:])
                expected_packet = state[header[3]]['expected_packet']
                expectecd_data = [0 for _ in range(len(data[16:]))]
                unpacked_data = [b for b in data[16:]]

                if payload_plus_id[0] == expected_packet and psecret == secret_a \
                        and len(data[12:]) == header[0] + (4 - (header[0] % 4)) and expectecd_data == unpacked_data:

                    MESSAGE = struct.pack('!IIHHI', 4, psecret, 2, header[3], payload_plus_id[0])
                    socket.sendto(MESSAGE, self.client_address)
                    state[header[3]]['expected_packet'] += 1
                    # check if last packet
                    if state[header[3]]['expected_packet'] == state[header[3]]['num_1']:
                        tcp_port = random.randint(40000, 50000)
                        secret_b = random.randint(1, 100)
                        state[header[3]]['secret_b'] = secret_b
                        tcp_to_id[tcp_port] = header[3]
                        # send next stage info
                        MESSAGE = struct.pack('!IIHHII', 8, psecret, 2, header[3], tcp_port, secret_b)
                        socket.sendto(MESSAGE, self.client_address)
                        stage_3(tcp_port)

        except:
            socket.close()


class MyStageCHandler(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            self.request.settimeout(3)
            secret_c = random.randint(1, 100)
            student_id = tcp_to_id[self.request.getsockname()[1]]
            secret_b = state[student_id]['secret_b']

            num_2 = random.randint(1, 10)
            len_2 = random.randint(1, 10)
            c = random.randint(1, 100)
            MESSAGE = struct.pack('!IIHHIIIBxxx', 13, secret_b, 2, student_id, num_2, len_2, secret_c, c)
            self.request.sendto(MESSAGE, self.client_address)
            pad = ''
            for _ in range(0, (4 - (len_2 % 4))):
                pad += 'x'
            buffer = 12 + len_2 + len(pad)
            for _ in range(0, num_2):
                data = self.request.recv(buffer).strip()
                header = struct.unpack('!IIHH' + str(len_2) + 's' + pad, data)
                expected_data = [c for _ in range(len_2)]
                unpacked_data = [b for b in header[4]]
                if header[1] != secret_c or len(header[4]) != header[0] or unpacked_data != expected_data:
                    self.request.close()
            secret_d = random.randint(1, 100)
            MESSAGE = struct.pack('!IIHHI', 4, secret_c, 2, student_id, secret_d)
            self.request.sendto(MESSAGE, self.client_address)
            del state[student_id]
        except Exception as e:
            print(e)
            self.request.close()


def stage_2(port):
    server_2 = socketserver.ThreadingUDPServer((HOST, port), MyStageBHandler)
    server_2_thread = threading.Thread(target=server_2.serve_forever())
    server_2_thread.daemon = True
    server_2_thread.start()


def stage_3(tcp_port):
    server_3 = socketserver.ThreadingTCPServer((HOST, tcp_port), MyStageCHandler, bind_and_activate=True)
    server3_thread = threading.Thread(target=server_3.serve_forever())
    server3_thread.daemon = True
    server3_thread.start()


if __name__ == "__main__":
    HOST, PORT = 'localhost', 12235
    server = socketserver.ThreadingUDPServer((HOST, PORT), MyStageAHandler)
    server_thread = threading.Thread(target=server.serve_forever())
    server_thread.daemon = True
    server_thread.start()
