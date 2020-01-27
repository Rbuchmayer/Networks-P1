import socket
import struct
import sys

# Stage a

IP = 'attu2.cs.washington.edu'
if len(sys.argv) > 1 and sys.argv[1] == '-local':
    IP = 'localhost'

UDP_PORT = 12235
ID = 495
MESSAGE = struct.pack('!IIHH11sx', 12, 0, 1, ID, bytes('hello world', 'ascii'))

# send UDP to server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(0.5)
sock.sendto(MESSAGE, (IP, UDP_PORT))

# receive UDP from server
data_a, addr = sock.recvfrom(28) # buffer size is 28 bytes
data_a = struct.unpack('!IIHHIIII', data_a)

# Stage b
num = data_a[4]
len = data_a[5]
udp_port = data_a[6]
secret_a = data_a[7]
print(num)
for i in range(0, num):
    print(i)
    pad = ''
    for _ in range(0, len + (4 - (len % 4))):
        pad += 'x'
    MESSAGE = struct.pack('!IIHHI' + pad, len+4, secret_a, 1, ID, i)

    while True:
        try:
            sock.sendto(MESSAGE, (IP, udp_port))
            print('waiting to recieve')
            data_ack, addr = sock.recvfrom(16)
            break
        except:
            continue


# b2
data_b2, addr = sock.recvfrom(20)
data_b2 = struct.unpack('!IIHHII', data_b2)
tcp_port = data_b2[4]
secret_b = data_b2[5]
sock.close()

# Stage C
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.connect((IP, tcp_port))
data_c2, addr = tcp_socket.recvfrom(28)
data_c2 = struct.unpack('!IIHHIIIBxxx', data_c2)
num_2 = data_c2[4]
len_2 = data_c2[5]
secret_c = data_c2[6]
c = data_c2[7]

# Stage D
for i in range(0, num_2):
    pad = ''
    payload = ''
    for _ in range(0, (4 - (len_2 % 4))):
        pad += 'x'

    for _ in range(0, len_2):
        payload += chr(c)

    MESSAGE = struct.pack('!IIHH' + str(len_2) + 's' + pad, len_2, secret_c, 1, ID, bytes(payload, 'ascii'))
    tcp_socket.sendto(MESSAGE, (IP, tcp_port))

# d2
data_d2, addr_d2 = tcp_socket.recvfrom(16)
data_d2 = struct.unpack('!IIHHI', data_d2)
secret_d = data_d2[4]
tcp_socket.close()
print(secret_a)
print(secret_b)
print(secret_c)
print(secret_d)
